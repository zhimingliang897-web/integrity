# AI 图片 <-> 提示词 工具箱

两个脚本组成完整链路：
1) `image_to_prompt.py`：图片 -> 提示词
2) `prompt_to_image.py`：提示词 -> 图片

## 项目结构

```text
.
├── image_to_prompt.py
├── prompt_to_image.py
├── raw/          # 图片输入目录（可含子目录）
├── prompts/      # 提示词输出目录
│   ├── dalle_style/
│   └── sd_style/
└── generated/    # 生图输出目录
```

默认路径都按“脚本所在目录”解析，可用 `-i` / `-o` 覆盖。

## 安装依赖

```bash
pip install openai requests
```

如果你在 `prompt_to_image.py` 使用 `wanx-*` 模型，还需要：

```bash
pip install dashscope
```

## API Key 配置

DashScope:

```bash
# Windows
set DASHSCOPE_API_KEY=sk-xxxx

# macOS / Linux
export DASHSCOPE_API_KEY=sk-xxxx
```

Volcengine:

```bash
# Windows
set VOLC_API_KEY=xxxx

# macOS / Linux
export VOLC_API_KEY=xxxx
```

也可以每次运行用 `--key` 临时传入。

## 快速使用

```bash
# 1) 图片 -> 提示词
python image_to_prompt.py

# 2) 提示词 -> 图片
python prompt_to_image.py -i prompts/dalle_style
```

## image_to_prompt.py

用途：读取图片，生成 `dalle_style` 与 `sd_style` 两类文本提示词。

参数：

| 参数 | 短参 | 默认值 | 说明 |
|:---|:---|:---|:---|
| `--input` | `-i` | `raw` | 图片输入目录 |
| `--output` | `-o` | `prompts` | 提示词输出目录 |
| `--mode` | `-m` | `both` | `dalle` / `sd` / `both` |
| `--workers` | `-w` | `5` | 并发线程数 |
| `--provider` | 无 | `dashscope` | `dashscope` / `volcengine` |
| `--model` | 无 | dashscope 下默认 `qwen3-vl-flash-2026-01-22` | volcengine 建议填写 Endpoint ID |
| `--key` | `-k` | 环境变量 | API Key |

示例：

```bash
# 仅生成 SD tags
python image_to_prompt.py -m sd

# 指定路径
python image_to_prompt.py -i D:\Data\raw -o D:\Data\prompts

# 使用 volcengine
python image_to_prompt.py --provider volcengine --model ep-xxxx
```

## prompt_to_image.py

用途：读取 `.txt` 提示词并生成图片，支持并发和全局限速。

参数：

| 参数 | 短参 | 默认值 | 说明 |
|:---|:---|:---|:---|
| `--input` | `-i` | `prompts` | 提示词输入目录（递归扫描 `.txt`） |
| `--output` | `-o` | `generated` | 图片输出目录 |
| `--provider` | `-p` | `dashscope` | `dashscope` / `volcengine` |
| `--model` | `-m` | `qwen-image-max`（dashscope） | volcengine 需要手动指定 Endpoint ID |
| `--size` | `-s` | `1024x1024` | 输出尺寸 |
| `--workers` | `-w` | `1` | 并发线程数 |
| `--interval` | 无 | `3` | 全局请求最小间隔（秒） |
| `--key` | `-k` | 环境变量 | API Key |

示例：

```bash
# DashScope 默认模型
python prompt_to_image.py -i prompts/dalle_style

# 增大并发，仍保留 2 秒全局间隔
python prompt_to_image.py -i prompts/sd_style -w 4 --interval 2

# 使用 wanx
python prompt_to_image.py -i prompts/dalle_style -m wanx-v1

# 使用 volcengine
python prompt_to_image.py --provider volcengine --model ep-xxxx
```

说明：
1. 已存在图片会自动跳过。
2. DashScope 下提示词超过 800 字符会自动截断。
3. `qwen-image-*` 走 HTTP 接口，其他模型按 `wanx` 方式调用。

## 常见问题

1. 报 `403`：通常是模型权限未开通，检查控制台权限。
2. 报 `429`：限流，增大 `--interval` 或降低 `--workers`。
3. 终端乱码：Windows 下脚本已自动切换到 UTF-8 输出。
