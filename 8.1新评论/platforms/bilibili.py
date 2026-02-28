"""
B站爬虫 - 搜索 + 评论抓取
"""
import re
import requests
from datetime import datetime
from typing import List, Optional
from urllib.parse import quote

from .base import BasePlatform, Content, Comment
import config


class BilibiliPlatform(BasePlatform):
    """B站爬虫"""

    PLATFORM_NAME = "bilibili"

    # API 地址
    SEARCH_API = "https://api.bilibili.com/x/web-interface/search/type"
    COMMENT_API = "https://api.bilibili.com/x/v2/reply/main"

    def __init__(self, cookie: str = None, speed: str = None):
        super().__init__(cookie or config.BILIBILI_COOKIE, speed)
        self.session = requests.Session()
        self.session.headers.update({
            **config.DEFAULT_HEADERS,
            'Referer': 'https://www.bilibili.com',
        })
        if self.cookie:
            self.session.headers['Cookie'] = self.cookie

    def search(self, keyword: str, max_results: int = None) -> List[Content]:
        """搜索视频"""
        max_results = max_results or config.DEFAULT_MAX_SEARCH
        results = []
        page = 1

        print(f"  [B站] 搜索: {keyword}")

        while len(results) < max_results:
            try:
                params = {
                    'keyword': keyword,
                    'search_type': 'video',
                    'page': page,
                    'page_size': 20,
                    'order': 'totalrank',
                }

                resp = self.session.get(self.SEARCH_API, params=params, timeout=30)
                data = resp.json()

                if data.get('code') != 0:
                    print(f"    [!] API错误: {data.get('message')}")
                    break

                items = data.get('data', {}).get('result', [])
                if not items:
                    break

                for item in items:
                    if len(results) >= max_results:
                        break

                    # 清理标题中的 HTML 标签
                    title = re.sub(r'<[^>]+>', '', item.get('title', ''))

                    content = Content(
                        platform=self.PLATFORM_NAME,
                        content_id=item.get('bvid', ''),
                        title=title,
                        url=f"https://www.bilibili.com/video/{item.get('bvid')}",
                        author=item.get('author', ''),
                        description=item.get('description', ''),
                        likes=item.get('like', 0),
                        comments=item.get('review', 0),
                        views=item.get('play', 0),
                        publish_time=datetime.fromtimestamp(item.get('pubdate', 0)) if item.get('pubdate') else None,
                    )
                    results.append(content)

                page += 1
                self._random_delay()

            except Exception as e:
                print(f"    [!] 搜索异常: {e}")
                break

        print(f"    找到 {len(results)} 个视频")
        return results

    def get_comments(self, content_id: str, url: str = None,
                     max_count: int = None) -> List[Comment]:
        """获取视频评论"""
        max_count = max_count or config.DEFAULT_MAX_COMMENTS
        comments = []

        # 获取视频 oid（av号）
        oid = self._get_oid(content_id)
        if not oid:
            print(f"    [!] 无法获取视频ID: {content_id}")
            return comments

        next_cursor = 0
        retry_count = 0
        max_retries = 3

        print(f"    获取评论: {content_id}")

        while len(comments) < max_count and retry_count < max_retries:
            try:
                params = {
                    'type': 1,
                    'oid': oid,
                    'mode': 3,
                    'next': next_cursor,
                    'ps': 20,
                }

                resp = self.session.get(self.COMMENT_API, params=params, timeout=30)
                data = resp.json()

                code = data.get('code')
                if code == -412:
                    # 风控，等待后重试
                    print(f"      触发风控，等待重试...")
                    retry_count += 1
                    self._random_delay()
                    self._random_delay()
                    continue

                if code != 0:
                    print(f"      API错误: {data.get('message')}")
                    break

                cursor = data.get('data', {}).get('cursor', {})
                replies = data.get('data', {}).get('replies', [])

                if not replies:
                    break

                for reply in replies:
                    if len(comments) >= max_count:
                        break

                    member = reply.get('member', {})
                    content = reply.get('content', {})

                    # 解析时间
                    ctime = reply.get('ctime')
                    create_time = datetime.fromtimestamp(ctime) if ctime else None

                    # IP 属地
                    ip_location = reply.get('reply_control', {}).get('location', '').replace('IP属地：', '')

                    comment = Comment(
                        platform=self.PLATFORM_NAME,
                        content_id=content_id,
                        comment_id=str(reply.get('rpid', '')),
                        username=member.get('uname', ''),
                        text=content.get('message', ''),
                        likes=reply.get('like', 0),
                        replies=reply.get('rcount', 0),
                        create_time=create_time,
                        ip_location=ip_location,
                    )
                    comments.append(comment)

                if not cursor.get('is_end', True):
                    next_cursor = cursor.get('next', 0)
                else:
                    break

                self._random_delay()
                retry_count = 0  # 重置重试计数

            except Exception as e:
                print(f"      异常: {e}")
                retry_count += 1
                self._random_delay()

        print(f"      获取 {len(comments)} 条评论")
        return comments

    def _get_oid(self, bvid: str) -> Optional[int]:
        """BV号转av号"""
        try:
            api = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
            resp = self.session.get(api, timeout=10)
            data = resp.json()
            if data.get('code') == 0:
                return data.get('data', {}).get('aid')
        except:
            pass

        # 备用方法：BV号解码
        try:
            return self._bv2av(bvid)
        except:
            return None

    @staticmethod
    def _bv2av(bvid: str) -> int:
        """BV号转av号算法"""
        table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
        tr = {c: i for i, c in enumerate(table)}
        s = [11, 10, 3, 8, 4, 6]
        xor = 177451812
        add = 8728348608

        r = sum(tr[bvid[s[i]]] * 58**i for i in range(6))
        return (r - add) ^ xor
