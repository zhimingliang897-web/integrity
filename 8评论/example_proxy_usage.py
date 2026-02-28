"""代理池使用示例"""

from utils.proxy import ProxyPool, ProxyRotator, init_global_proxy_pool
from scrapers.douyin import DouyinScraper
from scrapers.xiaohongshu import XiaohongshuScraper


# ========== 方式1: 直接在代码中定义代理列表 ==========
def example_inline_proxies():
    """直接在代码中定义代理"""
    proxies = [
        "http://127.0.0.1:7890",  # 本地代理
        "http://username:password@proxy.example.com:8080",  # 带认证的代理
        "socks5://127.0.0.1:1080",  # SOCKS5 代理
    ]

    # 创建代理池
    pool = ProxyPool(proxies)

    # 验证代理可用性（可选）
    # pool.validate_all()

    # 使用代理池抓取评论
    scraper = DouyinScraper(
        cookie="你的抖音Cookie",
        speed="normal",
        proxy_pool=pool  # 传入代理池
    )

    comments = scraper.fetch_comments(
        url="https://www.douyin.com/video/7xxxxxxxxxxxxxxxxx",
        max_count=100
    )

    print(f"抓取到 {len(comments)} 条评论")


# ========== 方式2: 从文件加载代理 ==========
def example_load_from_file():
    """从文件加载代理列表"""
    pool = ProxyPool()
    pool.load_from_file("proxies.txt")  # 从 proxies.txt 加载代理

    # 可选：验证所有代理是否可用
    pool.validate_all()

    # 使用代理池
    scraper = XiaohongshuScraper(
        cookie="你的小红书Cookie",
        speed="safe",
        proxy_pool=pool
    )

    comments = scraper.fetch_comments(
        url="https://www.xiaohongshu.com/explore/xxxxxxxxxxxxxxxx",
        max_count=50
    )

    print(f"抓取到 {len(comments)} 条评论")


# ========== 方式3: 使用代理轮换器（定期切换IP） ==========
def example_proxy_rotator():
    """使用代理轮换器，每N次请求自动切换IP"""
    pool = ProxyPool()
    pool.load_from_file("proxies.txt")

    # 创建轮换器：每5次请求切换一次代理
    rotator = ProxyRotator(pool, rotate_interval=5)

    # 多次抓取任务
    urls = [
        "https://www.douyin.com/video/7111111111111111111",
        "https://www.douyin.com/video/7222222222222222222",
        "https://www.douyin.com/video/7333333333333333333",
    ]

    for url in urls:
        # 获取当前代理
        current_proxy = rotator.get_proxy()

        # 创建临时代理池（只包含当前代理）
        temp_pool = ProxyPool()
        if current_proxy:
            temp_pool.add_proxy(current_proxy.get("server"))

        scraper = DouyinScraper(
            cookie="你的Cookie",
            proxy_pool=temp_pool
        )

        comments = scraper.fetch_comments(url, max_count=50)
        print(f"抓取到 {len(comments)} 条评论")


# ========== 方式4: 抓取免费代理（不推荐，仅供测试） ==========
def example_free_proxies():
    """抓取免费代理（质量差，仅供测试）"""
    pool = ProxyPool()

    # 抓取10个免费代理
    pool.fetch_free_proxies(count=10)

    # 验证可用性（免费代理大多不可用）
    pool.validate_all()

    if len(pool) > 0:
        print(f"可用代理数: {len(pool)}")
        scraper = DouyinScraper(cookie="你的Cookie", proxy_pool=pool)
        # ... 使用爬虫
    else:
        print("没有可用的免费代理")


# ========== 方式5: 全局代理池（推荐） ==========
def example_global_pool():
    """初始化全局代理池，在整个应用中共享"""
    # 初始化全局代理池
    init_global_proxy_pool(
        proxy_file="proxies.txt",
        validate=True  # 自动验证代理可用性
    )

    # 在任何地方使用全局代理池
    from utils.proxy import get_global_proxy_pool

    pool = get_global_proxy_pool()

    scraper = DouyinScraper(
        cookie="你的Cookie",
        proxy_pool=pool
    )

    comments = scraper.fetch_comments(
        url="https://www.douyin.com/video/7xxxxxxxxxxxxxxxxx",
        max_count=100
    )


# ========== 方式6: 不使用代理（默认行为） ==========
def example_no_proxy():
    """不使用代理，直连抓取"""
    scraper = DouyinScraper(
        cookie="你的Cookie",
        speed="normal"
        # 不传入 proxy_pool 参数，直连抓取
    )

    comments = scraper.fetch_comments(
        url="https://www.douyin.com/video/7xxxxxxxxxxxxxxxxx",
        max_count=100
    )


if __name__ == "__main__":
    print("=" * 60)
    print("代理池使用示例")
    print("=" * 60)
    print("\n请根据你的需求选择合适的方式：")
    print("1. example_inline_proxies()    - 代码中直接定义代理")
    print("2. example_load_from_file()    - 从文件加载代理")
    print("3. example_proxy_rotator()     - 使用代理轮换器")
    print("4. example_free_proxies()      - 抓取免费代理（不推荐）")
    print("5. example_global_pool()       - 全局代理池（推荐）")
    print("6. example_no_proxy()          - 不使用代理\n")

    # 取消注释以运行示例
    # example_load_from_file()
