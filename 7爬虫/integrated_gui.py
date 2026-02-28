# -*- coding: utf-8 -*-
"""
统一爬虫工具GUI - 集成XZ图片网爬虫和B站爬虫
运行方式: python integrated_gui.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import sys
import json
import re
from pathlib import Path
from datetime import datetime

# 尝试导入模块
xz_dir = Path(__file__).parent / "xz_图片"
if xz_dir.exists():
    sys.path.insert(0, str(xz_dir))

try:
    from xz_scraper import XZScraper
    HAS_XZ = True
except ImportError:
    HAS_XZ = False

sys.path.insert(0, str(Path(__file__).parent))
try:
    from bilibili_client import BilibiliClient
    HAS_BILIBILI = True
except ImportError:
    HAS_BILIBILI = False


class IntegratedScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("统一爬虫工具 - XZ图片网 + B站")
        self.root.geometry("1100x780")
        self.root.resizable(True, True)
        
        # 状态变量
        self.xz_scraper = None
        self.bili_client = None
        self.is_running_xz = False
        self.is_running_bili = False
        self.search_results = []
        
        # 输出目录
        self.output_dir = Path(__file__).parent / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.setup_ui()
        self.check_environment()
        
    def setup_ui(self):
        """设置界面"""
        
        # 标题栏
        title_frame = tk.Frame(self.root, bg="#2C3E50", height=60)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="统一爬虫工具", 
                              font=("Microsoft YaHei", 22, "bold"),
                              bg="#2C3E50", fg="white")
        title_label.pack(side="left", padx=20)
        
        # 版本信息
        version_label = tk.Label(title_frame, text="v1.1 - 完整版",
                              font=("Arial", 10), bg="#2C3E50", fg="#95A5A6")
        version_label.pack(side="right", padx=20)
        
        # 标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # XZ爬虫标签页
        self.xz_frame = tk.Frame(self.notebook)
        self.notebook.add(self.xz_frame, text="  XZ图片网爬虫  ")
        self.setup_xz_ui()
        
        # B站爬虫标签页
        self.bili_frame = tk.Frame(self.notebook)
        self.notebook.add(self.bili_frame, text="  B站爬虫  ")
        self.setup_bili_ui()
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                            bd=1, relief="sunken", anchor="w",
                            font=("Arial", 9), fg="#7F8C8D")
        status_bar.pack(side="bottom", fill="x")
        
    def setup_xz_ui(self):
        """设置XZ爬虫界面"""
        
        # 顶部设置区
        top = tk.Frame(self.xz_frame, pady=10)
        top.pack(fill="x", padx=10)
        
        # 左侧 - 基本设置
        left = tk.Frame(top)
        left.pack(side="left", fill="y")
        
        # 标题
        tk.Label(left, text="基本设置", font=("Microsoft YaHei", 12, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        
        # 速度档位
        tk.Label(left, text="速度档位:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.xz_speed_var = tk.StringVar(value="normal")
        
        speed_frame = tk.Frame(left)
        speed_frame.grid(row=2, column=0, sticky="w")
        tk.Radiobutton(speed_frame, text="快速", variable=self.xz_speed_var, value="fast").pack(side="left", padx=5)
        tk.Radiobutton(speed_frame, text="正常", variable=self.xz_speed_var, value="normal").pack(side="left", padx=5)
        tk.Radiobutton(speed_frame, text="慢速", variable=self.xz_speed_var, value="slow").pack(side="left", padx=5)
        tk.Radiobutton(speed_frame, text="安全", variable=self.xz_speed_var, value="safe").pack(side="left", padx=5)
        
        # 分类设置
        tk.Label(left, text="分类设置", font=("Microsoft YaHei", 12, "bold")).grid(row=3, column=0, sticky="w", pady=(15, 5))
        
        tk.Label(left, text="分类名称:").grid(row=4, column=0, sticky="w")
        self.xz_category_entry = tk.Entry(left, width=25)
        self.xz_category_entry.grid(row=5, column=0, sticky="w", pady=2)
        tk.Label(left, text="(如: 秀人网, 语画界, all=全部)", fg="gray", font=("Arial", 8)).grid(row=6, column=0, sticky="w")
        
        # 数量限制
        tk.Label(left, text="下载限制:").grid(row=7, column=0, sticky="w", pady=(10, 0))
        self.xz_max_var = tk.StringVar(value="0")
        tk.Entry(left, textvariable=self.xz_max_var, width=10).grid(row=8, column=0, sticky="w")
        tk.Label(left, text="(0=全部, 数字=每个分类最多)", fg="gray", font=("Arial", 8)).grid(row=9, column=0, sticky="w")
        
        # 右侧 - 代理设置
        right = tk.Frame(top)
        right.pack(side="left", padx=(40, 0), fill="y")
        
        tk.Label(right, text="网络设置", font=("Microsoft YaHei", 12, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        
        # 代理开关
        self.xz_use_proxy_var = tk.BooleanVar(value=False)
        tk.Checkbutton(right, text="使用代理", variable=self.xz_use_proxy_var, 
                      font=("Arial", 10)).grid(row=1, column=0, sticky="w")
        
        tk.Label(right, text="代理地址:").grid(row=2, column=0, sticky="w", pady=(5, 0))
        self.xz_proxy_entry = tk.Entry(right, width=25)
        self.xz_proxy_entry.insert(0, "http://127.0.0.1:7890")
        self.xz_proxy_entry.grid(row=3, column=0, sticky="w")
        
        # 常用代理快捷按钮
        proxy_frame = tk.Frame(right)
        proxy_frame.grid(row=4, column=0, sticky="w", pady=5)
        
        tk.Button(proxy_frame, text="Clash", width=8, command=lambda: self.set_xz_proxy("http://127.0.0.1:7890")).pack(side="left", padx=2)
        tk.Button(proxy_frame, text="V2Ray", width=8, command=lambda: self.set_xz_proxy("http://127.0.0.1:10809")).pack(side="left", padx=2)
        tk.Button(proxy_frame, text="不使用", width=8, command=lambda: self.set_xz_proxy("")).pack(side="left", padx=2)
        
        tk.Label(right, text="常用端口: Clash=7890, V2Ray=10809", fg="gray", font=("Arial", 8)).grid(row=5, column=0, sticky="w")
        
        # 无头模式
        self.xz_headless_var = tk.BooleanVar(value=False)
        tk.Checkbutton(right, text="无头模式(不显示浏览器)", variable=self.xz_headless_var).grid(row=6, column=0, sticky="w", pady=(10, 0))
        
        # 中间 - 按钮区
        mid = tk.Frame(top)
        mid.pack(side="left", padx=(40, 0), fill="y")
        
        tk.Label(mid, text="").pack()
        
        self.xz_start_btn = tk.Button(mid, text="开始执行", command=self.start_xz_task,
                                      bg="#27AE60", fg="white", font=("Microsoft YaHei", 12, "bold"),
                                      width=15, height=2)
        self.xz_start_btn.pack(pady=5)
        
        self.xz_stop_btn = tk.Button(mid, text="停止", command=self.stop_xz_task,
                                    bg="#E74C3C", fg="white", width=15, state="disabled")
        self.xz_stop_btn.pack(pady=5)
        
        # XZ日志区
        log_frame = tk.LabelFrame(self.xz_frame, text="运行日志", font=("Arial", 10, "bold"))
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.xz_log_text = scrolledtext.ScrolledText(log_frame, height=18, font=("Consolas", 9))
        self.xz_log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
    def setup_bili_ui(self):
        """设置B站爬虫界面"""
        
        # 顶部设置栏
        top_frame = tk.Frame(self.bili_frame, pady=10)
        top_frame.pack(fill="x", padx=10)
        
        # 左侧设置
        left = tk.Frame(top_frame)
        left.pack(side="left", fill="y")
        
        # 操作类型
        tk.Label(left, text="操作类型", font=("Microsoft YaHei", 12, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        
        self.bili_operation_var = tk.StringVar(value="search")
        
        op_frame = tk.Frame(left)
        op_frame.grid(row=1, column=0, sticky="w")
        tk.Radiobutton(op_frame, text="搜索视频", variable=self.bili_operation_var, value="search").pack(side="left", padx=5)
        tk.Radiobutton(op_frame, text="热门视频", variable=self.bili_operation_var, value="popular").pack(side="left", padx=5)
        tk.Radiobutton(op_frame, text="UP主空间", variable=self.bili_operation_var, value="up主").pack(side="left", padx=5)
        tk.Radiobutton(op_frame, text="获取评论", variable=self.bili_operation_var, value="comments").pack(side="left", padx=5)
        
        # 筛选条件
        tk.Label(left, text="筛选条件", font=("Microsoft YaHei", 12, "bold")).grid(row=2, column=0, sticky="w", pady=(15, 5))
        
        tk.Label(left, text="关键词:").grid(row=3, column=0, sticky="w")
        self.bili_keyword_entry = tk.Entry(left, width=20)
        self.bili_keyword_entry.grid(row=4, column=0, sticky="w", pady=2)
        tk.Label(left, text="(BV号/UP主名/关键词)", fg="gray", font=("Arial", 8)).grid(row=5, column=0, sticky="w")
        
        tk.Label(left, text="获取数量:").grid(row=6, column=0, sticky="w", pady=(10, 0))
        self.bili_count_var = tk.StringVar(value="10")
        tk.Entry(left, textvariable=self.bili_count_var, width=10).grid(row=7, column=0, sticky="w")
        
        # 右侧设置
        right = tk.Frame(top_frame)
        right.pack(side="left", padx=(30, 0))
        
        # 下载选项
        tk.Label(right, text="下载选项", font=("Microsoft YaHei", 12, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        
        self.bili_dl_cover = tk.BooleanVar(value=True)
        tk.Checkbutton(right, text="下载封面", variable=self.bili_dl_cover).grid(row=1, column=0, sticky="w")
        
        self.bili_dl_comments = tk.BooleanVar(value=True)
        tk.Checkbutton(right, text="下载评论", variable=self.bili_dl_comments).grid(row=2, column=0, sticky="w")
        
        # 视频下载 - 重点突出
        self.bili_dl_video = tk.BooleanVar(value=False)
        tk.Checkbutton(right, text="下载视频", variable=self.bili_dl_video, 
                      font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=(10, 0))
        
        tk.Label(right, text="视频质量:").grid(row=4, column=0, sticky="w", pady=(5, 0))
        self.bili_quality_var = tk.StringVar(value="32")
        
        quality_frame = tk.Frame(right)
        quality_frame.grid(row=5, column=0, sticky="w")
        tk.Radiobutton(quality_frame, text="360p", variable=self.bili_quality_var, value="16").pack(side="left", padx=3)
        tk.Radiobutton(quality_frame, text="480p", variable=self.bili_quality_var, value="32").pack(side="left", padx=3)
        tk.Radiobutton(quality_frame, text="720p", variable=self.bili_quality_var, value="64").pack(side="left", padx=3)
        tk.Radiobutton(quality_frame, text="1080p", variable=self.bili_quality_var, value="80").pack(side="left", padx=3)
        
        # 输出目录
        tk.Label(right, text="输出目录:").grid(row=6, column=0, sticky="w", pady=(15, 0))
        self.bili_dir_entry = tk.Entry(right, width=25)
        self.bili_dir_entry.insert(0, str(self.output_dir))
        self.bili_dir_entry.grid(row=7, column=0, sticky="w")
        tk.Button(right, text="选择", command=self.select_bili_dir, width=6).grid(row=7, column=1, padx=5)
        
        # 中间按钮区
        mid = tk.Frame(top_frame)
        mid.pack(side="left", padx=(30, 0), fill="y")
        
        tk.Label(mid, text="").pack()
        
        self.bili_search_btn = tk.Button(mid, text="搜索/获取", command=self.start_bili_task,
                                        bg="#3498DB", fg="white", font=("Microsoft YaHei", 12, "bold"),
                                        width=15, height=2)
        self.bili_search_btn.pack(pady=5)
        
        # 独立下载选中视频按钮
        self.bili_download_btn = tk.Button(mid, text="下载选中视频", command=self.download_bili_selected,
                                           bg="#E67E22", fg="white", font=("Microsoft YaHei", 11),
                                           width=15, height=2)
        self.bili_download_btn.pack(pady=5)
        
        self.bili_stop_btn = tk.Button(mid, text="停止", command=self.stop_bili_task,
                                      bg="#E74C3C", fg="white", width=15, state="disabled")
        self.bili_stop_btn.pack(pady=5)
        
        # 结果区域 - 标签页
        result_notebook = ttk.Notebook(self.bili_frame)
        result_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 视频列表页
        video_frame = tk.Frame(result_notebook)
        result_notebook.add(video_frame, text="视频列表")
        
        columns = ("序号", "标题", "UP主", "播放量", "时长", "BV号")
        self.bili_video_tree = ttk.Treeview(video_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            self.bili_video_tree.heading(col, text=col)
            if col == "序号":
                self.bili_video_tree.column(col, width=50, anchor="center")
            elif col == "标题":
                self.bili_video_tree.column(col, width=350)
            else:
                self.bili_video_tree.column(col, width=100, anchor="center")
        
        # 双击获取评论
        self.bili_video_tree.bind("<Double-1>", self.on_bili_video_double_click)
        
        vsb = ttk.Scrollbar(video_frame, orient="vertical", command=self.bili_video_tree.yview)
        self.bili_video_tree.configure(yscrollcommand=vsb.set)
        
        self.bili_video_tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        vsb.pack(side="right", fill="y", pady=5)
        
        # 评论页
        comment_frame = tk.Frame(result_notebook)
        result_notebook.add(comment_frame, text="评论数据")
        
        columns2 = ("视频", "用户", "评论", "点赞")
        self.bili_comment_tree = ttk.Treeview(comment_frame, columns=columns2, show="headings", height=12)
        
        for col in columns2:
            self.bili_comment_tree.heading(col, text=col)
            
        self.bili_comment_tree.column("视频", width=150)
        self.bili_comment_tree.column("用户", width=100)
        self.bili_comment_tree.column("评论", width=300)
        self.bili_comment_tree.column("点赞", width=80, anchor="center")
        
        csb = ttk.Scrollbar(comment_frame, orient="vertical", command=self.bili_comment_tree.yview)
        self.bili_comment_tree.configure(yscrollcommand=csb.set)
        
        self.bili_comment_tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        csb.pack(side="right", fill="y", pady=5)
        
        # 日志页
        log_frame = tk.Frame(result_notebook)
        result_notebook.add(log_frame, text="运行日志")
        
        self.bili_log_text = scrolledtext.ScrolledText(log_frame, height=15, font=("Consolas", 9))
        self.bili_log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
    def set_xz_proxy(self, proxy):
        """设置代理"""
        self.xz_proxy_entry.delete(0, "end")
        self.xz_proxy_entry.insert(0, proxy)
        if proxy:
            self.xz_use_proxy_var.set(True)
            self.xz_log(f"代理已设置: {proxy}")
        else:
            self.xz_use_proxy_var.set(False)
            self.xz_log("代理已禁用")
            
    def select_bili_dir(self):
        """选择输出目录"""
        d = filedialog.askdirectory(initialdir=self.bili_dir_entry.get())
        if d:
            self.bili_dir_entry.delete(0, "end")
            self.bili_dir_entry.insert(0, d)
            self.output_dir = Path(d)
            
    def check_environment(self):
        """检测环境"""
        self.xz_log("="*50)
        self.xz_log("环境检测")
        self.xz_log("="*50)
        
        # 检测Python
        self.xz_log(f"Python: ✅ 已安装")
        
        # 检测requests
        try:
            import requests
            self.xz_log(f"requests: ✅ 已安装")
        except:
            self.xz_log(f"requests: ❌ 未安装")
            
        # 检测XZ模块
        if HAS_XZ:
            self.xz_log(f"XZ爬虫模块: ✅ 已安装")
            self.status_var.set("就绪 - XZ和B站模块已加载")
        else:
            self.xz_log(f"XZ爬虫模块: ❌ 未找到 (需要 xz_图片 目录)")
            
        # 检测B站模块
        if HAS_BILIBILI:
            self.bili_log("="*50)
            self.bili_log("环境检测")
            self.bili_log("="*50)
            self.bili_log(f"B站爬虫模块: ✅ 已安装")
            self.init_bili_client()
        else:
            self.bili_log(f"B站爬虫模块: ❌ 未找到")
            self.status_var.set("警告: 部分模块缺失")
            
    def init_bili_client(self):
        """初始化B站客户端"""
        if HAS_BILIBILI:
            try:
                self.bili_client = BilibiliClient()
                self.bili_log("B站客户端初始化成功")
            except Exception as e:
                self.bili_log(f"API初始化失败: {e}")
                
    def xz_log(self, msg):
        """添加XZ日志"""
        ts = datetime.now().strftime("%H:%M:%S")
        self.xz_log_text.insert("end", f"[{ts}] {msg}\n")
        self.xz_log_text.see("end")
        self.root.update()
        
    def bili_log(self, msg):
        """添加B站日志"""
        ts = datetime.now().strftime("%H:%M:%S")
        self.bili_log_text.insert("end", f"[{ts}] {msg}\n")
        self.bili_log_text.see("end")
        self.root.update()
        
    # ========== XZ爬虫功能 ==========
    
    def start_xz_task(self):
        """开始XZ下载"""
        if self.is_running_xz:
            return
            
        # 获取代理
        proxy = ""
        if self.xz_use_proxy_var.get():
            proxy = self.xz_proxy_entry.get().strip()
            
        category = self.xz_category_entry.get().strip() or "all"
        max_albums = int(self.xz_max_var.get() or "0")
        speed = self.xz_speed_var.get()
        
        self.xz_log(f"开始任务: 分类={category}, 最大={max_albums}, 速度={speed}")
        self.xz_log(f"代理: {proxy if proxy else '不使用'}")
        
        if not HAS_XZ:
            self.xz_log("错误: XZ爬虫模块未安装")
            messagebox.showerror("错误", "XZ爬虫模块未找到\n请确保 xz_图片 目录存在")
            return
            
        self.is_running_xz = True
        self.xz_start_btn.config(state="disabled", bg="#95A5A6")
        self.xz_stop_btn.config(state="normal")
        self.status_var.set("XZ爬虫运行中...")
        
        # 在后台运行
        def run():
            try:
                # 动态导入并运行
                sys.path.insert(0, str(xz_dir))
                from xz_scraper import XZScraper
                
                scraper = XZScraper(
                    speed=speed,
                    headless=self.xz_headless_var.get(),
                    category_filter=category,
                    max_albums=max_albums,
                    proxy=proxy
                )
                scraper.run()
                
            except Exception as e:
                self.root.after(0, lambda: self.xz_log(f"错误: {e}"))
            finally:
                self.root.after(0, self.xz_task_done)
                
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        
    def stop_xz_task(self):
        """停止XZ任务"""
        self.is_running_xz = False
        self.xz_start_btn.config(state="normal", bg="#27AE60")
        self.xz_stop_btn.config(state="disabled")
        self.status_var.set("XZ任务已停止")
        self.xz_log("用户停止")
        
    def xz_task_done(self):
        """XZ任务完成"""
        self.is_running_xz = False
        self.xz_start_btn.config(state="normal", bg="#27AE60")
        self.xz_stop_btn.config(state="disabled")
        self.status_var.set("XZ任务完成")
        self.xz_log("任务完成!")
        
    # ========== B站爬虫功能 ==========
    
    def on_bili_video_double_click(self, event):
        """双击视频获取评论"""
        selection = self.bili_video_tree.selection()
        if not selection:
            return
        item = self.bili_video_tree.item(selection[0])
        values = item['values']
        if values:
            bvid = values[5]
            self.get_bili_video_comments(bvid)
            
    def get_bili_video_comments(self, bvid):
        """获取视频评论"""
        if not self.bili_client:
            self.bili_log("客户端未初始化")
            return
            
        try:
            self.bili_log(f"获取评论: {bvid}")
            info = self.bili_client.get_video_info(bvid)
            aid = info.get("aid", 0)
            
            if not aid:
                self.bili_log("无法获取视频ID")
                return
                
            comments = self.bili_client.get_comments(aid, count=20)
            
            for c in comments:
                self.bili_comment_tree.insert("", "end", values=(
                    info.get("title", "")[:20] if info.get("title") else "",
                    c.get("user", ""),
                    c.get("content", "")[:50] if c.get("content") else "",
                    c.get("like", 0)
                ))
                
            cf = self.bili_task_dir / f"comments_{bvid}.json"
            with open(cf, "w", encoding="utf-8") as f:
                json.dump({"video": info.get("title"), "comments": comments}, f, ensure_ascii=False, indent=2)
            self.bili_log(f"获取到 {len(comments)} 条评论")
            
        except Exception as e:
            self.bili_log(f"获取评论失败: {e}")
            
    def start_bili_task(self):
        """开始B站任务"""
        if self.is_running_bili:
            return
            
        op = self.bili_operation_var.get()
        kw = self.bili_keyword_entry.get().strip()
        
        if not kw and op in ["search", "up主", "comments"]:
            messagebox.showwarning("警告", "请输入关键词")
            return
            
        if not HAS_BILIBILI:
            self.bili_log("错误: B站爬虫模块未安装")
            messagebox.showerror("错误", "B站爬虫模块未找到")
            return
            
        self.is_running_bili = True
        self.bili_search_btn.config(state="disabled", bg="#95A5A6")
        self.bili_download_btn.config(state="disabled")
        self.bili_stop_btn.config(state="normal")
        self.status_var.set("B站爬虫运行中...")
        
        self.bili_log(f"开始: {op}")
        
        # 创建任务目录
        task_dir = self.output_dir / f"bilibili_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task_dir.mkdir(parents=True, exist_ok=True)
        self.bili_task_dir = task_dir
        
        # 根据操作类型启动线程
        if op == "search":
            t = threading.Thread(target=self.bili_search_worker, args=(kw,))
        elif op == "popular":
            t = threading.Thread(target=self.bili_popular_worker)
        elif op == "up主":
            t = threading.Thread(target=self.bili_up_worker, args=(kw,))
        elif op == "comments":
            t = threading.Thread(target=self.bili_comment_worker, args=(kw,))
            
        t.daemon = True
        t.start()
        
    def stop_bili_task(self):
        """停止B站任务"""
        self.is_running_bili = False
        self.bili_search_btn.config(state="normal", bg="#3498DB")
        self.bili_download_btn.config(state="normal")
        self.bili_stop_btn.config(state="disabled")
        self.status_var.set("B站任务已停止")
        self.bili_log("已停止")
        
    def bili_search_worker(self, keyword):
        """搜索视频工作线程"""
        try:
            count = int(self.bili_count_var.get() or "10")
            self.bili_log(f"搜索: {keyword}")
            
            # 判断是否是BV号
            if keyword.startswith("BV"):
                info = self.bili_client.get_video_info(keyword)
                results = [info]
            else:
                results = self.bili_client.search_video(keyword, page_size=count)
                
            self.bili_log(f"找到 {len(results)} 个结果")
            
            # 显示结果
            self.root.after(0, lambda: self.show_bili_videos(results))
            self.root.after(0, lambda: self.save_bili_results(results))
            
            # 下载选项
            if self.bili_dl_cover.get():
                self.root.after(0, lambda: self.download_bili_covers(results))
            if self.bili_dl_comments.get():
                self.root.after(0, lambda: self.download_bili_comments(results))
            if self.bili_dl_video.get():
                self.root.after(0, lambda: self.download_bili_videos(results))
                
        except Exception as e:
            self.bili_log(f"搜索失败: {e}")
        finally:
            self.root.after(0, self.bili_task_done)
            
    def bili_popular_worker(self):
        """热门视频工作线程"""
        try:
            count = int(self.bili_count_var.get() or "10")
            self.bili_log("获取热门视频...")
            
            results = self.bili_client.get_popular(page_size=count)
            self.bili_log(f"获取 {len(results)} 个")
            
            self.root.after(0, lambda: self.show_bili_videos(results))
            self.root.after(0, lambda: self.save_bili_results(results))
            
            if self.bili_dl_cover.get():
                self.root.after(0, lambda: self.download_bili_covers(results))
            if self.bili_dl_video.get():
                self.root.after(0, lambda: self.download_bili_videos(results))
                
        except Exception as e:
            self.bili_log(f"失败: {e}")
        finally:
            self.root.after(0, self.bili_task_done)
            
    def bili_up_worker(self, uid):
        """UP主工作线程"""
        try:
            count = int(self.bili_count_var.get() or "10")
            self.bili_log(f"获取UP主: {uid}")
            
            results = self.bili_client.search_video(uid, page_size=count)
            self.root.after(0, lambda: self.show_bili_videos(results))
            self.root.after(0, lambda: self.save_bili_results(results))
            
            if self.bili_dl_cover.get():
                self.root.after(0, lambda: self.download_bili_covers(results))
            if self.bili_dl_video.get():
                self.root.after(0, lambda: self.download_bili_videos(results))
                
        except Exception as e:
            self.bili_log(f"失败: {e}")
        finally:
            self.root.after(0, self.bili_task_done)
            
    def bili_comment_worker(self, bvid):
        """评论工作线程"""
        try:
            b = bvid
            # 处理URL
            if "bilibili.com" in bvid:
                m = re.search(r'BV[\w]+', bvid)
                if m:
                    b = m.group()
                    
            self.bili_log(f"获取评论: {b}")
            
            info = self.bili_client.get_video_info(b)
            self.root.after(0, lambda: self.show_bili_videos([info]))
            
            aid = info.get("aid", 0)
            
            if not aid:
                self.bili_log("无法获取视频ID")
                return
                
            comments = self.bili_client.get_comments(aid, count=20)
            
            # 显示评论
            for c in comments:
                self.bili_comment_tree.insert("", "end", values=(
                    info.get("title", "")[:20] if info.get("title") else "",
                    c.get("user", ""),
                    c.get("content", "")[:50] if c.get("content") else "",
                    c.get("like", 0)
                ))
                
            # 保存评论
            cf = self.bili_task_dir / "comments.json"
            with open(cf, "w", encoding="utf-8") as f:
                json.dump({"video": info.get("title"), "comments": comments}, f, ensure_ascii=False, indent=2)
            self.bili_log(f"评论已保存: {cf}")
            
        except Exception as e:
            self.bili_log(f"失败: {e}")
        finally:
            self.root.after(0, self.bili_task_done)
            
    def show_bili_videos(self, videos):
        """显示视频列表"""
        self.bili_video_tree.delete(*self.bili_video_tree.get_children())
        self.search_results = videos
        
        for i, v in enumerate(videos, 1):
            title = (v.get("title", "") or "")[:35]
            author = v.get("author", "") or ""
            play = v.get("play", v.get("view", 0) or 0)
            if play and isinstance(play, (int, float)) and play >= 10000:
                play = f"{play/10000:.1f}万"
            duration = v.get("duration", "") or ""
            bvid = v.get("bvid", "") or ""
            
            self.bili_video_tree.insert("", "end", values=(i, title, author, play, duration, bvid))
            
    def save_bili_results(self, videos):
        """保存结果"""
        jf = self.bili_task_dir / "videos.json"
        with open(jf, "w", encoding="utf-8") as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
        self.bili_log(f"已保存: {jf}")
        
    def download_bili_covers(self, videos):
        """下载封面"""
        self.bili_log("下载封面...")
        cd = self.bili_task_dir / "covers"
        cd.mkdir(exist_ok=True)
        
        for v in videos:
            if not self.is_running_bili:
                break
                
            pic = v.get("pic", "") or ""
            if not pic:
                continue
            if pic.startswith("//"):
                pic = "https:" + pic
                
            bvid = v.get("bvid", "") or ""
            if not bvid:
                continue
                
            ext = "jpg"
            if "." in pic:
                ext = pic.rsplit(".", 1)[-1].split("?")[0]
                if not ext or len(ext) > 4:
                    ext = "jpg"
                    
            try:
                self.bili_client.download_file(pic, cd / f"{bvid}.{ext}")
                self.bili_log(f"封面: {bvid}.{ext}")
            except Exception as e:
                self.bili_log(f"封面失败 {bvid}: {e}")
                
        self.bili_log("封面下载完成")
        
    def download_bili_comments(self, videos):
        """下载评论"""
        self.bili_log("下载评论...")
        
        for v in videos:
            if not self.is_running_bili:
                break
                
            bvid = v.get("bvid", "") or ""
            aid = v.get("aid", 0)
            
            if not aid:
                continue
                
            try:
                comments = self.bili_client.get_comments(aid, count=10)
                
                # 实时显示
                for c in comments:
                    self.bili_comment_tree.insert("", "end", values=(
                        v.get("title", "")[:20] if v.get("title") else "",
                        c.get("user", ""),
                        c.get("content", "")[:50] if c.get("content") else "",
                        c.get("like", 0)
                    ))
                    
            except Exception as e:
                self.bili_log(f"获取评论失败 {bvid}: {e}")
                
        self.bili_log("评论下载完成")
        
    def download_bili_videos(self, videos):
        """下载视频"""
        self.bili_log("="*50)
        self.bili_log("开始下载视频...")
        self.bili_log("="*50)
        
        vd = self.bili_task_dir / "videos"
        vd.mkdir(exist_ok=True)
        
        qn = int(self.bili_quality_var.get() or "32")
        
        success_count = 0
        fail_count = 0
        
        for i, v in enumerate(videos):
            if not self.is_running_bili:
                self.bili_log("下载已停止")
                break
                
            bvid = v.get("bvid", "") or ""
            if not bvid:
                continue
                
            title = v.get("title", "")[:30]
            self.bili_log(f"[{i+1}/{len(videos)}] {title}")
            self.bili_log(f"    BV号: {bvid}")
                
            try:
                # 获取视频详情
                info = self.bili_client.get_video_info(bvid)
                cid = info.get("cid", 0)
                
                if not cid:
                    self.bili_log(f"    ❌ 无法获取CID")
                    fail_count += 1
                    continue
                    
                # 获取播放地址
                play = self.bili_client.get_play_url(bvid, cid, qn=qn)
                urls = play.get("urls", [])
                
                if urls and urls[0].get("url"):
                    url = urls[0].get("url")
                    size_mb = urls[0].get("size", 0) / 1024 / 1024
                    
                    self.bili_log(f"    大小: {size_mb:.1f}MB")
                    self.bili_log(f"    正在下载...")
                    
                    self.bili_client.download_file(url, vd / f"{bvid}.mp4", max_mb=500)
                    self.bili_log(f"    ✅ 下载完成")
                    success_count += 1
                else:
                    self.bili_log(f"    ❌ 无播放地址")
                    fail_count += 1
                    
            except Exception as e:
                self.bili_log(f"    ❌ 失败: {e}")
                fail_count += 1
                
        self.bili_log("="*50)
        self.bili_log(f"视频下载完成: 成功{success_count}个, 失败{fail_count}个")
        self.bili_log(f"保存位置: {vd}")
        self.bili_log("="*50)
        
    def download_bili_selected(self):
        """下载选中的视频"""
        selection = self.bili_video_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先在视频列表中选择要下载的视频\n(可以多选)")
            return
            
        if not HAS_BILIBILI:
            messagebox.showerror("错误", "B站API模块未找到")
            return
            
        # 获取选中的视频
        selected_videos = []
        for item_id in selection:
            item = self.bili_video_tree.item(item_id)
            values = item['values']
            bvid = values[5] if len(values) > 5 else ""
            if bvid:
                for v in self.search_results:
                    if v.get("bvid") == bvid:
                        selected_videos.append(v)
                        break
                        
        if not selected_videos:
            messagebox.showwarning("警告", "未找到选中视频的详细信息")
            return
            
        count = len(selected_videos)
        if messagebox.askyesno("确认", f"确定要下载选中的 {count} 个视频吗？"):
            self.is_running_bili = True
            self.bili_search_btn.config(state="disabled")
            self.bili_download_btn.config(state="disabled")
            self.bili_stop_btn.config(state="normal")
            
            # 创建任务目录
            task_dir = self.output_dir / f"bilibili_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            task_dir.mkdir(parents=True, exist_ok=True)
            self.bili_task_dir = task_dir
            
            t = threading.Thread(target=self.download_bili_selected_worker, args=(selected_videos,))
            t.daemon = True
            t.start()
            
    def download_bili_selected_worker(self, videos):
        """下载选中视频的工作线程"""
        try:
            self.bili_log("="*50)
            self.bili_log("开始下载选中的视频...")
            self.bili_log("="*50)
            
            vd = self.bili_task_dir / "videos"
            vd.mkdir(exist_ok=True)
            
            qn = int(self.bili_quality_var.get() or "32")
            
            success_count = 0
            fail_count = 0
            
            for i, v in enumerate(videos):
                if not self.is_running_bili:
                    break
                    
                bvid = v.get("bvid", "") or ""
                if not bvid:
                    continue
                    
                title = v.get("title", "")[:30]
                self.bili_log(f"[{i+1}/{len(videos)}] {title}")
                
                try:
                    info = self.bili_client.get_video_info(bvid)
                    cid = info.get("cid", 0)
                    
                    if not cid:
                        self.bili_log(f"    ❌ 无法获取CID")
                        fail_count += 1
                        continue
                        
                    play = self.bili_client.get_play_url(bvid, cid, qn=qn)
                    urls = play.get("urls", [])
                    
                    if urls and urls[0].get("url"):
                        url = urls[0].get("url")
                        self.bili_log(f"    正在下载...")
                        self.bili_client.download_file(url, vd / f"{bvid}.mp4", max_mb=500)
                        self.bili_log(f"    ✅ 完成")
                        success_count += 1
                    else:
                        self.bili_log(f"    ❌ 无播放地址")
                        fail_count += 1
                        
                except Exception as e:
                    self.bili_log(f"    ❌ 失败: {e}")
                    fail_count += 1
                    
            self.bili_log("="*50)
            self.bili_log(f"下载完成: 成功{success_count}个, 失败{fail_count}个")
            self.bili_log(f"保存位置: {vd}")
            self.bili_log("="*50)
            
        except Exception as e:
            self.bili_log(f"下载失败: {e}")
        finally:
            self.root.after(0, self.bili_task_done)
        
    def bili_task_done(self):
        """B站任务完成"""
        self.is_running_bili = False
        self.bili_search_btn.config(state="normal", bg="#3498DB")
        self.bili_download_btn.config(state="normal")
        self.bili_stop_btn.config(state="disabled")
        self.status_var.set("B站任务完成")
        self.bili_log("任务完成!")


def main():
    root = tk.Tk()
    app = IntegratedScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
