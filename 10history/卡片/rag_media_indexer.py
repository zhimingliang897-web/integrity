#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import base64
import csv
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dateutil import parser as dtparser
from PIL import Image, ExifTags
from tqdm import tqdm
from openai import OpenAI


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}  # HEIC/HEIF 若本机 PIL 不支持会跳过
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm"}


# ----------------------------- utils -----------------------------

def sha1_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def safe_relpath(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception:
        return default


def dump_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), "utf-8")


def guess_mime(path: Path) -> str:
    mt, _ = mimetypes.guess_type(str(path))
    if mt:
        return mt
    # fallback
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if path.suffix.lower() == ".png":
        return "image/png"
    if path.suffix.lower() == ".webp":
        return "image/webp"
    if path.suffix.lower() in VIDEO_EXTS:
        return "video/mp4"
    return "application/octet-stream"


def parse_date_from_folder_name(name: str) -> Optional[str]:
    """
    支持：YYYY-MM-DD / YYYY_MM_DD / YYYYMMDD / 2026-01-15 something
    返回 YYYY-MM-DD 或 None
    """
    m = re.search(r"(\d{4})[-_]?(\d{2})[-_]?(\d{2})", name)
    if not m:
        return None
    y, mo, d = m.group(1), m.group(2), m.group(3)
    try:
        datetime(int(y), int(mo), int(d))
        return f"{y}-{mo}-{d}"
    except Exception:
        return None


def exif_datetime_original(img: Image.Image) -> Optional[datetime]:
    try:
        exif = img._getexif()
        if not exif:
            return None
        # map tags
        tag_map = {ExifTags.TAGS.get(k, str(k)): v for k, v in exif.items()}
        for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
            if key in tag_map:
                # common format: "2023:08:19 12:34:56"
                val = str(tag_map[key]).strip()
                val = val.replace(":", "-", 2)  # only first two colons in date portion
                return dtparser.parse(val)
    except Exception:
        return None
    return None


def file_mtime_dt(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime)


def resize_to_jpeg_bytes(image_path: Path, max_side: int = 1024, quality: int = 85) -> bytes:
    """
    统一转为 JPEG，降低体积，避免 base64 超限/烧 tokens。
    """
    with Image.open(image_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = min(max_side / max(w, h), 1.0)
        if scale < 1.0:
            im = im.resize((int(w * scale), int(h * scale)))
        from io import BytesIO
        buf = BytesIO()
        im.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()


def data_url_from_bytes(mime: str, b: bytes) -> str:
    return f"data:{mime};base64,{base64.b64encode(b).decode('utf-8')}"


def ffmpeg_exists() -> bool:
    return shutil.which("ffmpeg") is not None


def extract_video_frames(video_path: Path, out_dir: Path, fps: float = 0.5, max_frames: int = 12) -> List[Path]:
    """
    用 ffmpeg 抽帧：默认 0.5 fps => 每 2 秒 1 帧；最多 max_frames 帧。
    """
    ensure_dir(out_dir)
    # 先清空
    for p in out_dir.glob("frame_*.jpg"):
        try:
            p.unlink()
        except Exception:
            pass

    # -vf fps=... 抽帧
    # 通过 -frames:v 限制帧数
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-i", str(video_path),
        "-vf", f"fps={fps}",
        "-frames:v", str(max_frames),
        str(out_dir / "frame_%03d.jpg")
    ]
    subprocess.run(cmd, check=False)

    frames = sorted(out_dir.glob("frame_*.jpg"))
    return frames


# ----------------------------- model calls -----------------------------

def get_client(api_key: str, base_url: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url=base_url)


def robust_json_load(s: str) -> Dict[str, Any]:
    """
    尽量从输出里抠出 JSON（应对模型偶尔多说一句）
    """
    s = s.strip()
    try:
        return json.loads(s)
    except Exception:
        pass
    # find first {...} block
    m = re.search(r"\{.*\}", s, re.S)
    if m:
        return json.loads(m.group(0))
    raise ValueError("Model output is not valid JSON.")


def chat_json(client: OpenAI, model: str, messages: List[Dict[str, Any]],
              max_tokens: int = 900, temperature: float = 0.2) -> Dict[str, Any]:
    """
    使用结构化输出：response_format json_object
    注意：提示词必须包含“json”字样（平台常见要求）
    """
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    return robust_json_load(content)


# ----------------------------- prompts -----------------------------

SYSTEM_PROMPT = (
    "你是我的个人生活档案管理员。你的任务是把图片/视频内容整理成可检索的目录卡。"
    "要求：只基于可见内容推断；不确定就写“未知/不确定”；不要编造具体人名、地址、商家名。"
    "输出必须是严格 JSON（json 对象），不要输出任何额外文字。"
)

IMAGE_USER_PROMPT = (
    "请为这张图片生成一张目录卡（json）：\n"
    "字段：\n"
    "asset_id: string（来自输入）\n"
    "datetime: string（尽量用输入时间；不确定可留空）\n"
    "caption: string（1 句中文，20~35字）\n"
    "tags: string[]（5~15 个稳定标签，偏“场景/活动/内容/时间感”）\n"
    "where_hint: string（室内/室外/交通工具/餐厅/家/办公室等，无法判断写未知）\n"
    "people_count: string（0/1/2/多人/不确定）\n"
    "sensitivity: string（normal/private/secret；证件、隐私屏幕、儿童清晰正脸等更敏感）\n"
    "notable_objects: string[]（3~10 个关键物体或要素）\n"
    "importance: integer（1~5，纪念程度/未来检索价值）\n"
    "event_hint: string（这张图可能属于什么事件：如聚餐/旅行/通勤/会议/居家等）\n"
    "query_suggestions: string[]（6 条，未来我可能会怎么搜它）\n"
    "约束：输出严格 json。"
)

VIDEO_USER_PROMPT = (
    "这些是同一段视频抽取的关键帧序列。请为这段视频生成目录卡（json）：\n"
    "字段：\n"
    "asset_id: string（来自输入）\n"
    "datetime: string（尽量用输入时间；不确定可留空）\n"
    "caption: string（1 句中文，描述视频主要内容）\n"
    "tags: string[]（8~18 个）\n"
    "where_hint: string\n"
    "people_count: string\n"
    "sensitivity: string（normal/private/secret）\n"
    "notable_objects: string[]（5~12 个）\n"
    "importance: integer（1~5）\n"
    "event_hint: string\n"
    "highlights: string[]（3~6 条，描述视频亮点/动作）\n"
    "query_suggestions: string[]（8 条）\n"
    "约束：输出严格 json。"
)

DAY_CLUSTER_PROMPT = (
    "下面是同一天的一组素材目录卡（按时间顺序）。请把它们分成 2~6 个事件簇（json）。\n"
    "输出字段：\n"
    "date: string（YYYY-MM-DD）\n"
    "events: object[]，每个事件包含：\n"
    "  event_id: string（如 e1,e2...）\n"
    "  title: string（10 字以内）\n"
    "  summary: string（3~5 句中文）\n"
    "  tags: string[]（5~12 个）\n"
    "  asset_ids: string[]（属于此事件的 asset_id）\n"
    "  best_assets: string[]（精选 3~10 个 asset_id）\n"
    "day_summary: string（像日记一样 4~8 句，总结当天）\n"
    "约束：严格 json；不要编造具体地点人名；不确定就写“未知”。"
)


# ----------------------------- pipeline -----------------------------

@dataclass
class Settings:
    root: Path
    out: Path
    base_url: str
    api_key: str
    vl_model: str
    text_model: str
    max_side: int
    jpeg_quality: int
    video_fps: float
    video_max_frames: int
    max_tokens_asset: int
    max_tokens_day: int

def scan_date_folders(month_root: Path) -> List[Path]:
    """
    兼容两种结构：
    1) root 下有日期子文件夹：2026-01-01/ ...
    2) root 就是最小单位：root 里直接放图片/视频（此时返回 [root]）
    """
    subs = [p for p in month_root.iterdir() if p.is_dir()]
    subs.sort(key=lambda p: p.name)

    # 若存在日期子文件夹，只处理这些
    date_subs = [p for p in subs if parse_date_from_folder_name(p.name)]
    if date_subs:
        return date_subs

    # 否则：root 里直接是文件，就把 root 当作一个“合集目录”
    return [month_root]


def asset_id_for_file(relpath: str, sha1: str) -> str:
    # 保持稳定：路径+hash 截断
    return f"{relpath}#{sha1[:10]}"


def make_image_card(client: OpenAI, st: Settings, asset_id: str, dt_str: str, img_path: Path) -> Dict[str, Any]:
    jpeg_bytes = resize_to_jpeg_bytes(img_path, max_side=st.max_side, quality=st.jpeg_quality)
    data_url = data_url_from_bytes("image/jpeg", jpeg_bytes)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": data_url}},
            {"type": "text", "text": f"{IMAGE_USER_PROMPT}\nasset_id={asset_id}\ndatetime_input={dt_str}\n"}
        ]}
    ]
    obj = chat_json(client, st.vl_model, messages, max_tokens=st.max_tokens_asset)
    # 补齐关键字段
    obj.setdefault("asset_id", asset_id)
    obj.setdefault("datetime", dt_str)
    obj["kind"] = "image"
    return obj


def make_video_card_from_frames(client: OpenAI, st: Settings, asset_id: str, dt_str: str,
                                frames: List[Path]) -> Dict[str, Any]:
    # frames => data urls
    urls: List[str] = []
    for fp in frames:
        try:
            b = fp.read_bytes()
            urls.append(data_url_from_bytes("image/jpeg", b))
        except Exception:
            continue

    # OpenAI compatible: type=video, video=[data:image/jpeg;base64,...]  :contentReference[oaicite:3]{index=3}
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [
            {"type": "video", "video": urls},
            {"type": "text", "text": f"{VIDEO_USER_PROMPT}\nasset_id={asset_id}\ndatetime_input={dt_str}\n"}
        ]}
    ]
    obj = chat_json(client, st.vl_model, messages, max_tokens=st.max_tokens_asset)
    obj.setdefault("asset_id", asset_id)
    obj.setdefault("datetime", dt_str)
    obj["kind"] = "video"
    obj["frame_count_used"] = len(urls)
    return obj


def make_day_clusters(client: OpenAI, st: Settings, date_str: str, cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    # 给模型的输入尽量精简，避免烧 tokens
    slim = []
    for c in cards:
        slim.append({
            "asset_id": c.get("asset_id", ""),
            "datetime": c.get("datetime", ""),
            "caption": c.get("caption", ""),
            "tags": c.get("tags", []),
            "event_hint": c.get("event_hint", "")
        })

    messages = [
        {"role": "system", "content": "你是我的生活相册编辑。输出严格 json。"},
        {"role": "user", "content": f"{DAY_CLUSTER_PROMPT}\nDATE={date_str}\nCARDS_JSON={json.dumps(slim, ensure_ascii=False)}"}
    ]
    # B 档可以用 text_model（更省钱），也可以直接用 vl_model
    obj = chat_json(client, st.text_model, messages, max_tokens=st.max_tokens_day, temperature=0.1)
    obj.setdefault("date", date_str)
    return obj


def main():
    ap = argparse.ArgumentParser(description="Build personal RAG index from month folder (A+B).")
    ap.add_argument("--root", required=True, help="月份根目录（里面是按日期的子文件夹）")
    ap.add_argument("--out", default="./rag_out", help="输出目录")
    ap.add_argument("--base_url", default="https://dashscope.aliyuncs.com/compatible-mode/v1",
                help="Model Studio OpenAI-compatible base_url")

    ap.add_argument("--vl_model", default="qwen-vl-max-2025-08-13", help="视觉模型")
    ap.add_argument("--text_model", default="qwen-vl-max-2025-08-13",
                    help="做日内事件聚类的模型（可改成更便宜的 qwen-max / qwen-plus 等）")
    ap.add_argument("--max_side", type=int, default=1024, help="图片最长边压缩到多少像素")
    ap.add_argument("--jpeg_quality", type=int, default=85, help="JPEG 压缩质量")
    ap.add_argument("--video_fps", type=float, default=0.5, help="视频抽帧 fps（0.5 = 每2秒一帧）")
    ap.add_argument("--video_max_frames", type=int, default=12, help="每段视频最多用多少帧")
    ap.add_argument("--max_tokens_asset", type=int, default=900, help="每个素材目录卡输出 token 上限")
    ap.add_argument("--max_tokens_day", type=int, default=1200, help="每天聚类输出 token 上限")
    args = ap.parse_args()

    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("请先设置环境变量 DASHSCOPE_API_KEY")

    st = Settings(
        root=Path(args.root).expanduser().resolve(),
        out=Path(args.out).expanduser().resolve(),
        base_url=args.base_url,
        api_key=api_key,
        vl_model=args.vl_model,
        text_model=args.text_model,
        max_side=args.max_side,
        jpeg_quality=args.jpeg_quality,
        video_fps=args.video_fps,
        video_max_frames=args.video_max_frames,
        max_tokens_asset=args.max_tokens_asset,
        max_tokens_day=args.max_tokens_day,
    )

    ensure_dir(st.out)
    cards_path = st.out / "asset_cards.jsonl"
    day_path = st.out / "day_events.jsonl"
    csv_path = st.out / "index.csv"
    summaries_dir = st.out / "day_summaries"
    ensure_dir(summaries_dir)

    state_path = st.out / "state.json"
    state = load_json(state_path, default={"done": {}})  # relpath -> sha1
    done: Dict[str, str] = state.get("done", {})

    client = get_client(st.api_key, st.base_url)

    date_folders = scan_date_folders(st.root)
    if not date_folders:
        raise SystemExit(f"没找到日期子文件夹：{st.root}")

    # 用于快速重复判定
    seen_sha1: Dict[str, str] = {}  # sha1 -> asset_id

    # 先收集全部 cards（按天组织）
    cards_by_date: Dict[str, List[Dict[str, Any]]] = {}

    # 输出文件先创建（追加模式）
    cards_f = cards_path.open("a", encoding="utf-8")

    try:
        for ddir in tqdm(date_folders, desc="Scanning date folders"):
            date_str = parse_date_from_folder_name(ddir.name) or ddir.name
            files = [p for p in ddir.rglob("*") if p.is_file()]
            files.sort(key=lambda p: p.name)

            for fp in tqdm(files, desc=f"{ddir.name}", leave=False):
                ext = fp.suffix.lower()
                if ext not in IMAGE_EXTS and ext not in VIDEO_EXTS:
                    continue

                rel = safe_relpath(fp, st.root)
                sha1 = sha1_file(fp)

                # 已处理跳过
                if done.get(rel) == sha1:
                    continue

                asset_id = asset_id_for_file(rel, sha1)
                duplicate_suspect_of = seen_sha1.get(sha1)
                seen_sha1[sha1] = asset_id

                # datetime：优先 EXIF，其次文件 mtime；date folder 也会传给模型当参考
                dt_obj: Optional[datetime] = None
                if ext in IMAGE_EXTS:
                    try:
                        with Image.open(fp) as im:
                            dt_obj = exif_datetime_original(im)
                    except Exception:
                        dt_obj = None
                if dt_obj is None:
                    dt_obj = file_mtime_dt(fp)
                dt_str = dt_obj.isoformat(timespec="seconds")

                try:
                    if ext in IMAGE_EXTS:
                        card = make_image_card(client, st, asset_id, dt_str, fp)
                    else:
                        # 视频：抽帧 -> frames 输入
                        if not ffmpeg_exists():
                            print("警告：未检测到 ffmpeg，跳过视频：", rel)
                            continue
                        with tempfile.TemporaryDirectory() as td:
                            frames_dir = Path(td)
                            frames = extract_video_frames(fp, frames_dir, fps=st.video_fps, max_frames=st.video_max_frames)
                            if not frames:
                                print("警告：抽帧失败，跳过视频：", rel)
                                continue
                            card = make_video_card_from_frames(client, st, asset_id, dt_str, frames)

                    # 加一些本地字段
                    card["file_relpath"] = rel
                    card["sha1"] = sha1
                    card["date_folder"] = date_str
                    if duplicate_suspect_of:
                        card["duplicate_suspect_of"] = duplicate_suspect_of

                    # 写入 jsonl
                    cards_f.write(json.dumps(card, ensure_ascii=False) + "\n")
                    cards_f.flush()

                    # 归档到当天
                    cards_by_date.setdefault(date_str, []).append(card)

                    # 标记 done
                    done[rel] = sha1
                    state["done"] = done
                    dump_json(state_path, state)

                except Exception as e:
                    print(f"\n处理失败：{rel}\n原因：{e}\n")

    finally:
        cards_f.close()

    # B：按天聚类 + 生成 day_summary.md
    day_f = day_path.open("a", encoding="utf-8")
    try:
        for date_str, cards in tqdm(sorted(cards_by_date.items()), desc="Day clustering"):
            # 按 datetime 排序
            cards.sort(key=lambda c: c.get("datetime", ""))

            # 少于 3 个素材就不强行分事件
            if len(cards) < 3:
                simple = {
                    "date": date_str,
                    "events": [{
                        "event_id": "e1",
                        "title": "零散记录",
                        "summary": "当天素材数量较少，未细分事件。",
                        "tags": list({t for c in cards for t in (c.get("tags") or [])})[:12],
                        "asset_ids": [c.get("asset_id") for c in cards if c.get("asset_id")],
                        "best_assets": [c.get("asset_id") for c in cards if c.get("asset_id")][: min(5, len(cards))]
                    }],
                    "day_summary": "当天记录较少。"
                }
                day_obj = simple
            else:
                day_obj = make_day_clusters(client, st, date_str, cards)

            day_f.write(json.dumps(day_obj, ensure_ascii=False) + "\n")
            day_f.flush()

            # markdown 日记摘要
            md = [f"# {date_str} 日记摘要\n"]
            md.append(day_obj.get("day_summary", "").strip() + "\n\n")
            md.append("## 事件\n")
            for ev in day_obj.get("events", []):
                md.append(f"### {ev.get('title','(无题)')}\n")
                md.append((ev.get("summary", "") or "").strip() + "\n\n")
                if ev.get("tags"):
                    md.append("标签： " + "、".join(ev["tags"]) + "\n\n")
                if ev.get("best_assets"):
                    md.append("精选：\n")
                    for aid in ev["best_assets"]:
                        md.append(f"- {aid}\n")
                    md.append("\n")

            (summaries_dir / f"{date_str}.md").write_text("".join(md), "utf-8")

    finally:
        day_f.close()

    # 生成 CSV 索引（从 jsonl 回读更稳）
    rows: List[Dict[str, Any]] = []
    with cards_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass

    # 写 CSV
    fieldnames = [
        "date_folder", "datetime", "kind", "file_relpath", "asset_id",
        "caption", "where_hint", "people_count", "sensitivity",
        "importance", "tags", "notable_objects", "event_hint",
        "duplicate_suspect_of"
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            out = {k: r.get(k, "") for k in fieldnames}
            # list 字段展开为 | 分隔
            for lk in ("tags", "notable_objects"):
                if isinstance(out.get(lk), list):
                    out[lk] = "|".join([str(x) for x in out[lk]])
            w.writerow(out)

    print("\n完成 ✅")
    print("输出：")
    print(" -", cards_path)
    print(" -", day_path)
    print(" -", csv_path)
    print(" -", summaries_dir)


if __name__ == "__main__":
    main()
