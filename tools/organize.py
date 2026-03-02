"""
organize.py — 智能文件夹整理助手（LLM 驱动）入口

用法:
    python organize.py <目标目录> [--mode agent|scan|classify|clean] [--dry-run]

示例:
    python e:/integrity/tools/organize.py e:/integrity/13course_digest
    python e:/integrity/tools/organize.py e:/integrity/2台词 --dry-run
    python e:/integrity/tools/organize.py e:/integrity/7爬虫 --mode scan
"""

import argparse
import sys
import textwrap
from pathlib import Path

# 把 lib/ 加入包搜索路径
sys.path.insert(0, str(Path(__file__).parent))

from lib.utils   import REPORT_FILE, RED
from lib.llm     import load_api_config
from lib.modes   import mode_scan, mode_classify, mode_clean
from lib.agent   import mode_agent

SCRIPT_DIR = Path(__file__).parent


def main():
    parser = argparse.ArgumentParser(
        description="🗂️  智能文件夹整理助手（LLM 驱动）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        模式:
          agent    LLM 自主探索循环，充分研究后再建议  【默认，推荐】
          scan     一次性扫描分析，生成 organize_report.json
          classify 按 scan 报告执行移动
          clean    按 scan 报告审核删除

        示例:
          python organize.py e:/integrity/13course_digest
          python organize.py e:/integrity/2台词 --dry-run
          python organize.py e:/integrity/7爬虫 --mode scan
          python organize.py e:/integrity/8评论 --mode classify --dry-run
        """),
    )
    parser.add_argument("target",           help="要整理的目录路径（相对或绝对）")
    parser.add_argument("--mode",           choices=["agent", "scan", "classify", "clean"],
                        default="agent",    help="运行模式（默认: agent）")
    parser.add_argument("--dry-run",        action="store_true",
                        help="仅预演，不实际执行任何文件操作")
    parser.add_argument("--api-key",        default="",
                        help="LLM API Key（最高优先级，覆盖配置文件）")
    parser.add_argument("--report",         default="",
                        help=f"scan 报告文件路径（默认: <目标目录>/{REPORT_FILE}）")
    args = parser.parse_args()

    root = Path(args.target).resolve()
    if not root.exists() or not root.is_dir():
        print(RED(f"  [错误] 目录不存在: {root}"))
        sys.exit(1)

    report_path = Path(args.report) if args.report else root / REPORT_FILE
    api_cfg     = load_api_config(SCRIPT_DIR, root, args.api_key)

    dispatch = {
        "agent":    lambda: mode_agent(root, api_cfg, args.dry_run),
        "scan":     lambda: mode_scan(root, api_cfg, report_path),
        "classify": lambda: mode_classify(root, report_path, args.dry_run),
        "clean":    lambda: mode_clean(root, report_path),
    }
    dispatch[args.mode]()


if __name__ == "__main__":
    main()
