#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多图方案 - 分镜剧本生成器
用法: python gen_text.py <项目文件夹名> <场景描述>

依赖:
  pip install openai
"""
import os
import sys
import time
import re
import urllib.request
import urllib.error
import json
from openai import OpenAI

# ============================================================
# 配置
# ============================================================

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
BASE_URL = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
MODEL = os.environ.get("DASHSCOPE_TEXT_MODEL", "qwen-plus-2025-12-01")
IMAGE_MODEL = os.environ.get("DASHSCOPE_IMAGE_MODEL", "qwen-image-max")

# 从 settings.json 加载配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
SETTINGS_PATH = os.path.join(ROOT_DIR, "settings.json")
if os.path.exists(SETTINGS_PATH):
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            settings = json.load(f)
            if not API_KEY and settings.get("api_key"):
                API_KEY = settings["api_key"]
            if settings.get("text_model"):
                MODEL = settings["text_model"]
            if settings.get("image_model"):
                IMAGE_MODEL = settings["image_model"]
    except:
        pass

# ============================================================
# DashScope API 端点
# ============================================================
DASHSCOPE_MULTIMODAL_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
DASHSCOPE_WANX_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation"
DASHSCOPE_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

QWEN_IMAGE_MAX_RPM = 2
WANX_MAX_RPM = 10

_last_request_time = {}

# ============================================================
# 提示词模板
# ============================================================

PROMPT_TEMPLATE = """你是一个英语日常口语教学内容设计师。请为我创作一段英语日常对话。

【场景】{scene}
【时长】严格控制在 50-65 秒
【结构】必须包含 4 到 6 个场景（Scene）。

写作要求：
1. 角色只用 M1 M2 / F1 F2 标记。
2. 每句台词后用 | 分隔附中文翻译。
3. 用 --- 分隔不同的场景（Scene）。
4. 第一行写标题：English Title — 中文标题

【关键要求：视觉与文本对齐】
请在对话写完后，编写"分镜脚本"。
规则：**分镜的数量必须与上面的场景数量严格一致！**

【视觉一致性要求】：
A. 必须先设定主角的"视觉锚点"（例如：穿蓝色卫衣的短发男生）。
B. 每个 Panel 描述中，**必须重复**这些特征。

输出格式严格如下：
1) 第一部分：对话正文
2) ===
3) 第二部分：核心表达 5-8 个（格式：短语 — 中文 — 例句）
4) ===
5) 第三部分：分镜脚本
Panel 1: [对应的画面描述]
Panel 2: [对应的画面描述]
...
Panel N: [对应的画面描述]

请直接输出纯文本。"""

IMAGE_PROMPT_TEMPLATE = """
{desc}
【风格要求】
- 温暖的手绘水彩插图风格，类似经典英语教材插图。
- 或者是清新日系/韩系扁平插画。
- 构图清晰，主体突出。
- 画面中绝不要出现文字、气泡、拼贴框。
"""

# ============================================================
# API 工具函数
# ============================================================

def _dashscope_request(url, data=None, method="POST", timeout=120):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    if "multimodal-generation" not in url:
        headers["X-DashScope-Async"] = "enable" if method == "POST" else "disable"
    try:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            error_detail = e.read().decode("utf-8")
            error_json = json.loads(error_detail)
            msg = error_json.get("message", error_detail)
            code = error_json.get("code", "")
            if code:
                msg = f"{code}: {msg}"
        except:
            msg = str(e)
        print(f"  [DashScope API 错误] HTTP {e.code}: {msg}")
        return {"error": True, "code": e.code, "message": msg}
    except Exception as e:
        print(f"  [DashScope API 异常] {str(e)}")
        return {"error": True, "message": str(e)}


def _respect_rate_limit(model_type="qwen-image"):
    global _last_request_time
    limits = {
        "qwen-image": QWEN_IMAGE_MAX_RPM,
        "wanx": WANX_MAX_RPM
    }
    rpm = limits.get(model_type, QWEN_IMAGE_MAX_RPM)
    min_interval = 60 / rpm
    
    current_time = time.time()
    last_time = _last_request_time.get(model_type, 0)
    elapsed = current_time - last_time
    
    if elapsed < min_interval:
        wait_time = min_interval - elapsed
        print(f"    [INFO] 遵守频率限制，等待 {wait_time:.1f} 秒...")
        time.sleep(wait_time)
    
    _last_request_time[model_type] = time.time()

# ============================================================
# 工具函数
# ============================================================

def extract_panels_dynamic(text: str):
    if not text: return {}
    text = text.replace("：", ":")
    pattern = re.compile(r"^\s*Panel\s*(\d+)\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
    found = {}
    for m in pattern.finditer(text):
        found[int(m.group(1))] = m.group(2).strip()
    return found


def generate_text(scene_description):
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    print(f"  [Text] 场景：{scene_description}")
    print(f"  [Text] 正在构思剧本和分镜...")
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(scene=scene_description)}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [错误] 文本生成失败：{e}")
        return None


def generate_single_image(prompt_text, save_path):
    final_prompt = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', 
                         IMAGE_PROMPT_TEMPLATE.format(desc=prompt_text).strip())
    
    print(f"    模型：{IMAGE_MODEL}")
    
    NATIVE_MODELS = ["qwen-image-max", "qwen-image-plus", "wanx-v1"]
    
    if IMAGE_MODEL in NATIVE_MODELS:
        _respect_rate_limit("qwen-image")
        
        if IMAGE_MODEL == "qwen-image-max":
            api_url = DASHSCOPE_MULTIMODAL_API_URL
            payload = {
                "model": IMAGE_MODEL,
                "input": {"messages": [{"role": "user", "content": [{"text": final_prompt}]}]},
                "parameters": {"size": "1024*1024", "n": 1, "prompt_extend": True, "watermark": False}
            }
        else:
            api_url = DASHSCOPE_WANX_API_URL
            payload = {
                "model": IMAGE_MODEL,
                "input": {"prompt": final_prompt},
                "parameters": {"style": "<auto>", "size": "1024*1024", "n": 1}
            }
        
        res = _dashscope_request(api_url, payload)
        
        if "choices" in res.get("output", {}):
            output = res["output"]
            try:
                content_items = output["choices"][0]["message"]["content"]
                for item in content_items:
                    if "image" in item:
                        img_url = item["image"]
                        urllib.request.urlretrieve(img_url, save_path)
                        return True
            except Exception as e:
                print(f"  [原生API错误] 解析同步失败: {e}")
                return False
        
        if not res or "output" not in res or "task_id" not in res["output"]:
            print(f"  [原生API错误] 提交失败: {res}")
            return False
        
        task_id = res["output"]["task_id"]
        poll_url = DASHSCOPE_TASK_URL.format(task_id=task_id)
        
        for _ in range(60):
            time.sleep(2)
            status_res = _dashscope_request(poll_url, method="GET")
            output = status_res.get("output", {})
            task_status = output.get("task_status")
            
            if task_status == "SUCCEEDED":
                img_url = None
                if "choices" in output:
                    try:
                        content_items = output["choices"][0]["message"]["content"]
                        for item in content_items:
                            if "image" in item:
                                img_url = item["image"]
                                break
                    except:
                        pass
                
                if not img_url:
                    results = output.get("results", [])
                    img_url = results[0].get("url") if results else output.get("url")
                
                if img_url:
                    urllib.request.urlretrieve(img_url, save_path)
                    return True
                else:
                    print(f"  [错误] 未在响应中找到图片 URL: {output}")
                    return False
            elif task_status == "FAILED":
                print(f"  [任务失败] {output.get('message')}")
                return False
        return False
    
    else:
        try:
            client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
            _respect_rate_limit("wanx")
            
            response = client.images.generate(
                model=IMAGE_MODEL,
                prompt=final_prompt,
                n=1,
                size="1024x1024"
            )
            img_url = response.data[0].url
            if img_url:
                urllib.request.urlretrieve(img_url, save_path)
                return True
            return False
        except Exception as e:
            print(f"  [OpenAI接口错误] {e}")
            return False


def print_image_guide(panels, input_dir, project_name):
    sep = "=" * 62
    count = len(panels)
    lines = [
        sep,
        "  图片准备指南（手动模式）",
        sep,
        f"需要 {count} 张图片，全部放入以下文件夹：",
        f"  {input_dir}",
        "",
        "规格：1024 × 1024 像素，PNG 格式",
        "推荐工具：Midjourney、Stable Diffusion、DALL·E 3 等",
        "",
    ]
    for idx, desc in sorted(panels.items()):
        full_prompt = IMAGE_PROMPT_TEMPLATE.format(desc=desc).strip()
        lines += [
            "-" * 62,
            f"  图片 {idx}/{count}   →  文件名：{idx}.png",
            "",
            "  Prompt（可直接复制）：",
            "",
        ]
        for line in full_prompt.split("\n"):
            lines.append("    " + line)
        lines.append("")
    lines += [
        "=" * 62,
        "所有图片放好后，运行：",
        f"  python make_video.py {project_name}",
        sep,
    ]
    content = "\n".join(lines)
    print(content)
    guide_path = os.path.join(input_dir, "图片说明.txt")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n[已保存指南到：{guide_path}]")

# ============================================================
# 主流程
# ============================================================

def main():
    args_raw = sys.argv[1:]
    no_image = "--no-image" in args_raw
    args = [a for a in args_raw if not a.startswith("--")]
    
    if len(args) < 2:
        print("用法：python gen_text.py <项目文件夹名> <场景描述> [--no-image]")
        print("  --no-image  只生成剧本，打印图片 Prompt，不调用图片 API")
        sys.exit(1)
    if not API_KEY:
        print("请设置环境变量 DASHSCOPE_API_KEY 或检查 settings.json")
        sys.exit(1)
    
    project_name = args[0]
    scene_description = args[1]
    project_dir = os.path.join(ROOT_DIR, project_name)
    input_dir = os.path.join(project_dir, "input")
    os.makedirs(input_dir, exist_ok=True)
    text_path = os.path.join(input_dir, "文本.txt")
    
    print("=" * 40)
    print("步骤 1: 生成智能剧本")
    if os.path.exists(text_path):
        print("  读取已有文本...")
        with open(text_path, "r", encoding="utf-8") as f: 
            text = f.read()
    else:
        text = generate_text(scene_description)
        if text:
            with open(text_path, "w", encoding="utf-8") as f: 
                f.write(text)
        else:
            print("  [错误] 剧本生成失败，终止流程")
            sys.exit(1)
    
    panels = extract_panels_dynamic(text)
    if not panels:
        print("  [警告] 未提取到 Panel 信息。请检查文本格式是否符合要求。")
        print(f"  [调试] 完整文本已保存至：{text_path}")
        return
    
    count = len(panels)
    print(f"  ✓ AI 规划了 {count} 个分镜。")
    print("=" * 40)
    
    if not no_image:
        if IMAGE_MODEL.startswith("qwen-image"):
            print(f"  [提示] 使用 qwen-image 系列模型")
        elif IMAGE_MODEL.startswith("wanx") or IMAGE_MODEL.startswith("wan"):
            print(f"  [提示] 使用 wanx/wan 模型，通过 OpenAI 兼容接口生成图片")
    
    if no_image:
        print("步骤 2: 输出图片准备指南（手动模式，不调用图片 API）")
        print_image_guide(panels, input_dir, project_name)
    else:
        print(f"步骤 2: 生成 {count} 张插图")
        for idx, desc in sorted(panels.items()):
            filename = f"{idx}.png"
            save_path = os.path.join(input_dir, filename)
            if os.path.exists(save_path):
                print(f"  [{idx}/{count}] 已存在，跳过。")
                continue
            
            print(f"  [{idx}/{count}] 生成中：{desc[:30]}...")
            success = generate_single_image(desc, save_path)
            if success: 
                print(f"     ✓ 完成 → {filename}")
            else: 
                print(f"     ✗ 失败 → {filename}")
                print(f"     ℹ️ 建议：可运行 'python gen_text.py {project_name} \"{scene_description}\" --no-image' 获取图片生成指南")
    
    print("\n" + "=" * 40)
    print("✓ 全部完成！")
    print(f"  剧本路径：{text_path}")
    print(f"  图片目录：{input_dir}")
    
    if not no_image:
        missing = [f"{i}.png" for i in range(1, count+1) if not os.path.exists(os.path.join(input_dir, f"{i}.png"))]
        if missing:
            print("\n⚠️  注意：部分图片生成失败")
            print(f"   缺失：{', '.join(missing)}")
        else:
            print("\n✅ 所有图片生成成功！")

if __name__ == "__main__":
    main()
