# 分镜视频生成器

一键生成英语口语学习短视频 + 学习海报，用于社交媒体发布。

## 两套方案

| | 多图方案 | 四宫格方案 |
|---|---|---|
| 脚本 | `gen_text.py` + `make_video.py` | `gen_text_pre.py` + `make_video_pre.py` |
| 图片策略 | 每个场景单独生成一张图 | 一张四宫格合成图，代码切割 |
| 场景数量 | 动态 4-6 个 | 固定 4 个 |
| 视频版本 | 正常速度 | 正常 + 慢速 |
| 风格一致性 | 靠 AI 自觉 | 同画面内天然统一 |

---

## 快速使用

### 方案一：多图方案

```bash
# 1. 生成文本 + 多张分镜图片
python gen_text.py 8超市 "在超市买水果"

# 2. 生成视频 + 海报
python make_video.py 8超市
```

### 方案二：四宫格方案

```bash
# 1. 生成文本（含 Panel 分镜脚本）+ 四宫格合成图
python gen_text_pre.py 8超市 "在超市买水果"

# 2. 生成视频（正常 + 慢速）+ 海报
python make_video_pre.py 8超市
```

---

## 输出

```
项目文件夹/output/
├── 项目名.mp4          ← 正常速度视频
├── 项目名_slow.mp4     ← 慢速版（仅四宫格方案）
├── poster.png          ← 学习海报（发评论区）
├── subtitles.srt       ← 字幕文件
└── audio_clips/        ← 语音片段
```

---

## 项目文件夹结构

```
video_maker/
├── gen_text.py             ← 多图方案：文本 + 图片生成
├── gen_text_pre.py         ← 四宫格方案：文本 + 图片生成
├── make_video.py           ← 多图方案：视频合成
├── make_video_pre.py       ← 四宫格方案：视频合成
├── CHANGELOG.md
├── README.md
├── WHAT_WE_LEARN.md
│
├── 3地铁搭讪/
│   ├── input/
│   │   ├── 图片.png        ← 四宫格合成图（四宫格方案）
│   │   ├── 1.png ~ 4.png   ← 独立分镜图（多图方案）
│   │   └── 文本.txt
│   └── output/
│       ├── 3地铁搭讪.mp4
│       ├── poster.png
│       └── ...
└── ...
```

---

## 文本格式

```
Ordering Coffee — 咖啡店点单
---
M1: Hey, could I get a medium latte? | 嘿，能来一杯中杯拿铁吗？
F1: Sure! For here or to go? | 好的！堂食还是外带？
---
M1: To go, please. | 外带，谢谢。
F1: That'll be $4.50. | 一共4.5美元。
===
could I get... — 能来一个…（点单用语） — Could I get a black coffee?
for here or to go — 堂食还是外带 — For here or to go?
```

- 第一行 = 标题（`English — 中文`，视频开头显示 1.5 秒）
- `M1/M2` = 男声，`F1/F2` = 女声
- `|` = 英中双语分隔
- `---` = 场景分隔
- `===` = 核心表达分隔（之后内容生成海报）
- 核心表达格式：`短语 — 中文释义 — 例句`

---

## 依赖

```bash
pip install pillow edge-tts openai
```

另需安装 [FFmpeg](https://ffmpeg.org/download.html)。

---

## 环境变量

```bash
# Windows
set DASHSCOPE_API_KEY=你的API密钥

# Mac/Linux
export DASHSCOPE_API_KEY=你的API密钥
```

API 密钥从 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/) 获取。

---

## 声音池

| 编号 | 男声 | 女声 |
|------|------|------|
| 1 | en-US-GuyNeural | en-US-JennyNeural |
| 2 | en-US-ChristopherNeural | en-US-AriaNeural |
| 3 | en-US-EricNeural | en-US-MichelleNeural |
| 4 | en-US-AndrewNeural | en-US-AnaNeural |
