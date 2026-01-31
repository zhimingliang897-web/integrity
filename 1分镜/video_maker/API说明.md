# API 说明

## 当前模型

| 用途 | 模型 | 免费额度 |
|------|------|---------|
| 文本生成 | `qwen3-max-2026-01-23` | 100万 token（到 2026/04/23） |
| 图片生成 | `qwen-image` | - |

## 环境变量

```bash
set DASHSCOPE_API_KEY=你的API密钥
```

密钥从 [阿里云百炼控制台](https://dashscope.console.aliyun.com/) 获取。

## 切换模型

修改 `gen_text.py` 顶部：

```python
MODEL = "qwen3-max-2026-01-23"
IMAGE_MODEL = "qwen-image"
```
