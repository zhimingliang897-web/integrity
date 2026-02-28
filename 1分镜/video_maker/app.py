#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分镜视频生成器 - 桌面 GUI
运行: python app.py
依赖: 仅使用 Python 内置 tkinter，无需额外安装
"""
import os, sys, json, subprocess, threading, queue
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "api_key": "",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "text_model": "kimi-k2.5",
    "image_model": "qwen-image",
}

TEXT_MODELS  = ["kimi-k2.5", "qwen3-max-2026-01-23", "qwen-plus", "qwen-turbo", "qwen-max"]
IMAGE_MODELS = ["qwen-image", "wanx2.1-t2i-turbo", "wanx2.1-t2i-plus","qwen-image-plus-2026-01-09"]


# ── 设置 I/O ──────────────────────────────────────────────────────────────────

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_env():
    s = load_settings()
    env = os.environ.copy()
    env["DASHSCOPE_API_KEY"]    = s["api_key"]
    env["DASHSCOPE_BASE_URL"]   = s["base_url"]
    env["DASHSCOPE_TEXT_MODEL"] = s["text_model"]
    env["DASHSCOPE_IMAGE_MODEL"]= s["image_model"]
    env["PYTHONUNBUFFERED"]     = "1"
    env["PYTHONIOENCODING"]     = "utf-8"
    return env


# ── 主窗口 ────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("分镜视频生成器")
        self.geometry("980x700")
        self.minsize(820, 580)
        self._q    = queue.Queue()
        self._busy = False
        self._build_ui()
        self._tick()

    # ── 整体布局 ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        for title, builder in [
            ("  生成  ", self._tab_generate),
            ("  文本  ", self._tab_text),
            ("  配置  ", self._tab_settings),
            ("  说明  ", self._tab_help),
        ]:
            f = ttk.Frame(nb)
            nb.add(f, text=title)
            builder(f)

    # ── Tab: 生成 ─────────────────────────────────────────────────────────────

    def _tab_generate(self, p):
        # 参数区
        pf = ttk.LabelFrame(p, text="生成参数", padding=8)
        pf.pack(fill=tk.X, padx=8, pady=(8, 4))

        # row 0 : 项目名 + 方案 + 图片模式
        ttk.Label(pf, text="项目文件夹名:").grid(row=0, column=0, sticky=tk.W)
        self._v_proj = tk.StringVar()
        ttk.Entry(pf, textvariable=self._v_proj, width=16).grid(
            row=0, column=1, sticky=tk.EW, padx=(4, 20))

        ttk.Label(pf, text="方案:").grid(row=0, column=2, sticky=tk.W)
        self._v_strategy = tk.StringVar(value="多图方案")
        ttk.Combobox(pf, textvariable=self._v_strategy,
                     values=["多图方案", "四宫格方案"],
                     state="readonly", width=12).grid(row=0, column=3, padx=(4, 20))

        ttk.Label(pf, text="图片模式:").grid(row=0, column=4, sticky=tk.W)
        self._v_img_mode = tk.StringVar(value="API 自动生成")
        ttk.Combobox(pf, textvariable=self._v_img_mode,
                     values=["API 自动生成", "手动准备（查看 Prompt）"],
                     state="readonly", width=18).grid(row=0, column=5, padx=(4, 0))

        # row 1 : 场景描述
        ttk.Label(pf, text="场景描述:").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        self._v_scene = tk.StringVar()
        ttk.Entry(pf, textvariable=self._v_scene).grid(
            row=1, column=1, columnspan=5, sticky=tk.EW, padx=(4, 0), pady=(8, 0))

        pf.columnconfigure(1, weight=1)

        # 按钮行
        bf = ttk.Frame(p)
        bf.pack(fill=tk.X, padx=8, pady=4)

        self._btn1    = ttk.Button(bf, text="① 剧本 + 图片",  command=self._step1)
        self._btn2    = ttk.Button(bf, text="② 合成视频",     command=self._step2)
        self._btn_all = ttk.Button(bf, text="⚡ 一键全流程",   command=self._run_all)
        for b in (self._btn1, self._btn2, self._btn_all):
            b.pack(side=tk.LEFT, padx=(0, 4))

        ttk.Button(bf, text="清空日志", command=self._clear_log).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(bf, text="打开项目文件夹", command=self._open_folder).pack(side=tk.LEFT)

        self._v_status = tk.StringVar(value="就绪")
        ttk.Label(bf, textvariable=self._v_status, foreground="#777777").pack(side=tk.RIGHT)

        # 图片模式切换时更新按钮状态和标签
        def _on_img_mode(*_):
            manual = self._v_img_mode.get().startswith("手动")
            self._btn_all.config(state=tk.DISABLED if manual else tk.NORMAL)
            self._btn1.config(text="① 只生成剧本" if manual else "① 剧本 + 图片")
        self._v_img_mode.trace_add("write", _on_img_mode)

        # 日志区
        lf = ttk.LabelFrame(p, text="运行日志", padding=4)
        lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self._log = scrolledtext.ScrolledText(
            lf, state=tk.DISABLED, wrap=tk.WORD,
            font=("Consolas", 9), bg="#1c1c1c", fg="#d0d0d0",
            insertbackground="white", relief=tk.FLAT,
        )
        self._log.pack(fill=tk.BOTH, expand=True)

    # ── Tab: 文本 ─────────────────────────────────────────────────────────────

    def _tab_text(self, p):
        top = ttk.Frame(p)
        top.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(top, text="项目文件夹名:").pack(side=tk.LEFT)
        self._v_text_proj = tk.StringVar()
        ttk.Entry(top, textvariable=self._v_text_proj, width=16).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="加载", command=self._load_text).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(top, text="保存", command=self._save_text_file).pack(side=tk.LEFT)
        self._v_text_msg = tk.StringVar()
        ttk.Label(top, textvariable=self._v_text_msg, foreground="#28a745").pack(
            side=tk.LEFT, padx=8)

        ttk.Label(p, text=(
            "提示：修改文本后点「保存」，再切到「生成」标签点「② 合成视频」即可用新文本重新合成。"
        ), foreground="#888888").pack(anchor=tk.W, padx=8)

        self._text_ed = scrolledtext.ScrolledText(
            p, wrap=tk.WORD, font=("Consolas", 10), undo=True)
        self._text_ed.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))

    # ── Tab: 配置 ─────────────────────────────────────────────────────────────

    def _tab_settings(self, p):
        s = load_settings()

        frm = ttk.LabelFrame(p, text="API 配置", padding=12)
        frm.pack(fill=tk.X, padx=12, pady=12)

        self._cfg = {}
        fields = [
            ("API Key:",  "api_key",     True,  None),
            ("Base URL:", "base_url",    False, None),
            ("文本模型:", "text_model",  False, TEXT_MODELS),
            ("图片模型:", "image_model", False, IMAGE_MODELS),
        ]
        for i, (label, key, masked, choices) in enumerate(fields):
            ttk.Label(frm, text=label).grid(row=i, column=0, sticky=tk.W, pady=5, padx=(0, 8))
            var = tk.StringVar(value=s[key])
            self._cfg[key] = var
            if choices:
                w = ttk.Combobox(frm, textvariable=var, values=choices, width=44)
            else:
                w = ttk.Entry(frm, textvariable=var, width=52, show="*" if masked else "")
            w.grid(row=i, column=1, sticky=tk.EW)

        frm.columnconfigure(1, weight=1)

        bf = ttk.Frame(p)
        bf.pack(anchor=tk.W, padx=12, pady=4)
        ttk.Button(bf, text="保存配置", command=self._save_cfg).pack(side=tk.LEFT)
        self._v_cfg_msg = tk.StringVar()
        ttk.Label(bf, textvariable=self._v_cfg_msg, foreground="#28a745").pack(
            side=tk.LEFT, padx=8)

        info = ttk.LabelFrame(p, text="说明", padding=10)
        info.pack(fill=tk.X, padx=12, pady=8)
        ttk.Label(info, justify=tk.LEFT, font=("Consolas", 9), text=(
            "API Key             →  阿里云 DashScope 控制台 → API Key 管理\n"
            "Base URL            →  DashScope 兼容 OpenAI 格式接口，通常不用修改\n"
            "kimi-k2.5           →  文本生成，免费 100 万 token（截止 2026/04）\n"
            "qwen3-max-2026-0123 →  通义千问 3 Max，免费额度至 2026/04/23\n"
            "qwen-image          →  通义万相图片生成（默认推荐）\n"
            "wanx2.1-t2i-turbo  →  万象 2.1 快速版"
        )).pack(anchor=tk.W)

    # ── Tab: 说明 ─────────────────────────────────────────────────────────────

    def _tab_help(self, p):
        txt = scrolledtext.ScrolledText(p, wrap=tk.WORD, font=("Consolas", 9))
        txt.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        txt.insert(tk.END, HELP_TEXT)
        txt.config(state=tk.DISABLED)

    # ── 日志 ──────────────────────────────────────────────────────────────────

    def _tick(self):
        try:
            while True:
                msg = self._q.get_nowait()
                self._log.config(state=tk.NORMAL)
                self._log.insert(tk.END, msg + "\n")
                self._log.see(tk.END)
                self._log.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        self.after(80, self._tick)

    def _clear_log(self):
        self._log.config(state=tk.NORMAL)
        self._log.delete("1.0", tk.END)
        self._log.config(state=tk.DISABLED)

    def _open_folder(self):
        name = self._v_proj.get().strip()
        if not name:
            messagebox.showinfo("提示", "请先填写项目文件夹名")
            return
        path = os.path.join(SCRIPT_DIR, name)
        if os.path.isdir(path):
            os.startfile(path)
        else:
            messagebox.showinfo("提示", f"文件夹不存在:\n{path}")

    # ── 配置 ──────────────────────────────────────────────────────────────────

    def _save_cfg(self):
        save_settings({k: v.get().strip() for k, v in self._cfg.items()})
        self._v_cfg_msg.set("已保存 ✓")
        self.after(3000, lambda: self._v_cfg_msg.set(""))

    # ── 文本编辑 ──────────────────────────────────────────────────────────────

    def _load_text(self):
        name = self._v_text_proj.get().strip()
        if not name:
            messagebox.showwarning("提示", "请填写项目文件夹名")
            return
        path = os.path.join(SCRIPT_DIR, name, "input", "文本.txt")
        if not os.path.exists(path):
            messagebox.showinfo("提示", f"文件不存在:\n{path}")
            return
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self._text_ed.delete("1.0", tk.END)
        self._text_ed.insert(tk.END, content)
        self._v_text_msg.set(f"已加载 ✓  ({path})")
        self.after(5000, lambda: self._v_text_msg.set(""))

    def _save_text_file(self):
        name = self._v_text_proj.get().strip()
        if not name:
            messagebox.showwarning("提示", "请填写项目文件夹名")
            return
        path = os.path.join(SCRIPT_DIR, name, "input", "文本.txt")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._text_ed.get("1.0", tk.END))
        self._v_text_msg.set("已保存 ✓")
        self.after(3000, lambda: self._v_text_msg.set(""))

    # ── 生成流程 ──────────────────────────────────────────────────────────────

    def _check(self, need_scene=False):
        s = load_settings()
        if not s["api_key"]:
            messagebox.showwarning("未配置", "请先到【配置】页填写 API Key 并保存")
            return False
        if not self._v_proj.get().strip():
            messagebox.showwarning("未填写", "请填写项目文件夹名（例如: 8超市）")
            return False
        if need_scene and not self._v_scene.get().strip():
            messagebox.showwarning("未填写", "请填写场景描述")
            return False
        return True

    def _lock(self):
        self._busy = True
        for b in (self._btn1, self._btn2, self._btn_all):
            b.config(state=tk.DISABLED)
        self._v_status.set("运行中…")

    def _unlock(self):
        self._busy = False
        self._btn1.config(state=tk.NORMAL)
        self._btn2.config(state=tk.NORMAL)
        # 手动模式下全流程按钮保持禁用
        if not self._v_img_mode.get().startswith("手动"):
            self._btn_all.config(state=tk.NORMAL)
        self._v_status.set("就绪")

    def _launch(self, cmd, on_done=None):
        """在后台线程运行命令，将输出推入队列。"""
        self._lock()
        display = " ".join(
            os.path.basename(c) if (os.sep in c or "/" in c) else c
            for c in cmd
        )
        self._q.put(f"\n▶  {display}")

        def _worker():
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=build_env(),
                cwd=SCRIPT_DIR,
            )
            for raw in proc.stdout:
                self._q.put(raw.decode("utf-8", errors="replace").rstrip())
            proc.wait()
            ok = proc.returncode == 0
            self._q.put("✅ 完成！" if ok else f"❌ 退出码: {proc.returncode}")
            if on_done and ok:
                self.after(0, on_done)
            else:
                self.after(0, self._unlock)

        threading.Thread(target=_worker, daemon=True).start()

    def _step1(self):
        if self._busy or not self._check(need_scene=True):
            return
        # 根据方案选择对应的文件夹和脚本
        if self._v_strategy.get() == "多图方案":
            script_dir = os.path.join(SCRIPT_DIR, "multi")
        else:
            script_dir = os.path.join(SCRIPT_DIR, "grid")
        cmd = [sys.executable, "-u", os.path.join(script_dir, "gen_text.py"),
               self._v_proj.get().strip(), self._v_scene.get().strip()]
        if self._v_img_mode.get().startswith("手动"):
            cmd.append("--no-image")
        self._launch(cmd)

    def _step2(self):
        if self._busy or not self._check():
            return
        # 根据方案选择对应的文件夹和脚本
        if self._v_strategy.get() == "多图方案":
            script_dir = os.path.join(SCRIPT_DIR, "multi")
        else:
            script_dir = os.path.join(SCRIPT_DIR, "grid")
        self._launch([
            sys.executable, "-u", os.path.join(script_dir, "make_video.py"),
            self._v_proj.get().strip(),
        ])

    def _run_all(self):
        if self._busy or not self._check(need_scene=True):
            return
        # 根据方案选择对应的文件夹
        if self._v_strategy.get() == "多图方案":
            script_dir = os.path.join(SCRIPT_DIR, "multi")
        else:
            script_dir = os.path.join(SCRIPT_DIR, "grid")
        cmd1 = [sys.executable, "-u",
                os.path.join(script_dir, "gen_text.py"),
                self._v_proj.get().strip(), self._v_scene.get().strip()]
        cmd2 = [sys.executable, "-u",
                os.path.join(script_dir, "make_video.py"),
                self._v_proj.get().strip()]

        def _start2():
            self._q.put("\n" + "─" * 50 + "\n▶  步骤 2：开始合成视频...\n")
            self._launch(cmd2)

        self._launch(cmd1, on_done=_start2)


# ── 帮助文本 ──────────────────────────────────────────────────────────────────

HELP_TEXT = """\
快速上手
════════════════════════════════════════════════════

1. 配置 API（切换到"配置"标签）
   ① 填写 API Key，从 https://dashscope.console.aliyun.com/ 获取
   ② 点击"保存配置"

2. 选择方案
   • 多图方案     — 每场景单独生成图片，4-6 个场景，风格多样
   • 四宫格方案   — 一张四格图，视觉风格统一，固定 4 场景

3. 生成视频
   ① 填写"项目文件夹名"，例如：8超市
   ② 填写"场景描述"，越具体越好，例如：
        在超市买水果，和店员讨价还价
   ③ 点击"① 剧本+图片"（约 1-2 分钟）
   ④ 点击"② 合成视频"
      或直接点击"⚡ 一键全流程"一步到位

4. 修改剧本重新合成（可选）
   • 切换到"文本"标签 → 加载 → 手动修改 → 保存
   • 回到"生成"标签 → 点击"② 合成视频"

输出文件
════════════════════════════════════════════════════

  项目文件夹/
  ├── input/
  │   ├── 文本.txt        ← AI 剧本（可手动编辑）
  │   ├── 1.png ~ N.png   ← 分镜图（多图方案）
  │   └── 图片.png        ← 四宫格图（四宫格方案）
  └── output/
      ├── 项目名.mp4       ← 最终视频（正常语速）
      ├── 项目名_slow.mp4 ← 慢速版（仅四宫格，语速 -30%）
      └── poster.png       ← 学习海报（适合发评论区）

文本格式
════════════════════════════════════════════════════

  Ordering Coffee — 咖啡店点单
  ---
  M1: Hey, could I get a medium latte? | 嘿，能来一杯中杯拿铁吗？
  F1: Sure! For here or to go?         | 好的！堂食还是外带？
  ---
  M1: To go, please. | 外带，谢谢。
  ===
  could I get... — 能来一个… — Could I get a black coffee?
  ===
  Panel 1: 男生走进咖啡店，拿起菜单，表情茫然
  Panel 2: 男生指着菜单问，店员微笑回答

  符号说明：
  • 第一行          = 标题（英文 — 中文，视频开头显示 1.5 秒）
  • M1/M2           = 男声，F1/F2 = 女声
  • |               = 英文台词与中文翻译的分隔
  • ---             = 场景分隔
  • === ... ===     = 核心表达区域（生成学习海报）
  • Panel N:        = 分镜描述（用于图片生成）

声音列表
════════════════════════════════════════════════════

  M1  →  en-US-GuyNeural           F1  →  en-US-JennyNeural
  M2  →  en-US-ChristopherNeural   F2  →  en-US-AriaNeural

依赖安装
════════════════════════════════════════════════════

  pip install pillow edge-tts openai

  另需安装 FFmpeg 并加入系统 PATH：
  https://ffmpeg.org/download.html

  本 GUI 使用 Python 内置 tkinter，无需额外安装。
"""


if __name__ == "__main__":
    app = App()
    app.mainloop()
