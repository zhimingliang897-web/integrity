# 🎓 CourseDigest: 智能课程分析与助考助手

> **全自动将课程视频与 PDF 资料转化为高效的学习指南与模拟考题。**

CourseDigest 是一个专门为留学生和 STEM 课程学生设计的智能工具。它能够深度解析英文录播课视频及配套 PPT 讲义，利用领先的 AI 技术（如通义千问、Llama 3 等）输出针对性极强的中文「考试导向复习大纲」与「全真模拟试题」。

---

## ✨ 核心特性

- 🎙️ **本地语音转文字**：基于 `faster-whisper`，完全本地化运行，高精度且免费，保护隐私。
- 📄 **多维资料对齐**：支持 PDF/PPTX 文本提取，自动整合课件、视频逻辑与往年真题。
- 🤖 **多模型支持**：兼容阿里巴巴百炼（DashScope）与 Groq API，适配各种算力与预算需求。
- 🎯 **考试导向分析**：
  - 提取高频考点（带时间戳）。
  - 自动对比往年真题对应关系。
  - **新功能**：一键生成双倍题量（40+6）的模拟试卷与详尽解析。

---

## 🚀 快速开始

### 1. 环境准备

推荐使用 Conda 管理环境：

```bash
# 创建并激活环境
conda create -n coursedigest python=3.11 -y
conda activate coursedigest

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key

在项目根目录的 `config.yaml` 中填入你的 API 密钥：

```yaml
api:
  provider: "dashscope" # 或 "groq"
  api_key: "sk-your-key-here"
  model: "qwen-max"
```

---

## 🛠️ 三大应用场景

### 场景一：视频+课件 深度精读
最标准的用法，将视频与对应 PPT 传入，生成带时间戳的学习指南。
```bash
python main.py "lecture1.mp4" --ppt "slides.pdf" --exams "past_exams.pdf"
```

### 场景二：考前突击 模拟实战 (CV 专项 🌟)
**针对紧急考试设计的强化版工具。** 无需视频，直接扫描 `cache/ACV/` 下的所有 PDF 讲义（如 CV 课程的 7 节 PPT），一键生成深度考点及双倍模拟题。
```bash
python process_cv_exam.py
```
*   **输出结果**：`output/CV_Final_Exam_Prep.md`
*   **包含内容**：全章节考点图谱、40 道单选题、6 道填空题、每道题的【详细知识点分析】与【题解】。

### 场景三：智能资料匹配
不知道哪节课对应哪个 PPT？让 AI 帮你想办法：
```bash
python auto_match.py
```
该脚本会自动匹配视频与 PDF，并为你生成一个可直接运行的 `.bat` 批处理脚本。

---

## 📁 项目结构

```text
course_digest/
├── main.py            # 视频+资料处理主入口
├── process_cv_exam.py # ⭐ CV 专项考前模拟工具
├── transcribe.py      # 本地 Whisper 转录引擎
├── extract.py         # PDF/PPTX 文本提取器
├── analyze.py         # AI 调用中心
├── config.yaml        # API 与路径配置
├── input/             # 存放原始视频
└── cache/             # 存放缓存与 PPT 片段
    └── ACV/           # CV 专项资料存放处
```

---

## ❓ 常见问题

- **Q: 运行报错 `No module named 'xxx'`？**
  A: 请确保运行了 `pip install -r requirements.txt`。CV 专项工具需要 `pdfplumber` 和 `dashscope`。
- **Q: 转录速度慢？**
  A: 默认使用 CPU。如有 Nvidia 显卡，建议安装 CUDA 版 PyTorch 以获得 10 倍速提升。

---

## ⚖️ 费用说明

| 组件 | 费用 | 来源 |
| :--- | :--- | :--- |
| **Whisper 转录** | 免费 | 本地计算 |
| **PPT 提取** | 免费 | 本地计算 |
| **AI 分析** | 按量计费 | 阿里百炼/Groq |

---

## 📬 技术支持

如有疑问或反馈，请检查 Python 版本（>= 3.10）并确保 API 余额充足。
