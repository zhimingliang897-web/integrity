import os
import json
import requests
import feedparser
from openai import OpenAI
from datetime import datetime

# --- 配置 ---
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1003878273027")
MODEL_NAME = "qwen3-vl-flash-2026-01-22"

client = OpenAI(
    api_key=QWEN_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# --- 信源列表 ---
SOURCES = [
    {
        "name": "Hacker News",
        "url": "https://hnrss.org/newest?q=AI+LLM+Transformer",
        "type": "general",
    },
    {
        "name": "HF Papers",
        "url": "https://rsshub.app/huggingface/daily-papers",
        "type": "general",
    },
    {
        "name": "GitHub Trending",
        "url": "https://rsshub.app/github/trending/daily/python?since=daily",
        "type": "general",
    },
    {
        "name": "ArXiv cs.AI",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "type": "general",
    },
    {
        "name": "Reddit LocalLLaMA",
        "url": "https://www.reddit.com/r/LocalLLaMA/.rss",
        "type": "general",
    },
    {
        "name": "机器之心",
        "url": "https://www.jiqizhixin.com/rss",
        "type": "cn_media",
    },
]


def call_qwen(prompt: str) -> str | None:
    """调用 Qwen API (OpenAI 兼容接口)"""
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"[Qwen API Error] {e}")
        return None


def analyze_news(title: str, summary: str, source_type: str) -> dict | None:
    """使用 LLM 对单条新闻评级，返回 dict 或 None"""
    anti_hype = ""
    if source_type == "cn_media":
        anti_hype = (
            "注意：本文来自中文自媒体，请严格忽略'炸裂''颠覆''神作'等营销词汇，"
            "只关注是否有代码/论文/实质技术架构。"
        )

    prompt = f"""你是一个严苛的 AI 技术情报分析师。
{anti_hype}

请分析以下新闻：
标题：{title}
摘要：{summary}

评级标准：
- S级 (9-10): 行业里程碑 (如 Sora/GPT-5)、颠覆性架构突破。
- A级 (7-8): 高质量论文、实用工具重大更新、大厂重要开源。
- B级 (4-6): 普通迭代、观点文章。
- C级 (1-3): 纯公关稿、无实质内容。

请只输出一个合法 JSON，不要包含 Markdown 代码块标记：
{{"rating":"S/A/B/C","score":整数1到10,"comment":"毒舌点评50字内","tags":["标签1","标签2"]}}"""

    text = call_qwen(prompt)
    if not text:
        return None

    clean = text.replace("```json", "").replace("```", "").strip()
    # 尝试提取 JSON 部分
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start == -1 or end == 0:
        print(f"[JSON 提取失败] {title}")
        return None
    try:
        return json.loads(clean[start:end])
    except json.JSONDecodeError:
        print(f"[JSON 解析失败] {title}")
        return None


def fetch_source(source: dict) -> list[dict]:
    """抓取单个 RSS 信源并评级，返回 S/A 级条目列表"""
    name = source["name"]
    print(f">> 正在抓取: {name} ...")
    try:
        feed = feedparser.parse(source["url"])
    except Exception as e:
        print(f"[RSS 抓取失败] {name}: {e}")
        return []

    results = []
    for entry in feed.entries[:5]:
        title = getattr(entry, "title", "")
        summary = getattr(entry, "summary", "")[:800]
        link = getattr(entry, "link", "")

        analysis = analyze_news(title, summary, source["type"])
        if not analysis:
            continue

        rating = analysis.get("rating", "C")
        if rating in ("S", "A"):
            results.append(
                {
                    "source": name,
                    "title": title,
                    "link": link,
                    "rating": rating,
                    "score": analysis.get("score", 0),
                    "comment": analysis.get("comment", ""),
                    "tags": analysis.get("tags", []),
                }
            )
            print(f"   [{rating}] {title}")
        else:
            print(f"   [{rating}] (已过滤) {title}")

    return results


def build_report(all_news: list[dict]) -> str:
    """构建 Telegram HTML 格式的日报"""
    all_news.sort(key=lambda x: x["score"], reverse=True)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    lines = [f"<b>AI 每日情报 ({today})</b>\n"]

    for item in all_news:
        icon = "S" if item["rating"] == "S" else "A"
        tags = ", ".join(item["tags"]) if item["tags"] else ""
        lines.append(
            f"[{icon}|{item['score']}] <b>{item['title']}</b>\n"
            f"<i>{item['comment']}</i>\n"
            f"{tags}\n"
            f"<a href='{item['link']}'>原文</a> | {item['source']}\n"
        )

    return "\n".join(lines)


def send_telegram(text: str):
    """发送消息到 Telegram，自动分段"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    max_len = 3800

    for i in range(0, len(text), max_len):
        chunk = text[i : i + max_len]
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code != 200:
                print(f"[Telegram 发送失败] {resp.text}")
        except Exception as e:
            print(f"[Telegram 网络错误] {e}")


def main():
    print("=== AI 每日情报 Agent 启动 ===")
    all_news = []
    for src in SOURCES:
        all_news.extend(fetch_source(src))

    if not all_news:
        print("今日无 S/A 级内容，不推送。")
        return

    report = build_report(all_news)
    print(f"\n共 {len(all_news)} 条高价值内容，正在推送 Telegram ...")
    send_telegram(report)
    print("推送完成。")


if __name__ == "__main__":
    main()
