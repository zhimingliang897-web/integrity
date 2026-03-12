#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
21视频下载器 - 核心下载模块
支持API调用、进度回调、多任务管理
"""

import os
import uuid
import subprocess
import threading
import time
from typing import Dict, Callable, Optional, List
from datetime import datetime


class DownloadTask:
    """下载任务类"""
    
    def __init__(self, task_id: str, url: str, output_dir: str = "downloads"):
        self.task_id = task_id
        self.url = url
        self.output_dir = output_dir
        self.status = "pending"  # pending, downloading, completed, failed, cancelled
        self.progress = 0
        self.speed = ""
        self.filename = ""
        self.error_message = ""
        self.start_time = None
        self.end_time = None
        self.process = None
    
    def to_dict(self):
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "url": self.url,
            "status": self.status,
            "progress": self.progress,
            "speed": self.speed,
            "filename": self.filename,
            "error_message": self.error_message,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


class VideoDownloaderCore:
    """视频下载器核心类"""
    
    def __init__(self, download_dir: str = "downloads", cookies_file: str = "cookies.txt"):
        """
        初始化下载器
        
        Args:
            download_dir: 下载保存目录
            cookies_file: Cookie文件路径
        """
        self.download_dir = download_dir
        self.cookies_file = cookies_file
        self.tasks: Dict[str, DownloadTask] = {}
        self._ensure_download_dir()
    
    def _ensure_download_dir(self):
        """确保下载目录存在"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
    
    def check_dependencies(self) -> Dict[str, bool]:
        """
        检查系统依赖
        
        Returns:
            dict: 依赖检查结果
        """
        results = {}
        
        # 检查yt-dlp
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
            results["yt-dlp"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            results["yt-dlp"] = False
        
        # 检查ffmpeg
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            results["ffmpeg"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            results["ffmpeg"] = False
        
        return results
    
    def create_task(self, url: str) -> str:
        """
        创建下载任务
        
        Args:
            url: 视频URL
            
        Returns:
            str: 任务ID
        """
        task_id = str(uuid.uuid4())[:8]
        task = DownloadTask(task_id, url, self.download_dir)
        self.tasks[task_id] = task
        return task_id
    
    def start_download(self, task_id: str, progress_callback: Optional[Callable] = None):
        """
        开始下载任务
        
        Args:
            task_id: 任务ID
            progress_callback: 进度回调函数
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task.status = "downloading"
        task.start_time = datetime.now()
        
        # 构建下载命令
        cmd = [
            "yt-dlp",
            "-P", self.download_dir,
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "--no-playlist",
            "--no-color",
            "--progress",
            "-o", "%(title)s.%(ext)s"
        ]
        
        # 添加cookies支持
        if os.path.exists(self.cookies_file):
            cmd.extend(["--cookies", self.cookies_file])
        
        cmd.append(task.url)
        
        try:
            # 启动下载进程
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            task.process = process
            
            # 实时读取输出
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                if line:
                    # 解析进度
                    if "download" in line.lower() and "%" in line:
                        # 尝试提取进度百分比
                        try:
                            import re
                            match = re.search(r'(\d+\.?\d*)%', line)
                            if match:
                                task.progress = float(match.group(1))
                        except:
                            pass
                    
                    # 提取速度
                    if "speed" in line.lower():
                        try:
                            import re
                            match = re.search(r'speed:\s*([\d.]+[KMG]?/s)', line)
                            if match:
                                task.speed = match.group(1)
                        except:
                            pass
                    
                    # 提取文件名
                    if "Destination:" in line:
                        task.filename = line.replace("Destination:", "").strip()
                    
                    # 调用进度回调
                    if progress_callback:
                        progress_callback(task.to_dict())
            
            # 检查结果
            return_code = process.wait()
            
            if return_code == 0:
                task.status = "completed"
                task.progress = 100
            else:
                task.status = "failed"
                stderr = process.stderr.read()
                task.error_message = stderr[-500:] if stderr else "Unknown error"
        
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
        
        finally:
            task.end_time = datetime.now()
            if progress_callback:
                progress_callback(task.to_dict())
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 取消成功返回True
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        if task.process:
            task.process.terminate()
            try:
                task.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                task.process.kill()
        
        task.status = "cancelled"
        task.end_time = datetime.now()
        return True
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict: 任务状态字典
        """
        if task_id in self.tasks:
            return self.tasks[task_id].to_dict()
        return None
    
    def get_all_tasks(self) -> List[Dict]:
        """
        获取所有任务
        
        Returns:
            list: 所有任务列表
        """
        return [task.to_dict() for task in self.tasks.values()]
    
    def clear_completed_tasks(self):
        """清理已完成的任务"""
        completed_statuses = ["completed", "failed", "cancelled"]
        self.tasks = {
            k: v for k, v in self.tasks.items() 
            if v.status not in completed_statuses
        }
    
    def save_cookies(self, cookies_content: str) -> bool:
        """
        保存Cookie到文件
        
        Args:
            cookies_content: Cookie文件内容
            
        Returns:
            bool: 保存成功返回True
        """
        try:
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                f.write(cookies_content)
            return True
        except Exception as e:
            print(f"Error saving cookies: {e}")
            return False
    
    def load_cookies(self) -> Optional[str]:
        """
        加载Cookie文件内容
        
        Returns:
            str: Cookie内容，不存在返回None
        """
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return None
        return None


# 全局下载器实例
downloader = VideoDownloaderCore()
