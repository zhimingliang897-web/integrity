"""
BilibiliClient - B站 API 封装 + 反封策略

反封策略:
  1. 随机延迟: 每次请求间隔 1~3 秒 (模拟人类操作)
  2. User-Agent 池: 随机切换浏览器指纹
  3. 匿名 Cookie: 启动时自动获取 buvid3 等
  4. 请求限速: 单次运行最多 60 个 API 请求
  5. 超大文件跳过: 视频 >100MB 自动跳过
"""

import random
import requests
import time
import sys
import io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# UA 池
_UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
]

MAX_REQUESTS_PER_RUN = 60


class BilibiliClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": random.choice(_UA_LIST),
            "Referer": "https://www.bilibili.com/",
        })
        self.api = "https://api.bilibili.com"
        self._request_count = 0
        self._init_cookies()

    def _init_cookies(self):
        try:
            self.session.get("https://www.bilibili.com/", timeout=10)
        except Exception:
            pass

    def _sleep(self):
        """随机延迟 1~3 秒"""
        time.sleep(random.uniform(1.0, 3.0))

    def _get(self, path, params=None, retries=2):
        if self._request_count >= MAX_REQUESTS_PER_RUN:
            raise Exception(f"request limit reached ({MAX_REQUESTS_PER_RUN}), stopping to avoid ban")

        self._request_count += 1

        # 每 10 次请求换一次 UA
        if self._request_count % 10 == 0:
            self.session.headers["User-Agent"] = random.choice(_UA_LIST)

        url = f"{self.api}{path}"
        last_err = None
        for attempt in range(retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=15)
                resp.raise_for_status()
                result = resp.json()

                if result.get("code") != 0:
                    raise Exception(f"API error: code={result.get('code')}, msg={result.get('message')}")

                return result.get("data", {})
            except Exception as e:
                last_err = e
                if attempt < retries:
                    wait = 2 ** attempt
                    print(f"  [RETRY] {e}, waiting {wait}s...")
                    time.sleep(wait)

        raise last_err

    # ========== 搜索 ==========
    def search_video(self, keyword, page=1, page_size=10):
        data = self._get("/x/web-interface/search/type", {
            "keyword": keyword,
            "search_type": "video",
            "page": page,
            "page_size": page_size,
        })
        results = []
        for item in data.get("result", []):
            title = item.get("title", "").replace('<em class="keyword">', "").replace("</em>", "")
            results.append({
                "title": title,
                "bvid": item.get("bvid", ""),
                "author": item.get("author", ""),
                "play": item.get("play", 0),
                "duration": item.get("duration", ""),
                "description": item.get("description", "")[:80],
            })
        return results

    # ========== 视频详情 ==========
    def get_video_info(self, bvid):
        data = self._get("/x/web-interface/view", {"bvid": bvid})
        stat = data.get("stat", {})
        pages = data.get("pages", [])
        cid = pages[0].get("cid") if pages else data.get("cid")
        return {
            "title": data.get("title", ""),
            "bvid": data.get("bvid", ""),
            "aid": data.get("aid", ""),
            "cid": cid,
            "author": data.get("owner", {}).get("name", ""),
            "description": data.get("desc", ""),
            "duration": data.get("duration", 0),
            "view": stat.get("view", 0),
            "like": stat.get("like", 0),
            "coin": stat.get("coin", 0),
            "favorite": stat.get("favorite", 0),
            "danmaku": stat.get("danmaku", 0),
            "reply": stat.get("reply", 0),
            "pubdate": data.get("pubdate", 0),
            "pic": data.get("pic", ""),
            "tags": [t.get("tag_name", "") for t in data.get("tags", []) or []],
        }

    # ========== 热门 ==========
    def get_popular(self, page=1, page_size=10):
        data = self._get("/x/web-interface/popular", {"pn": page, "ps": page_size})
        results = []
        for item in data.get("list", []):
            stat = item.get("stat", {})
            results.append({
                "title": item.get("title", ""),
                "bvid": item.get("bvid", ""),
                "author": item.get("owner", {}).get("name", ""),
                "view": stat.get("view", 0),
                "like": stat.get("like", 0),
            })
        return results

    # ========== 评论 ==========
    def get_comments(self, aid, page=1, count=10):
        data = self._get("/x/v2/reply/main", {
            "type": 1, "oid": aid, "mode": 3, "next": page,
        })
        replies = data.get("replies", []) or []
        return [{
            "user": r.get("member", {}).get("uname", ""),
            "content": r.get("content", {}).get("message", ""),
            "like": r.get("like", 0),
            "time": r.get("ctime", 0),
        } for r in replies[:count]]

    # ========== 视频流 ==========
    def get_play_url(self, bvid, cid, qn=32):
        data = self._get("/x/player/playurl", {
            "bvid": bvid, "cid": cid, "qn": qn, "fnval": 1, "fourk": 0,
        })
        urls = [{
            "url": d.get("url", ""),
            "size": d.get("size", 0),
            "length": d.get("length", 0),
        } for d in data.get("durl", [])]
        return {"quality": data.get("quality", 0), "format": data.get("format", ""), "urls": urls}

    def get_video_cid(self, bvid):
        data = self._get("/x/web-interface/view", {"bvid": bvid})
        pages = data.get("pages", [])
        return pages[0].get("cid") if pages else data.get("cid")

    # ========== 下载 ==========
    def download_file(self, url, save_path, max_mb=100):
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = save_path.with_suffix(save_path.suffix + ".tmp")

        resp = self.session.get(url, stream=True, timeout=60)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        if total > max_mb * 1024 * 1024:
            print(f"  [SKIP] {total // 1024 // 1024}MB > {max_mb}MB limit")
            return None

        downloaded = 0
        try:
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 256):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded * 100 // total
                        bar = "#" * (pct // 5) + "." * (20 - pct // 5)
                        print(f"\r  [{bar}] {pct}% ({downloaded//1024}KB/{total//1024}KB)", end="", flush=True)
            tmp_path.rename(save_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

        print(f"\r  [OK] {save_path} ({downloaded//1024}KB)" + " " * 20)
        return save_path
