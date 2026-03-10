# 多语言 Token 消耗对比工具

对比相同语义问题使用 **中文/英文/图片中文** 提问时，各大模型的 Token 消耗差异。

## 功能特性

- 支持三种输入方式：中文文本、英文文本、图片中文
- 支持多种模型：
  - 阿里云 Qwen 系列：qwen-turbo、qwen-plus、qwen-max、qwen-vl-plus
  - OpenAI GPT 系列：gpt-4o、gpt-4o-mini、gpt-4-turbo
- 实时显示 Token 消耗明细（Prompt/Completion/Total）
- 图形化界面，操作简单

## 安装

```bash
pip install -r requirements.txt
```

## 依赖

- Python 3.8+
- requests - HTTP 请求库
- Pillow - 图片处理库
- tkinter - GUI 库（Python 自带）

## 配置

使用前需在 `main.py` 中配置 API Key：

```python
DASHSCOPE_API_KEY = "your-aliyun-key"  # 阿里云 DashScope Key
OPENAI_API_KEY = "your-openai-key"     # OpenAI Key
```

## 运行

```bash
python main.py
```

## 使用说明

1. 输入问题内容
2. 选择输入语言（中文/英文/图片中文）
3. 选择大模型
4. 点击「开始分析」查看 Token 消耗结果

## 注意事项

- 图片中文模式仅支持 qwen-vl-plus 模型
- 所有请求均强制要求模型用中文回答
- 请确保 API Key 有效且有足够额度
