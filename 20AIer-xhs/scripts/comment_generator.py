"""
评论区热心建议 + Tag标签生成
风格：精炼、干货、准确、不夸大、不打广告
"""
import json
import re
from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL, TIMEOUT_SEC

_client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=TIMEOUT_SEC)

COMMENT_SYSTEM_PROMPT = """你是真诚分享经验的老网民。不整虚的，不打广告，只给实在话。

### 原则
1. 精炼：一条建议不超过20字
2. 干货：给具体数字、具体操作
3. 准确：不确定的不说，避免误导
4. 不夸大：好就是好，不好的地方也直说
5. 不打广告：不推荐特定产品/服务

### 输出格式（JSON）
{
  "comments": [
    {"number": "1", "content": "建议内容（15字内）"},
    {"number": "2", "content": "建议内容"},
    {"number": "3", "content": "建议内容"}
  ],
  "tags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
}

### 示例
好的建议（精炼干货）：
- "首月成本约200，用量不大别上头"
- "先搞懂本地部署，再考虑云端"
- "当辅助工具可以，别当主力"

Tags示例：
- #AI工具 #避坑指南 #实用分享 #科技真相 #学习笔记"""


def generate_comments(article_text: str, slides_summary: str = "") -> dict:
    """生成评论和Tags"""
    print("Generating comments and tags...")

    # slides_summary 作为上下文补充，避免 tag/建议跑偏
    summary_line = f"\n\nSlides summary: {slides_summary}" if slides_summary else ""
    user_prompt = f"""Based on this article, generate 3 short suggestions + 5 relevant tags.

Article: {article_text[:1000]}
{summary_line}

Output as JSON only."""

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": COMMENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        response_format={"type": "json_object"},
    )

    raw_output = response.choices[0].message.content.strip()

    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if not json_match:
            raise ValueError(f"Parse error: {raw_output[:300]}")
        data = json.loads(json_match.group(0))

    print("Done!")
    return data


def format_comments_text(data: dict) -> str:
    """格式化输出"""
    lines = ["💡 三条实在建议：", ""]

    for comment in data.get("comments", []):
        num = comment.get("number", "•")
        content = comment.get("content", "")
        lines.append(f"{num}. {content}")

    # Tags
    tags = data.get("tags", [])
    if tags:
        lines.append("")
        lines.append("🏷️ " + " ".join(tags))

    return "\n".join(lines)


def save_comments(data: dict, output_path: str):
    """保存到文件"""
    text = format_comments_text(data)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    return text