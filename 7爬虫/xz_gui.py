# -*- coding: utf-8 -*-
"""
XZ图片网爬虫图形化界面
运行方式: python xz_gui.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# 尝试导入XZ爬虫模块
xz_dir = Path(__file__).parent / "xz_图片"
if xz_dir.exists():
    sys.path.insert(0, str(xz_dir))

try:
    from xz_scraper import XZScraper
    HAS_SCRAPER = True
except ImportError as e:
    HAS_SCRAPER = False
    IMPORT_ERROR = str(e)


class XZScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("XZ图片网爬虫工具")
        self.root.geometry("950x700")
        
        self.scraper = None
        self.is_running = False
        self.categories = []
        
        self.setup_ui()
        self.check_environment()
        
    def setup_ui(self):
        """设置界面"""
        
        # 标题
        title = tk.Label(self.root, text="XZ图片网爬虫工具", font=("Arial", 20, "bold"),
                        bg="#FF6B6B", fg="white", height=2)
        title.pack(fill="x")
        
        # 顶部设置区
        top = tk.Frame(self.root, pady=10)
        top.pack(fill="x", padx=10)
        
        # 左侧 - 基本设置
        left = tk.Frame(top)
        left.pack(side="left", fill="y")
        
        # 速度档位
        tk.Label(left, text="速度档位:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.speed_var = tk.StringVar(value="normal")
        
        speed_frame = tk.Frame(left)
        speed_frame.grid(row=1, column=0, sticky="w")
        tk.Radiobutton(speed_frame, text="快速", variable=self.speed_var, value="fast").pack(side="left")
        tk.Radiobutton(speed_frame, text="正常", variable=self.speed_var, value="normal").pack(side="left")
        tk.Radiobutton(speed_frame, text="慢速", variable=self.speed_var, value="slow").pack(side="left")
        tk.Radiobutton(speed_frame, text="安全", variable=self.speed_var, value="safe").pack(side="left")
        
        # 分类设置
        tk.Label(left, text="选择分类:", font=("Arial", 11, "bold")).grid(row=2, column=0, sticky="w", pady=(15, 5))
        
        tk.Label(left, text="分类名称:").grid(row=3, column=0, sticky="w")
        self.category_entry = tk.Entry(left, width=25)
        self.category_entry.grid(row=4, column=0, sticky="w", pady=2)
        tk.Label(left, text="(如: 秀人网, 语画界, all=全部)", fg="gray", font=("Arial", 8)).grid(row=5, column=0, sticky="w")
        
        # 数量限制
        tk.Label(left, text="下载限制:").grid(row=6, column=0, sticky="w", pady=(10, 0))
        self.max_var = tk.StringVar(value="0")
        tk.Entry(left, textvariable=self.max_var, width=10).grid(row=7, column=0, sticky="w")
        tk.Label(left, text="(0=全部, 数字=每个分类最多)", fg="gray", font=("Arial", 8)).grid(row=8, column=0, sticky="w")
        
        # 右侧 - 代理设置
        right = tk.Frame(top)
        right.pack(side="left", padx=(40, 0), fill="y")
        
        tk.Label(right, text="网络设置:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        
        # 代理开关
        self.use_proxy_var = tk.BooleanVar(value=False)
        tk.Checkbutton(right, text="使用代理", variable=self.use_proxy_var, 
                      font=("Arial", 10)).grid(row=1, column=0, sticky="w")
        
        tk.Label(right, text="代理地址:").grid(row=2, column=0, sticky="w", pady=(5, 0))
        self.proxy_entry = tk.Entry(right, width=25)
        self.proxy_entry.insert(0, "http://127.0.0.1:7890")
        self.proxy_entry.grid(row=3, column=0, sticky="w")
        
        # 常用代理快捷按钮
        proxy_frame = tk.Frame(right)
        proxy_frame.grid(row=4, column=0, sticky="w", pady=5)
        
        tk.Button(proxy_frame, text="Clash", width=8, command=lambda: self.set_proxy("http://127.0.0.1:7890")).pack(side="left", padx=2)
        tk.Button(proxy_frame, text="V2Ray", width=8, command=lambda: self.set_proxy("http://127.0.0.1:10809")).pack(side="left", padx=2)
        tk.Button(proxy_frame, text="不使用", width=8, command=lambda: self.set_proxy("")).pack(side="left", padx=2)
        
        tk.Label(right, text="常用端口: Clash=7890, V2Ray=10809", fg="gray", font=("Arial", 8)).grid(row=5, column=0, sticky="w")
        
        # 无头模式
        self.headless_var = tk.BooleanVar(value=False)
        tk.Checkbutton(right, text="无头模式(不显示浏览器)", variable=self.headless_var).grid(row=6, column=0, sticky="w", pady=(10, 0))
        
        # 中间 - 按钮区
        mid = tk.Frame(top)
        mid.pack(side="left", padx=(40, 0), fill="y")
        
        tk.Label(mid, text="").pack()  # 间距
        
        self.start_btn = tk.Button(mid, text="开始执行", command=self.start_task,
                                  bg="#28A745", fg="white", font=("Arial", 14, "bold"),
                                  width=15, height=2)
        self.start_btn.pack(pady=5)
        
        self.stop_btn = tk.Button(mid, text="停止", command=self.stop_task,
                                bg="#DC3545", fg="white", width=15, state="disabled")
        self.stop_btn.pack(pady=5)
        
        self.scan_btn = tk.Button(mid, text="扫描分类", command=self.scan_task,
                                 bg="#17A2B8", fg="white", width=15)
        self.scan_btn.pack(pady=5)
        
        # 环境检测显示
        env_frame = tk.LabelFrame(self.root, text="环境状态", font=("Arial", 10, "bold"))
        env_frame.pack(fill="x", padx=10, pady=5)
        
        self.env_text = tk.Text(env_frame, height=4, font=("Consolas", 9))
        self.env_text.pack(fill="x", padx=5, pady=5)
        
        # 结果区
        result_frame = tk.LabelFrame(self.root, text="分类列表", font=("Arial", 10, "bold"))
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("序号", "分类名称", "预估图集", "状态")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.tree.heading(col, text=col)
            
        self.tree.column("序号", width=50, anchor="center")
        self.tree.column("分类名称", width=300)
        self.tree.column("预估图集", width=100, anchor="center")
        self.tree.column("状态", width=150, anchor="center")
        
        sb = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        sb.pack(side="right", fill="y", pady=5)
        
        # 日志区
        log_frame = tk.LabelFrame(self.root, text="运行日志", font=("Arial", 10, "bold"))
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(self.root, textvariable=self.status_var, bd=1, relief="sunken", 
                anchor="w").pack(side="bottom", fill="x")
        
    def set_proxy(self, proxy):
        """设置代理"""
        self.proxy_entry.delete(0, "end")
        self.proxy_entry.insert(0, proxy)
        if proxy:
            self.use_proxy_var.set(True)
            self.log(f"代理已设置: {proxy}")
        else:
            self.use_proxy_var.set(False)
            self.log("代理已禁用")
            
    def check_environment(self):
        """检测环境"""
        self.env_text.insert("end", "="*50 + "\n")
        self.env_text.insert("end", "环境检测\n")
        self.env_text.insert("end", "="*50 + "\n\n")
        
        # 检测Python
        self.env_text.insert("end", f"Python: ✅ 已安装\n")
        
        # 检测requests
        try:
            import requests
            self.env_text.insert("end", f"requests: ✅ 已安装\n")
        except:
            self.env_text.insert("end", f"requests: ❌ 未安装\n")
            
        # 检测playwright
        try:
            import playwright
            self.env_text.insert("end", f"playwright: ✅ 已安装\n")
        except:
            self.env_text.insert("end", f"playwright: ❌ 未安装 (pip install playwright)\n")
            
        # 检测chromium
        try:
            from playwright.sync_api import sync_playwright
            pw = sync_playwright().start()
            pw.chromium.launch()
            pw.stop()
            self.env_text.insert("end", f"chromium: ✅ 已安装\n")
        except Exception as e:
            self.env_text.insert("end", f"chromium: ❌ 未安装 (playwright install chromium)\n")
            
        # 检测stealth
        try:
            sys.path.insert(0, str(xz_dir / "utils"))
            from stealth import STEALTH_JS, BROWSER_ARGS
            self.env_text.insert("end", f"stealth模块: ✅ 已安装\n")
            self.env_text.insert("end", f"\n状态: ✅ 所有依赖正常，可以运行\n")
            self.status_var.set("就绪 - 环境正常")
        except Exception as e:
            self.env_text.insert("end", f"stealth模块: ❌ 未找到\n")
            self.env_text.insert("end", f"错误: {e}\n")
            self.env_text.insert("end", f"\n状态: ❌ 请检查依赖\n")
            self.status_var.set("就绪 - 缺少依赖")
            
    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        self.root.update()
        
    def scan_task(self):
        """扫描分类"""
        self.log("扫描功能需要在命令行运行: python xz_scraper.py --scan")
        messagebox.showinfo("提示", "扫描功能请使用命令行:\n\ncd xz_图片\npython xz_scraper.py --scan")
        
    def start_task(self):
        """开始下载"""
        if self.is_running:
            return
            
        # 获取代理
        proxy = ""
        if self.use_proxy_var.get():
            proxy = self.proxy_entry.get().strip()
            
        category = self.category_entry.get().strip() or "all"
        max_albums = int(self.max_var.get() or "0")
        speed = self.speed_var.get()
        
        self.log(f"开始任务: 分类={category}, 最大={max_albums}, 速度={speed}")
        self.log(f"代理: {proxy if proxy else '不使用'}")
        
        # 这里需要调用命令行运行
        cmd = [
            sys.executable, 
            "-c",
            f"""
import sys
sys.path.insert(0, r'{xz_dir}')
from xz_scraper import XZScraper
import threading

scraper = XZScraper(
    speed='{speed}',
    headless={self.headless_var.get()},
    category_filter='{category}',
    max_albums={max_albums},
    proxy='{proxy}'
)
scraper.run()
"""
        ]
        
        self.is_running = True
        self.start_btn.config(state="disabled", bg="#6c757d")
        self.stop_btn.config(state="normal")
        self.status_var.set("运行中...")
        
        # 在后台运行
        def run():
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                      universal_newlines=True)
                for line in proc.stdout:
                    self.root.after(0, lambda l=line: self.log(l.strip()))
                proc.wait()
            except Exception as e:
                self.root.after(0, lambda: self.log(f"错误: {e}"))
            finally:
                self.root.after(0, self.task_done)
                
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        
    def stop_task(self):
        self.is_running = False
        self.start_btn.config(state="normal", bg="#28A745")
        self.stop_btn.config(state="disabled")
        self.status_var.set("已停止")
        self.log("用户停止")
        
    def task_done(self):
        self.is_running = False
        self.start_btn.config(state="normal", bg="#28A745")
        self.stop_btn.config(state="disabled")
        self.status_var.set("完成")
        self.log("任务完成!")


def main():
    root = tk.Tk()
    app = XZScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
