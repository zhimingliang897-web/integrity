"""小红书评论抓取模块"""

import re
from datetime import datetime

from .base import BaseScraper


class XiaohongshuScraper(BaseScraper):
    """小红书笔记评论抓取器"""

    platform_name = "xiaohongshu"

    API_URL = "https://edith.xiaohongshu.com/api/sns/web/v2/comment/page"

    def _setup_session(self):
        """设置小红书特定的请求头"""
        super()._setup_session()
        self.session.headers.update({
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com/",
            "Content-Type": "application/json",
        })

    def extract_id(self, url: str) -> str:
        """
        从小红书链接中提取笔记ID (note_id)

        支持格式:
        - https://www.xiaohongshu.com/explore/xxxxxxxxxxxxxxxx
        - https://www.xiaohongshu.com/discovery/item/xxxxxxxxxxxxxxxx
        - https://xhslink.com/xxxxx (短链接)
        - 纯 note_id
        """
        url = url.strip()

        # 24位十六进制字符串，视为 note_id
        if re.match(r"^[0-9a-f]{24}$", url):
            return url

        # 标准链接
        match = re.search(r"(?:explore|discovery/item|note)/([0-9a-f]{24})", url)
        if match:
            return match.group(1)

        # 短链接
        if "xhslink.com" in url:
            try:
                resp = self.session.get(url, allow_redirects=True, timeout=10)
                match = re.search(r"(?:explore|discovery/item|note)/([0-9a-f]{24})", resp.url)
                if match:
                    return match.group(1)
            except Exception as e:
                print(f"短链接解析失败: {e}")

        raise ValueError(f"无法从链接中提取笔记ID: {url}")

    def fetch_comments(self, url: str, max_count: int = 100) -> list[dict]:
        """抓取小红书笔记评论"""
        if not self.cookie:
            print("警告: 小红书抓取需要提供 Cookie，请在 config.py 中配置")
            print("获取方式: 浏览器打开小红书网页版 -> F12 -> Network -> 复制 Cookie")
            return []

        note_id = self.extract_id(url)
        comments = []
        cursor = ""

        print(f"开始抓取小红书笔记 (id={note_id}) 的评论...")

        while len(comments) < max_count:
            params = {
                "note_id": note_id,
                "cursor": cursor,
                "top_comment_id": "",
                "image_formats": "jpg,webp,avif",
            }

            try:
                resp = self.session.get(self.API_URL, params=params, timeout=15)
                data = resp.json()
            except Exception as e:
                print(f"请求失败: {e}")
                print("提示: 小红书反爬较严格，可能需要更新 Cookie 或添加签名参数")
                break

            if not data.get("success", False):
                msg = data.get("msg", "未知错误")
                print(f"API 返回错误: {msg}")
                if "签名" in msg or "sign" in msg.lower():
                    print("提示: 小红书需要请求签名 (X-s, X-t)，纯 API 模式可能受限")
                break

            data_body = data.get("data", {})
            comment_list = data_body.get("comments") or []

            if not comment_list:
                print("没有更多评论了")
                break

            for item in comment_list:
                if len(comments) >= max_count:
                    break

                # 解析时间
                create_time = item.get("create_time", "")
                if isinstance(create_time, (int, float)) and create_time > 0:
                    create_time = datetime.fromtimestamp(create_time / 1000).strftime("%Y-%m-%d %H:%M:%S")

                ip_location = item.get("ip_location", "")

                user_info = item.get("user_info", {})

                comment = self._build_comment(
                    comment_id=item.get("id", ""),
                    username=user_info.get("nickname", ""),
                    content=item.get("content", ""),
                    like_count=item.get("like_count", 0),
                    reply_count=item.get("sub_comment_count", 0),
                    create_time=create_time,
                    ip_location=ip_location,
                )
                comments.append(comment)

            print(f"  已抓取 {len(comments)} 条评论...")

            # 翻页
            has_more = data_body.get("has_more", False)
            if not has_more:
                break
            cursor = data_body.get("cursor", "")
            if not cursor:
                break

            self._delay()  # 小红书反爬严格，延迟按速度档位控制

        print(f"抓取完成，共 {len(comments)} 条评论")
        return comments
