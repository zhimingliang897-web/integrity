# 多模型对比平台

## 功能
- **多供应商集成**：从 API.md 自动读取 Qwen, Doubao, DeepSeek, Kimi, OpenAI 等供应商信息。
- **多模型并行对比**：支持同一个供应商下选择多个模型进行并行提问，直观对比回复质量。
- **高度自由度**：
  - **自定义模型**：可在前端手动添加新模型。
  - **一键全选/取消**：快速切换对比范围。
  - **持久化存储**：Base URL 与模型选择自动保存到浏览器本地。
- **响应式 UI**：现代化的深色界面，支持卡片式布局与流式展示。

## 目录结构
- `server.js`：Node.js 后端，负责 API 转发与 API.md 解析。
- `public/`：前端静态资源（HTML, CSS, JS）。
- `API.md`：配置文件，存储 API Key 与默认模型。

## 启动方式
### 使用 Node.js
```bash
node server.js
```
浏览器访问 http://localhost:3000

### 使用 Python (快捷启动)
```bash
python start.py [端口]
```

## API.md 规则
- 供应商标题以 `## ` 开头。
- **API Key**、**模型**、**Base URL** 使用反引号包裹。
- **多模型**：在“模型”行使用逗号分隔多个模型名，例如：`模型:` \`gpt-4o\`, \`gpt-4o-mini\`。

## 环境变量
支持通过环境变量覆盖 API.md 中的 Key：
- `QWEN_API_KEY`
- `DOUBAO_API_KEY`
- `DEEPSEEK_API_KEY`
- `KIMI_API_KEY`
- `OPENAI_API_KEY`
