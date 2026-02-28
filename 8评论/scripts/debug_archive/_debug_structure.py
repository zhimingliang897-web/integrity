"""检查拦截到的API响应的具体数据结构"""
import sys, time, json, urllib.parse
sys.path.insert(0, ".")
import config
from playwright.sync_api import sync_playwright

def debug_douyin_structure():
    keyword = "iPhone"
    search_url = f"https://www.douyin.com/search/{urllib.parse.quote(keyword)}?type=video"
    collected = []

    def handle(response):
        if "search/item" in response.url or "general/search" in response.url:
            try:
                data = response.json()
                collected.append(data)
            except: pass

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
        page.on("response", handle)
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        except: pass
        time.sleep(8)
        browser.close()

    print(f"=== DOUYIN: {len(collected)} responses ===")
    for i, d in enumerate(collected):
        print(f"\n--- Response {i} ---")
        print(f"Top keys: {list(d.keys())}")
        # check data key
        if "data" in d:
            val = d["data"]
            print(f"  d['data'] type={type(val).__name__}, len={len(val) if isinstance(val, (list, dict)) else 'N/A'}")
            if isinstance(val, list) and val:
                print(f"  d['data'][0] keys: {list(val[0].keys()) if isinstance(val[0], dict) else val[0]}")
            elif isinstance(val, dict):
                print(f"  d['data'] keys: {list(val.keys())}")
        # check aweme_list
        if "aweme_list" in d:
            al = d["aweme_list"]
            print(f"  d['aweme_list'] type={type(al).__name__}, len={len(al) if isinstance(al, list) else 'N/A'}")
            if isinstance(al, list) and al:
                item = al[0]
                print(f"  d['aweme_list'][0] keys: {list(item.keys()) if isinstance(item, dict) else item}")
                if isinstance(item, dict):
                    print(f"    aweme_id: {item.get('aweme_id')}")
                    print(f"    desc: {str(item.get('desc', ''))[:60]}")
                    print(f"    statistics: {item.get('statistics', {})}")
                    print(f"    author.nickname: {item.get('author', {}).get('nickname', '')}")

def debug_xhs_structure():
    keyword = "iPhone"
    search_url = f"https://www.xiaohongshu.com/search_result?keyword={urllib.parse.quote(keyword)}&source=web_search_result_note"
    collected = []

    def handle(response):
        if "search/notes" in response.url or "search_notes" in response.url:
            try:
                data = response.json()
                collected.append(data)
            except: pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        if config.XIAOHONGSHU_COOKIE:
            cookies = []
            for item in config.XIAOHONGSHU_COOKIE.split("; "):
                if "=" in item:
                    n, v = item.split("=", 1)
                    cookies.append({"name": n.strip(), "value": v.strip(), "domain": ".xiaohongshu.com", "path": "/"})
            ctx.add_cookies(cookies)

        page = ctx.new_page()
        page.on("response", handle)
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        except: pass
        time.sleep(8)
        browser.close()

    print(f"\n=== XIAOHONGSHU: {len(collected)} responses ===")
    for i, d in enumerate(collected):
        print(f"\n--- Response {i} ---")
        print(f"Top keys: {list(d.keys())}")
        if "data" in d:
            val = d["data"]
            print(f"  d['data'] type={type(val).__name__}")
            if isinstance(val, dict):
                print(f"  d['data'] keys: {list(val.keys())}")
                if "items" in val:
                    items = val["items"]
                    print(f"  d['data']['items'] len={len(items)}")
                    if items:
                        item = items[0]
                        print(f"  items[0] keys: {list(item.keys())}")
                        print(f"    id: {item.get('id')}")
                        print(f"    model_type: {item.get('model_type')}")
                        if "note_card" in item:
                            nc = item["note_card"]
                            print(f"    note_card keys: {list(nc.keys())}")
                            print(f"    display_title: {nc.get('display_title', '')[:60]}")
                elif "note_list" in val:
                    items = val["note_list"]
                    print(f"  d['data']['note_list'] len={len(items)}")
                    if items:
                        print(f"  note_list[0] keys: {list(items[0].keys())}")
                else:
                    # print all nested keys
                    for k, v in val.items():
                        print(f"  d['data']['{k}'] = {type(v).__name__} {str(v)[:80] if not isinstance(v, (dict, list)) else ''}")

if __name__ == "__main__":
    debug_douyin_structure()
    debug_xhs_structure()
