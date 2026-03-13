"""
LLM formatter - 将文章转为小红书图文结构
"""
import json
import re
import os
from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL, MAX_SLIDES, TIMEOUT_SEC

_client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=TIMEOUT_SEC)

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
_SKILL_PATH = os.path.join(_PROJECT_ROOT, "毒舌skill.md")


def _load_skill_prompt() -> str:
    try:
        with open(_SKILL_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


_SKILL_PROMPT = _load_skill_prompt()

_SKILL_SECTION = (
    "## 毒舌人设参考（必须遵守“绝对严谨”）\n" + _SKILL_PROMPT
    if _SKILL_PROMPT
    else ""
)

SYSTEM_PROMPT = f"""你是一个做技术科普的朋友，把干货文章改写成有态度的小红书图文。

## 核心目标
**科普祛魅**：讲清楚技术概念，帮读者少踩坑，同时有点态度、不无聊。

## 你的风格
- **毒舌但专业**：嘴毒是外衣，专业是内核。可以刻薄，但不能胡说。
- **先结论再解释**：每个观点先给结论，再用一句人话解释 + 一个小例子/对比。
- **算账祛魅**：能给数字/成本/时间就给，不能就写“大概/通常”。
- **读起来像朋友吐槽**：短句、口语，但别堆网络黑话。

## 语言风格示例
❌ 太书面：
"各大云平台已具备一键部署能力，但当时压着不推广"

❌ 太黑话（为了毒舌而说错）：
"云平台早就能一键装了，装什么装，无利不起早呗"

✅ 刚刚好（有态度但准确）：
"云平台早就能一键部署，但之前没大力推——没利可图罢了"

❌ 太干：
"Token消耗是普通对话的30倍"

❌ 太花（黑话堆砌）：
"一个任务烧掉30倍Token，说白了就是赛博碎钞机"

✅ 刚刚好（有态度+准确）：
"一个任务烧30倍Token，成本是普通对话30倍，贵得离谱"

## 写作规则
- 技术术语后面跟一句人话解释
- 俚语/网络用语每段最多1个，不堆砌
- 毒舌是为了强调真相，不是为了装
- 每句话20字以内更好
- 有数据给数据，没数据说"大概"
- 每一页必须同时满足：**1个解释块（normal/note）+ 1个核心真相（key）+ 1个避坑吐槽（bad）+ 1个可执行建议（good）**

## 输出结构
生成 4-{MAX_SLIDES} 张图片，每张包含：
- title: 标题（8-12字，点明核心，可以有点态度）
- content: **优先5个**内容区块（信息密度更像成品），最多6个，最少4个

## 区块类型（保持视觉层次）
1. **normal** - 背景铺垫（白色背景）
2. **key** - 核心真相，label用"说白了"、"真相是"（浅黄背景）
3. **bad** - 吐槽/避坑，label用"醒醒"、"别傻了"（浅红背景）
4. **good** - 实用建议，label用"抄作业"、"正经建议"（浅绿背景）
5. **note** - 补充/彩蛋，label用"多嘴一句"、"懂的都懂"（浅蓝背景）

## 输出格式（严格JSON）
{{
  "cover_title": "封面标题（8-12字，含核心关键词，有态度）",
  "slides": [
    {{
      "title": "标题",
      "content": [
        {{"type": "normal", "text": "铺垫内容..."}},
        {{"type": "key", "label": "说白了", "text": "核心真相"}},
        {{"type": "bad", "label": "醒醒", "text": "吐槽/避坑"}},
        {{"type": "good", "label": "抄作业", "text": "实用建议"}},
        {{"type": "note", "label": "多嘴一句", "text": "补充信息"}}
      ]
    }}
  ]
}}

## 禁止
- 技术错误、为了吐槽而说错话
- 网络黑话堆砌（赛博XX、数字XX连续出现）
- 书面语、官腔
- "评论区见"等引流话术
- tag标签、emoji
- 每页少于4个区块

{_SKILL_SECTION}
"""


def _extract_json(raw_output: str) -> dict:
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if not json_match:
            raise ValueError(f"无法解析JSON: {raw_output[:300]}")
        return json.loads(json_match.group(0))


def _normalize_and_validate(data: dict) -> tuple[dict, list[str]]:
    """轻量校验+规范化；严重不合格交给 LLM 修复。"""
    errors: list[str] = []
    slides = data.get("slides")
    if not isinstance(slides, list) or not slides:
        return {"cover_title": data.get("cover_title", ""), "slides": []}, ["slides缺失或为空"]

    # 页数限制
    if MAX_SLIDES and isinstance(MAX_SLIDES, int) and len(slides) > MAX_SLIDES:
        slides = slides[:MAX_SLIDES]

    normalized_slides: list[dict] = []
    for idx, s in enumerate(slides, 1):
        if not isinstance(s, dict):
            errors.append(f"第{idx}页不是对象")
            continue
        title = s.get("title", "") if isinstance(s.get("title", ""), str) else ""
        content = s.get("content", [])
        if not isinstance(content, list):
            errors.append(f"第{idx}页content不是数组")
            content = []

        # 清理无效块、裁剪到 6
        blocks: list[dict] = []
        for blk in content:
            if isinstance(blk, str):
                blk = {"type": "normal", "text": blk}
            if not isinstance(blk, dict):
                continue
            text = blk.get("text", "")
            if not isinstance(text, str) or not text.strip():
                continue
            btype = blk.get("type", "normal")
            if btype not in {"normal", "key", "bad", "good", "note"}:
                btype = "normal"
            item = {"type": btype, "text": text.strip()}
            if btype != "normal":
                label = blk.get("label", "")
                if isinstance(label, str) and label.strip():
                    item["label"] = label.strip()
            blocks.append(item)
            if len(blocks) >= 6:
                break

        if len(blocks) < 4:
            errors.append(f"第{idx}页区块少于4个({len(blocks)})")

        types = {b.get("type") for b in blocks}
        if "key" not in types:
            errors.append(f"第{idx}页缺少key块")
        if "bad" not in types:
            errors.append(f"第{idx}页缺少bad块")
        if "good" not in types:
            errors.append(f"第{idx}页缺少good块")
        if not (("normal" in types) or ("note" in types)):
            errors.append(f"第{idx}页缺少解释块(normal/note)")

        normalized_slides.append({"title": title, "content": blocks})

    cover_title = data.get("cover_title", "")
    cover_title = cover_title if isinstance(cover_title, str) else ""
    return {"cover_title": cover_title.strip(), "slides": normalized_slides}, errors


def _repair_with_llm(raw_text: str, bad_json: dict, reasons: list[str]) -> dict:
    """让模型按硬规则修复输出（一次重排）。"""
    response = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "你上一次的输出不符合硬规则，请修复并只输出严格JSON。\n"
                    f"不合格原因：{'; '.join(reasons)[:800]}\n\n"
                    "硬规则：\n"
                    "- slides 为数组，4-" + str(MAX_SLIDES) + "页（若MAX_SLIDES为空则4-6页）\n"
                    "- 每页content **4-6块，优先5块**\n"
                    "- 每页必须包含：key、bad、good、以及解释块(normal或note)\n"
                    "- 句子短、口语、毒舌但准确；结论后跟一句人话解释+小例子/对比\n\n"
                    "原文章：\n"
                    f"{raw_text[:6000]}\n\n"
                    "你上一次的JSON（供你修复，不要照抄错误）：\n"
                    f"{json.dumps(bad_json, ensure_ascii=False)[:6000]}"
                ),
            },
        ],
        temperature=0.4,
        response_format={"type": "json_object"},
    )
    return _extract_json(response.choices[0].message.content.strip())


def format_text_to_slides(raw_text: str) -> dict:
    """调用LLM将文章转为slides，返回包含slides和cover_title的字典"""
    print(f"⏳ 调用 {MODEL}...")

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"把这篇文章改写成小红书图文，每页必须4-6个区块，输出JSON：\n\n{raw_text}"},
        ],
        temperature=0.6,
        response_format={"type": "json_object"},
    )

    raw_output = response.choices[0].message.content.strip()
    data = _extract_json(raw_output)

    normalized, errors = _normalize_and_validate(data)
    if errors:
        print(f"  ⚠️ 输出需修复：{'; '.join(errors)[:200]}")
        try:
            repaired = _repair_with_llm(raw_text, data, errors)
            normalized2, errors2 = _normalize_and_validate(repaired)
            if errors2:
                print(f"  ⚠️ 修复后仍不完美：{'; '.join(errors2)[:200]}")
            normalized = normalized2 if normalized2.get("slides") else normalized
        except Exception as e:
            print(f"  ⚠️ 修复失败，使用原输出（可能略空/不齐）：{e}")

    cover_title = normalized.get("cover_title", "")
    if cover_title:
        print(f"📌 封面标题：{cover_title}")

    return normalized

PLAIN_PROMPT = """你是一个技术博主，把文章改写成纯干货、易读的科普版本。

## 核心目标
把复杂概念讲清楚，让小白能看懂，让老手不觉得废话。

## 风格
- 纯干货：不说废话，每句都有信息量
- 大白话：技术术语后面紧跟人话解释
- 结构清晰：分点、分段，层次分明
- 无黑话：不用"赛博"、"韭菜"等网络用语

## 输出格式
生成一份简洁的科普摘要，包含：
1. 一句话总结（20字内）
2. 3-5个核心要点（每点2-3句话）
3. 实用建议（2-3条具体可操作的建议）

## 格式示例
一句话总结：
大模型是文本引擎，智能体是长了手脚的数字助手。

核心要点：
1. 大模型只是纯文本引擎，懂逻辑但没手脚，必须配合工具才能干活
2. 网页端套了工具调用外壳，能联网能画图，但权限有限只能在浏览器跑
3. 真正的智能体能操作电脑终端，有Root权限，能执行复杂任务
4. 生成模型包括文字、图片、视频，底层都是基于概率生成内容

实用建议：
- 简单任务直接用网页端，别折腾API
- 复杂调试用Claude Code这类Agent，别自己点UI
- 硬核问题用推理模型+深度搜索，别用便宜模型硬碰

## 禁止
- 网络黑话、俚语
- 为了吐槽而说错话
- 废话、寒暄
- 引流话术"""


def generate_plain_summary(raw_text: str) -> str:
    """生成纯干货版本，用于评论区"""
    print(f"⏳ 生成纯干货版本...")
    
    response = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PLAIN_PROMPT},
            {"role": "user", "content": f"把这篇文章改写成纯干货科普版本：\n\n{raw_text}"},
        ],
        temperature=0.5,
    )
    
    return response.choices[0].message.content.strip()
