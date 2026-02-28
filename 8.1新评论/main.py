"""
社媒辅助搜索引擎 - 主入口

使用方式:
    # 启动 GUI
    python main.py

    # 命令行搜索
    python main.py search "关键词" --platforms bilibili,douyin

    # 启动 GUI（指定端口）
    python main.py gui --port 7861
"""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description='社媒辅助搜索引擎',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # GUI 命令
    gui_parser = subparsers.add_parser('gui', help='启动 GUI 界面')
    gui_parser.add_argument('--host', default='127.0.0.1', help='服务器地址')
    gui_parser.add_argument('--port', type=int, default=7860, help='服务器端口')
    gui_parser.add_argument('--share', action='store_true', help='生成公开链接')

    # 搜索命令
    search_parser = subparsers.add_parser('search', help='命令行搜索')
    search_parser.add_argument('keyword', help='搜索关键词')
    search_parser.add_argument(
        '-p', '--platforms',
        default='bilibili,douyin,xiaohongshu',
        help='平台列表，逗号分隔'
    )
    search_parser.add_argument('-ms', '--max-search', type=int, default=5, help='每平台搜索数')
    search_parser.add_argument('-mc', '--max-comments', type=int, default=50, help='每内容评论数')

    args = parser.parse_args()

    # 默认启动 GUI
    if args.command is None or args.command == 'gui':
        run_gui(args)
    elif args.command == 'search':
        run_search(args)
    else:
        parser.print_help()


def run_gui(args):
    """启动 GUI"""
    from gui import create_app
    import config

    host = getattr(args, 'host', config.GUI_HOST)
    port = getattr(args, 'port', config.GUI_PORT)
    share = getattr(args, 'share', False)

    print(f"\n启动社媒辅助搜索引擎...")
    print(f"地址: http://{host}:{port}")
    print("-" * 40)

    app = create_app()
    app.launch(
        server_name=host,
        server_port=port,
        share=share,
    )


def run_search(args):
    """命令行搜索"""
    from core.engine import SearchEngine
    from storage import Database
    import config

    db = Database(config.DB_PATH)
    engine = SearchEngine(db=db)

    platforms = [p.strip() for p in args.platforms.split(',')]

    print(f"\n{'='*50}")
    print(f"社媒辅助搜索引擎 - 命令行模式")
    print(f"{'='*50}")

    session = engine.search(
        keyword=args.keyword,
        platforms=platforms,
        max_search=args.max_search,
        max_comments=args.max_comments,
    )

    print(f"\n会话ID: {session.session_id}")
    print(f"可使用 GUI 查看详细结果")


if __name__ == '__main__':
    main()
