## BY Liang

- **v1** (1.30) — 从 PDF 中提取字母，利用大模型整理出正确单词；使用网页接口访问台词查询网站返回结果；使用大模型把返回的杂乱台词整理
- **v2** (1.31) — 新增了网页，解决了阅读起来费劲的问题，把 API 设置隐藏了，每次得自己 set 一下 API 保证隐私，在网页端拖拽即可添加新的单词天
- **v3** (2.05) — 双击启动、网页设置 API Key、音标显示、TTS 语音朗读

---

## By Claude

# 台词学习工具

从 PDF 提取单词 -> 查询影视台词 -> 整理成学习材料 -> 生成语音 -> 网页美化展示。

## 文件结构

```
2台词\
├── app.py                   # Web 界面（Flask）
├── pdf_extractor.py         # 步骤1: PDF 提取单词
├── pop_mystic_scraper.py    # 步骤2: 查询影视台词
├── quote_formatter.py       # 步骤3: LLM 整理学习笔记
├── tts_generator.py         # 步骤4: edge-tts 生成语音
├── 启动.bat                 # 双击启动（自动开浏览器）
├── templates/
│   └── index.html           # 前端页面
├── config.json              # [自动生成] API Key 等配置（已 gitignore）
└── word/
    ├── day1/
    │   ├── day1.pdf         # [你放的] PDF 原件
    │   ├── day1.txt         # [自动生成] 提取的单词
    │   ├── day1.json        # [自动生成] 台词原始数据
    │   ├── day1.csv         # [自动生成] 台词表格
    │   ├── day1_study.md    # [自动生成] 学习笔记
    │   └── audio/           # [自动生成] TTS 语音文件
    │       ├── w_0.mp3      # 单词发音
    │       ├── d_0_0_0.mp3  # 台词朗读
    │       └── ...
    ├── day2/
    └── ...
```

## 依赖安装

```bat
pip install requests beautifulsoup4 pdfplumber flask edge-tts
```

## 运行方式

### 方式一：双击启动（推荐）

1. 双击 `启动.bat`，浏览器自动打开
2. 首次使用点右上角齿轮设置 API Key（自动保存，以后不用再设）
3. 拖拽 PDF 上传，等待处理完成即可学习

### 方式二：命令行

```bat
set DASHSCOPE_API_KEY=你的API密钥
python app.py
```

浏览器打开 `http://localhost:5000`。

### 方式三：命令行逐步执行

```bat
set DASHSCOPE_API_KEY=你的API密钥

python pdf_extractor.py        & :: 步骤1: PDF -> 单词
python pop_mystic_scraper.py   & :: 步骤2: 单词 -> 台词
python quote_formatter.py      & :: 步骤3: 台词 -> 学习笔记
python tts_generator.py word/day1/day1_study.md  & :: 步骤4: 生成语音
```

所有脚本都有跳过机制：已生成的文件不会重复处理。

## 功能特性

- 音标显示（Free Dictionary API）
- 单词真人发音 + 台词 TTS 朗读（edge-tts 预生成 mp3）
- 网页端设置 API Key（保存到本地 config.json，不上传 GitHub）
- 拖拽上传 PDF，自动完成全部处理流水线
- 处理进度实时显示（extracting → scraping → formatting → tts → done）
