# 分镜视频生成器

## 一句话总结

**大语言模型负责"理解"（写 config.json），脚本负责"执行"（一键出片）。**

---

## 你每次要做的事

```
你提供：图片 + 文本
        │
        ▼
大语言模型帮你写 config.json（哪句话配哪张图）
        │
        ▼
运行：python make_video.py
        │
        ▼
得到：最终视频.mp4
```

**脚本永远不用改，只改 config.json。**

---

## config.json 怎么写

```json
{
    "voice": "en-US-GuyNeural",        // TTS 声音
    "gap": 0.3,                         // 每句间隔（秒）
    "output": "最终视频.mp4",            // 输出文件名

    "source_image": "四格图.png",       // 可选：需要切割的原图
    "grid": [2, 2],                     // 可选：切割方式（行, 列）

    "scenes": [
        {
            "image": "scene_1.png",     // 这个场景用哪张图
            "lines": [                  // 这个场景说哪些话
                "第一句台词",
                "第二句台词"
            ]
        },
        {
            "image": "scene_2.png",
            "lines": ["第三句", "第四句"]
        }
    ]
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `voice` | 是 | TTS 声音，见下方声音列表 |
| `gap` | 是 | 每句话之间的静音间隔（秒） |
| `output` | 是 | 输出视频文件名 |
| `source_image` | 否 | 如果是多格图，填原图文件名，脚本自动切割 |
| `grid` | 否 | 切割方式 `[行数, 列数]`，配合 source_image 使用 |
| `scenes` | 是 | 场景列表，每个场景 = 图片 + 台词数组 |

**两种图片模式：**
- **有 source_image + grid**：脚本自动切图，scene 里的 image 是切出来的文件名
- **没有 source_image**：你自己准备好单张图片，scene 里的 image 指向已有文件

---

## 核心问题

### Q1: 怎么知道每张图片显示多久？

**不是预设的，是测出来的。**

```
台词文本 → TTS → MP3 文件 → ffprobe 测量实际时长 → 决定图片显示多久
                                    ↑
                               这步是关键
```

场景时长 = 该场景所有台词的语音时长 + 间隔之和。

### Q2: 怎么知道哪句话配哪张图？

**大语言模型（或你手动）写在 config.json 的 scenes 里。**

这需要「看懂图片 + 理解文本」的能力，所以交给 AI 做。

### Q3: 为什么不会声音重叠？

音频是按顺序拼接的（每句后面插入 0.3 秒静音），不是同时播放。

---

## 脚本内部流程

```
config.json
    │
    ▼
步骤 0: 读取配置
步骤 1: 切割图片（如果配置了 source_image）
步骤 2: 生成语音（Edge TTS）→ 每句一个 MP3
步骤 3: 测量时长（ffprobe）→ 计算每个场景显示多久
步骤 4: 生成字幕（SRT）→ 时间与语音对齐
步骤 5: 拼接音频（FFmpeg）→ 顺序播放不重叠
步骤 6: 合成视频（FFmpeg）
        ├─ 6a: 图片 → 无声视频
        ├─ 6b: 合并音频
        └─ 6c: 烧录字幕
    │
    ▼
最终视频.mp4
```

---

## 可用声音

| 声音 ID | 描述 |
|---------|------|
| `en-US-GuyNeural` | 美式英语男声 |
| `en-US-JennyNeural` | 美式英语女声 |
| `en-GB-RyanNeural` | 英式英语男声 |
| `zh-CN-XiaoxiaoNeural` | 中文女声 |
| `zh-CN-YunxiNeural` | 中文男声 |

---

## 运行方式

```bash
# 默认读取同目录下的 config.json
python make_video.py

# 指定配置文件路径
python make_video.py path/to/config.json
```

---

## 依赖

```bash
pip install pillow edge-tts
```

另需安装 [FFmpeg](https://ffmpeg.org/download.html)。

---

## 文件结构

```
分镜目录/
├── config.json          ← 大语言模型帮你写的配置（唯一需要改的文件）
├── make_video.py        ← 脚本（永远不用改）
├── 原始图片.png          ← 你的素材
├── scene_1~N.png        ← 自动切割的图片
├── audio_clips/         ← 自动生成的语音
├── subtitles.srt        ← 自动生成的字幕
├── voiceover.mp3        ← 自动生成的配音
└── 最终视频.mp4          ← 输出成品
```
