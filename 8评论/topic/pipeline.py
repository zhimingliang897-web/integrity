"""话题分析流水线 — 编排搜索、抓取、分析的完整流程"""

import os
from datetime import datetime

import pandas as pd

import config
from searchers import BilibiliSearcher, DouyinSearcher, XiaohongshuSearcher
from searchers.base import SearchResult
from scrapers import BilibiliScraper, DouyinScraper, XiaohongshuScraper
from analyzer.client import LLMClient
from analyzer import tasks


# 平台名 -> (搜索器类, 爬虫类, Cookie配置key)
PLATFORM_REGISTRY = {
    "bilibili": (BilibiliSearcher, BilibiliScraper, "BILIBILI_COOKIE"),
    "douyin": (DouyinSearcher, DouyinScraper, "DOUYIN_COOKIE"),
    "xiaohongshu": (XiaohongshuSearcher, XiaohongshuScraper, "XIAOHONGSHU_COOKIE"),
}


def run_topic_pipeline(
    keyword: str,
    platforms: list[str],
    max_search: int = 5,
    max_comments: int = 50,
    speed: str = "normal",
    output_dir: str = "output",
):
    """
    执行完整话题分析流水线

    Args:
        keyword: 话题关键词
        platforms: 要搜索的平台列表
        max_search: 每个平台最大搜索结果数
        max_comments: 每个视频/帖子最大抓取评论数
        speed: 速度档位
        output_dir: 输出目录
    """
    print(f"\n{'='*60}")
    print(f"  话题分析: 「{keyword}」")
    print(f"  平台: {', '.join(platforms)}")
    print(f"  每平台搜索: {max_search} 个内容, 每内容抓取: {max_comments} 条评论")
    print(f"{'='*60}\n")

    # ===== 阶段1+2: 搜索 + 抓取评论 =====
    # 小红书使用 search_and_scrape（搜索与评论抓取共用同一个浏览器会话，
    # 解决新会话访问笔记详情被 461 拒绝的问题）
    # 其他平台使用传统的分步流程

    print("[阶段1/4] 搜索相关内容...\n")
    all_search_results: list[SearchResult] = []
    all_comments = []

    # 先处理小红书（合并搜索+抓取）
    if "xiaohongshu" in platforms:
        xhs_cookie_key = PLATFORM_REGISTRY["xiaohongshu"][2]
        xhs_cookie = getattr(config, xhs_cookie_key, "")
        xhs_searcher = XiaohongshuSearcher(cookie=xhs_cookie, speed=speed)

        try:
            xhs_results, xhs_comments_map = xhs_searcher.search_and_scrape(
                keyword, max_search=max_search, max_comments=max_comments
            )
            all_search_results.extend(xhs_results)
            # 将评论整合到 all_comments
            for sr in xhs_results:
                comments = xhs_comments_map.get(sr.content_id, [])
                for c in comments:
                    c["source_title"] = sr.title
                    c["source_url"] = sr.url
                    c["source_author"] = sr.author
                all_comments.extend(comments)
        except Exception as e:
            print(f"  xiaohongshu 搜索+抓取失败: {e}")

    # 处理其他平台
    for platform in platforms:
        if platform == "xiaohongshu":
            continue  # 已处理
        if platform not in PLATFORM_REGISTRY:
            print(f"  跳过未知平台: {platform}")
            continue
        searcher_cls, _, cookie_key = PLATFORM_REGISTRY[platform]
        cookie = getattr(config, cookie_key, "")
        searcher = searcher_cls(cookie=cookie, speed=speed)

        try:
            results = searcher.search(keyword, max_results=max_search)
            all_search_results.extend(results)
        except Exception as e:
            print(f"  {platform} 搜索失败: {e}")

    if not all_search_results:
        print("\n未找到任何相关内容，流程终止")
        return

    # 打印搜索结果汇总
    print(f"\n共找到 {len(all_search_results)} 个相关内容:")
    for i, sr in enumerate(all_search_results, 1):
        title_display = sr.title[:50] + "..." if len(sr.title) > 50 else sr.title
        print(f"  {i}. [{sr.platform}] {title_display}  (评论: {sr.comment_count})")

    # ===== 阶段2: 批量抓取评论（非小红书平台） =====
    other_results = [sr for sr in all_search_results if sr.platform != "xiaohongshu"]

    if other_results:
        print(f"\n[阶段2/4] 批量抓取评论...\n")

        for i, sr in enumerate(other_results, 1):
            platform = sr.platform
            _, scraper_cls, cookie_key = PLATFORM_REGISTRY[platform]
            cookie = getattr(config, cookie_key, "")
            scraper = scraper_cls(cookie=cookie, speed=speed)

            title_display = sr.title[:40] + "..." if len(sr.title) > 40 else sr.title
            print(f"  [{i}/{len(other_results)}] 抓取 [{sr.platform}] {title_display}")
            try:
                comments = scraper.fetch_comments(sr.url, max_count=max_comments)
                for c in comments:
                    c["source_title"] = sr.title
                    c["source_url"] = sr.url
                    c["source_author"] = sr.author
                all_comments.extend(comments)
                print(f"    -> 获取 {len(comments)} 条评论")
            except Exception as e:
                print(f"    -> 抓取失败: {e}")

    if not all_comments:
        print("\n未抓取到任何评论，流程终止")
        return

    print(f"\n共抓取 {len(all_comments)} 条评论")

    # 中间结果保存（原始评论）
    topic_dir = os.path.join(output_dir, "topic")
    os.makedirs(topic_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = keyword.replace(" ", "_")[:30]
    raw_path = os.path.join(topic_dir, f"topic_{safe_keyword}_{timestamp}_raw.csv")
    pd.DataFrame(all_comments).to_csv(raw_path, index=False, encoding="utf-8-sig")
    print(f"  原始评论已保存: {raw_path}")

    # ===== 阶段3: LLM 话题相关性分析 =====
    print(f"\n[阶段3/4] 话题相关性分析...\n")

    base_url = getattr(config, "LLM_BASE_URL", "")
    api_key = getattr(config, "LLM_API_KEY", "")
    model = getattr(config, "LLM_MODEL", "")
    batch_size = getattr(config, "LLM_BATCH_SIZE", 50)

    if not api_key or not base_url:
        print("警告: LLM 未配置，跳过分析阶段。原始评论已保存。")
        return

    client = LLMClient(base_url=base_url, api_key=api_key, model=model)
    analyzed = tasks.topic_relevance(client, all_comments, keyword, batch_size)

    # ===== 阶段4: 结果整理与导出 =====
    print(f"\n[阶段4/4] 整理结果...\n")

    # 分离有效信息和无效信息
    valid_comments = [c for c in analyzed if c.get("info_type") == "有效信息"]
    invalid_comments = [c for c in analyzed if c.get("info_type") != "有效信息"]

    # 导出完整分析结果
    full_path = os.path.join(topic_dir, f"topic_{safe_keyword}_{timestamp}_analyzed.csv")
    pd.DataFrame(analyzed).to_csv(full_path, index=False, encoding="utf-8-sig")
    print(f"  完整分析结果: {full_path}")

    # 单独导出有效信息
    valid_path = os.path.join(topic_dir, f"topic_{safe_keyword}_{timestamp}_valid.csv")
    if valid_comments:
        pd.DataFrame(valid_comments).to_csv(valid_path, index=False, encoding="utf-8-sig")
        print(f"  有效信息: {valid_path}")
    else:
        print("  未找到有效信息")

    # 生成话题摘要报告
    if valid_comments:
        print("  正在生成话题摘要报告...")
        summary = tasks.summarize_comments(client, valid_comments)
        summary_path = os.path.join(topic_dir, f"topic_{safe_keyword}_{timestamp}_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"话题: {keyword}\n")
            f.write(f"分析时间: {timestamp}\n")
            f.write(f"搜索平台: {', '.join(platforms)}\n")
            f.write(f"搜索内容数: {len(all_search_results)}\n")
            f.write(f"评论总数: {len(all_comments)}\n")
            f.write(f"有效信息: {len(valid_comments)} 条\n")
            f.write(f"无效信息: {len(invalid_comments)} 条\n")
            f.write(f"\n{'='*50}\n\n")
            f.write(summary)
        print(f"  话题摘要: {summary_path}")

    # 最终汇总
    print(f"\n{'='*60}")
    print(f"  话题分析完成!")
    print(f"  话题: {keyword}")
    print(f"  搜索内容: {len(all_search_results)} 个")
    print(f"  评论总数: {len(all_comments)} 条")
    print(f"  有效信息: {len(valid_comments)} 条")
    print(f"  无效信息: {len(invalid_comments)} 条")
    print(f"  结果目录: {topic_dir}")
    print(f"{'='*60}")
