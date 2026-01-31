# 药店对话视频制作

## 文件说明

| 文件 | 说明 |
|------|------|
| 1.png - 5.png | 5张分镜图片 |
| subtitle.srt | 字幕文件 |
| images.txt | 图片时长配置 |

## 生成视频

打开命令行，进入此文件夹：

```bash
cd "e:\分镜\1药店"
```

运行 ffmpeg：

```bash
ffmpeg -f concat -i images.txt -vf "subtitles=subtitle.srt:force_style='FontSize=24'" -c:v libx264 -pix_fmt yuv420p output.mp4
```

生成的视频为 `output.mp4`，总时长约 41 秒。

## 调整字幕样式

如需修改字幕样式，修改 `force_style` 参数：

```bash
# 更大字体 + 黄色
ffmpeg -f concat -i images.txt -vf "subtitles=subtitle.srt:force_style='FontSize=28,PrimaryColour=&H00FFFF&'" -c:v libx264 -pix_fmt yuv420p output.mp4
```

## 添加音频（可选）

如果有配音文件 `audio.mp3`：

```bash
ffmpeg -f concat -i images.txt -i audio.mp3 -vf "subtitles=subtitle.srt:force_style='FontSize=24'" -c:v libx264 -c:a aac -shortest -pix_fmt yuv420p output.mp4
```
