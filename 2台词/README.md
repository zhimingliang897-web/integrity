## BY Liang

- **v1** (1.30) — 从 PDF 中提取字母，利用大模型整理出正确单词；使用网页接口访问台词查询网站返回结果；使用大模型把返回的杂乱台词整理
- **v2** (1.31) — 新增了网页，解决了阅读起来费劲的问题，把 API 设置隐藏了，每次得自己 set 一下 API 保证隐私，在网页端拖拽即可添加新的单词天

---

## By Claude

# 台词学习工具

从 PDF 提取单词 -> 查询影视台词 -> 整理成学习材料 -> 网页美化展示。

## 文件结构

```
2台词\
├── app.py                   # Web 界面（Flask）
├── pdf_extractor.py         # 步骤1: PDF 提取单词
├── pop_mystic_scraper.py    # 步骤2: 查询影视台词
├── quote_formatter.py       # 步骤3: LLM 整理学习笔记
├── templates/
│   └── index.html           # 前端页面
└── word/
    ├── day1/
    │   ├── day1.pdf         # [你放的] PDF 原件
    │   ├── day1.txt         # [自动生成] 提取的单词
    │   ├── day1.json        # [自动生成] 台词原始数据
    │   ├── day1.csv         # [自动生成] 台词表格
    │   └── day1_study.md    # [自动生成] 学习笔记
    ├── day2/
    └── ...
```

## 依赖安装

```bat
pip install requests beautifulsoup4 pdfplumber flask
```

## 运行方式

### 方式一：Web 界面（推荐）

```bat
set DASHSCOPE_API_KEY=你的API密钥
python app.py
```

浏览器打开 `http://localhost:5000`：
- 首页展示所有 Day 卡片，点击进入学习页
- 拖拽 PDF 到上传区，指定 Day 编号，自动完成全部处理

### 方式二：命令行

```bat
set DASHSCOPE_API_KEY=你的API密钥

python pdf_extractor.py        & :: 步骤1: PDF -> 单词
python pop_mystic_scraper.py   & :: 步骤2: 单词 -> 台词
python quote_formatter.py      & :: 步骤3: 台词 -> 学习笔记
```

三个脚本都有跳过机制：已经生成过的文件不会重复处理，可以放心每次三个一起跑。

命令行方式需要手动创建文件夹并放入 PDF：

```bat
mkdir word\day3
:: 把 day3.pdf 复制到 word\day3\ 里
```
