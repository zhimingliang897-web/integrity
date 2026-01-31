"""LLM 分析任务：筛选、情感分析、摘要、分类"""

import json

from .client import LLMClient


def _batch(items: list, size: int) -> list[list]:
    """将列表按 size 分批"""
    return [items[i:i + size] for i in range(0, len(items), size)]


def _format_comments_for_prompt(comments: list[dict]) -> str:
    """将评论列表格式化为 prompt 文本"""
    lines = []
    for c in comments:
        lines.append(f"[{c['comment_id']}] {c['content']}")
    return "\n".join(lines)


def _parse_json_response(text: str) -> dict:
    """从 LLM 回复中提取 JSON（兼容 markdown 代码块）"""
    text = text.strip()
    if text.startswith("```"):
        # 去掉 ```json ... ```
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)


# ============================================================
# 1. 评论筛选
# ============================================================

def filter_comments(
    client: LLMClient,
    comments: list[dict],
    criteria: str,
    batch_size: int = 50,
) -> list[dict]:
    """
    根据自然语言条件筛选评论

    Args:
        client: LLM 客户端
        comments: 评论列表
        criteria: 筛选条件（自然语言描述）
        batch_size: 每批处理数量

    Returns:
        符合条件的评论列表
    """
    matched_ids = set()
    batches = _batch(comments, batch_size)

    for i, batch in enumerate(batches, 1):
        print(f"  筛选中 [{i}/{len(batches)}]...")
        prompt_text = _format_comments_for_prompt(batch)
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个评论筛选助手。用户会给你一批评论和筛选条件，"
                    "你需要返回符合条件的评论ID列表。\n"
                    "严格按 JSON 数组格式返回，例如: [\"id1\", \"id2\", \"id3\"]\n"
                    "如果没有符合条件的评论，返回空数组: []"
                ),
            },
            {
                "role": "user",
                "content": f"筛选条件: {criteria}\n\n评论列表:\n{prompt_text}",
            },
        ]

        try:
            resp = client.chat(messages)
            ids = _parse_json_response(resp)
            if isinstance(ids, list):
                matched_ids.update(str(x) for x in ids)
        except Exception as e:
            print(f"  第{i}批筛选出错: {e}")

    result = [c for c in comments if str(c["comment_id"]) in matched_ids]
    print(f"  筛选完成: {len(result)}/{len(comments)} 条符合条件")
    return result


# ============================================================
# 2. 情感分析
# ============================================================

def sentiment_analysis(
    client: LLMClient,
    comments: list[dict],
    batch_size: int = 50,
) -> list[dict]:
    """
    对每条评论进行情感分析（正面/中性/负面）

    Returns:
        带有 sentiment 字段的评论列表
    """
    id_to_sentiment = {}
    batches = _batch(comments, batch_size)

    for i, batch in enumerate(batches, 1):
        print(f"  情感分析 [{i}/{len(batches)}]...")
        prompt_text = _format_comments_for_prompt(batch)
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个情感分析助手。对每条评论判断情感倾向。\n"
                    "返回 JSON 对象，key 为评论ID，value 为情感标签。\n"
                    "情感标签只能是: positive（正面）、neutral（中性）、negative（负面）\n"
                    '格式示例: {"id1": "positive", "id2": "negative", "id3": "neutral"}'
                ),
            },
            {
                "role": "user",
                "content": f"请对以下评论进行情感分析:\n{prompt_text}",
            },
        ]

        try:
            resp = client.chat(messages)
            mapping = _parse_json_response(resp)
            if isinstance(mapping, dict):
                id_to_sentiment.update({str(k): v for k, v in mapping.items()})
        except Exception as e:
            print(f"  第{i}批情感分析出错: {e}")

    result = []
    for c in comments:
        new_c = dict(c)
        new_c["sentiment"] = id_to_sentiment.get(str(c["comment_id"]), "unknown")
        result.append(new_c)

    counts = {}
    for c in result:
        s = c["sentiment"]
        counts[s] = counts.get(s, 0) + 1
    print(f"  情感分析完成: {counts}")
    return result


# ============================================================
# 3. 摘要总结
# ============================================================

def summarize_comments(
    client: LLMClient,
    comments: list[dict],
) -> str:
    """
    生成评论整体摘要

    Returns:
        摘要文本
    """
    # 拼接所有评论内容，截断防止超长
    all_text = "\n".join(
        f"- {c['content']}" for c in comments if c.get("content")
    )
    # 限制总长度（大约 15000 字符，留空间给 prompt）
    if len(all_text) > 15000:
        all_text = all_text[:15000] + "\n... (更多评论已省略)"

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个评论分析助手。请对用户提供的评论列表进行整体总结。\n"
                "从以下三个维度进行分析:\n"
                "1. 主要观点: 评论中出现频率最高的观点和话题\n"
                "2. 情感倾向: 整体情感是偏正面、负面还是中性，大致比例\n"
                "3. 高频话题: 评论中反复提及的关键词或主题\n\n"
                "用中文回答，简洁清晰，分点列出。"
            ),
        },
        {
            "role": "user",
            "content": f"以下是 {len(comments)} 条评论，请进行总结分析:\n\n{all_text}",
        },
    ]

    print(f"  正在分析 {len(comments)} 条评论...")
    summary = client.chat(messages, temperature=0.5)
    print("  摘要生成完成")
    return summary


# ============================================================
# 4. 评论分类
# ============================================================

def classify_comments(
    client: LLMClient,
    comments: list[dict],
    categories: list[str],
    batch_size: int = 50,
) -> list[dict]:
    """
    将每条评论分配到指定分类中

    Args:
        client: LLM 客户端
        comments: 评论列表
        categories: 分类标签列表
        batch_size: 每批处理数量

    Returns:
        带有 category 字段的评论列表
    """
    cat_str = "、".join(categories)
    id_to_category = {}
    batches = _batch(comments, batch_size)

    for i, batch in enumerate(batches, 1):
        print(f"  分类中 [{i}/{len(batches)}]...")
        prompt_text = _format_comments_for_prompt(batch)
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个评论分类助手。将每条评论归入指定的分类中。\n"
                    f"可用分类: {cat_str}\n"
                    "返回 JSON 对象，key 为评论ID，value 为分类标签。\n"
                    "每条评论只能归入一个分类。\n"
                    f'格式示例: {{"id1": "{categories[0]}", "id2": "{categories[-1]}"}}'
                ),
            },
            {
                "role": "user",
                "content": f"请对以下评论进行分类:\n{prompt_text}",
            },
        ]

        try:
            resp = client.chat(messages)
            mapping = _parse_json_response(resp)
            if isinstance(mapping, dict):
                id_to_category.update({str(k): v for k, v in mapping.items()})
        except Exception as e:
            print(f"  第{i}批分类出错: {e}")

    result = []
    for c in comments:
        new_c = dict(c)
        new_c["category"] = id_to_category.get(str(c["comment_id"]), "未分类")
        result.append(new_c)

    counts = {}
    for c in result:
        cat = c["category"]
        counts[cat] = counts.get(cat, 0) + 1
    print(f"  分类完成: {counts}")
    return result
