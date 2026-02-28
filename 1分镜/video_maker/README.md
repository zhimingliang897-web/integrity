# 分镜视频生成器

自动生成英语口语学习短视频：AI 剧本 → 分镜插图 → 配音 → 字幕 → 学习海报，一键出片。

---

## 两种方案对比

| 特性 | 多图方案 (multi) | 四宫格方案 (grid) |
|------|-----------------|------------------|
| **脚本** | `gen_text.py` + `make_video.py` | `gen_text.py` + `make_video.py` |
| **图片策略** | 每个场景单独生成 1 张图 | 一张四格图，自动裁切 |
| **场景数量** | 动态 4-6 个 | 固定 4 个 |
| **视频版本** | 正常速度 | 正常 + 慢速（-30%） |
| **风格一致性** | 依赖 AI 理解 | 同一画面天然一致 |
| **适用场景** | 场景变化大、需要多样视觉 | 强调连贯叙事 |

---

## 快速开始

### 安装依赖

```bash
pip install pillow edge-tts openai
# 另需安装 FFmpeg：https://ffmpeg.org/download.html
```

### 启动 GUI

```bash
python app.py
```

或直接双击 **`启动GUI.bat`**

---

## 使用方式

### 方式一：多图方案 (multi)

每个场景单独生成一张图片，灵活多变。

```bash
# 步骤 1：生成剧本 + 分镜图片
python multi/gen_text.py <项目名> <场景描述>

# 例：
python multi/gen_text.py 8超市 "在超市买水果，和店员讨价还价"

# 步骤 2：合成视频
python multi/make_video.py 8超市
```

### 方式二：四宫格方案 (grid)

一张四格漫画图，视觉风格统一。

```bash
# 步骤 1：生成剧本 + 四宫格图片
python grid/gen_text.py <项目名> <场景描述>

# 例：
python grid/gen_text.py 8超市 "在超市买水果"

# 步骤 2：合成视频
python grid/make_video.py 8超市
```

---

## 项目结构

```
video_maker/
├── app.py                   ← GUI 主界面
├── 启动GUI.bat              ← Windows 一键启动
├── requirements.txt         ← Python 依赖
├── settings.json            ← 配置文件（含 API Key）
├── README.md                ← 本文档
│
├── multi/                   ← 多图方案
│   ├── gen_text.py         ← 生成剧本 + 分镜图
│   ├── make_video.py       ← 合成视频
│   ├── 1药店/              ← 示例项目
│   │   ├── input/
│   │   │   ├── 文本.txt
│   │   │   ├── 1.png
│   │   │   ├── 2.png
│   │   │   └── ...
│   │   └── output/
│   │       └── output.mp4
│   │
│   └── 2开车/
│       └── ...
│
└── grid/                    ← 四宫格方案
    ├── gen_text.py         ← 生成剧本 + 四格图
    ├── make_video.py       ← 合成视频
    ├── 1药店/
    │   ├── input/
    │   │   ├── 文本.txt
    │   │   └── 图片.png    ← 四宫格原图
    │   └── output/
    │       ├── output.mp4
    │       └── output_slow.mp4
    │
    └── 2开车/
        └── ...
```

---

## 输出文件格式

### 多图方案 (multi)

```
项目文件夹/
├── input/
│   ├── 文本.txt         ← AI 生成的剧本（可手动编辑）
│   ├── 1.png            ← 第 1 个分镜图
│   ├── 2.png            ← 第 2 个分镜图
│   └── ...
└── output/
    └── 项目名.mp4       ← 视频文件
```

### 四宫格方案 (grid)

```
项目文件夹/
├── input/
│   ├── 文本.txt         ← AI 生成的剧本
│   └── 图片.png         ← 四宫格原图
└── output/
    ├── 项目名.mp4        ← 正常速度视频
    └── 项目名_slow.mp4  ← 慢速版（语速 -30%）
```

---

## 环境配置

### API Key

**获取地址**：https://dashscope.console.aliyun.com/

**配置方式（选一种）**：

1. **GUI 配置页填写**（推荐，保存在 `settings.json`）

2. **环境变量**
   ```bash
   # Windows CMD
   set DASHSCOPE_API_KEY=你的密钥
   
   # PowerShell
   $env:DASHSCOPE_API_KEY="你的密钥"
   
   # macOS/Linux
   export DASHSCOPE_API_KEY=你的密钥
   ```

3. **直接在 settings.json 编辑**
   ```json
   {
     "api_key": "sk-xxxxx",
     "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
     "text_model": "qwen-plus-2025-12-01",
     "image_model": "qwen-image-max"
   }
   ```

### 可配置项

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| API Key | `DASHSCOPE_API_KEY` | — | 必需 |
| Base URL | `DASHSCOPE_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 通常不用改 |
| 文本模型 | `DASHSCOPE_TEXT_MODEL` | `qwen-plus-2025-12-01` | 用于生成剧本 |
| 图片模型 | `DASHSCOPE_IMAGE_MODEL` | `qwen-image-max` | 用于生成图片 |

### 推荐模型组合

| 用途 | 文本模型 | 图片模型 |
|------|----------|----------|
| 平衡方案 | `qwen-plus-2025-12-01` | `qwen-image-max` |
| 性价比 | `qwen-plus` | `wanx2.1-t2i-turbo` |
| 快速测试 | `qwen-turbo` | `wanx2.1-t2i-turbo` |

---

## 文本格式规范

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
===
Panel 1: 男生走进咖啡店，拿起菜单，表情茫然
Panel 2: 男生指着菜单问，店员微笑回答
Panel 3: 男生尴尬地看着价格
Panel 4: 男生付完钱，拿到咖啡，开心离开
```

| 符号 | 含义 |
|------|------|
| 第一行 | 标题（英文 — 中文，视频开头显示 1.5 秒） |
| `M1/M2` | 男声角色 |
| `F1/F2` | 女声角色 |
| `\|` | 英文台词与中文翻译的分隔符 |
| `---` | 场景（Scene）分隔 |
| `===`...`===` | 核心表达区域（生成学习海报用） |
| `Panel N:` | 分镜画面描述（用于图片生成） |

---

## 声音列表

| 标记 | 男声 | 标记 | 女声 |
|------|------|------|------|
| M1 | en-US-GuyNeural | F1 | en-US-JennyNeural |
| M2 | en-US-ChristopherNeural | F2 | en-US-AriaNeural |

---

## 注意事项

1. **API Key 安全**：`settings.json` 包含 API Key，已加入 `.gitignore`，请勿提交到公开仓库

2. **生成时间**：每张图片约需 30-60 秒（受 API 限速影响）

3. **手动编辑**：生成剧本后可手动修改 `文本.txt`，重新运行 `make_video.py` 即可应用更改

4. **无需 dashscope 包**：代码使用 `urllib` 直接调用 API，只需安装 `openai` 即可

---

## 常见问题

### Q: 两种方案该选哪个？

- **多图方案**：场景变化大、需要丰富视觉表现
- **四宫格方案**：强调叙事连贯性、风格统一

### Q: 图片生成失败怎么办？

1. 检查 API Key 是否正确
2. 检查网络连接
3. 尝试更换图片模型
4. 使用 `--no-image` 参数只生成剧本，手动准备图片

### Q: 如何只生成剧本不生成图片？

```bash
python multi/gen_text.py 项目名 "场景描述" --no-image
```
