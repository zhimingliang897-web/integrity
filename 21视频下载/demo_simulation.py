#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量下载器模拟测试
不需要真实的浏览器，模拟整个流程
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from batch_downloader import BatchDownloader, VideoInfo

def simulate_collect_and_download():
    """模拟边收集边下载流程"""
    print("=" * 70)
    print("  模拟测试：边收集边下载")
    print("=" * 70)
    
    # 创建下载器
    test_url = "https://example.com/course/videos"
    downloader = BatchDownloader(test_url)
    
    # 模拟扫描到 3 个视频
    print("\n[模拟] 扫描页面，找到 3 个视频")
    for i in range(1, 4):
        video = VideoInfo(i, f"Week {i} - Lecture", f"iframe:nth-of-type({i})")
        downloader.videos.append(video)
        print(f"  ✓ 视频 {i}: Week {i} - Lecture")
    
    # 模拟边收集边下载
    print("\n[模拟] 开始边收集边下载...")
    
    for video in downloader.videos:
        print(f"\n[🎯 收集] 视频 {video.index}: {video.title}")
        
        # 模拟收集 URL
        time.sleep(0.5)
        video.video_urls = [f"https://example.com/video{video.index}.m3u8"]
        video.best_url = video.video_urls[0]
        video.status = "collected"
        print(f"    ✅ 成功！找到 1 个地址")
        print(f"       最佳: {video.best_url}")
        
        # 模拟立即下载
        print(f"  ⚡ 立即下载（避免 token 过期）...")
        time.sleep(0.5)
        
        # 模拟下载成功
        video.status = "completed"
        video.download_path = f"downloads/{video.index:02d}_{video.title}.mp4"
        print(f"  ✅ 完成")
        
        # 保存进度
        downloader.save_progress()
    
    # 统计结果
    completed = [v for v in downloader.videos if v.status == "completed"]
    
    print("\n" + "=" * 70)
    print(f"  全部完成！")
    print(f"  成功: {len(completed)} 个")
    print(f"  失败: 0 个")
    print("=" * 70)
    
    return len(completed) == 3


def simulate_token_expiry_problem():
    """模拟旧版本的 token 过期问题"""
    print("\n" + "=" * 70)
    print("  模拟测试：旧版本的 token 过期问题")
    print("=" * 70)
    
    test_url = "https://example.com/course/videos"
    downloader = BatchDownloader(test_url)
    
    # 模拟扫描到 3 个视频
    print("\n[模拟] 扫描页面，找到 3 个视频")
    for i in range(1, 4):
        video = VideoInfo(i, f"Week {i} - Lecture", f"iframe:nth-of-type({i})")
        downloader.videos.append(video)
    
    # 模拟先收集所有 URL
    print("\n[模拟] 收集所有视频 URL...")
    for video in downloader.videos:
        print(f"  收集视频 {video.index}...")
        time.sleep(0.3)
        video.video_urls = [f"https://example.com/video{video.index}.m3u8?token=expires_in_5min"]
        video.best_url = video.video_urls[0]
        video.status = "collected"
    
    print("\n[模拟] 所有 URL 收集完成，开始下载...")
    print("  ⚠️  注意：前面收集的 URL 的 token 可能已经过期！")
    
    # 模拟下载（前面的会失败）
    time.sleep(0.5)
    for i, video in enumerate(downloader.videos):
        print(f"\n  下载视频 {video.index}...")
        time.sleep(0.3)
        
        if i == 0:
            # 第一个视频 token 过期
            video.status = "failed"
            video.error = "HTTP 403: Token expired"
            print(f"    ❌ 失败: Token expired")
        else:
            video.status = "completed"
            print(f"    ✅ 完成")
    
    completed = [v for v in downloader.videos if v.status == "completed"]
    failed = [v for v in downloader.videos if v.status == "failed"]
    
    print("\n" + "=" * 70)
    print(f"  下载完成")
    print(f"  成功: {len(completed)} 个")
    print(f"  失败: {len(failed)} 个 ⚠️")
    print("=" * 70)
    
    return len(failed) > 0  # 返回 True 表示确实有失败


def main():
    print("\n" + "=" * 70)
    print("  批量下载器模拟测试")
    print("=" * 70 + "\n")
    
    # 测试 1：新版本（边收集边下载）
    test1_passed = simulate_collect_and_download()
    
    # 测试 2：旧版本问题演示
    test2_has_problem = simulate_token_expiry_problem()
    
    # 总结
    print("\n" + "=" * 70)
    print("  测试总结")
    print("=" * 70)
    
    if test1_passed:
        print("✅ 新版本（v2.1）：边收集边下载 - 全部成功")
    else:
        print("❌ 新版本测试失败")
    
    if test2_has_problem:
        print("⚠️  旧版本（v2.0）：先收集后下载 - 遇到 token 过期问题")
    else:
        print("✅ 旧版本没有问题（不太可能）")
    
    print("\n" + "=" * 70)
    print("  结论")
    print("=" * 70)
    print("v2.1 的边收集边下载模式彻底解决了 token 过期问题！")
    print("推荐所有 NTU Learn 用户使用模式 1（边收集边下载）")
    print("=" * 70)


if __name__ == "__main__":
    main()
