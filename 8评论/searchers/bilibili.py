"""B站视频搜索模块 — 通过搜索API"""

import re

from .base import BaseSearcher, SearchResult


class BilibiliSearcher(BaseSearcher):
    """B站视频搜索器"""

    platform_name = "bilibili"
    SEARCH_API = "https://api.bilibili.com/x/web-interface/search/type"

    def search(self, keyword: str, max_results: int = 10) -> list[SearchResult]:
        results = []
        page = 1
        page_size = 20
        
        # 关键词预处理
        keywords = [k.lower() for k in keyword.split() if k.strip()]

        while len(results) < max_results:
            # API 参数
            params = {
                "keyword": keyword,
                "page": page,
                "pagesize": page_size,
                "search_type": "video",
                "order": "",  # 默认综合排序
            }

            try:
                # 随机延迟，避免被ban
                self._delay()
                
                resp = self.session.get("https://api.bilibili.com/x/web-interface/search/type", params=params, timeout=10)
                if resp.status_code != 200:
                    print(f"  B站搜索请求失败: HTTP {resp.status_code}")
                    break
                    
                data = resp.json()
                if data.get("code") != 0:
                    print(f"  B站API错误: {data.get('message', '未知')}")
                    break
                
                items = data.get("data", {}).get("result")
                if not items:
                    break
                    
                for item in items:
                    if len(results) >= max_results:
                        break
                        
                    # 清洗标题 (去除 <em> 高亮标签)
                    raw_title = item.get("title", "")
                    title = re.sub(r"<[^>]+>", "", raw_title)
                    
                    # === 关键词过滤 ===
                    if keywords:
                        title_lower = title.lower()
                        # 必须包含所有关键词分词 (AND 逻辑)
                        if not all(k in title_lower for k in keywords):
                            continue
                            
                    results.append(SearchResult(
                        platform="bilibili",
                        content_id=str(item.get("aid", "")),
                        title=title,
                        url=f"https://www.bilibili.com/video/{item.get('bvid')}",
                        author=item.get("author", ""),
                        description=item.get("description", ""),
                        like_count=item.get("like", 0),
                        comment_count=item.get("review", 0),
                        view_count=item.get("play", 0),
                        publish_time=str(item.get("pubdate", "")),
                    ))
                
                # 翻页检查
                num_pages = data.get("data", {}).get("numPages", 1)
                if page >= num_pages:
                    break
                page += 1
                
            except Exception as e:
                print(f"  B站搜索异常: {e}")
                break

        print(f"  B站搜索「{keyword}」: 找到 {len(results)} 个视频")
        return results
