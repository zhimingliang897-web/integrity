import os
import json
import requests
import feedparser
from openai import OpenAI
from datetime import datetime, timezone, timedelta

# --- 配置 ---
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1003878273027")
MODEL_NAME = "qwen3-vl-flash-2026-01-22"
TARGET_COUNT = 10  # 目标推送条数

client = OpenAI(
    api_key=QWEN_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# --- 信源列表 ---
SOURCES = [
    # ===== 国际硬核 =====
    {
        "name": "Hacker News",
        "url": "https://hnrss.org/newest?q=AI+LLM+Transformer+GPT",
        "type": "general",
        "count": 8,
    },
    {
        "name": "HF Papers",
        "url": "https://rsshub.app/huggingface/daily-papers",
        "type": "general",
        "count": 8,
    },
    {
        "name": "GitHub Trending",
        "url": "https://rsshub.app/github/trending/daily/python?since=daily",
        "type": "general",
        "count": 6,
    },
    {
        "name": "ArXiv cs.AI",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "type": "general",
        "count": 6,
    },
    {
        "name": "ArXiv cs.CL",
        "url": "https://rss.arxiv.org/rss/cs.CL",
        "type": "general",
        "count": 6,
    },
    # ===== 国际社区 =====
    {
        "name": "Reddit LocalLLaMA",
        "url": "https://www.reddit.com/r/LocalLLaMA/.rss",
        "type": "general",
        "count": 6,
    },
    {
        "name": "Reddit MachineLearning",
        "url": "https://www.reddit.com/r/MachineLearning/.rss",
        "type": "general",
        "count": 6,
    },
    {
        "name": "OpenAI Blog",
        "url": "https://rsshub.app/openai/blog",
        "type": "general",
        "count": 5,
    },
    {
        "name": "Google AI Blog",
        "url": "https://rsshub.app/google/research",
        "type": "general",
        "count": 5,
    },
    {
        "name": "MIT Tech Review AI",
        "url": "https://www.technologyreview.com/feed/",
        "type": "general",
        "count": 5,
    },
    # ===== 国内权威 =====
    {
        "name": "机器之心",
        "url": "https://www.jiqizhixin.com/rss",
        "type": "cn_media",
        "count": 6,
    },
    {
        "name": "量子位",
        "url": "https://rsshub.app/qbitai/category/资讯",
        "type": "cn_media",
        "count": 6,
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
            "注意：本文来自中文自媒体，请适当忽略'炸裂''颠覆''神作'等营销词汇，"
            "侧重关注是否有代码/论文/实质技术内容。但如果底层内容确实有价值，不要因为标题夸张就降分。"
        )

    prompt = f"""你是一位 AI 技术情报分析师，负责为技术从业者筛选每日值得关注的内容。
{anti_hype}

请分析以下新闻：
标题：{title}
摘要：{summary}

评级标准（请合理给分，不要过于苛刻）：
- S级 (9-10): 行业里程碑事件、颠覆性架构突破、重量级产品发布。
- A级 (7-8): 高质量论文、实用工具重大更新、大厂重要开源、值得关注的行业动态。
- B级 (5-6): 有一定参考价值的内容、中等质量的技术分享、普通产品迭代。
- C级 (1-4): 纯水文、无实质内容的公关稿、重复旧闻。

请只输出一个合法 JSON，不要包含 Markdown 代码块标记：
{{"rating":"S/A/B/C","score":整数1到10,"comment":"一句话点评(中文,30字内)","tags":["标签1","标签2"]}}"""

    text = call_qwen(prompt)
    if not text:
        return None

    clean = text.replace("```json", "").replace("```", "").strip()
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
    """抓取单个 RSS 信源并评级，返回带评分的条目列表"""
    name = source["name"]
    count = source.get("count", 5)
    print(f">> 正在抓取: {name} ...")
    try:
        feed = feedparser.parse(source["url"])
    except Exception as e:
        print(f"[RSS 抓取失败] {name}: {e}")
        return []

    if not feed.entries:
        print(f"   (无内容)")
        return []

    results = []
    for entry in feed.entries[:count]:
        title = getattr(entry, "title", "").strip()
        summary = getattr(entry, "summary", "")[:800]
        link = getattr(entry, "link", "")
        if not title:
            continue

        analysis = analyze_news(title, summary, source["type"])
        if not analysis:
            continue

        rating = analysis.get("rating", "C")
        score = analysis.get("score", 0)
        results.append(
            {
                "source": name,
                "title": title,
                "link": link,
                "rating": rating,
                "score": score,
                "comment": analysis.get("comment", ""),
                "tags": analysis.get("tags", []),
            }
        )
        print(f"   [{rating}|{score}] {title}")

    return results


def select_top_news(all_news: list[dict]) -> list[dict]:
    """按评分排序，优先 S/A，不够则补 B 级，目标 TARGET_COUNT 条"""
    all_news.sort(key=lambda x: x["score"], reverse=True)

    # 去重：同标题只保留最高分
    seen = set()
    unique = []
    for item in all_news:
        key = item["title"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    # 先选 S/A 级
    selected = [n for n in unique if n["rating"] in ("S", "A")]

    # 不够则补 B 级
    if len(selected) < TARGET_COUNT:
        b_pool = [n for n in unique if n["rating"] == "B"]
        selected.extend(b_pool[: TARGET_COUNT - len(selected)])

    # 最终按分数排序
    selected.sort(key=lambda x: x["score"], reverse=True)
    return selected


def generate_summary(news_list: list[dict]) -> str:
    """让 LLM 生成今日总结概览"""
    headlines = "\n".join(
        [f"- [{n['rating']}|{n['score']}] {n['title']}" for n in news_list]
    )

    prompt = f"""你是一位 AI 领域情报编辑。以下是今天筛选出的高价值 AI 新闻标题列表：

{headlines}

请用中文写一段 3-5 句话的「今日概览」，概括今天 AI 领域的整体动态和最值得关注的方向。
要求：语言简洁有洞察力，像一位资深编辑写的晨报导语，不要用 Markdown 格式。"""

    result = call_qwen(prompt)
    return result.strip() if result else "今日 AI 领域动态汇总如下。"


def build_report(news_list: list[dict], summary: str) -> str:
    """构建 Telegram HTML 格式日报：总结在前，逐条在后"""
    bj_time = datetime.now(timezone(timedelta(hours=8)))
    today = bj_time.strftime("%Y-%m-%d")

    lines = []
    # ===== 标题 =====
    lines.append(f"<b>📡 AI 每日情报 | {today}</b>")
    lines.append("")

    # ===== 今日概览 =====
    lines.append("<b>🧭 今日概览</b>")
    lines.append(f"<i>{summary}</i>")
    lines.append("")
    lines.append(f"共筛选 <b>{len(news_list)}</b> 条值得关注的内容：")
    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("")

    # ===== 逐条展示 =====
    for i, item in enumerate(news_list, 1):
        # 评级 icon
        if item["rating"] == "S":
            badge = "🔴 S"
        elif item["rating"] == "A":
            badge = "🟠 A"
        else:
            badge = "🟡 B"

        tags = " ".join([f"#{t}" for t in item["tags"]]) if item["tags"] else ""

        lines.append(f"<b>{i}. {item['title']}</b>")
        lines.append(f"   {badge} · {item['score']}分 · {item['source']}")
        lines.append(f"   💬 {item['comment']}")
        if tags:
            lines.append(f"   {tags}")
        lines.append(f"   🔗 <a href='{item['link']}'>阅读原文</a>")
        lines.append("")

    # ===== 尾部 =====
    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("<i>🤖 由 AI 情报 Agent 自动生成</i>")

    return "\n".join(lines)


def send_telegram(text: str):
    """发送消息到 Telegram，按段落智能分割"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    max_len = 3800

    # 按空行分段，尽量不在条目中间截断
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 > max_len:
            if current:
                chunks.append(current)
            current = para
        else:
            current = current + "\n\n" + para if current else para

    if current:
        chunks.append(current)

    for chunk in chunks:
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
    print("=== AI 每日情报 Agent 启动 ===\n")
    all_news = []
    for src in SOURCES:
        all_news.extend(fetch_source(src))

    print(f"\n共抓取并评级 {len(all_news)} 条内容")

    # 筛选 top N
    selected = select_top_news(all_news)
    if not selected:
        print("今日无值得推送的内容。")
        return

    print(f"筛选出 {len(selected)} 条推送内容，正在生成总结 ...")

    # LLM 生成今日总结
    summary = generate_summary(selected)
    print(f"今日概览: {summary}\n")

    # 构建并发送报告
    report = build_report(selected, summary)
    print("正在推送 Telegram ...")
    send_telegram(report)
    print("推送完成。")


if __name__ == "__main__":
    main()
