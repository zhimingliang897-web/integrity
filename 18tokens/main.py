import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import base64
from PIL import Image, ImageTk
import threading
import os

try:
    from translate import Translator
    HAS_TRANSLATE = True
except ImportError:
    HAS_TRANSLATE = False

# API配置
DASHSCOPE_API_KEY = ""your-key-replaced"
OPENAI_API_KEY = ""your-key-replaced"

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
OPENAI_BASE_URL = "https://api.openai.com/v1"

# 模型分组
MODELS = {
    "阿里云百炼": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen-vl-plus"],
    "OpenAI": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
}


class TokenAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Token消耗对比分析工具")
        self.root.geometry("1100x800")
        self.root.minsize(1000, 700)
        self.selected_image = None
        self.history = []

        # 主布局：左侧输入 + 右侧结果
        main_paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ========== 左侧面板：输入区 ==========
        left_frame = ttk.LabelFrame(main_paned, text=" 输入设置 ", padding=15)
        main_paned.add(left_frame, weight=1)

        # 问题输入
        ttk.Label(left_frame, text="问题内容:", font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")
        self.question_text = tk.Text(left_frame, height=4, font=("Microsoft YaHei", 10), wrap="word")
        self.question_text.insert("1.0", "北京今天天气怎么样")
        self.question_text.pack(fill="x", pady=(5, 15))

        # 语言选择
        ttk.Label(left_frame, text="输入语言:", font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")
        self.language_var = tk.StringVar(value="中文")
        lang_frame = ttk.Frame(left_frame)
        lang_frame.pack(fill="x", pady=(5, 15))
        for lang in ["中文", "英文", "图片中文"]:
            ttk.Radiobutton(lang_frame, text=lang, variable=self.language_var, value=lang,
                            command=self.on_language_change).pack(side="left", padx=10)

        # 模型选择
        ttk.Label(left_frame, text="选择模型:", font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")
        self.model_var = tk.StringVar(value="qwen-plus")
        self.model_combo = ttk.Combobox(left_frame, textvariable=self.model_var, state="readonly",
                                         font=("Microsoft YaHei", 10), width=30)
        self.update_model_list()
        self.model_combo.pack(anchor="w", pady=(5, 15))

        # 图片选择区（初始隐藏）
        self.image_frame = ttk.LabelFrame(left_frame, text=" 图片选择 ", padding=10)
        self.image_preview = ttk.Label(self.image_frame)
        self.image_preview.pack(pady=5)
        self.image_path_label = ttk.Label(self.image_frame, text="未选择图片", foreground="gray")
        self.image_path_label.pack()
        ttk.Button(self.image_frame, text="选择图片", command=self.choose_image).pack(pady=5)

        # 按钮区
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill="x", pady=20)
        self.run_btn = ttk.Button(btn_frame, text="开始分析", command=self.start_analysis, width=12)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="清空历史", command=self.clear_history, width=12).pack(side="left", padx=5)

        # 翻译结果预览
        self.trans_frame = ttk.LabelFrame(left_frame, text=" 翻译预览 ", padding=10)
        self.trans_label = ttk.Label(self.trans_frame, text="", wraplength=300, foreground="blue")
        self.trans_label.pack(fill="x")

        # ========== 右侧面板：结果区 ==========
        right_frame = ttk.LabelFrame(main_paned, text=" 分析结果 ", padding=15)
        main_paned.add(right_frame, weight=2)

        # 当前结果
        current_frame = ttk.LabelFrame(right_frame, text=" 本次分析 ", padding=10)
        current_frame.pack(fill="x", pady=(0, 10))

        # Token统计表格
        self.current_info = ttk.Frame(current_frame)
        self.current_info.pack(fill="x")

        # 创建统计标签
        stats_frame = ttk.Frame(self.current_info)
        stats_frame.pack(fill="x", pady=5)

        self.stat_labels = {}
        for i, (key, text) in enumerate([
            ("model", "模型"),
            ("lang", "语言"),
            ("prompt", "输入Token"),
            ("completion", "输出Token"),
            ("total", "总Token")
        ]):
            ttk.Label(stats_frame, text=f"{text}:", font=("Microsoft YaHei", 9)).grid(row=0, column=i*2, sticky="e", padx=(10, 2))
            self.stat_labels[key] = ttk.Label(stats_frame, text="-", font=("Microsoft YaHei", 10, "bold"), foreground="navy")
            self.stat_labels[key].grid(row=0, column=i*2+1, sticky="w", padx=(0, 10))

        # 实际发送内容
        ttk.Label(current_frame, text="实际发送:", font=("Microsoft YaHei", 9)).pack(anchor="w", pady=(10, 2))
        self.sent_text = tk.Text(current_frame, height=2, font=("Consolas", 9), wrap="word", bg="#f5f5f5")
        self.sent_text.pack(fill="x")
        self.sent_text.config(state="disabled")

        # 模型回答
        ttk.Label(current_frame, text="模型回答:", font=("Microsoft YaHei", 9)).pack(anchor="w", pady=(10, 2))
        self.response_text = tk.Text(current_frame, height=5, font=("Microsoft YaHei", 9), wrap="word", bg="#f5f5f5")
        self.response_text.pack(fill="x")
        self.response_text.config(state="disabled")

        # 历史对比表格
        history_frame = ttk.LabelFrame(right_frame, text=" 历史对比 ", padding=10)
        history_frame.pack(fill="both", expand=True)

        # 表格
        columns = ("序号", "语言", "模型", "输入Token", "输出Token", "总Token", "输入字符数", "问题内容")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=12)

        # 设置列宽和对齐
        col_widths = [40, 70, 100, 80, 80, 80, 80, 200]
        for col, width in zip(columns, col_widths):
            self.history_tree.heading(col, text=col)
            anchor = "center" if col != "问题内容" else "w"
            self.history_tree.column(col, width=width, anchor=anchor)

        # 滚动条
        scrollbar_y = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        scrollbar_x = ttk.Scrollbar(history_frame, orient="horizontal", command=self.history_tree.xview)
        self.history_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")

        # 统计摘要
        self.summary_label = ttk.Label(right_frame, text="", font=("Microsoft YaHei", 9), foreground="green")
        self.summary_label.pack(anchor="w", pady=(10, 0))

        # ========== 底部状态栏 ==========
        self.status_var = tk.StringVar(value="就绪 | 百炼默认qwen-plus | 图片模式仅支持qwen-vl-plus")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w", padding=5)
        status_bar.pack(side="bottom", fill="x")

        # 绑定事件
        self.language_var.trace("w", lambda *args: self.update_model_list())
        self.on_language_change()

    def update_model_list(self):
        lang = self.language_var.get()
        if lang == "图片中文":
            models = ["百炼: qwen-vl-plus"]
        else:
            models = [f"百炼: {m}" for m in MODELS["阿里云百炼"] if m != "qwen-vl-plus"] + \
                     [f"OpenAI: {m}" for m in MODELS["OpenAI"]]
        self.model_combo["values"] = models
        if models:
            self.model_combo.current(0)

    def on_language_change(self):
        lang = self.language_var.get()
        if lang == "图片中文":
            self.image_frame.pack(fill="x", pady=(0, 15))
            self.trans_frame.pack_forget()
            self.status_var.set("图片中文模式 | 仅支持qwen-vl-plus")
        elif lang == "英文":
            self.image_frame.pack_forget()
            self.trans_frame.pack(fill="x", pady=(0, 15))
            self.selected_image = None
            self.status_var.set("英文模式 | 问题将自动翻译为英文")
        else:
            self.image_frame.pack_forget()
            self.trans_frame.pack_forget()
            self.selected_image = None
            self.status_var.set("中文模式 | 直接发送中文问题")

    def choose_image(self):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片", "*.jpg *.jpeg *.png *.bmp *.webp")]
        )
        if path and os.path.exists(path):
            try:
                img = Image.open(path)
                img.thumbnail((250, 150))
                self.tk_img = ImageTk.PhotoImage(img)
                self.image_preview.config(image=self.tk_img)
                self.selected_image = path
                self.image_path_label.config(text=os.path.basename(path), foreground="green")
            except Exception as e:
                messagebox.showerror("错误", f"无法加载图片:\n{e}")

    def clear_history(self):
        self.history.clear()
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        self.summary_label.config(text="")
        self.status_var.set("已清空历史")

    def translate_to_english(self, chinese_text):
        if HAS_TRANSLATE:
            translator = Translator(from_lang="zh", to_lang="en")
            return translator.translate(chinese_text)
        else:
            trans_map = {
                "北京今天天气怎么样": "What's the weather like in Beijing today?",
                "你好": "Hello",
                "今天天气怎么样": "What's the weather like today?",
                "人工智能是什么": "What is artificial intelligence?",
            }
            return trans_map.get(chinese_text, chinese_text)

    def start_analysis(self):
        question = self.question_text.get("1.0", tk.END).strip()
        lang = self.language_var.get()
        model_full = self.model_combo.get()

        if not question:
            messagebox.showwarning("错误", "请输入问题内容")
            return
        if lang == "图片中文" and not self.selected_image:
            messagebox.showwarning("错误", "请先选择图片")
            return
        if not model_full:
            messagebox.showwarning("错误", "请选择模型")
            return

        model = model_full.split(": ")[1] if ": " in model_full else model_full

        self.run_btn.config(state="disabled", text="分析中...")
        self.status_var.set(f"正在调用 {model}...")

        threading.Thread(target=self.run_analysis, args=(question, lang, model), daemon=True).start()

    def run_analysis(self, question, lang, model):
        try:
            if lang == "中文":
                content = f"请用中文回答：{question}"
                display_content = content
                input_chars = len(content)
            elif lang == "英文":
                self.root.after(0, lambda: self.status_var.set("正在翻译..."))
                eng_q = self.translate_to_english(question)
                content = f"Please answer in Chinese: {eng_q}"
                display_content = content
                input_chars = len(content)
                self.root.after(0, lambda: self.trans_label.config(text=eng_q))
            else:
                if not self.selected_image:
                    raise ValueError("未选择图片")
                with open(self.selected_image, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                ext = os.path.splitext(self.selected_image)[1].lower()
                mime_map = {'.jpg': 'jpeg', '.jpeg': 'jpeg', '.png': 'png', '.webp': 'webp'}
                mime_type = mime_map.get(ext, 'jpeg')
                content = [
                    {"type": "image_url", "image_url": {"url": f"data:image/{mime_type};base64,{img_b64}"}},
                    {"type": "text", "text": "请用中文回答图片中的问题"}
                ]
                display_content = f"[图片: {os.path.basename(self.selected_image)}]"
                input_chars = len(img_b64) + 20

            # 调用API
            self.root.after(0, lambda: self.status_var.set(f"正在调用 {model}..."))
            if model in MODELS["阿里云百炼"]:
                tokens, response = self.call_dashscope(model, content)
            else:
                tokens, response = self.call_openai(model, content)

            record = {
                "model": model,
                "lang": lang,
                "question": question,
                "display_content": display_content,
                "input_chars": input_chars,
                "tokens": tokens,
                "response": response
            }
            self.history.append(record)
            self.root.after(0, self.show_result, record)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
            self.root.after(0, lambda: self.status_var.set("分析失败"))
        finally:
            self.root.after(0, lambda: self.run_btn.config(state="normal", text="开始分析"))

    def call_dashscope(self, model, content):
        headers = {"Authorization": f"Bearer {DASHSCOPE_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": content}]}
        resp = requests.post(f"{DASHSCOPE_BASE_URL}/chat/completions", headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["usage"], data["choices"][0]["message"]["content"]

    def call_openai(self, model, content):
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": content}]}
        resp = requests.post(f"{OPENAI_BASE_URL}/chat/completions", headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["usage"], data["choices"][0]["message"]["content"]

    def show_result(self, record):
        tokens = record["tokens"]

        # 更新统计标签
        self.stat_labels["model"].config(text=record["model"])
        self.stat_labels["lang"].config(text=record["lang"])
        self.stat_labels["prompt"].config(text=str(tokens.get("prompt_tokens", 0)))
        self.stat_labels["completion"].config(text=str(tokens.get("completion_tokens", 0)))
        self.stat_labels["total"].config(text=str(tokens.get("total_tokens", 0)))

        # 更新发送内容
        self.sent_text.config(state="normal")
        self.sent_text.delete("1.0", tk.END)
        self.sent_text.insert("1.0", record["display_content"])
        self.sent_text.config(state="disabled")

        # 更新回答
        self.response_text.config(state="normal")
        self.response_text.delete("1.0", tk.END)
        self.response_text.insert("1.0", record["response"])
        self.response_text.config(state="disabled")

        # 添加到历史表格
        idx = len(self.history)
        question_preview = record["question"][:30] + "..." if len(record["question"]) > 30 else record["question"]
        self.history_tree.insert("", "end", values=(
            idx,
            record["lang"],
            record["model"],
            tokens.get("prompt_tokens", 0),
            tokens.get("completion_tokens", 0),
            tokens.get("total_tokens", 0),
            record["input_chars"],
            question_preview
        ))

        # 更新统计摘要
        if len(self.history) > 1:
            prompt_tokens = [h["tokens"].get("prompt_tokens", 0) for h in self.history]
            total_tokens = [h["tokens"].get("total_tokens", 0) for h in self.history]
            self.summary_label.config(
                text=f"统计: 共{len(self.history)}次测试 | 输入Token范围: {min(prompt_tokens)}-{max(prompt_tokens)} | 总Token范围: {min(total_tokens)}-{max(total_tokens)}"
            )

        self.status_var.set(f"完成 | {record['model']} | 输入:{tokens.get('prompt_tokens', 0)} 输出:{tokens.get('completion_tokens', 0)} 总计:{tokens.get('total_tokens', 0)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TokenAnalyzerApp(root)
    root.mainloop()
