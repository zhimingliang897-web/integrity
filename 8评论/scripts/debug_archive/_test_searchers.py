"""测试抖音和小红书搜索器修复"""
import sys
sys.path.insert(0, ".")

import config

def test_xiaohongshu():
    """测试小红书搜索"""
    from searchers.xiaohongshu import XiaohongshuSearcher

    print("=" * 60)
    print("  测试小红书搜索")
    print("=" * 60)

    cookie = getattr(config, "XIAOHONGSHU_COOKIE", "")
    if not cookie:
        print("  跳过: 未配置 XIAOHONGSHU_COOKIE")
        return

    searcher = XiaohongshuSearcher(cookie=cookie, speed="normal")
    results = searcher.search("iPhone", max_results=3)

    print(f"\n  结果数量: {len(results)}")
    for i, r in enumerate(results, 1):
        print(f"  {i}. [{r.platform}] {r.title[:50]}")
        print(f"     ID: {r.content_id}")
        print(f"     URL: {r.url}")
        print(f"     作者: {r.author}")
        print(f"     点赞: {r.like_count}  评论: {r.comment_count}")
        print()

    return len(results) > 0


def test_douyin():
    """测试抖音搜索"""
    from searchers.douyin import DouyinSearcher

    print("=" * 60)
    print("  测试抖音搜索")
    print("=" * 60)

    cookie = getattr(config, "DOUYIN_COOKIE", "")
    if not cookie:
        print("  跳过: 未配置 DOUYIN_COOKIE")
        return

    searcher = DouyinSearcher(cookie=cookie, speed="normal")
    results = searcher.search("iPhone", max_results=3)

    print(f"\n  结果数量: {len(results)}")
    for i, r in enumerate(results, 1):
        print(f"  {i}. [{r.platform}] {r.title[:50]}")
        print(f"     ID: {r.content_id}")
        print(f"     URL: {r.url}")
        print(f"     作者: {r.author}")
        print(f"     点赞: {r.like_count}  评论: {r.comment_count}")
        print()

    return len(results) > 0


if __name__ == "__main__":
    print("\n开始测试搜索器...\n")

    xhs_ok = test_xiaohongshu()
    print("\n" + "-" * 60 + "\n")
    dy_ok = test_douyin()

    print("\n" + "=" * 60)
    print(f"  小红书搜索: {'✓ 通过' if xhs_ok else '✗ 失败'}")
    print(f"  抖音搜索:   {'✓ 通过' if dy_ok else '✗ 失败'}")
    print("=" * 60)
