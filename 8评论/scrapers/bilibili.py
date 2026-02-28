"""B站评论抓取模块"""

import re
import time
from datetime import datetime
from typing import Optional

from .base import BaseScraper


class BilibiliScraper(BaseScraper):
    """Bilibili 视频评论抓取器"""

    platform_name = "bilibili"

    API_URL = "https://api.bilibili.com/x/v2/reply/main"
    MAX_RETRIES = 3

    def extract_id(self, url: str) -> str:
        """
        从 B站链接中提取视频 oid（aid）

        支持格式:
        - https://www.bilibili.com/video/BVxxxx
        - https://www.bilibili.com/video/avxxxx
        - 纯 BV 号或 av 号
        """
        url = url.strip()

        if url.isdigit():
            return url

        av_match = re.search(r"av(\d+)", url, re.IGNORECASE)
        if av_match:
            return av_match.group(1)

        bv_match = re.search(r"(BV[\w]+)", url)
        if bv_match:
            return self._bv_to_aid(bv_match.group(1))

        raise ValueError(f"无法从链接中提取视频ID: {url}")

    def _bv_to_aid(self, bv_id: str) -> str:
        """通过 B站 API 将 BV 号转换为 aid"""
        resp = self.session.get(
            "https://api.bilibili.com/x/web-interface/view",
            params={"bvid": bv_id},
        )
        data = resp.json()
        if data.get("code") != 0:
            raise ValueError(f"BV号转换失败: {data.get('message', '未知错误')}")
        return str(data["data"]["aid"])

    def _get_total_count(self, oid: str) -> int:
        """获取评论总数"""
        try:
            resp = self.session.get(self.API_URL, params={
                "oid": oid, "type": 1, "mode": 3, "next": 0, "ps": 1,
            })
            data = resp.json()
            if data.get("code") == 0:
                return data["data"]["cursor"].get("all_count", 0)
        except Exception:
            pass
        return 0

    def _request_with_retry(self, params: dict) -> Optional[dict]:
        """带重试的 API 请求"""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = self.session.get(self.API_URL, params=params, timeout=15)
                data = resp.json()
                if data.get("code") == 0:
                    return data
                # -412 表示请求被风控，等待后重试
                if data.get("code") == -412:
                    wait = attempt * 5
                    print(f"  触发风控限制，等待 {wait}s 后重试 ({attempt}/{self.MAX_RETRIES})...")
                    time.sleep(wait)
                    continue
                print(f"  API 错误: {data.get('message', '未知错误')}")
                return None
            except Exception as e:
                if attempt < self.MAX_RETRIES:
                    wait = attempt * 3
                    print(f"  请求失败: {e}，{wait}s 后重试 ({attempt}/{self.MAX_RETRIES})...")
                    time.sleep(wait)
                else:
                    print(f"  请求失败且重试耗尽: {e}")
                    return None
        return None

    def fetch_comments(self, url: str, max_count: int = 100) -> list[dict]:
        """抓取B站视频评论"""
        oid = self.extract_id(url)
        total_count = self._get_total_count(oid)
        target = min(max_count, total_count) if total_count > 0 else max_count

        print(f"B站视频 oid={oid} | 评论总数: {total_count} | 目标抓取: {target}")
        print(f"速度档位: {self.speed} (延迟 {self._delay_min}-{self._delay_max}s)\n")

        comments = []
        next_cursor = 0
        mode = 3  # 3=按热度, 2=按时间
        page = 0

        try:
            while len(comments) < target:
                page += 1
                params = {
                    "oid": oid,
                    "type": 1,
                    "mode": mode,
                    "next": next_cursor,
                    "ps": 20,
                }

                data = self._request_with_retry(params)
                if data is None:
                    break

                cursor_info = data.get("data", {}).get("cursor", {})
                replies = data.get("data", {}).get("replies") or []

                if not replies:
                    print("  没有更多评论了")
                    break

                for reply in replies:
                    if len(comments) >= target:
                        break

                    ctime = reply.get("ctime", 0)
                    time_str = datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M:%S") if ctime else ""

                    location = reply.get("reply_control", {}).get("location", "")
                    if location:
                        location = location.replace("IP属地：", "")

                    comments.append(self._build_comment(
                        comment_id=reply.get("rpid", ""),
                        username=reply.get("member", {}).get("uname", ""),
                        content=reply.get("content", {}).get("message", ""),
                        like_count=reply.get("like", 0),
                        reply_count=reply.get("rcount", 0),
                        create_time=time_str,
                        ip_location=location,
                    ))

                print(f"  第{page}页 | {self._progress_bar(len(comments), target)}")

                # 翻页
                next_cursor = cursor_info.get("next", 0)
                if cursor_info.get("is_end", True):
                    break

                self._delay()

        except KeyboardInterrupt:
            print(f"\n  用户中断，已抓取的 {len(comments)} 条评论将保留导出")

        print(f"\n抓取完成，共 {len(comments)} 条评论")
        return comments
