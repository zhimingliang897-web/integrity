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

### 1. 一句话用法（TL;DR）

整门课资料都在一个文件夹里（推荐 `cache/dl/6103/`），直接运行：

```bash
python dl_generate.py cache/dl/6103 --transcribe-all
```

就会在 `output/` 生成：

- `6103_复习指南.md`
- `6103_考试指南.md`

其他模式和更多细节见下文。

### 2. 环境准备

推荐使用 Conda 管理环境：

```bash
# 创建并激活环境
conda create -n coursedigest python=3.11 -y
conda activate coursedigest

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置 API Key 与模型

在项目根目录的 `config.yaml` 中填入你的 API 密钥：

```yaml
api:
  provider: "dashscope"      # 使用百炼 / 千问
  api_key: "sk-your-key-here"
  model: "glm-5"             # 例如使用 GLM-5，也可以改成 qwen-plus 等

input_dir: "input"
cache_dir: "cache"
output_dir: "output"
```

---

## 🛠️ 四大应用场景

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

### 场景四：整课程资料目录 → 一键复习/考试指南（dl 模式）

当你已经把某门课的所有资料（**视频 + syllabus + 考试说明 + 往年试卷 + 讲义 + md/txt 说明** 等）整理在一个目录里时，可以使用 **dl 模式** 一键生成两份高层级文档：

- `<课程名>_复习指南.md`：站在“怎么学完这门课、怎么安排复习”的角度。
- `<课程名>_考试指南.md`：站在“考试怎么考、怎么拿高分”的角度。

#### 目录组织方式

推荐在 `cache` 下创建 `dl` 子目录，并按课程划分子目录，例如：

```text
13course_digest/
  cache/
    dl/
      AI6131/
        lecture1.mp4
        lecture2.mp4
        syllabus.pdf
        exam_info.pdf
        past_exams.pdf
        notes.md
        ...
      MATH101/
        ...
```

你只需要保证**同一门课的所有资料**都放在同一个子目录（如 `cache/dl/AI6131/`）下即可，可以继续按你习惯再分小文件夹。

#### 一键生成命令

在 `13course_digest` 目录下运行：

```bash
python dl_generate.py cache/dl/AI6131
```

或使用绝对路径：

```bash
python dl_generate.py E:/integrity/13course_digest/cache/dl/AI6131
```

脚本会自动完成：

1. **扫描并分类文件**：区分视频、PDF/PPTX、md/txt 等。
2. **本地提取预览**：
   - 视频：用 `faster-whisper` 生成前若干段转写（走 `cache` 缓存）。
   - PDF/PPTX：用 `extract.py` 提取前几页内容。
   - md/txt：读取前若干行。
3. **调用 LLM 自动判定每个文件的角色**：
   - 课程说明/教学大纲（`course_overview`）
   - 课程要求/学习目标（`course_requirements`）
   - 考试说明/成绩构成/题型（`exam_requirements`）
   - 讲义 / PPT（`lecture_slides`）
   - 往年试卷/题库（`past_exams`）
   - 参考资料/论文（`reference`）
4. **汇总为课程级上下文**，提炼出：
   - 课程简介与学习目标
   - 考试政策与考试范围
   - 主要授课内容与参考资料
5. **再次调用 LLM 输出两份 Markdown 文档**：
   - `output/<课程名>_复习指南.md`
   - `output/<课程名>_考试指南.md`

你只管把资料往 `cache/dl/<课程名>/` 丢，然后执行一条命令即可拿到全局视角的复习/考试指导。

---

## 📋 常用命令速查

| 场景 | 命令 | 说明 |
| --- | --- | --- |
| 单节课：视频 + PPT | `python main.py "lecture1.mp4" --ppt "slides.pdf" --exams "past_exams.pdf"` | 生成 `output/<视频名>_学习指南.md` |
| CV 课程突击 | `python process_cv_exam.py` | 扫描 `cache/ACV/*.pdf`，生成 `CV_Final_Exam_Prep.md` |
| 智能匹配视频和 PDF | `python auto_match.py` | 自动匹配并生成批处理脚本 |
| 整课程资料目录 → 复习/考试指南 | `python dl_generate.py cache/dl/<课程名>` | 生成 `<课程名>_复习指南.md` 与 `<课程名>_考试指南.md` |

---

## 📁 项目结构（13course_digest）

```text
13course_digest/
├── main.py              # 单节课：视频 + 课件 → 学习指南
├── analyze.py           # LLM 调用与分块分析核心
├── transcribe.py        # 本地 Whisper 转录引擎（带缓存）
├── extract.py           # PDF / PPTX 文本提取
├── prompts.py           # 所有 Prompt 模板（含 dl / CV 等）
├── config.py            # 配置读取（config.yaml 包装）
├── config.yaml          # 路径与 API Key 配置
├── requirements.txt     # Python 依赖
│
├── process_cv_exam.py   # ⭐ CV 专项：多 PDF → 考前强化大纲 + 题库
├── auto_match.py        # 智能匹配视频 ↔ PDF，并生成批处理脚本
├── preview.py           # 快速预览 PDF/视频转写片段
├── compress_pdf.py      # PDF 压缩工具
├── compress_video.py    # 视频压缩工具（转码/降分辨率）
│
├── dl_course.py         # dl 模式：课程目录扫描与静态分类
├── dl_preview.py        # dl 模式：为各类文件生成预览文本
├── dl_course_context.py # dl 模式：LLM 角色识别 + 课程级上下文
├── dl_generate.py       # dl 模式：一键生成复习指南 + 考试指南
│
├── input/               # 推荐放原始视频的目录
├── cache/               # 各类缓存与课程资料
│   ├── ACV/             # CV 专项资料所在目录
│   └── dl/              # 按课程划分的资料目录（dl 模式专用）
└── output/              # 所有生成的 Markdown / HTML 结果
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
