"""调试搜索器 - 截图+打印所有拦截到的响应"""
import sys
import time
import urllib.parse
sys.path.insert(0, ".")
import config

from playwright.sync_api import sync_playwright

def debug_douyin():
    keyword = "iPhone"
    search_url = f"https://www.douyin.com/search/{urllib.parse.quote(keyword)}?type=video"

    all_responses = []

    def handle_response(response):
        url = response.url
        # 记录所有API响应
        if "search" in url or "aweme" in url:
            try:
                data = response.json()
                all_responses.append({"url": url[:120], "keys": list(data.keys()) if isinstance(data, dict) else type(data).__name__})
            except:
                all_responses.append({"url": url[:120], "type": "non-json"})

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"
            ),
            viewport={"width": 1920, "height": 1080},
        )

        if config.DOUYIN_COOKIE:
            cookies = []
            for item in config.DOUYIN_COOKIE.split("; "):
                if "=" in item:
                    name, value = item.split("=", 1)
                    cookies.append({"name": name.strip(), "value": value.strip(), "domain": ".douyin.com", "path": "/"})
            context.add_cookies(cookies)

        page = context.new_page()
        page.on("response", handle_response)

        print(f"[抖音] 打开: {search_url}")
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"  goto异常: {e}")

        time.sleep(8)

        # 截图
        page.screenshot(path="_debug_douyin.png", full_page=False)
        print(f"  截图已保存: _debug_douyin.png")
        print(f"  当前URL: {page.url}")
        print(f"  页面标题: {page.title()}")

        # 打印拦截到的响应
        print(f"\n  拦截到 {len(all_responses)} 个相关响应:")
        for r in all_responses:
            print(f"    {r}")

        browser.close()

def debug_xiaohongshu():
    keyword = "iPhone"
    search_url = (
        f"https://www.xiaohongshu.com/search_result"
        f"?keyword={urllib.parse.quote(keyword)}"
        f"&source=web_search_result_note"
    )

    all_responses = []

    def handle_response(response):
        url = response.url
        if "search" in url or "note" in url:
            try:
                data = response.json()
                all_responses.append({"url": url[:120], "keys": list(data.keys()) if isinstance(data, dict) else type(data).__name__})
            except:
                all_responses.append({"url": url[:120], "type": "non-json", "status": response.status})

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )

        if config.XIAOHONGSHU_COOKIE:
            cookies = []
            for item in config.XIAOHONGSHU_COOKIE.split("; "):
                if "=" in item:
                    name, value = item.split("=", 1)
                    cookies.append({"name": name.strip(), "value": value.strip(), "domain": ".xiaohongshu.com", "path": "/"})
            context.add_cookies(cookies)

        page = context.new_page()
        page.on("response", handle_response)

        print(f"\n[小红书] 打开: {search_url}")
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"  goto异常: {e}")

        time.sleep(8)

        # 截图
        page.screenshot(path="_debug_xiaohongshu.png", full_page=False)
        print(f"  截图已保存: _debug_xiaohongshu.png")
        print(f"  当前URL: {page.url}")
        print(f"  页面标题: {page.title()}")

        # 打印拦截到的响应
        print(f"\n  拦截到 {len(all_responses)} 个相关响应:")
        for r in all_responses:
            print(f"    {r}")

        browser.close()

if __name__ == "__main__":
    debug_douyin()
    print("\n" + "="*60 + "\n")
    debug_xiaohongshu()
