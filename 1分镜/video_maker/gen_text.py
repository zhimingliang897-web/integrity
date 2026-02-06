import os
import sys
import json
import time
import re
import urllib.request
import urllib.error

# ============================================================
# 配置
# ============================================================

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "kimi-k2.5"      # 文本生成模型
IMAGE_MODEL = "qwen-image"  # 图片生成模型 (通义万相)

IMAGE_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
IMAGE_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 提示词模板（文本生成：动态分镜版）
# ============================================================

PROMPT_TEMPLATE = """你是一个英语日常口语教学内容设计师。请为我创作一段英语日常对话：

【场景】{scene}
【时长】整段对话朗读时长控制在 50-70 秒
【风格】地道日常口语，自然、接地气

写作要求：
1. 角色只用 M1 M2 / F1 F2 标记。
2. 每句台词后用 | 分隔附中文翻译。
3. 用 --- 分隔场景。
4. 【分镜数量】：请根据剧情需要，自动决定场景数量（最少 3 个，最多 6 个）。不强制要求 4 个。
5. 第一行写标题：English Title — 中文标题

关键要求（用于AI自动绘图）：
在最后输出“分镜脚本”时，请严格遵守以下规则，以保证生成的图片人物一致：
A. 必须先设定主角的“视觉锚点”（例如：穿蓝色卫衣的短发男生）。
B. 在每个 Panel 的描述中，**必须重复**这些视觉特征。不要只写“他”，要写“那个穿蓝色卫衣的男生”。

输出格式严格如下：
1) 第一部分：对话正文
2) ===
3) 第二部分：核心表达 5-8 个
4) ===
5) 第三部分：分镜脚本（Panel 1 开始，自动决定结束）：
Panel 1: [画面描述]
Panel 2: [画面描述]
...
Panel N: [画面描述]

要求：
- 每行只写 1 句【中文】镜头描述。
- 描述必须具体，包含人物穿着、动作、环境。
- 不要出现引号。

请直接输出纯文本。"""

# ============================================================
# 提示词模板（单张图片生成）
# ============================================================

# 注意：因为是单张生成，这里不需要 grid 布局指令了
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
    """
    动态解析 Panel 1 到 Panel N
    返回一个字典: {1: "描述...", 2: "描述..."}
    """
    if not text:
        return {}

    # 替换中文冒号
    text = text.replace("：", ":")
    
    # 查找所有 Panel X: ...
    # 格式支持: Panel 1: xxx 或 Panel 1 : xxx
    pattern = re.compile(r"^\s*Panel\s*(\d+)\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
    
    found = {}
    for m in pattern.finditer(text):
        idx = int(m.group(1))
        content = m.group(2).strip()
        found[idx] = content
        
    return found


def _dashscope_request(url, data=None, method="POST"):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    if method == "POST":
        headers["X-DashScope-Async"] = "enable"

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def generate_text(scene_description):
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    print(f"  [Text] 场景: {scene_description}")
    print(f"  [Text] 正在构思剧本和分镜...")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": PROMPT_TEMPLATE.format(scene=scene_description)}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [错误] 文本生成失败: {e}")
        return None


def generate_single_image(prompt_text, save_path):
    """
    调用通义万相生成单张图片
    """
    final_prompt = IMAGE_PROMPT_TEMPLATE.format(desc=prompt_text)
    
    # print(f"  [Image] Prompt: {prompt_text[:20]}...")

    payload = {
        "model": IMAGE_MODEL, 
        "input": {"prompt": final_prompt},
        "parameters": {
            "size": "1024*1024", # 单图标准尺寸
            "n": 1
        },
    }

    try:
        result = _dashscope_request(IMAGE_API_URL, payload)
        task_id = result.get("output", {}).get("task_id")
        if not task_id:
            print("  [错误] 任务提交失败")
            return False
    except Exception as e:
        print(f"  [错误] API请求异常: {e}")
        return False

    # 轮询等待
    poll_url = IMAGE_TASK_URL.format(task_id=task_id)
    for _ in range(45): # 最多等待 90秒
        time.sleep(2)
        try:
            status = _dashscope_request(poll_url, method="GET")
            task_status = status.get("output", {}).get("task_status")
            
            if task_status == "SUCCEEDED":
                img_url = status.get("output", {}).get("results", [])[0].get("url")
                urllib.request.urlretrieve(img_url, save_path)
                return True
            
            if task_status == "FAILED":
                print(f"  [失败] {status.get('output', {}).get('message')}")
                return False
        except:
            continue
            
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

    # ---- 1. 生成文本 & 提取分镜 ----
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

    # 动态提取 Panel
    panels = extract_panels_dynamic(text)
    
    if not panels:
        print("  [警告] 未提取到 Panel 信息，无法生成图片。")
        return

    count = len(panels)
    print(f"  AI 规划了 {count} 个分镜场景。")
    print("=" * 40)

    # ---- 2. 循环生成图片 ----
    print(f"步骤 2: 生成 {count} 张插图")
    
    for idx, desc in panels.items():
        filename = f"{idx}.png"
        save_path = os.path.join(input_dir, filename)
        
        if os.path.exists(save_path):
            print(f"  [{idx}/{count}] {filename} 已存在，跳过。")
            continue
            
        print(f"  [{idx}/{count}] 正在生成: {desc[:30]}...")
        success = generate_single_image(desc, save_path)
        
        if success:
            print(f"     -> 保存成功")
        else:
            print(f"     -> 生成失败")

    print("\n" + "=" * 40)
    print("全部完成！")
    print(f"素材目录: {input_dir}")
    print(f"包含: 文本.txt 和 {len(panels)} 张分镜图片")

if __name__ == "__main__":
    main()