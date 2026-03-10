"""
Cookie管理器 - 自动化获取小红书Cookie
通过Playwright打开浏览器，用户登录后自动提取Cookie
"""

import asyncio
import json
from pathlib import Path
from typing import Optional
import yaml


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_config(config: dict):
    """保存配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


class CookieManager:
    """Cookie管理器"""

    COOKIE_FILE = Path(__file__).parent / "cookies.json"
    XHS_URL = "https://www.xiaohongshu.com"

    def __init__(self):
        self.cookies = None

    async def get_cookie_interactive(self, headless: bool = False) -> str:
        """
        交互式获取Cookie - 打开浏览器让用户登录

        Args:
            headless: 是否无头模式（默认False，显示浏览器窗口）

        Returns:
            Cookie字符串
        """
        from playwright.async_api import async_playwright

        print("=" * 50)
        print("小红书Cookie获取向导")
        print("=" * 50)
        print("即将打开浏览器，请在浏览器中登录小红书账号")
        print("登录成功后，程序会自动获取Cookie")
        print("=" * 50)

        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=headless,
                args=['--start-maximized']
            )

            # 创建上下文（可以保存登录状态）
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            # 如果有保存的cookies，先加载
            if self.COOKIE_FILE.exists():
                try:
                    with open(self.COOKIE_FILE, 'r') as f:
                        cookies = json.load(f)
                        await context.add_cookies(cookies)
                        print("已加载历史Cookie，尝试自动登录...")
                except:
                    pass

            page = await context.new_page()

            # 访问小红书
            await page.goto(self.XHS_URL)

            print("\n请在浏览器中完成登录...")
            print("登录成功后会自动检测（最长等待5分钟）\n")

            # 先记录初始的cookie，用于对比
            initial_cookies = await context.cookies()
            initial_cookie_names = set(c['name'] for c in initial_cookies)

            # 等待用户登录 - 自动检测登录状态
            max_wait = 300  # 最多等待5分钟
            check_interval = 3  # 每3秒检查一次
            dots = 0
            login_detected = False

            # 登录后才会出现的关键cookie（不包括访问时就有的a1, webId等）
            login_cookies = ['customer-sso-sid', 'access_token', 'access-token', 'web_session', 'galaxy_creator_session_id', 'gid']

            for i in range(max_wait // check_interval):
                await asyncio.sleep(check_interval)

                # 显示等待动画和时间
                dots = (dots + 1) % 4
                elapsed = (i + 1) * check_interval
                print(f"\r等待登录中{'.' * dots}{' ' * (3 - dots)} ({elapsed}秒)", end='', flush=True)

                # 检查是否已登录
                try:
                    # 获取当前页面的cookies
                    current_cookies = await context.cookies()
                    current_cookie_names = set(c['name'] for c in current_cookies)

                    # 检查是否有新增的登录cookie
                    new_cookies = current_cookie_names - initial_cookie_names
                    has_login_cookie = any(name in current_cookie_names for name in login_cookies)

                    # 也检查页面是否有登录后的用户元素（更严格的选择器）
                    has_user_element = await page.evaluate('''() => {
                        // 检查是否有用户昵称或头像
                        const hasNickname = document.querySelector('.user-nickname') !== null ||
                                           document.querySelector('[class*="nickname"]') !== null;
                        const hasLoggedInAvatar = document.querySelector('.logged-in') !== null ||
                                                  document.querySelector('[class*="logged"]') !== null;
                        // 检查URL是否变化（登录后可能跳转）
                        const isHomePage = window.location.pathname === '/' ||
                                          window.location.pathname.includes('/user/');
                        return hasNickname || hasLoggedInAvatar;
                    }''')

                    # 需要有登录cookie才算登录成功
                    if has_login_cookie:
                        print(f"\n\n✅ 检测到已登录！（发现登录Cookie）")
                        print("等待10秒后获取Cookie（可继续操作浏览器）...")
                        await asyncio.sleep(100)  # 等待10秒让用户有时间操作
                        login_detected = True
                        break
                    elif len(new_cookies) > 3 and has_user_element:
                        # 有多个新cookie且有用户元素
                        print(f"\n\n✅ 检测到已登录！（发现用户信息）")
                        print("等待10秒后获取Cookie（可继续操作浏览器）...")
                        await asyncio.sleep(100)
                        login_detected = True
                        break
                except Exception as e:
                    pass

            if not login_detected:
                print("\n\n⚠️ 等待超时，尝试获取当前Cookie...")

            # 获取所有cookies
            cookies = await context.cookies()

            # 保存cookies到文件
            with open(self.COOKIE_FILE, 'w') as f:
                json.dump(cookies, f, indent=2)

            # 分离两个域名的cookie
            xhs_cookies = [c for c in cookies if 'xiaohongshu.com' in c.get('domain', '')]
            rednote_cookies = [c for c in cookies if 'rednote.com' in c.get('domain', '')]

            # 判断用户登录的是哪个版本（检查web_session）
            xhs_has_session = any(c['name'] == 'web_session' for c in xhs_cookies)
            rednote_has_session = any(c['name'] == 'web_session' for c in rednote_cookies)

            if rednote_has_session and not xhs_has_session:
                # 用户登录的是国际版
                target_cookies = rednote_cookies
                print("检测到登录的是国际版(rednote.com)")
            else:
                # 默认使用国内版
                target_cookies = xhs_cookies
                if xhs_has_session:
                    print("检测到登录的是国内版(xiaohongshu.com)")

            # 转换为cookie字符串（只使用目标域名的cookie）
            cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in target_cookies])

            await browser.close()

            return cookie_str

    def get_cookie_sync(self, headless: bool = False) -> str:
        """同步版本的获取Cookie"""
        return asyncio.run(self.get_cookie_interactive(headless))

    def save_cookie_to_config(self, cookie: str):
        """保存Cookie到配置文件"""
        config = load_config()
        if 'xiaohongshu' not in config:
            config['xiaohongshu'] = {}
        config['xiaohongshu']['cookie'] = cookie
        save_config(config)
        print(f"Cookie已保存到配置文件")

    def get_saved_cookie(self) -> Optional[str]:
        """获取已保存的Cookie"""
        config = load_config()
        return config.get('xiaohongshu', {}).get('cookie', '')

    def validate_cookie(self, cookie: str) -> bool:
        """验证Cookie是否有效（仅检查格式，不调用API）"""
        if not cookie or len(cookie) < 50:
            print("Cookie为空或太短")
            return False

        import re

        def extract_cookie_value(cookie_str: str, key: str) -> str:
            match = re.search(rf'{key}=([^;]+)', cookie_str)
            return match.group(1) if match else ""

        a1 = extract_cookie_value(cookie, 'a1')
        web_session = extract_cookie_value(cookie, 'web_session')

        if a1 and web_session:
            print(f"✅ Cookie格式有效！")
            print(f"   a1: {a1[:15]}...")
            print(f"   web_session: {web_session[:15]}...")
            return True
        elif a1:
            print(f"⚠️ Cookie缺少web_session，可能无法发布")
            return True
        else:
            print("❌ Cookie格式无效：缺少必要字段")
            return False


def get_cookie_auto() -> str:
    """
    自动获取Cookie的便捷函数

    Returns:
        Cookie字符串
    """
    manager = CookieManager()

    # 先检查已保存的Cookie是否有效
    saved_cookie = manager.get_saved_cookie()
    if saved_cookie:
        print("检查已保存的Cookie...")
        if manager.validate_cookie(saved_cookie):
            return saved_cookie
        print("已保存的Cookie已失效，需要重新登录")

    # 打开浏览器获取新Cookie
    cookie = manager.get_cookie_sync()

    # 只要cookie不为空就保存
    if cookie and len(cookie) > 50:
        manager.save_cookie_to_config(cookie)
        manager.validate_cookie(cookie)  # 尝试验证但不阻止
        return cookie
    else:
        raise ValueError("获取的Cookie为空，请重试")


def refresh_cookie():
    """强制刷新Cookie"""
    manager = CookieManager()
    cookie = manager.get_cookie_sync()

    # 只要cookie不为空就保存
    if cookie and len(cookie) > 50:
        manager.save_cookie_to_config(cookie)
        # 尝试验证，但不影响保存
        manager.validate_cookie(cookie)
        print("Cookie刷新成功！")
        return cookie
    else:
        print("Cookie刷新失败：未获取到有效Cookie")
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="小红书Cookie管理工具")
    parser.add_argument("--refresh", action="store_true", help="强制刷新Cookie")
    parser.add_argument("--validate", action="store_true", help="验证当前Cookie")

    args = parser.parse_args()

    manager = CookieManager()

    if args.validate:
        cookie = manager.get_saved_cookie()
        if cookie:
            manager.validate_cookie(cookie)
        else:
            print("未找到已保存的Cookie")
    elif args.refresh:
        refresh_cookie()
    else:
        # 默认：自动获取
        get_cookie_auto()
