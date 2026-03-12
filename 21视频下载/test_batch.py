#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量下载器测试脚本
"""

import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from batch_downloader import BatchDownloader, VideoInfo, is_video_url

def test_video_url_detection():
    """测试视频URL识别"""
    print("=" * 70)
    print("测试 1: 视频URL识别")
    print("=" * 70)
    
    test_cases = [
        ("https://example.com/video.m3u8", True),
        ("https://example.com/video.mp4", True),
        ("https://kaltura.com/p/123/video", True),
        ("https://panopto.com/delivery/video", True),
        ("https://example.com/thumbnail.jpg", False),
        ("https://example.com/analytics.js", False),
    ]
    
    passed = 0
    for url, expected in test_cases:
        result = is_video_url(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} {url[:50]} -> {result} (期望: {expected})")
        if result == expected:
            passed += 1
    
    print(f"\n通过: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_video_info():
    """测试VideoInfo类"""
    print("\n" + "=" * 70)
    print("测试 2: VideoInfo 类")
    print("=" * 70)
    
    video = VideoInfo(1, "测试视频", "iframe:nth-of-type(1)")
    video.video_urls = ["https://example.com/video.m3u8"]
    video.best_url = "https://example.com/video.m3u8"
    video.status = "collected"
    
    # 测试序列化
    data = video.to_dict()
    print(f"✅ 序列化成功: {data['title']}")
    
    # 测试反序列化
    video2 = VideoInfo.from_dict(data)
    print(f"✅ 反序列化成功: {video2.title}")
    
    assert video.index == video2.index
    assert video.title == video2.title
    assert video.best_url == video2.best_url
    
    print("\n通过: VideoInfo 类测试")
    return True


def test_progress_save_load():
    """测试进度保存和加载"""
    print("\n" + "=" * 70)
    print("测试 3: 进度保存和加载")
    print("=" * 70)
    
    test_url = "https://example.com/course"
    
    # 创建下载器
    downloader = BatchDownloader(test_url)
    
    # 添加测试视频
    video = VideoInfo(1, "测试视频1")
    video.status = "collected"
    video.best_url = "https://example.com/video1.m3u8"
    downloader.videos.append(video)
    
    # 保存进度
    downloader.save_progress()
    print("✅ 进度已保存")
    
    # 加载进度
    downloader2 = BatchDownloader.load_progress(test_url)
    
    if downloader2:
        print(f"✅ 进度已加载: {len(downloader2.videos)} 个视频")
        assert len(downloader2.videos) == 1
        assert downloader2.videos[0].title == "测试视频1"
        print("\n通过: 进度保存和加载测试")
        return True
    else:
        print("❌ 加载进度失败")
        return False


def main():
    print("\n" + "=" * 70)
    print("  批量下载器单元测试")
    print("=" * 70 + "\n")
    
    results = []
    
    # 运行测试
    results.append(("视频URL识别", test_video_url_detection()))
    results.append(("VideoInfo类", test_video_info()))
    results.append(("进度保存加载", test_progress_save_load()))
    
    # 总结
    print("\n" + "=" * 70)
    print("  测试总结")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
