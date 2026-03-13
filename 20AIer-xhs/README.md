# 小红书图文生成器 v4.0

把一篇普通文章，用"毒舌但真诚"的人设，自动生成小红书风格的图文组图 + 评论区文案。

---

## 效果示例

输入一篇关于 AI 工具的文章，自动输出：
- 1 张封面图（大标题居中，视觉冲击感强）
- 4-6 张内容图（每张 4-6 个色块，毒舌解析）
- 1 个 `comments.txt`（3条实在建议 + 5个话题标签）

图片规格：1080×1440 px（小红书标准竖版）

---

## 目录结构

```
20AIer-xhs/
├── scripts/                 # Python 脚本
│   ├── main.py              # 入口，运行这个
│   ├── comments.py          # 仅生成评论区文案
│   ├── config.py            # 配置加载器
│   ├── llm_formatter.py     # LLM 调用 + Prompt
│   ├── image_generator.py   # PIL 图片渲染
│   ├── comment_generator.py # 评论区文案生成
│   └── font_detector.py     # 跨平台字体检测
├── input/                   # 放你的文章 .txt 文件
│   ├── test_article.txt
│   └── ai_lobster.txt
├── output/                  # 生成结果（自动创建）
│   └── <文章名>/
│       ├── slide_00_cover.png
│       ├── slide_01.png
│       ├── ...
│       └── comments.txt
├── config.yaml              # API 密钥、图片样式配置
├── requirements.txt         # Python 依赖
├── 毒舌skill.md             # 毒舌人设 System Prompt 文档
└── DESIGN.md                # 设计规范与 Prompt 工程笔记
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

推荐用**环境变量**配置 API Key（避免把密钥写进仓库）：

```bash
# Windows PowerShell
$env:XHS_API_KEY="sk-xxxxxxxx"

# macOS/Linux
export XHS_API_KEY="sk-xxxxxxxx"
```

你也可以创建 `config.local.yaml`（会覆盖 `config.yaml`，且已加入 `.gitignore`）：

```yaml
api:
  api_key: sk-xxxxxxxxxxxxxxxx
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  model: qwen3.5-plus
  timeout_sec: 180
```

### 3. 放入文章

把你的文章保存为 `.txt` 文件，放到 `input/` 目录：

```
input/my_article.txt
```

### 4. 运行

```bash
python scripts/main.py input/my_article.txt
```

完成后自动打开输出文件夹。

---

## 命令参数

```
python scripts/main.py <文章路径> [--no-comments] [--comments-only]
```

| 参数 | 说明 |
|------|------|
| `<文章路径>` | 必填，txt 文件路径 |
| `--no-comments` | 跳过评论区文案生成（省一次 API 调用） |
| `--comments-only` | 只生成评论区文案（不生成图片） |

示例：

```bash
# 完整生成（图片 + 评论区）
python scripts/main.py input/ai_lobster.txt

# 只生成图片
python scripts/main.py input/ai_lobster.txt --no-comments

# 只生成评论（不生成图片）
python scripts/main.py input/ai_lobster.txt --comments-only

# 单独生成评论（脚本模式）
python scripts/comments.py input/ai_lobster.txt
```

---

## 配置说明

`config.yaml` 主要参数：

```yaml
api:
  api_key:   # 阿里云百炼 API Key
  model:     # 默认 qwen3.5-plus，可换其他兼容模型

style:
  img_width:       1080   # 图片宽度（px）
  img_height:      1440   # 图片高度（px）
  max_slides:      6      # 最多生成几张内容图
  output_base_dir: ./output  # 输出目录（支持相对路径和 ~ 路径）
```

---

## 内容风格

图文使用"毒舌但真诚"的人设（详见 `毒舌skill.md`），每张内容图包含 4-6 个色块：

| 色块类型 | 颜色 | 用途 |
|---------|------|------|
| `normal` | 白色 | 铺垫背景、陈述事实 |
| `key` | 黄色 | 扎心真相，标签"说白了" |
| `bad` | 红色 | 毒舌吐槽，标签"韭菜行为" |
| `good` | 绿色 | 正经建议，标签"认真的" |
| `note` | 蓝色 | 补刀彩蛋，标签"多嘴一句" |

---

## 依赖

- Python 3.10+
- `openai` — LLM API 调用
- `pillow` — 图片渲染
- `pyyaml` — 配置读取

字体：自动检测系统中文字体（macOS 优先苹方，Windows 优先微软雅黑，Linux 优先 Noto CJK）。

---

## 常见问题

**Q: 提示找不到字体？**
A: 确保系统安装了中文字体。macOS 通常自带苹方，无需额外安装。

**Q: JSON 解析失败？**
A: 模型偶尔不稳定，重跑一次通常即可。可适当调高 `temperature`。

**Q: 报错 `Request timed out`？**
A: 把 `api.timeout_sec` 提高到 `180` 或 `300`，并检查网络能否访问 `dashscope.aliyuncs.com`。

**Q: 想换其他 LLM？**
A: 修改 `config.yaml` 中的 `base_url` 和 `model`，任何兼容 OpenAI SDK 的接口均可接入。
