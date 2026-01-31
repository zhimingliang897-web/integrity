"""
gen_text.py — 调用通义千问 API 自动生成对话文本 + 通义万相生成四宫格插图
用法: python gen_text.py <项目文件夹名> <场景描述>
例如: python gen_text.py 6买咖啡 "在咖啡店点单，一个男生第一次去星巴克不知道怎么点"
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error

# ============================================================
# 配置
# ============================================================

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen3-max-2026-01-23"  # 免费额度 100万token，到 2026/04/23

# 通义万相图片生成
IMAGE_MODEL = "qwen-image"
IMAGE_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
IMAGE_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 提示词模板
# ============================================================

PROMPT_TEMPLATE = """你是一个英语口语教学内容设计师。请为我创作一段英语日常对话，要求如下：

【场景】{scene}
【时长】对话控制在 30-60 秒内朗读完
【难度】雅思口语 5-6 分水平（日常交流，自然但不过于俚语化）

写作要求：
1. 对话必须自然真实，像真人日常交流，不要书面化或教材腔
2. 每段对话包含 3-5 个实用表达/句型，这些表达要有通用性（换个场景也能用）
3. 角色用编号标记：M1 M2（男）/ F1 F2（女），冒号后面直接跟台词
4. 每句台词后用 | 分隔附上中文翻译，如：M1: What stop? | 哪一站？
5. 不要加括号动作描述，不要加 Scene/Setting 等说明文字
6. 用 --- 分隔场景（我会用四宫格插图，所以分成 4 个场景）
7. 对话结尾自然收束，不要强行升华
8. 第一行写场景标题（英文），如：On a bus — asking for directions

对话结束后，用 === 分隔，列出核心表达（每行格式：短语 — 中文释义 — 例句）

请直接输出对话文本，不要加任何额外说明或 markdown 格式标记。"""

IMAGE_PROMPT_TEMPLATE = """A 2x2 grid comic illustration for an English learning video.
Four panels showing: {scene}
Style: colorful manga/comic style, expressive characters, bright colors,
similar to New Concept English textbook illustrations.
No text or speech bubbles on the image.
Characters should look consistent across all four panels.
Clean lines, simple backgrounds, warm and friendly atmosphere."""


# ============================================================
# 文本生成
# ============================================================

def generate_text(scene_description):
    """调用通义千问 API 生成对话文本"""
    from openai import OpenAI

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    print(f"  调用模型: {MODEL}")
    print(f"  场景: {scene_description}")
    print(f"  生成中...\n")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": PROMPT_TEMPLATE.format(scene=scene_description)}
        ],
        temperature=0.8,
    )

    text = response.choices[0].message.content.strip()

    # 去掉可能的 markdown 代码块标记
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    return text


# ============================================================
# 图片生成（通义万相）
# ============================================================

def _dashscope_request(url, data=None, method="POST"):
    """发送 DashScope HTTP 请求"""
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


def generate_image(scene_description, output_path):
    """调用通义万相 API 生成四宫格插图"""
    prompt = IMAGE_PROMPT_TEMPLATE.format(scene=scene_description)

    print(f"  调用模型: {IMAGE_MODEL}")
    print(f"  提交图片生成任务...")

    # 1. 提交异步任务
    payload = {
        "model": IMAGE_MODEL,
        "input": {"prompt": prompt},
        "parameters": {"size": "1024*1024", "n": 1},
    }

    try:
        result = _dashscope_request(IMAGE_API_URL, payload)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"  [错误] 提交任务失败: {e.code}")
        print(f"  {body[:300]}")
        return False

    task_id = result.get("output", {}).get("task_id")
    if not task_id:
        print(f"  [错误] 未获取到 task_id: {result}")
        return False

    print(f"  任务 ID: {task_id}")
    print(f"  等待生成", end="", flush=True)

    # 2. 轮询等待完成
    poll_url = IMAGE_TASK_URL.format(task_id=task_id)
    for _ in range(60):  # 最多等 120 秒
        time.sleep(2)
        print(".", end="", flush=True)

        try:
            status = _dashscope_request(poll_url, method="GET")
        except urllib.error.HTTPError:
            continue

        task_status = status.get("output", {}).get("task_status")
        if task_status == "SUCCEEDED":
            print(" 完成!")
            results = status["output"].get("results", [])
            if results:
                img_url = results[0].get("url") or results[0].get("b64_image")
                if img_url and img_url.startswith("http"):
                    # 下载图片
                    urllib.request.urlretrieve(img_url, output_path)
                    print(f"  已保存: {output_path}")
                    return True
            print(f"  [错误] 无图片结果: {status}")
            return False
        elif task_status == "FAILED":
            print(" 失败!")
            msg = status.get("output", {}).get("message", "未知错误")
            print(f"  [错误] {msg}")
            return False

    print(" 超时!")
    print("  [错误] 图片生成超时（120秒）")
    return False


# ============================================================
# 主流程
# ============================================================

def main():
    if len(sys.argv) < 3:
        print("用法: python gen_text.py <项目文件夹名> <场景描述>")
        print('例如: python gen_text.py 6买咖啡 "在咖啡店点单，一个男生第一次去星巴克不知道怎么点"')
        sys.exit(1)

    if not API_KEY:
        print("[错误] 未设置环境变量 DASHSCOPE_API_KEY")
        print("请先运行: set DASHSCOPE_API_KEY=你的API密钥")
        sys.exit(1)

    project_name = sys.argv[1]
    scene_description = sys.argv[2]

    # 创建项目目录
    project_dir = os.path.join(SCRIPT_DIR, project_name)
    input_dir = os.path.join(project_dir, "input")
    os.makedirs(input_dir, exist_ok=True)

    text_path = os.path.join(input_dir, "文本.txt")
    image_path = os.path.join(input_dir, "图片.png")

    # ---- 生成文本 ----
    print("=" * 50)
    print("步骤 0a: 生成对话文本")
    print("=" * 50)

    if os.path.exists(text_path):
        print(f"  [警告] {text_path} 已存在")
        answer = input("  是否覆盖？(y/N): ").strip().lower()
        if answer != "y":
            print("  跳过文本生成。\n")
            text = None
        else:
            text = generate_text(scene_description)
    else:
        text = generate_text(scene_description)

    if text:
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
        print("  生成结果:")
        print("-" * 40)
        print(text)
        print("-" * 40)
        print(f"  已保存到: {text_path}\n")

    # ---- 生成图片 ----
    print("=" * 50)
    print("步骤 0b: 生成四宫格插图")
    print("=" * 50)

    if os.path.exists(image_path):
        print(f"  [警告] {image_path} 已存在")
        answer = input("  是否覆盖？(y/N): ").strip().lower()
        if answer != "y":
            print("  跳过图片生成。\n")
        else:
            generate_image(scene_description, image_path)
    else:
        generate_image(scene_description, image_path)

    # ---- 完成 ----
    print()
    print("=" * 50)
    print("  素材生成完毕！")
    print("=" * 50)
    print(f"\n  下一步: python make_video.py {project_name}")
    print(f"  如果对图片不满意，可以手动替换 {image_path}")


if __name__ == "__main__":
    main()
