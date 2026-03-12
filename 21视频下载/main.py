#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
21视频下载器 - 命令行版本
支持B站和NTU课程网站视频下载
"""

import os
import sys
import subprocess
import platform


class VideoDownloader:
    """视频下载器类"""
    
    def __init__(self, download_dir="downloads"):
        self.download_dir = download_dir
        self.cookies_file = "cookies.txt"
        self._ensure_download_dir()
    
    def _ensure_download_dir(self):
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            print(f"已创建下载目录: {self.download_dir}")
    
    def check_dependencies(self):
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
            print("yt-dlp 已安装")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("错误: yt-dlp 未安装，请运行: pip install yt-dlp")
            return False
        
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            print("ffmpeg 已安装")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("错误: ffmpeg 未安装")
            return False
        
        return True
    
    def check_cookies(self):
        if os.path.exists(self.cookies_file):
            print(f"找到cookies文件: {self.cookies_file}")
            return True
        else:
            print(f"提示: 未找到cookies文件，部分视频可能无法下载高清画质")
            return False
    
    def download_single(self, url):
        print(f"\n开始下载: {url}")
        
        cmd = [
            "yt-dlp",
            "-P", self.download_dir,
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "--no-playlist",
            "--progress",
        ]
        
        if os.path.exists(self.cookies_file):
            cmd.extend(["--cookies", self.cookies_file])
        
        cmd.append(url)
        
        try:
            subprocess.run(cmd, check=True)
            print("\n下载完成!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n下载失败: {e}")
            return False


def print_banner():
    banner = """
    ===============================
         21 视频下载器 CLI
    ===============================
    """
    print(banner)


def main():
    print_banner()
    
    downloader = VideoDownloader()
    
    print("检查系统依赖...")
    if not downloader.check_dependencies():
        input("\n按回车键退出...")
        sys.exit(1)
    
    downloader.check_cookies()
    
    print("\n使用方法:")
    print("  输入视频URL下载")
    print("  输入多个URL（用空格分隔）批量下载")
    print("  输入 'q' 退出\n")
    
    while True:
        try:
            user_input = input("请输入视频URL: ").strip()
            
            if user_input.lower() in ['q', 'quit', 'exit']:
                print("\n再见！")
                break
            
            if not user_input:
                continue
            
            urls = user_input.replace(',', ' ').split()
            
            for url in urls:
                if url.strip():
                    downloader.download_single(url.strip())
                
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n错误: {e}")


if __name__ == "__main__":
    main()
