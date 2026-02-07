"""
gen_text.py — 调用通义千问 API 自动生成对话文本 + 通义万相生成标准四宫格插图（连续四分镜故事）
用法: python gen_text.py <项目文件夹名> <场景描述>
例如: python gen_text.py 6买咖啡 "在咖啡店点单，一个男生第一次去星巴克不知道怎么点"

依赖:
  pip install openai
环境变量:
  set DASHSCOPE_API_KEY=你的API密钥   (Windows CMD)
  export DASHSCOPE_API_KEY=你的API密钥 (macOS/Linux)
"""

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
MODEL = "kimi-k2.5"  # 免费额度 100万token，到 2026/04/23

# 通义万相图片生成
IMAGE_MODEL = "qwen-image"
IMAGE_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
IMAGE_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 提示词模板（文本）
# ============================================================

PROMPT_TEMPLATE = """你是一个英语日常口语教学内容设计师。请为我创作一段英语日常对话：

【场景】{scene}
【时长】整段对话朗读时长严格控制在 50-65 秒，总共不超过 12 句台词
【风格】地道日常口语，像母语者真实对话那样自然、接地气

写作要求：
1. 必须口语化、自然，不要书面腔
2. 对话中包含 4-6 个高频、可迁移的实用表达/句型（换场景也能用）
3. 角色只用 M1 M2（男）/ F1 F2（女）标记；冒号后直接跟台词；禁止出现人名或职业称呼（如 Waiter/Barista/Teacher 等）
4. 每句台词后用 | 分隔附中文翻译
5. 禁止加入括号动作说明、舞台提示、Scene/Setting 等说明文字
6. 用 --- 分隔场景：必须恰好 4 个场景；每个场景 2-3 句台词；整体连贯、按时间推进（像短剧分镜）
7. 结尾自然收束，不要喊口号、不要强行升华
8. 第一行写标题：English Title — 中文标题

关键额外要求（用于四宫格分镜）：
A. 4 个场景必须构成一个“连续故事”，人物、地点一致，事件有起因→过程→转折→结尾。
B. 每个场景的第一句台词要能体现该场景发生了什么（让读者只看第一句也知道剧情推进）。
C. 故事里必须出现一个小小的“转折/小误会/小尴尬”（轻松幽默即可），并在第 4 场景解决。

输出格式严格如下：
1) 第一部分：对话正文（按要求用 --- 分成 4 段）
2) 然后输出一行：===
3) 第二部分：核心表达 5-8 个（每行：短语 — 中文释义 — 一个简短例句）
4) 然后输出一行：===
5) 第三部分：四镜头分镜板（用于画图），必须恰好 4 行：
Panel 1: ...
Panel 2: ...
Panel 3: ...
Panel 4: ...
要求：
- 每行只写 1 句中文镜头描述，写清楚人物在做什么、表情/情绪、关键道具、环境
- 必须连续，且与对话四段一一对应
- 不要出现任何台词，不要出现引号

请直接输出纯文本，不要加任何额外说明或 markdown 标记。"""

# ============================================================
# 提示词模板（图片：严格四宫格 + 四分镜）
# ============================================================

IMAGE_PROMPT_TEMPLATE = """Draw a 2x2 COMIC STRIP with exactly 4 SEPARATE panels telling a sequential story.

LAYOUT RULES:
- The image is divided into 4 equal quadrants by one horizontal and one vertical white divider line (about 8px wide, pure white, perfectly straight, crossing at the center).
- Each panel is its own INDEPENDENT scene — different background details, different character poses, different moment in time.
- IMPORTANT: Do NOT draw one single panoramic scene and split it with lines. Each panel must be a DISTINCT comic frame showing a DIFFERENT action/moment.

STORYBOARD (4 sequential moments):
Top-left: {p1}
Top-right: {p2}
Bottom-left: {p3}
Bottom-right: {p4}

ART STYLE:
- Warm hand-drawn watercolor illustration, like New Concept English textbook
- Clean line art with soft watercolor fill
- Warm muted colors (beige, soft blue, light brown, warm yellow)
- Same characters with consistent appearance (face, hair, clothing) across all 4 panels
- Simple, uncluttered backgrounds
- NO text, NO speech bubbles, NO captions, NO labels, NO signs, NO watermarks
"""

# 兜底：如果解析不到 Panel 1-4，就用 scene 自动写四步故事
IMAGE_PROMPT_FALLBACK = """Draw a 2x2 COMIC STRIP with exactly 4 SEPARATE panels telling a sequential story.

LAYOUT: 4 equal quadrants divided by one horizontal + one vertical white line (8px, pure white, straight, crossing at center).
Each panel is its own INDEPENDENT scene — different poses, different moment. Do NOT draw one panoramic image split by lines.

SCENE: {scene}
- Panel 1 (top-left): arrival / start of interaction
- Panel 2 (top-right): development / asking / choosing
- Panel 3 (bottom-left): small twist or mild misunderstanding
- Panel 4 (bottom-right): resolution, friendly ending

ART STYLE:
- Warm hand-drawn watercolor, like New Concept English textbook
- Clean line art, soft watercolor fill, warm muted colors
- Same characters with consistent appearance in all 4 panels
- Simple backgrounds, NO text, NO speech bubbles, NO labels, NO watermarks
"""


# ============================================================
# 工具：解析四分镜
# ============================================================

def extract_panels(text: str):
    """
    从模型输出中提取:
      Panel 1: ...
      Panel 2: ...
      Panel 3: ...
      Panel 4: ...
    返回 (p1, p2, p3, p4) 或 None
    """
    if not text:
        return None

    # 容错：Panel 1: / Panel1: / panel 1:
    pattern = re.compile(r"^\s*Panel\s*([1-4])\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
    found = {int(m.group(1)): m.group(2).strip() for m in pattern.finditer(text)}

    if all(i in found for i in (1, 2, 3, 4)):
        return found[1], found[2], found[3], found[4]

    return None


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


def generate_image(scene_description, output_path, panels=None):
    """
    调用通义万相 API 生成四宫格插图
    panels: (p1,p2,p3,p4) 或 None
    """
    if panels:
        p1, p2, p3, p4 = panels
        prompt = IMAGE_PROMPT_TEMPLATE.format(p1=p1, p2=p2, p3=p3, p4=p4)
    else:
        prompt = IMAGE_PROMPT_FALLBACK.format(scene=scene_description)

    print(f"  调用模型: {IMAGE_MODEL}")
    print(f"  提交图片生成任务...")

    payload = {
        "model": IMAGE_MODEL,
        "input": {"prompt": prompt},
        "parameters": {"size": "1328*1328", "n": 1},
    }

    try:
        result = _dashscope_request(IMAGE_API_URL, payload)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"  [错误] 提交任务失败: {e.code}")
        print(f"  {body[:300]}")
        return False
    except Exception as e:
        print(f"  [错误] 提交任务异常: {e}")
        return False

    task_id = result.get("output", {}).get("task_id")
    if not task_id:
        print(f"  [错误] 未获取到 task_id: {result}")
        return False

    print(f"  任务 ID: {task_id}")
    print(f"  等待生成", end="", flush=True)

    poll_url = IMAGE_TASK_URL.format(task_id=task_id)

    # 最多等 120 秒
    for _ in range(60):
        time.sleep(2)
        print(".", end="", flush=True)

        try:
            status = _dashscope_request(poll_url, method="GET")
        except urllib.error.HTTPError:
            continue
        except Exception:
            continue

        task_status = status.get("output", {}).get("task_status")

        if task_status == "SUCCEEDED":
            print(" 完成!")
            results = status.get("output", {}).get("results", [])
            if results:
                img_url = results[0].get("url")
                if img_url and isinstance(img_url, str) and img_url.startswith("http"):
                    urllib.request.urlretrieve(img_url, output_path)
                    print(f"  已保存: {output_path}")
                    return True

            print(f"  [错误] 无图片结果: {status}")
            return False

        if task_status == "FAILED":
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

    text = None
    panels = None

    # ---- 生成文本 ----
    print("=" * 50)
    print("步骤 0a: 生成对话文本（含四镜头分镜板）")
    print("=" * 50)

    if os.path.exists(text_path):
        print(f"  [警告] {text_path} 已存在")
        answer = input("  是否覆盖？(y/N): ").strip().lower()
        if answer != "y":
            print("  跳过文本生成。\n")
        else:
            text = generate_text(scene_description)
    else:
        text = generate_text(scene_description)

    if text:
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

        panels = extract_panels(text)

        print("  生成结果:")
        print("-" * 40)
        print(text)
        print("-" * 40)
        print(f"  已保存到: {text_path}\n")

        if panels:
            print("  已提取四镜头分镜板:")
            print(f"    Panel 1: {panels[0]}")
            print(f"    Panel 2: {panels[1]}")
            print(f"    Panel 3: {panels[2]}")
            print(f"    Panel 4: {panels[3]}\n")
        else:
            print("  [提示] 未解析到 Panel 1-4，将用场景描述作为图片兜底分镜。\n")

    # ---- 生成图片 ----
    print("=" * 50)
    print("步骤 0b: 生成标准四宫格插图（连续四分镜）")
    print("=" * 50)

    if os.path.exists(image_path):
        print(f"  [警告] {image_path} 已存在")
        answer = input("  是否覆盖？(y/N): ").strip().lower()
        if answer != "y":
            print("  跳过图片生成。\n")
        else:
            generate_image(scene_description, image_path, panels=panels)
    else:
        generate_image(scene_description, image_path, panels=panels)

    # ---- 完成 ----
    print()
    print("=" * 50)
    print("  素材生成完毕！")
    print("=" * 50)
    print(f"\n  下一步: python make_video.py {project_name}")
    print(f"  如果对图片不满意，可以手动替换 {image_path}")


if __name__ == "__main__":
    main()
