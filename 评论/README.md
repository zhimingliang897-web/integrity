# 社交媒体评论抓取 & 分析工具

支持 B站、抖音、小红书三个平台的评论抓取，并通过 LLM 对评论进行智能分析（筛选、情感分析、摘要、分类），导出为 CSV/Excel。

## 安装

```bash
pip install -r requirements.txt

# 抖音需要额外安装 Playwright
pip install playwright
python -m playwright install chromium
```

## 项目结构

```
评论/
├── main.py              # 命令行入口（scrape / analyze 子命令）
├── config.py            # 配置文件（Cookie、LLM、导出设置）
├── scrapers/            # 评论抓取模块
│   ├── base.py          # 抓取器基类
│   ├── bilibili.py      # B站抓取（纯 API）
│   ├── douyin.py        # 抖音抓取（Playwright 浏览器）
│   └── xiaohongshu.py   # 小红书抓取（API）
├── analyzer/            # LLM 分析模块
│   ├── client.py        # OpenAI 兼容 LLM 客户端
│   └── tasks.py         # 分析任务（筛选/情感/摘要/分类）
├── utils/
│   └── export.py        # CSV/Excel 导出
├── output/              # 导出文件目录
└── requirements.txt
```

---

## 一、评论抓取

### 基本用法

```bash
# B站（无需Cookie）
python main.py scrape -p bilibili -u "视频链接" -m 200

# 抖音（需在 config.py 配置Cookie）
python main.py scrape -p douyin -u "视频链接" -m 200

# 小红书（需在 config.py 配置Cookie）
python main.py scrape -p xiaohongshu -u "笔记链接" -m 200

# 抓取全部评论
python main.py scrape -p bilibili -u "视频链接" --all

# 指定速度档位
python main.py scrape -p bilibili -u "视频链接" -m 500 -s safe

# 导出为 Excel
python main.py scrape -p bilibili -u "视频链接" -m 100 -f excel
```

### scrape 参数

| 参数 | 说明 |
|------|------|
| `-p` | 平台：bilibili / douyin / xiaohongshu |
| `-u` | 视频/笔记链接或ID |
| `-m` | 最大抓取条数（默认100） |
| `-a` | 抓取全部评论（忽略 -m 限制） |
| `-s` | 速度档位：fast / normal / slow / safe |
| `-f` | 导出格式：csv / excel |
| `-o` | 输出目录（默认 output/） |

### 速度档位

| 档位 | 请求延迟 | 说明 |
|------|----------|------|
| fast | 0.5~1s | 速度最快，少量抓取或测试用，有风控风险 |
| normal | 1.5~3s | 默认推荐，日常使用 |
| slow | 3~6s | 较安全，适合大量抓取 |
| safe | 5~10s | 最安全，适合长期批量抓取 |

也可以在 `config.py` 中设置 `DEFAULT_SPEED` 修改全局默认速度。

### Cookie 配置

抖音和小红书需要在 `config.py` 中填写 Cookie：

1. 浏览器打开对应平台网页版并登录
2. 按 F12 打开开发者工具 → Network 标签
3. 刷新页面，点击任意请求，在 Request Headers 中复制 Cookie 值
4. 粘贴到 `config.py` 对应变量中

Cookie 会过期，失效后需重新获取。

---

## 二、LLM 评论分析

抓取完成后，可以用 LLM 对导出的评论文件进行智能分析。

### LLM 配置

在 `config.py` 中配置 LLM 接口信息：

```python
LLM_BASE_URL = "https://api.deepseek.com/v1"   # API 地址
LLM_API_KEY = "sk-xxxx"                          # API Key
LLM_MODEL = "deepseek-v3-0324"                   # 模型名称
LLM_BATCH_SIZE = 50                              # 每批处理评论数
```

支持任意 OpenAI 兼容接口，切换服务商只需修改这三个值：

| 服务商 | BASE_URL | MODEL 示例 |
|--------|----------|------------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-v3-0324` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| 其他兼容接口 | 对应地址 | 对应模型名 |

### 分析任务

提供 4 种分析任务 + 一键全部执行，均从已导出的 CSV/Excel 文件读取评论。

分析结果统一保存在 `output/analysis/` 目录下，文件名基于源文件自动生成，不会覆盖原始数据。

#### 1. 情感分析（sentiment）

为每条评论标注情感倾向：正面(positive)、中性(neutral)、负面(negative)。

```bash
python main.py analyze -i output/bilibili_comments_20260131_120000.csv --task sentiment
```

输出：`output/analysis/bilibili_comments_20260131_120000_sentiment.csv`

#### 2. 摘要总结（summary）

对所有评论生成整体摘要，从主要观点、情感倾向、高频话题三个维度分析。

```bash
python main.py analyze -i output/bilibili_comments_20260131_120000.csv --task summary
```

输出：`output/analysis/bilibili_comments_20260131_120000_summary.txt`

#### 3. 评论筛选（filter）

根据自然语言描述的条件筛选评论。

```bash
python main.py analyze -i output/bilibili_comments_20260131_120000.csv --task filter --criteria "包含产品反馈或改进建议的评论"
```

输出：`output/analysis/bilibili_comments_20260131_120000_filter.csv`

#### 4. 评论分类（classify）

将每条评论归入自定义的分类标签中。

```bash
python main.py analyze -i output/bilibili_comments_20260131_120000.csv --task classify --categories "好评,差评,建议,提问,闲聊"
```

输出：`output/analysis/bilibili_comments_20260131_120000_classify.csv`

#### 5. 一键全部（all）

一条命令执行全部 4 项分析任务，自动使用默认筛选条件和分类标签（也可自定义）。

```bash
# 使用默认条件一键分析
python main.py analyze -i output/bilibili_comments_20260131_120000.csv --task all

# 自定义条件一键分析
python main.py analyze -i output/bilibili_comments_20260131_120000.csv --task all --criteria "与产品体验相关的评论" --categories "好评,差评,建议,提问"
```

输出 `output/analysis/` 下会生成 4 个文件：
```
bilibili_comments_20260131_120000_sentiment.csv
bilibili_comments_20260131_120000_summary.txt
bilibili_comments_20260131_120000_classify.csv
bilibili_comments_20260131_120000_filter.csv
```

### analyze 参数

| 参数 | 说明 |
|------|------|
| `-i` | 输入文件路径（CSV 或 Excel） |
| `-t` | 分析任务：filter / sentiment / summary / classify / **all** |
| `-c` | filter 任务的筛选条件（自然语言描述） |
| `--categories` | classify 任务的分类标签（逗号分隔） |
| `-o` | 输出目录（默认 output/） |

### 完整工作流示例

```bash
# 第一步：抓取 B站视频评论
python main.py scrape -p bilibili -u "https://www.bilibili.com/video/BVxxxxx" -m 500

# 第二步：一键执行全部分析
python main.py analyze -i output/bilibili_comments_20260131_120000.csv --task all

# 或者单独执行某项分析
python main.py analyze -i output/bilibili_comments_20260131_120000.csv --task sentiment
```

---

## 抓取原理

### B站 — 纯 API 请求

B站的评论接口是公开的，无需身份验证：

```
GET https://api.bilibili.com/x/v2/reply/main?oid=视频ID&type=1&next=页码
```

直接用 `requests` 发送 HTTP 请求即可获取 JSON 数据。B站对该接口几乎没有反爬措施，只要请求频率合理就不会被拦截。因此 B站模块速度快、无需 Cookie。

### 抖音 — Playwright 浏览器拦截

抖音的评论接口虽然也存在，但有**签名校验机制**。每个请求必须携带 `a_bogus`、`X-Bogus` 等加密参数，这些参数由浏览器中的 JavaScript 实时计算生成。服务端会验证签名，签名缺失或错误则返回空内容。

纯 `requests` 无法执行 JS，因此无法生成合法签名。本工具的解决方案是通过 Playwright 启动真实的 Chromium 浏览器：

1. 启动浏览器，注入用户 Cookie（登录态）
2. 访问抖音视频页面，浏览器正常加载并执行 JS
3. 浏览器中的 JS 自动计算签名，向 API 发送合法请求
4. 监听浏览器网络响应（`page.on("response")`），拦截评论数据
5. 模拟滚动页面，触发浏览器加载更多评论，持续拦截

本质上是让浏览器完成签名计算，程序只是"监听"浏览器与服务器之间的通信。

### 为什么抖音需要 Cookie

Cookie 中包含登录态（`sessionid`、`sid_tt` 等）。抖音对未登录用户限制较大，评论接口可能不返回数据或只返回极少量。Cookie 让浏览器以用户账号身份访问，才能正常加载评论区。

### 对比

| | B站 | 抖音 |
|---|---|---|
| 请求方式 | requests 直接调 API | Playwright 真实浏览器 |
| 签名校验 | 无 | 有（JS 运行时计算） |
| Cookie | 可选 | 必须 |
| 速度 | 快（纯网络请求） | 慢（启动浏览器+渲染页面） |
| 稳定性 | 高 | 中（依赖页面结构） |
