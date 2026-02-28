"""评论数据导出工具"""

import os
from datetime import datetime

import pandas as pd


def export_comments(
    comments: list[dict],
    platform: str,
    output_dir: str = "output",
    fmt: str = "csv",
) -> str:
    """
    将评论列表导出为 CSV 或 Excel 文件

    Args:
        comments: 评论字典列表
        platform: 平台名称（用于文件命名）
        output_dir: 输出目录
        fmt: 导出格式，"csv" 或 "excel"

    Returns:
        导出文件的路径
    """
    if not comments:
        print("没有评论数据可导出")
        return ""

    os.makedirs(output_dir, exist_ok=True)

    df = pd.DataFrame(comments)

    # 列顺序：基础列 + 分析结果列（如有）
    base_columns = [
        "platform", "comment_id", "username", "content",
        "like_count", "reply_count", "create_time", "ip_location",
    ]
    extra_columns = [c for c in df.columns if c not in base_columns]
    columns = base_columns + extra_columns
    df = df.reindex(columns=[c for c in columns if c in df.columns])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if fmt == "excel":
        filename = f"{platform}_comments_{timestamp}.xlsx"
        filepath = os.path.join(output_dir, filename)
        df.to_excel(filepath, index=False, engine="openpyxl")
    else:
        filename = f"{platform}_comments_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False, encoding="utf-8-sig")

    print(f"已导出 {len(comments)} 条评论到 {filepath}")
    return filepath
