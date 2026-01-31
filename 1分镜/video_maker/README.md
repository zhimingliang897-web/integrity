# 分镜视频生成器

## GPT 提示词（生成对话内容 + 插图）

### 提示词 1：生成对话文本

```
你是一个英语口语教学内容设计师。请为我创作一段英语日常对话，要求如下：

【场景】<在这里描述具体场景，如：两个年轻人在公交车上，一个问另一个在哪站下车>
【时长】对话控制在 30-60 秒内朗读完
【难度】雅思口语 5-6 分水平（日常交流，自然但不过于俚语化）

写作要求：
1. 对话必须自然真实，像真人日常交流，不要书面化或教材腔
2. 每段对话包含 3-5 个实用表达/句型，这些表达要有通用性（换个场景也能用）
3. 角色用编号标记：M1 M2（男）/ F1 F2（女），冒号后面直接跟台词
4. 每句台词后用 | 分隔附上中文翻译，如：M1: What stop? | 哪一站？
5. 不要加括号动作描述，不要加 Scene/Setting 等说明文字
6. 用 --- 分隔场景（我会用四宫格插图，所以分成 4 个场景）
7. 对话结尾自然收束，不要强行升华
8. 第一行写场景标题（英文），如：On a bus — asking for directions

对话结束后，用 === 分隔，列出核心表达（每行格式：短语 — 中文释义 — 例句）
```

### 提示词 2：生成四宫格插图

```
根据以下对话内容，帮我生成一张四宫格插图（2×2排列）。

要求：
- 漫画/插画风格，色彩明快，人物表情生动
- 不要在图上标注任何文字（后期会加字幕）
- 每格对应一个场景片段，画面要能看出在做什么
- 人物造型在四格之间保持一致
- 风格参考：新概念英语课本插图，或日式轻漫画

对话内容：
<粘贴对话文本>
```

---

## Claude 提示词（处理素材 + 生成视频）

```
我在 video_maker/<文件夹名>/input/ 里放了新的图片和文本。
请帮我：
1. 读取文本，根据图片格数加上 --- 场景分隔
2. 把文本改成 M1/F1 格式并保存回 文本.txt
3. 然后帮我运行 python make_video.py <文件夹名>
```

---

## 你每次要做的事

```
第 1 步：用 GPT 提示词 1 生成对话文本
第 2 步：用 GPT 提示词 2 生成四宫格插图
第 3 步：在 video_maker/ 下新建项目文件夹（如 5咖啡店点单/）
第 4 步：把文本和图片放进 项目文件夹/input/
第 5 步：把 Claude 提示词发给 Claude，等视频生成完毕
第 6 步：去 项目文件夹/output/ 拿视频
```

---

## 项目文件夹结构

```
video_maker/
├── make_video.py           ← 脚本（不用改）
├── README.md               ← 本文档
│
├── 3地铁搭讪/
│   ├── input/
│   │   ├── 图片.png
│   │   └── 文本.txt
│   └── output/
│       ├── 3地铁搭讪.mp4    ← 成品视频
│       ├── audio_clips/
│       ├── subtitles.srt
│       └── ...
│
├── 4哪站下车/
│   ├── input/
│   └── output/
│
└── ...更多项目/
```

---

## 文本格式规范

```
On a bus — asking for directions
---
M1: Hey, what stop are you getting off at? | 嘿，你在哪站下车？
M2: Maple Street. Why? | 枫叶街，怎么了？
---
M1: I always miss my stop when I'm on my phone. | 我看手机的时候总是坐过站。
M2: Same here. The algorithm wins every time. | 我也是，算法每次都赢。
===
get off at — 在…下车 — I get off at the next stop.
miss my stop — 坐过站 — I almost missed my stop again.
```

- 第一行 = 场景标题（视频开头显示 3 秒）
- `M1` `M2` = 男性角色，`F1` `F2` = 女性角色
- `|` = 英中双语分隔（英文在前，中文在后）
- `---` = 场景分隔（对应图片网格的一格）
- `===` = 核心表达分隔（之后的内容生成片尾卡片）
- 核心表达格式：`短语 — 中文释义 — 例句`
- 不需要括号动作描述，代码会自动去除
- 其他非台词行会被自动忽略

---

## 声音池（自动分配）

| 编号 | 男声 | 女声 |
|------|------|------|
| 1 | en-US-GuyNeural | en-US-JennyNeural |
| 2 | en-US-ChristopherNeural | en-US-AriaNeural |
| 3 | en-US-EricNeural | en-US-MichelleNeural |
| 4 | en-US-AndrewNeural | en-US-AnaNeural |

---

## 运行方式

### 方式 1：全自动（API 生成文本 + 图片 + 生成视频）

```bash
# 第 1 步：自动生成对话文本 + 四宫格插图
python gen_text.py 6买咖啡 "在咖啡店点单，一个男生第一次去星巴克不知道怎么点"
# → 6买咖啡/input/文本.txt（通义千问生成）
# → 6买咖啡/input/图片.png（通义万相生成，不满意可手动替换）

# 第 2 步：生成视频
python make_video.py 6买咖啡
```

### 方式 2：手动（自己写文本 + 生成视频）

```bash
python make_video.py <项目文件夹名>
# 例如：
python make_video.py 3地铁搭讪
```

---

## 依赖

```bash
pip install pillow edge-tts openai
```

另需安装 [FFmpeg](https://ffmpeg.org/download.html)。

---

## 环境变量

使用 `gen_text.py` 前需设置通义千问 API 密钥：

```bash
# Windows
set DASHSCOPE_API_KEY=你的API密钥

# Mac/Linux
export DASHSCOPE_API_KEY=你的API密钥
```

API 密钥从 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/) 获取。
