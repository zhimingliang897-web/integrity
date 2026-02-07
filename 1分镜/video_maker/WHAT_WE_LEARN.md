# What We Learn - 技术心得

## 1. 中文路径与 FFmpeg

Windows 下 FFmpeg 的 `-i` 参数和 concat 文件中遇到中文路径会乱码/报错。

**解法**：concat 文件中只写 `file 'filename.ext'`（basename），因为 concat 列表的文件路径是相对于列表文件所在目录解析的。只要列表和素材在同一个目录，就不需要绝对路径。

```python
# 正确：只写文件名
f.write(f"file '{os.path.basename(img_path)}'\n")

# 错误：写绝对路径（中文会炸）
f.write(f"file '{img_path}'\n")
```

SRT 字幕路径则需要 `\\:` 转义冒号：
```python
escaped = srt_path.replace("\\", "/").replace(":", "\\:")
```

## 2. subprocess 的 GBK 陷阱

Windows 下 `subprocess.run(text=True)` 默认用系统编码（GBK）解码 stdout/stderr，遇到非 GBK 字符直接崩溃。

**解法**：永远用 `text=False`（bytes 模式），手动解码：
```python
result = subprocess.run(args, capture_output=True, text=False)
output = result.stdout.decode("utf-8", errors="ignore")
```

## 3. 中英文混合换行

中文没有空格分词，按空格拆分会把整段中文当成一个"词"。纯字符拆分又会把英文单词从中间切断。

**解法**：混合策略 — 遇到 ASCII 字母时收集完整单词，遇到中文字符逐字测量：
```python
if ch.isascii() and ch.isalpha():
    # 收集完整英文单词
    word = ""
    while i < len(text) and text[i].isascii() and not text[i].isspace():
        word += text[i]; i += 1
else:
    # 中文字符逐个处理
    test = current + ch; i += 1
```

## 4. 四宫格图片的两个坑

### 坑 1：AI 生成"一张全景被切割"而非"四个独立场景"

给 AI 模型说 "2x2 grid" 时，模型有时理解为"画一张大图然后加两条线分割"。

**解法**：prompt 中强调 "COMIC STRIP"、"4 SEPARATE panels"、"each panel is its own INDEPENDENT scene"，并明确写 "Do NOT draw one single panoramic scene and split it with lines"。

### 坑 2：切割后白边不均匀

四宫格中间的白色分割线宽度不固定，简单的均分切割会把白线残留切进图片里。

**解法**（两种思路）：

- **分割线检测法**（`make_video_pre.py`）：逐像素扫描中间 35%-65% 区域，找到白色占比最高的列/行作为分割线中心，估算线宽，然后按线宽内缩切割。
- **暴力剥边法**（`_strip_solid_border`）：切完后逐像素检查四边，如果边缘像素 97%+ 是背景色就剥掉一行。最多迭代 4000 次。

最终用 **cover 模式**缩放（`max` 而非 `min`）+ 居中裁切铺满画布，彻底消灭白边。

## 5. 视频编码：单次 vs 多次

早期流程：图片→无声视频(有损) → 加音频(再编码) → 烧字幕(第三次编码)。每次编码都损失画质。

**解法**：中间步骤用 CRF 0（无损），最终合并音视频+字幕一步完成：
```
ffmpeg -i 无声.mp4(CRF0) -i 音频.mp3
       -vf "subtitles=..."
       -crf 18 -preset slow -movflags +faststart
       output.mp4
```

`-movflags +faststart` 把 moov atom 移到文件头，社交媒体可以边下边播。

## 6. 海报设计迭代

经历了三版设计：

| 版本 | 问题 |
|------|------|
| v1 白底圆点列表 | 太简陋，没有品牌感 |
| v2 暖棕底+竖条+分割线 | 配色太杂（8种颜色），竖条太细看不见，字号层级不对 |
| v3 卡片式 | 每条一个圆角卡片，配色三档+一个强调色，干净清晰 |

**心得**：
- 颜色不超过 4 种（深/中/浅 + 强调色），多了就乱
- 用"卡片"自然分区比"分割线"好看得多
- `rounded_rectangle` 在低版本 Pillow 不支持，需要 `hasattr` 兜底

## 7. Edge TTS 的声音分配

Edge TTS 免费但不稳定，偶尔超时。声音池设计要点：
- 按 `M1→男声池[0]`, `M2→男声池[1]` 自动分配，不需要手动配置
- 男女各 4 个声音足够覆盖绝大多数对话场景
- 用 `rate="-30%"` 实现慢速版，不需要额外 API 调用

## 8. 提示词工程

### 对话提示词
- "地道日常口语" 比 "雅思5-6分" 效果好 — 后者产出书面化表达
- 限制台词数量（"不超过12句"）比限制秒数更可控
- 角色名必须强制 `M1/F1` 格式，否则模型会用 Waiter/Barista 等词导致解析失败
- 要求 "宁短勿长"，否则 AI 倾向生成冗长对话

### 图片提示词
- "COMIC STRIP" 比 "grid" 更能引导模型画出独立场景
- 必须明确写 "NO text" — 否则模型会在图中画文字/气泡
- 强调"same characters with consistent appearance"保持人物一致性
- 风格参考用具体的 "New Concept English textbook" 比抽象的 "教材风格" 效果好
