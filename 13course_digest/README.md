# CourseDigest: 智能课程复习助手

> 一键将课程视频与 PDF 资料转化为复习指南和考试指南

---

## 快速开始

```bash
# 一键全流程（推荐）
python cli.py all cache/dl/6103

# 分步执行
python cli.py transcribe cache/dl/6103  # 只转写视频
python cli.py generate cache/dl/6103    # 只生成指南

# 其他命令
python cli.py preview cache/dl/6103     # 预览资料
python cli.py match cache/dl/6103       # 智能匹配
```

**输出**：`output/<课程名>_复习指南.md` + `output/<课程名>_考试指南.md`

---

## 目录结构

```
cache/dl/<课程名>/
├── lecture1.mp4        # 视频（可选）
├── lecture2.mp4
├── syllabus.pdf        # 教学大纲
├── exam_info.pdf       # 考试说明
├── past_exams.pdf      # 往年试卷
├── slides.pdf          # 讲义 PPT
└── notes.md            # 笔记（可选）
```

---

## 安装

```bash
conda create -n coursedigest python=3.11 -y
conda activate coursedigest
pip install -r requirements.txt

# GPU 加速（可选）
conda install -n coursedigest -c nvidia libcublas=12.9 -y
```

---

## 配置

编辑 `config.yaml`：

```yaml
api:
  provider: "dashscope"
  api_key: "sk-your-key"
  model: "glm-5"

whisper:
  model: "medium"
  device: "cuda"
  language: "en"
```

---

## 命令说明

| 命令 | 说明 |
|------|------|
| `transcribe <目录>` | 视频转文字（写入缓存） |
| `generate <目录>` | 生成复习/考试指南 |
| `all <目录>` | 一键全流程 |
| `preview <目录>` | 预览资料内容 |
| `match <目录>` | 智能匹配视频和 PDF |

---

## 功能特点

- 本地 Whisper 转写，免费且隐私安全
- 自动检测学科类型（AI/数学/统计），针对性生成建议
- 支持 MP4/PDF/PPTX/MD/TXT 等格式
- 转写结果自动缓存，避免重复处理

---

## 项目结构

```
13course_digest/
├── cli.py              # 统一入口
├── config.yaml         # 配置文件
├── prompts.py          # Prompt 模板
├── transcribe.py       # 视频转文字
├── extract.py          # 文档提取
├── analyze.py          # LLM 调用
├── dl_*.py             # 核心流程
├── auto_match.py       # 智能匹配
├── cache/              # 课程资料
└── output/             # 输出结果
```

---

## 常见问题

**Q: 转写很慢？**
设置 `whisper.device: "cuda"` 启用 GPU 加速

**Q: 只有 PDF 没有视频？**
直接运行 `python cli.py generate <目录>`

**Q: 支持哪些 API？**
阿里百炼（DashScope）和 Groq