# What We Learn

这个项目过程中涉及的原理和技术点。

## PDF 文本提取

用 `pdfplumber` 读取 PDF，每个字符对象带有 `size`（字号）、`text`（内容）等属性。
通过筛选最大字号的字符，提取出需要学习的单词。

提取出来的字符是连续的（如 `renewalbarter`），程序不知道哪里断词，
所以调 LLM（deepseek-v3.2）来判断边界，拆分成独立单词。

## SPA 网站的数据获取

popmystic.com 是一个 Vue 单页应用（SPA），页面内容由 JavaScript 动态渲染。
直接用 `requests.get` 请求网页 URL 只能拿到空壳 HTML，看不到搜索结果。

```
浏览器访问:  URL → 下载 HTML → 执行 JS → JS 调 API → 渲染结果到页面  ✓
requests:   URL → 下载 HTML → 完了（不执行 JS）→ 空页面              ✗
直接调 API:  API URL → POST JSON → 直接拿到数据                      ✓ ← 我们用这个
```

**怎么找到真正的 API：**

1. 打开 Chrome，按 F12 打开开发者工具
2. 切到 Network 标签，勾选 "Fetch/XHR"
3. 在 popmystic.com 搜索一个词
4. 观察 Network 面板，会看到一个 POST 请求发往：
   `https://pop-opensearch-api-myxi6.ondigitalocean.app/search-scroll`
5. 点击请求查看 Request Payload 和 Response

这是一个 OpenSearch（Elasticsearch 的开源分支）查询接口。
用同样的 JSON 格式直接 POST，就能拿到搜索结果，不需要浏览器渲染。

## LLM 整理学习材料

原始台词数据量大且杂乱（每个词数百条引用），不适合直接阅读。
调 LLM 做筛选和加工：

- 从大量结果中挑出 2-3 段最能体现自然用法的台词
- 补充上下文，还原为对话形式
- 添加中英释义和中文翻译

Prompt 的关键是给出明确的输出格式，让 LLM 返回结构化的 Markdown，方便后续解析。

## Flask 本地 Web 应用

用 Flask 搭建本地服务器，前端是单个 HTML 文件（SPA 风格，用 JS 控制路由和渲染）。

关键设计：

- **Markdown 解析不依赖库**：`_study.md` 格式固定，用正则按 `## word` 分块提取结构化数据，返回 JSON 给前端渲染
- **后台异步处理**：上传 PDF 后用 `threading.Thread` 在后台依次跑三个脚本，前端轮询 `/api/status` 获取进度
- **SPA 路由**：用 `history.pushState` + `popstate` 事件实现前端路由，Flask 端对 `/day/<n>` 统一返回同一个 HTML
