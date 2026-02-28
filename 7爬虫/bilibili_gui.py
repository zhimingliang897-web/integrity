# -*- coding: utf-8 -*-
"""
B站爬虫图形化界面 - 完整版
运行方式: python bilibili_gui.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import sys
import json
import re
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from bilibili_client import BilibiliClient
    HAS_CLIENT = True
except ImportError:
    HAS_CLIENT = False


class BilibiliGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("B站爬虫工具 - 完整版")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        self.client = None
        self.is_running = False
        self.search_results = []
        self.output_dir = Path(__file__).parent / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.setup_ui()
        self.init_client()
        
    def setup_ui(self):
        """设置界面布局"""
        
        # 标题
        title = tk.Label(self.root, text="B站爬虫工具", font=("Microsoft YaHei", 24, "bold"), 
                        bg="#23ADE5", fg="white", height=2)
        title.pack(fill="x")
        
        # 顶部设置栏
        top_frame = tk.Frame(self.root, pady=10)
        top_frame.pack(fill="x", padx=10)
        
        # 左侧设置
        left = tk.Frame(top_frame)
        left.pack(side="left", fill="y")
        
        # 操作类型
        tk.Label(left, text="操作类型:", font=("Microsoft YaHei", 12, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.operation_var = tk.StringVar(value="search")
        
        op_frame = tk.Frame(left)
        op_frame.grid(row=1, column=0, sticky="w")
        tk.Radiobutton(op_frame, text="搜索视频", variable=self.operation_var, value="search").pack(side="left", padx=5)
        tk.Radiobutton(op_frame, text="热门视频", variable=self.operation_var, value="popular").pack(side="left", padx=5)
        tk.Radiobutton(op_frame, text="UP主空间", variable=self.operation_var, value="up主").pack(side="left", padx=5)
        tk.Radiobutton(op_frame, text="获取评论", variable=self.operation_var, value="comments").pack(side="left", padx=5)
        
        # 筛选条件
        tk.Label(left, text="筛选条件:", font=("Microsoft YaHei", 12, "bold")).grid(row=2, column=0, sticky="w", pady=(15, 5))
        
        tk.Label(left, text="关键词:").grid(row=3, column=0, sticky="w")
        self.keyword_entry = tk.Entry(left, width=22)
        self.keyword_entry.grid(row=4, column=0, sticky="w", pady=2)
        tk.Label(left, text="(输入BV号/UP主名/关键词)", fg="gray", font=("Arial", 8)).grid(row=5, column=0, sticky="w")
        
        tk.Label(left, text="数量:").grid(row=6, column=0, sticky="w", pady=(10, 0))
        self.count_var = tk.StringVar(value="10")
        tk.Entry(left, textvariable=self.count_var, width=10).grid(row=7, column=0, sticky="w")
        
        # 右侧设置
        right = tk.Frame(top_frame)
        right.pack(side="left", padx=(30, 0))
        
        # 下载选项
        tk.Label(right, text="下载选项:", font=("Microsoft YaHei", 12, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        
        self.dl_cover = tk.BooleanVar(value=True)
        tk.Checkbutton(right, text="下载封面", variable=self.dl_cover).grid(row=1, column=0, sticky="w")
        
        self.dl_comments = tk.BooleanVar(value=True)
        tk.Checkbutton(right, text="下载评论", variable=self.dl_comments).grid(row=2, column=0, sticky="w")
        
        # 视频下载 - 独立区域
        self.dl_video = tk.BooleanVar(value=False)
        tk.Checkbutton(right, text="下载视频", variable=self.dl_video, font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=(10, 0))
        
        tk.Label(right, text="视频质量:").grid(row=4, column=0, sticky="w", pady=(5, 0))
        self.quality_var = tk.StringVar(value="32")
        
        quality_frame = tk.Frame(right)
        quality_frame.grid(row=5, column=0, sticky="w")
        tk.Radiobutton(quality_frame, text="360p", variable=self.quality_var, value="16").pack(side="left", padx=3)
        tk.Radiobutton(quality_frame, text="480p", variable=self.quality_var, value="32").pack(side="left", padx=3)
        tk.Radiobutton(quality_frame, text="720p", variable=self.quality_var, value="64").pack(side="left", padx=3)
        tk.Radiobutton(quality_frame, text="1080p", variable=self.quality_var, value="80").pack(side="left", padx=3)
        
        # 输出目录
        tk.Label(right, text="输出目录:", font=("Microsoft YaHei", 12, "bold")).grid(row=6, column=0, sticky="w", pady=(15, 0))
        self.dir_entry = tk.Entry(right, width=28)
        self.dir_entry.insert(0, str(self.output_dir))
        self.dir_entry.grid(row=7, column=0, sticky="w")
        tk.Button(right, text="选择", command=self.select_dir, width=6).grid(row=7, column=1, padx=5)
        
        # 中间按钮区
        mid = tk.Frame(top_frame)
        mid.pack(side="left", padx=(30, 0), fill="y")
        
        tk.Label(mid, text="").pack()
        
        # 搜索按钮
        self.search_btn = tk.Button(mid, text="搜索/获取", command=self.start_task,
                                  bg="#3498DB", fg="white", font=("Microsoft YaHei", 12, "bold"),
                                  width=15, height=2)
        self.search_btn.pack(pady=5)
        
        # 独立下载按钮
        self.download_btn = tk.Button(mid, text="下载选中视频", command=self.download_selected,
                                     bg="#E67E22", fg="white", font=("Microsoft YaHei", 11),
width=15, height=2)
        self.download_btn.pack(pady=5)
        
        self.stop_btn = tk.Button(mid, text="停止", command=self.stop_task,
                                bg="#E74C3C", fg="white", font=("Arial", 11),
                                width=15, state="disabled")
        self.stop_btn.pack(pady=5)
        
        # 结果区域
        result_frame = tk.Frame(self.root)
        result_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标签页
        self.notebook = ttk.Notebook(result_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # 视频列表页
        video_frame = tk.Frame(self.notebook)
        self.notebook.add(video_frame, text="视频列表")
        
        columns = ("序号", "标题", "UP主", "播放量", "时长", "BV号")
        self.video_tree = ttk.Treeview(video_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            self.video_tree.heading(col, text=col)
            if col == "序号":
                self.video_tree.column(col, width=50, anchor="center")
            elif col == "标题":
                self.video_tree.column(col, width=350)
            else:
                self.video_tree.column(col, width=100, anchor="center")
        
        # 双击事件
        self.video_tree.bind("<Double-1>", self.on_video_double_click)
        
        vsb = ttk.Scrollbar(video_frame, orient="vertical", command=self.video_tree.yview)
        self.video_tree.configure(yscrollcommand=vsb.set)
        
        self.video_tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        vsb.pack(side="right", fill="y", pady=5)
        
        # 评论页
        comment_frame = tk.Frame(self.notebook)
        self.notebook.add(comment_frame, text="评论数据")
        
        columns2 = ("视频", "用户", "评论", "点赞")
        self.comment_tree = ttk.Treeview(comment_frame, columns=columns2, show="headings", height=12)
        
        for col in columns2:
            self.comment_tree.heading(col, text=col)
            
        self.comment_tree.column("视频", width=150)
        self.comment_tree.column("用户", width=100)
        self.comment_tree.column("评论", width=350)
        self.comment_tree.column("点赞", width=80, anchor="center")
        
        csb = ttk.Scrollbar(comment_frame, orient="vertical", command=self.comment_tree.yview)
        self.comment_tree.configure(yscrollcommand=csb.set)
        
        self.comment_tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        csb.pack(side="right", fill="y", pady=5)
        
        # 日志页
        log_frame = tk.Frame(self.notebook)
        self.notebook.add(log_frame, text="运行日志")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(self.root, textvariable=self.status_var, bd=1, relief="sunken", 
                anchor="w", font=("Arial", 9)).pack(side="bottom", fill="x")
        
    def init_client(self):
        """初始化客户端"""
        if HAS_CLIENT:
            try:
                self.client = BilibiliClient()
                self.status_var.set("就绪 - 已连接B站API")
                self.log("B站客户端初始化成功")
            except Exception as e:
                self.status_var.set(f"API连接失败: {e}")
                self.log(f"API初始化失败: {e}")
        else:
            self.status_var.set("未找到API模块")
            self.log("警告: 未找到bilibili_client模块")
            
    def log(self, msg):
        """添加日志"""
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        self.root.update()
        
    def select_dir(self):
        d = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if d:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, d)
            self.output_dir = Path(d)
            
    def on_video_double_click(self, event):
        """双击视频项获取评论"""
        selection = self.video_tree.selection()
        if not selection:
            return
        item = self.video_tree.item(selection[0])
        values = item['values']
        if values:
            bvid = values[5]  # BV号
            self.get_video_comments(bvid)
            
    def get_video_comments(self, bvid):
        """获取单个视频的评论"""
        if not self.client:
            self.log("客户端未初始化")
            return
            
        try:
            self.log(f"获取评论: {bvid}")
            info = self.client.get_video_info(bvid)
            aid = info.get("aid", 0)
            
            if not aid:
                self.log("无法获取视频ID")
                return
                
            comments = self.client.get_comments(aid, count=20)
            
            # 显示评论
            for c in comments:
                self.comment_tree.insert("", "end", values=(
                    info.get("title", "")[:20] if info.get("title") else "",
                    c.get("user", ""),
                    c.get("content", "")[:50] if c.get("content") else "",
                    c.get("like", 0)
                ))
                
            self.log(f"获取到 {len(comments)} 条评论")
            
            # 保存评论
            self.task_dir.mkdir(parents=True, exist_ok=True)
            cf = self.task_dir / f"comments_{bvid}.json"
            with open(cf, "w", encoding="utf-8") as f:
                json.dump({"video": info.get("title"), "bvid": bvid, "comments": comments}, f, ensure_ascii=False, indent=2)
            self.log(f"评论已保存: {cf}")
            
        except Exception as e:
            self.log(f"获取评论失败: {e}")
            
    def start_task(self):
        """开始搜索任务"""
        if self.is_running:
            return
            
        op = self.operation_var.get()
        kw = self.keyword_entry.get().strip()
        
        if not kw and op in ["search", "up主"]:
            messagebox.showwarning("警告", "请输入关键词")
            return
            
        if not HAS_CLIENT:
            messagebox.showerror("错误", "B站API模块未找到")
            return
            
        self.is_running = True
        self.search_btn.config(state="disabled", bg="#95A5A6")
        self.download_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        self.log(f"开始: {op} - {kw if kw else '(热门)'}")
        
        # 创建任务目录
        task_dir = self.output_dir / f"bilibili_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task_dir.mkdir(parents=True, exist_ok=True)
        self.task_dir = task_dir
        
        # 启动工作线程
        if op == "search":
            t = threading.Thread(target=self.search_worker, args=(kw,))
        elif op == "popular":
            t = threading.Thread(target=self.popular_worker)
        elif op == "up主":
            t = threading.Thread(target=self.up_worker, args=(kw,))
        elif op == "comments":
            t = threading.Thread(target=self.comments_worker, args=(kw,))
            
        t.daemon = True
        t.start()
        
    def stop_task(self):
        self.is_running = False
        self.search_btn.config(state="normal", bg="#3498DB")
        self.download_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("已停止")
        self.log("用户停止")
        
    def search_worker(self, keyword):
        """搜索视频工作线程"""
        try:
            count = int(self.count_var.get() or "10")
            self.log(f"搜索: {keyword}")
            
            # 判断是否是BV号
            if keyword.startswith("BV"):
                info = self.client.get_video_info(keyword)
                results = [info]
            else:
                results = self.client.search_video(keyword, page_size=count)
                
            self.log(f"找到 {len(results)} 个结果")
            
            # 在主线程更新界面
            self.root.after(0, lambda: self.show_videos(results))
            self.root.after(0, lambda: self.save_results(results))
            
            # 下载封面
            if self.dl_cover.get() and results:
                self.root.after(0, lambda: self.download_covers(results))
                
            # 下载评论
            if self.dl_comments.get() and results:
                self.root.after(0, lambda: self.download_all_comments(results))
                
            # 下载视频
            if self.dl_video.get() and results:
                self.root.after(0, lambda: self.download_videos(results))
                
        except Exception as e:
            self.log(f"搜索失败: {e}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            self.root.after(0, self.task_done)
            
    def popular_worker(self):
        """热门视频工作线程"""
        try:
            count = int(self.count_var.get() or "10")
            self.log("获取热门视频...")
            
            results = self.client.get_popular(page_size=count)
            self.log(f"获取 {len(results)} 个")
            
            self.root.after(0, lambda: self.show_videos(results))
            self.root.after(0, lambda: self.save_results(results))
            
            if self.dl_cover.get() and results:
                self.root.after(0, lambda: self.download_covers(results))
            if self.dl_video.get() and results:
                self.root.after(0, lambda: self.download_videos(results))

        except Exception as e:
            self.log(f"失败: {e}")
        finally:
            self.root.after(0, self.task_done)
            
    def up_worker(self, uid):
        """UP主工作线程"""
        try:
            count = int(self.count_var.get() or "10")
            self.log(f"获取UP主: {uid}")
            
            results = self.client.search_video(uid, page_size=count)
            self.root.after(0, lambda: self.show_videos(results))
            self.root.after(0, lambda: self.save_results(results))
            
            if self.dl_cover.get() and results:
                self.root.after(0, lambda: self.download_covers(results))
            if self.dl_video.get() and results:
                self.root.after(0, lambda: self.download_videos(results))
                
        except Exception as e:
            self.log(f"失败: {e}")
        finally:
            self.root.after(0, self.task_done)
            
    def comments_worker(self, bvid):
        """评论工作线程"""
        try:
            b = bvid
            # 处理URL
            if "bilibili.com" in bvid:
                m = re.search(r'BV[\w]+', bvid)
                if m:
                    b = m.group()
                    
            self.log(f"获取评论: {b}")
            
            info = self.client.get_video_info(b)
            self.root.after(0, lambda: self.show_videos([info]))
            
            aid = info.get("aid", 0)
            if not aid:
                self.log("无法获取视频ID")
                return
                
            comments = self.client.get_comments(aid, count=20)
            
            # 显示评论
            for c in comments:
                self.root.after(0, lambda c=c: self.comment_tree.insert("", "end", values=(
                    info.get("title", "")[:20] if info.get("title") else "",
                    c.get("user", ""),
                    c.get("content", "")[:50] if c.get("content") else "",
                    c.get("like", 0)
                )))
                
            cf = self.task_dir / "comments.json"
            with open(cf, "w", encoding="utf-8") as f:
                json.dump({"video": info.get("title"), "comments": comments}, f, ensure_ascii=False, indent=2)
            self.log(f"评论已保存: {cf}")
            
        except Exception as e:
            self.log(f"失败: {e}")
        finally:
            self.root.after(0, self.task_done)
            
    def show_videos(self, videos):
        """显示视频列表"""
        self.video_tree.delete(*self.video_tree.get_children())
        self.search_results = videos
        
        for i, v in enumerate(videos, 1):
            title = (v.get("title", "") or "")[:35]
            author = v.get("author", "") or ""
            play = v.get("play", v.get("view", 0) or 0)
            if play and isinstance(play, (int, float)) and play >= 10000:
                play = f"{play/10000:.1f}万"
            duration = v.get("duration", "") or ""
            bvid = v.get("bvid", "") or ""
            
            self.video_tree.insert("", "end", values=(i, title, author, play, duration, bvid))
            
    def save_results(self, videos):
        """保存结果"""
        jf = self.task_dir / "videos.json"
        with open(jf, "w", encoding="utf-8") as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
        self.log(f"已保存: {jf}")
        
    def download_covers(self, videos):
        """下载封面"""
        self.log("下载封面...")
        cd = self.task_dir / "covers"
        cd.mkdir(exist_ok=True)
        
        for v in videos:
            if not self.is_running:
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
                self.client.download_file(pic, cd / f"{bvid}.{ext}")
                self.log(f"封面: {bvid}.{ext}")
            except Exception as e:
                self.log(f"封面失败 {bvid}: {e}")
                
        self.log("封面下载完成")
        
    def download_all_comments(self, videos):
        """下载所有视频的评论"""
        self.log("下载评论...")
        
        for v in videos:
            if not self.is_running:
                break
                
            bvid = v.get("bvid", "") or ""
            aid = v.get("aid", 0)
            
            if not aid:
                continue
                
            try:
                comments = self.client.get_comments(aid, count=10)
                
                # 显示
                for c in comments:
                    self.comment_tree.insert("", "end", values=(
                        v.get("title", "")[:20] if v.get("title") else "",
                        c.get("user", ""),
                        c.get("content", "")[:50] if c.get("content") else "",
                        c.get("like", 0)
                    ))
                    
            except Exception as e:
                self.log(f"评论失败 {bvid}: {e}")
                
        self.log("评论下载完成")
        
    def download_videos(self, videos):
        """下载视频"""
        self.log("="*50)
        self.log("开始下载视频...")
        self.log("="*50)
        
        vd = self.task_dir / "videos"
        vd.mkdir(exist_ok=True)
        
        qn = int(self.quality_var.get() or "32")
        
        success_count = 0
        fail_count = 0
        
        for i, v in enumerate(videos):
            if not self.is_running:
                self.log("下载已停止")
                break
                
            bvid = v.get("bvid", "") or ""
            if not bvid:
                continue
            
            title = v.get("title", "")[:30]
            self.log(f"[{i+1}/{len(videos)}] {title}")
            self.log(f"    BV号: {bvid}")
                
            try:
                # 获取视频详情
                info = self.client.get_video_info(bvid)
                cid = info.get("cid", 0)
                
                if not cid:
                    self.log(f"    ❌ 无法获取CID")
                    fail_count += 1
                    continue
                    
                # 获取播放地址
                play = self.client.get_play_url(bvid, cid, qn=qn)
                urls = play.get("urls", [])
                
                if urls and urls[0].get("url"):
                    url = urls[0].get("url")
                    size_mb = urls[0].get("size", 0) / 1024 / 1024
                    
                    self.log(f"    大小: {size_mb:.1f}MB")
                    self.log(f"    正在下载...")
                    
                    self.client.download_file(url, vd / f"{bvid}.mp4", max_mb=500)
                    self.log(f"    ✅ 下载完成")
                    success_count += 1
                else:
                    self.log(f"    ❌ 无播放地址")
                    fail_count += 1
                    
            except Exception as e:
                self.log(f"    ❌ 失败: {e}")
                fail_count += 1
                
        self.log("="*50)
        self.log(f"视频下载完成: 成功{success_count}个, 失败{fail_count}个")
        self.log(f"保存位置: {vd}")
        self.log("="*50)
        
    def download_selected(self):
        """下载选中的视频"""
        selection = self.video_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先在视频列表中选择要下载的视频\n(可以多选)")
            return
            
        if not HAS_CLIENT:
            messagebox.showerror("错误", "B站API模块未找到")
            return
            
        # 获取选中的视频
        selected_videos = []
        for item_id in selection:
            item = self.video_tree.item(item_id)
            values = item['values']
            bvid = values[5] if len(values) > 5 else ""
            if bvid:
                # 查找对应的视频信息
                for v in self.search_results:
                    if v.get("bvid") == bvid:
                        selected_videos.append(v)
                        break
                        
        if not selected_videos:
            messagebox.showwarning("警告", "未找到选中视频的详细信息")
            return
            
        # 确认下载
        count = len(selected_videos)
        if messagebox.askyesno("确认", f"确定要下载选中的 {count} 个视频吗？"):
            self.is_running = True
            self.search_btn.config(state="disabled")
            self.download_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            
            # 创建任务目录
            task_dir = self.output_dir / f"bilibili_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            task_dir.mkdir(parents=True, exist_ok=True)
            self.task_dir = task_dir
            
            t = threading.Thread(target=self.download_selected_worker, args=(selected_videos,))
            t.daemon = True
            t.start()
            
    def download_selected_worker(self, videos):
        """下载选中视频的工作线程"""
        try:
            self.log("="*50)
            self.log("开始下载选中的视频...")
            self.log("="*50)
            
            vd = self.task_dir / "videos"
            vd.mkdir(exist_ok=True)
            
            qn = int(self.quality_var.get() or "32")
            
            success_count = 0
            fail_count = 0
            
            for i, v in enumerate(videos):
                if not self.is_running:
                    break
                    
                bvid = v.get("bvid", "") or ""
                if not bvid:
                    continue
                    
                title = v.get("title", "")[:30]
                self.log(f"[{i+1}/{len(videos)}] {title}")
                
                try:
                    info = self.client.get_video_info(bvid)
                    cid = info.get("cid", 0)
                    
                    if not cid:
                        self.log(f"    ❌ 无法获取CID")
                        fail_count += 1
                        continue
                        
                    play = self.client.get_play_url(bvid, cid, qn=qn)
                    urls = play.get("urls", [])
                    
                    if urls and urls[0].get("url"):
                        url = urls[0].get("url")
                        self.log(f"    正在下载...")
                        self.client.download_file(url, vd / f"{bvid}.mp4", max_mb=500)
                        self.log(f"    ✅ 完成")
                        success_count += 1
                    else:
                        self.log(f"    ❌ 无播放地址")
                        fail_count += 1
                        
                except Exception as e:
                    self.log(f"    ❌ 失败: {e}")
                    fail_count += 1
                    
            self.log("="*50)
            self.log(f"下载完成: 成功{success_count}个, 失败{fail_count}个")
            self.log(f"保存位置: {vd}")
            self.log("="*50)
            
        except Exception as e:
            self.log(f"下载失败: {e}")
        finally:
            self.root.after(0, self.task_done)
            
    def task_done(self):
        self.is_running = False
        self.search_btn.config(state="normal", bg="#3498DB")
        self.download_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("完成")
        self.log("任务完成!")


def main():
    root = tk.Tk()
    app = BilibiliGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
