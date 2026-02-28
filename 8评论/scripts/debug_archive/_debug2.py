"""最小化调试 - 打印所有拦截到的API URL"""
import sys, time, urllib.parse
sys.path.insert(0, ".")
import config
from playwright.sync_api import sync_playwright

keyword = "iPhone"

# ---- 抖音 ----
print("=== DOUYIN ===")
search_url = f"https://www.douyin.com/search/{urllib.parse.quote(keyword)}?type=video"
captured = []

def dy_handle(response):
    url = response.url
    # 打印所有包含 aweme 的 API
    if "/aweme/" in url and "static" not in url:
        status = response.status
        try:
            body = response.json()
            keys = list(body.keys()) if isinstance(body, dict) else type(body).__name__
            captured.append(body)
            print(f"  [JSON] status={status} keys={keys}")
            print(f"    url={url[:150]}")
            # 如果有 aweme_list, 打印详情
            if "aweme_list" in body and body["aweme_list"]:
                al = body["aweme_list"]
                print(f"    aweme_list: {len(al)} items")
                for a in al[:2]:
                    print(f"      id={a.get('aweme_id')} desc={str(a.get('desc',''))[:50]}")
            if "data" in body and isinstance(body["data"], list) and body["data"]:
                print(f"    data: {len(body['data'])} items")
                for d in body["data"][:2]:
                    if isinstance(d, dict):
                        aw = d.get("aweme_info", d)
                        print(f"      id={aw.get('aweme_id')} desc={str(aw.get('desc',''))[:50]}")
        except:
            print(f"  [NON-JSON] status={status} url={url[:150]}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
        viewport={"width": 1920, "height": 1080},
    )
    if config.DOUYIN_COOKIE:
        cookies = []
        for item in config.DOUYIN_COOKIE.split("; "):
            if "=" in item:
                n, v = item.split("=", 1)
                cookies.append({"name": n.strip(), "value": v.strip(), "domain": ".douyin.com", "path": "/"})
        ctx.add_cookies(cookies)

    page = ctx.new_page()
    page.on("response", dy_handle)
    try:
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"  goto error: {e}")
    time.sleep(10)
    print(f"\nCaptured {len(captured)} JSON responses with /aweme/ pattern")
    browser.close()
