import os
import sys
import json
import time
import re
import urllib.request
import urllib.error
from openai import OpenAI

# ============================================================
# 配置
# ============================================================

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "kimi-k2.5"      # 文本模型
IMAGE_MODEL = "qwen-image"  # 图片模型

IMAGE_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
IMAGE_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 提示词模板（严格对齐版）
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
请在对话写完后，编写“分镜脚本”。
规则：**分镜的数量必须与上面的场景数量严格一致！**
（例如：如果对话用了 4 个 '---' 分隔，这里就必须写 4 个 Panel）。

【视觉一致性要求】：
A. 必须先设定主角的“视觉锚点”（例如：穿蓝色卫衣的短发男生）。
B. 每个 Panel 描述中，**必须重复**这些特征（不要只写“他”，要写“那个穿蓝色卫衣的男生”）。

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

# ============================================================
# 单图 Prompt 模板
# ============================================================

IMAGE_PROMPT_TEMPLATE = """
{desc}
【风格要求】
- 温暖的手绘水彩插图风格，类似经典英语教材插图。
- 或者是清新日系/韩系扁平插画。
- 构图清晰，主体突出。
- 画面中绝不要出现文字、气泡、拼贴框。
"""

# ============================================================
# 工具函数
# ============================================================

def extract_panels_dynamic(text: str):
    """提取 Panel 1...N"""
    if not text: return {}
    text = text.replace("：", ":")
    pattern = re.compile(r"^\s*Panel\s*(\d+)\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
    found = {}
    for m in pattern.finditer(text):
        found[int(m.group(1))] = m.group(2).strip()
    return found

def _dashscope_request(url, data=None, method="POST"):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    if method == "POST": headers["X-DashScope-Async"] = "enable"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def generate_text(scene_description):
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    print(f"  [Text] 场景: {scene_description}")
    print(f"  [Text] 正在构思剧本和分镜...")
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(scene=scene_description)}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [错误] 文本生成失败: {e}")
        return None

def generate_single_image(prompt_text, save_path):
    final_prompt = IMAGE_PROMPT_TEMPLATE.format(desc=prompt_text)
    payload = {
        "model": IMAGE_MODEL, 
        "input": {"prompt": final_prompt},
        "parameters": {"size": "1024*1024", "n": 1}
    }
    try:
        result = _dashscope_request(IMAGE_API_URL, payload)
        task_id = result.get("output", {}).get("task_id")
        if not task_id: return False
    except Exception as e:
        print(f"  [错误] API请求异常: {e}")
        return False

    poll_url = IMAGE_TASK_URL.format(task_id=task_id)
    for _ in range(45):
        time.sleep(2)
        try:
            status = _dashscope_request(poll_url, method="GET")
            task_status = status.get("output", {}).get("task_status")
            if task_status == "SUCCEEDED":
                img_url = status.get("output", {}).get("results", [])[0].get("url")
                urllib.request.urlretrieve(img_url, save_path)
                return True
            if task_status == "FAILED": return False
        except: continue
    return False

# ============================================================
# 主流程
# ============================================================

def main():
    if len(sys.argv) < 3:
        print("用法: python gen_text.py <项目文件夹名> <场景描述>")
        sys.exit(1)
    if not API_KEY:
        print("请设置环境变量 DASHSCOPE_API_KEY")
        sys.exit(1)

    project_name = sys.argv[1]
    scene_description = sys.argv[2]
    project_dir = os.path.join(SCRIPT_DIR, project_name)
    input_dir = os.path.join(project_dir, "input")
    os.makedirs(input_dir, exist_ok=True)
    text_path = os.path.join(input_dir, "文本.txt")

    print("=" * 40)
    print("步骤 1: 生成智能剧本")
    if os.path.exists(text_path):
        print("  读取已有文本...")
        with open(text_path, "r", encoding="utf-8") as f: text = f.read()
    else:
        text = generate_text(scene_description)
        if text:
            with open(text_path, "w", encoding="utf-8") as f: f.write(text)

    panels = extract_panels_dynamic(text)
    if not panels:
        print("  [警告] 未提取到 Panel 信息。")
        return

    count = len(panels)
    print(f"  AI 规划了 {count} 个分镜。")
    print("=" * 40)
    print(f"步骤 2: 生成 {count} 张插图")
    
    for idx, desc in panels.items():
        filename = f"{idx}.png"
        save_path = os.path.join(input_dir, filename)
        if os.path.exists(save_path):
            print(f"  [{idx}/{count}] 已存在，跳过。")
            continue
        print(f"  [{idx}/{count}] 生成中: {desc[:20]}...")
        success = generate_single_image(desc, save_path)
        if success: print(f"     -> 完成")
        else: print(f"     -> 失败")

    print("\n" + "=" * 40)
    print("全部完成！")

if __name__ == "__main__":
    main()