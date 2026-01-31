"""社交媒体评论抓取 & 分析工具 — 命令行入口"""

import os
import sys
import argparse

import pandas as pd

import config
from scrapers import BilibiliScraper, DouyinScraper, XiaohongshuScraper
from utils.export import export_comments


PLATFORM_MAP = {
    "bilibili": {
        "class": BilibiliScraper,
        "cookie_key": "BILIBILI_COOKIE",
        "name": "B站",
    },
    "douyin": {
        "class": DouyinScraper,
        "cookie_key": "DOUYIN_COOKIE",
        "name": "抖音",
    },
    "xiaohongshu": {
        "class": XiaohongshuScraper,
        "cookie_key": "XIAOHONGSHU_COOKIE",
        "name": "小红书",
    },
}


# ============================================================
# scrape 子命令
# ============================================================

def cmd_scrape(args):
    """执行评论抓取"""
    platform_info = PLATFORM_MAP[args.platform]
    cookie = getattr(config, platform_info["cookie_key"], "")

    print(f"=== {platform_info['name']}评论抓取工具 ===\n")

    speed = args.speed or getattr(config, "DEFAULT_SPEED", "normal")
    scraper = platform_info["class"](cookie=cookie, speed=speed)

    try:
        max_count = 999999999 if args.all else args.max
        comments = scraper.fetch_comments(args.url, max_count=max_count)
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断抓取")
        sys.exit(0)

    if not comments:
        print("未获取到评论数据")
        sys.exit(0)

    output_dir = args.output or config.OUTPUT_DIR
    output_fmt = args.format or config.OUTPUT_FORMAT
    export_comments(
        comments=comments,
        platform=args.platform,
        output_dir=output_dir,
        fmt=output_fmt,
    )


# ============================================================
# analyze 子命令
# ============================================================

def cmd_analyze(args):
    """执行 LLM 评论分析"""
    from datetime import datetime
    from analyzer.client import LLMClient
    from analyzer import tasks

    # 检查 LLM 配置
    base_url = getattr(config, "LLM_BASE_URL", "")
    api_key = getattr(config, "LLM_API_KEY", "")
    model = getattr(config, "LLM_MODEL", "")

    if not api_key:
        print("错误: 请先在 config.py 中配置 LLM_API_KEY")
        sys.exit(1)
    if not base_url:
        print("错误: 请先在 config.py 中配置 LLM_BASE_URL")
        sys.exit(1)

    # 读取输入文件
    input_path = args.input
    if not os.path.exists(input_path):
        print(f"错误: 文件不存在 — {input_path}")
        sys.exit(1)

    # 从输入文件名提取来源标识（如 bilibili_comments_20260131_120000 → bilibili）
    source_name = os.path.splitext(os.path.basename(input_path))[0]

    task = args.task
    print(f"=== 评论分析工具 ===\n")
    print(f"输入文件: {input_path}")
    print(f"分析任务: {task}")
    print(f"LLM 模型: {model}\n")

    if input_path.endswith(".xlsx"):
        df = pd.read_excel(input_path)
    else:
        df = pd.read_csv(input_path)

    comments = df.to_dict("records")
    if not comments:
        print("输入文件中没有评论数据")
        sys.exit(0)

    print(f"共读取 {len(comments)} 条评论\n")

    # 初始化 LLM 客户端
    client = LLMClient(base_url=base_url, api_key=api_key, model=model)
    batch_size = getattr(config, "LLM_BATCH_SIZE", 50)

    # 分析结果保存到 output/analysis/ 子目录
    base_output = args.output or config.OUTPUT_DIR
    analysis_dir = os.path.join(base_output, "analysis")
    os.makedirs(analysis_dir, exist_ok=True)

    # all 任务需要 filter 的默认条件和 classify 的默认分类
    if task == "all":
        if not args.criteria:
            args.criteria = "有价值的、包含具体观点或反馈的评论"
        if not args.categories:
            args.categories = "好评,差评,建议,提问,闲聊"

    # 确定要执行的任务列表
    if task == "all":
        task_list = ["sentiment", "summary", "classify", "filter"]
    else:
        task_list = [task]

    for current_task in task_list:
        if len(task_list) > 1:
            print(f"\n{'─'*50}")
            print(f"  [{task_list.index(current_task)+1}/{len(task_list)}] 正在执行: {current_task}")
            print(f"{'─'*50}\n")

        if current_task == "filter":
            criteria = args.criteria
            if not criteria:
                print("错误: filter 任务需要 --criteria 参数指定筛选条件")
                sys.exit(1)
            print(f"筛选条件: {criteria}\n")
            result = tasks.filter_comments(client, comments, criteria, batch_size)
            if result:
                path = os.path.join(analysis_dir, f"{source_name}_filter.csv")
                _save_csv(result, path)
            else:
                print("没有符合条件的评论")

        elif current_task == "sentiment":
            result = tasks.sentiment_analysis(client, comments, batch_size)
            path = os.path.join(analysis_dir, f"{source_name}_sentiment.csv")
            _save_csv(result, path)

        elif current_task == "summary":
            summary = tasks.summarize_comments(client, comments)
            print(f"\n{'='*50}")
            print("评论摘要:")
            print('='*50)
            print(summary)
            print('='*50)
            summary_path = os.path.join(analysis_dir, f"{source_name}_summary.txt")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary)
            print(f"\n摘要已保存到 {summary_path}")

        elif current_task == "classify":
            categories_str = args.categories
            if not categories_str:
                print("错误: classify 任务需要 --categories 参数指定分类标签")
                print('示例: --categories "好评,差评,建议,提问"')
                sys.exit(1)
            categories = [c.strip() for c in categories_str.split(",") if c.strip()]
            print(f"分类标签: {categories}\n")
            result = tasks.classify_comments(client, comments, categories, batch_size)
            path = os.path.join(analysis_dir, f"{source_name}_classify.csv")
            _save_csv(result, path)

    if len(task_list) > 1:
        print(f"\n{'='*50}")
        print(f"  全部分析任务完成！结果保存在: {analysis_dir}")
        print(f"{'='*50}")


def _save_csv(data: list[dict], path: str):
    """将分析结果保存为 CSV"""
    df = pd.DataFrame(data)
    base_columns = [
        "platform", "comment_id", "username", "content",
        "like_count", "reply_count", "create_time", "ip_location",
    ]
    extra_columns = [c for c in df.columns if c not in base_columns]
    columns = [c for c in base_columns + extra_columns if c in df.columns]
    df = df.reindex(columns=columns)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  已保存 {len(data)} 条数据到 {path}")


# ============================================================
# 命令行解析
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="社交媒体评论抓取 & 分析工具 — 支持B站、抖音、小红书"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # ---------- scrape 子命令 ----------
    sp_scrape = subparsers.add_parser("scrape", help="抓取评论")
    sp_scrape.add_argument(
        "--platform", "-p",
        required=True,
        choices=PLATFORM_MAP.keys(),
        help="目标平台: bilibili / douyin / xiaohongshu",
    )
    sp_scrape.add_argument(
        "--url", "-u",
        required=True,
        help="视频/笔记链接或ID",
    )
    sp_scrape.add_argument(
        "--max", "-m",
        type=int,
        default=100,
        help="最大抓取评论数 (默认: 100)",
    )
    sp_scrape.add_argument(
        "--all", "-a",
        action="store_true",
        help="抓取全部评论（忽略 --max 限制）",
    )
    sp_scrape.add_argument(
        "--format", "-f",
        choices=["csv", "excel"],
        default=None,
        help="导出格式: csv / excel (默认从 config.py 读取)",
    )
    sp_scrape.add_argument(
        "--output", "-o",
        default=None,
        help="输出目录 (默认从 config.py 读取)",
    )
    sp_scrape.add_argument(
        "--speed", "-s",
        choices=["fast", "normal", "slow", "safe"],
        default=None,
        help="速度档位: fast/normal/slow/safe (默认从 config.py 读取)",
    )

    # ---------- analyze 子命令 ----------
    sp_analyze = subparsers.add_parser("analyze", help="LLM 分析评论")
    sp_analyze.add_argument(
        "--input", "-i",
        required=True,
        help="输入文件路径 (CSV 或 Excel)",
    )
    sp_analyze.add_argument(
        "--task", "-t",
        required=True,
        choices=["filter", "sentiment", "summary", "classify", "all"],
        help="分析任务: filter / sentiment / summary / classify / all(一键全部)",
    )
    sp_analyze.add_argument(
        "--criteria", "-c",
        default=None,
        help="filter 任务的筛选条件 (自然语言描述)",
    )
    sp_analyze.add_argument(
        "--categories",
        default=None,
        help='classify 任务的分类标签 (逗号分隔，如 "好评,差评,建议,提问")',
    )
    sp_analyze.add_argument(
        "--output", "-o",
        default=None,
        help="输出目录 (默认从 config.py 读取)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "scrape":
        cmd_scrape(args)
    elif args.command == "analyze":
        cmd_analyze(args)


if __name__ == "__main__":
    main()
