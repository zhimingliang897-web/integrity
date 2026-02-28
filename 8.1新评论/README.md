# 社媒辅助搜索引擎

多平台社交媒体搜索引擎，支持 B站、抖音、小红书的内容搜索和评论抓取，带有智能筛选和分析功能。

## 功能特性

### 核心功能

- **多平台搜索**：B站、抖音、小红书三平台并行搜索
- **三层筛选**：
  - Layer 1：规则粗筛（过滤广告、标题党、低互动、重复内容）
  - Layer 2：LLM 精筛（相关性评分、实质性内容判断）
  - Layer 3：评论抓取与分析
- **数据存储**：SQLite + CSV 混合存储，支持手动保存
- **四维统计**：时间趋势、平台分布、热度分析、用户/KOL 分析
- **Gradio GUI**：可视化操作界面

### LLM 分析能力

- **评论筛选**：自然语言条件筛选评论
- **情感分析**：正面/中性/负面情感判断
- **话题相关性**：区分有效信息和无效信息
- **摘要总结**：自动生成评论摘要报告
- **评论分类**：按自定义分类标签归类

### 安全特性

- **反检测机制**：绕过平台 bot 检测（WebDriver、plugins、WebGL 等）
- **Cookie 自动获取**：无需手动复制 Cookie
- **速度档位控制**：fast/normal/slow/safe 四档可调
- **代理支持**：支持 HTTP/SOCKS 代理

## 快速开始

### 1. 安装依赖

```bash
cd "8.1新评论"
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. 获取 Cookie（推荐自动获取）

```bash
# 方式1：双击运行
update_cookie.bat

# 方式2：命令行
python scripts/refresh_cookie.py -p douyin
python scripts/refresh_cookie.py -p xiaohongshu
python scripts/refresh_cookie.py -p bilibili
```

### 3. 配置 LLM（可选，用于精筛）

编辑 `config.py`：

```python
# 默认使用阿里百炼，也可以换成其他 OpenAI 兼容接口
LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LLM_API_KEY = "your_api_key_here"
LLM_MODEL = "deepseek-v3"
```

支持的 LLM 服务商：
- 阿里百炼（默认）
- DeepSeek
- OpenAI
- 智谱 GLM
- 月之暗面
- 硅基流动

### 4. 启动

```bash
# 方式1：双击启动
启动.bat

# 方式2：命令行启动 GUI
python main.py

# 方式3：命令行搜索
python main.py search "春招AI岗位" -p bilibili,douyin
```

## 项目结构

```
8.1新评论/
├── main.py              # 主入口
├── gui.py               # Gradio 界面
├── config.py            # 配置文件
├── requirements.txt     # 依赖
├── 启动.bat             # Windows 启动脚本
├── update_cookie.bat    # Cookie 自动获取
│
├── scripts/             # 脚本工具
│   └── refresh_cookie.py # Cookie 刷新脚本
│
├── core/                # 核心引擎
│   ├── engine.py        # 搜索引擎（四阶段流水线）
│   └── session.py       # 会话管理
│
├── platforms/           # 平台爬虫
│   ├── base.py          # 基类和数据结构
│   ├── bilibili.py      # B站（API + BV号转换）
│   ├── douyin.py        # 抖音（Playwright + API 拦截）
│   └── xiaohongshu.py   # 小红书（同会话模式避免 461）
│
├── filters/             # 筛选模块
│   ├── rules.py         # 规则配置
│   ├── layer1.py        # 规则粗筛
│   └── layer2.py        # LLM 精筛
│
├── llm/                 # LLM 模块
│   ├── client.py        # OpenAI 兼容客户端
│   └── tasks.py         # 分析任务（情感/摘要/分类等）
│
├── storage/             # 数据存储
│   ├── models.py        # SQLite 表结构
│   ├── database.py      # CRUD 操作
│   └── export.py        # CSV/Excel 导出
│
├── stats/               # 统计分析
│   ├── analyzer.py      # 四维统计聚合
│   └── charts.py        # Plotly 图表生成
│
├── utils/               # 工具
│   └── stealth.py       # 反检测（10项绕过）
│
├── data/                # 数据目录
│   ├── search.db        # SQLite 数据库
│   └── exports/         # 导出文件
│
└── output/              # 话题分析输出
```

## 使用说明

### GUI 界面

1. **搜索标签页**：
   - 输入搜索关键词
   - 选择搜索平台（可多选）
   - 设置每平台最大结果数
   - 设置每内容最大评论数
   - 选择速度档位
   - 点击"开始搜索"

2. **筛选设置**：
   - Layer 1 规则：点赞数、评论数、广告过滤、标题党过滤
   - Layer 2 LLM：相关性评分阈值、实质性内容要求

3. **结果查看**：
   - 粗筛结果：规则过滤后的内容
   - 精筛结果：LLM 评估后的内容
   - 评论列表：抓取的评论详情

4. **统计分析**：
   - 时间趋势图
   - 平台分布饼图
   - 热度分析
   - KOL 识别

### 筛选配置

**Layer 1 规则粗筛**（config.py 中配置）：

```python
LAYER1_CONFIG = {
    "min_likes": 10,           # 最低点赞数
    "min_comments": 5,         # 最低评论数
    "min_views": 100,          # 最低播放量
    "duplicate_threshold": 0.85,  # 重复内容相似度阈值

    # 广告关键词
    "ad_keywords": ["私信", "加微", "VX", "优惠", ...],

    # 标题党关键词
    "clickbait_keywords": ["震惊", "必看", "绝了", ...],
}
```

**Layer 2 LLM 精筛**：

```python
LAYER2_CONFIG = {
    "min_score": 3,            # 最低相关性评分（1-5）
    "require_substance": True, # 是否要求有实质性内容
    "batch_size": 50,          # LLM 批处理大小
}
```

### LLM 分析任务

```python
from llm import LLMClient, tasks

client = LLMClient()

# 情感分析
results = tasks.sentiment_analysis(client, comments)

# 话题相关性分析
results = tasks.topic_relevance(client, comments, "AI 产品")

# 评论摘要
summary = tasks.summarize_comments(client, comments)

# 自定义条件筛选
results = tasks.filter_comments(client, comments, "包含具体使用体验的评论")

# 评论分类
results = tasks.classify_comments(client, comments, ["咨询", "吐槽", "建议", "其他"])
```

### 速度档位

| 档位 | 延迟范围 | 适用场景 |
|------|----------|----------|
| fast | 0.5-1s | 测试用，有风控风险 |
| normal | 1.5-3s | 日常使用，默认推荐 |
| slow | 3-6s | 大批量抓取 |
| safe | 5-10s | 最安全，长时间抓取 |

## Cookie 获取方法

### 方式1：自动获取（推荐）

双击运行 `update_cookie.bat`，选择平台后：

1. 程序会自动打开浏览器
2. 在浏览器中手动登录账号
3. 登录成功后返回命令行按回车
4. Cookie 自动保存到 `config.py`

命令行方式：

```bash
# 获取单个平台
python scripts/refresh_cookie.py -p douyin
python scripts/refresh_cookie.py -p xiaohongshu
python scripts/refresh_cookie.py -p bilibili

# 只打印不保存
python scripts/refresh_cookie.py -p douyin --no-update

# 保存到指定文件
python scripts/refresh_cookie.py -p douyin --save-path cookies/douyin.txt
```

### 方式2：手动获取

1. 打开浏览器，登录对应平台
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 刷新页面，点击任意请求
5. 在 Headers 中找到 Cookie 字段
6. 复制整个 Cookie 值到 `config.py`

## 平台特性说明

### B站

- 使用官方 API，无需 Cookie 也能抓取（但可能被限流）
- BV 号自动转换为 av 号
- 支持热度排序和时间排序

### 抖音

- 必须配置 Cookie
- 使用 Playwright 模拟搜索 + API 响应拦截
- 自动处理滑块验证（通过 stealth 脚本绕过）

### 小红书

- 必须配置 Cookie
- 使用同会话模式（搜索和评论抓取共用浏览器会话）
- 解决新会话访问笔记详情被 461 拒绝的问题

## 数据存储

### SQLite 表结构

- `sessions`：搜索会话记录
- `contents`：内容/视频/笔记
- `comments`：评论
- `saved`：用户手动保存的数据

### 导出格式

- CSV：通用格式，Excel 可直接打开
- Excel：带格式的 xlsx 文件

## 注意事项

1. **Cookie 有效期**：平台 Cookie 一般 7-30 天过期，需定期更新
2. **风控提示**：如果频繁出现验证码或空结果，请降低速度档位
3. **LLM 成本**：精筛功能会消耗 LLM API 额度，可在 GUI 中关闭
4. **数据安全**：抓取的数据仅供个人研究使用，请遵守平台规定
5. **代理使用**：如需使用代理，可在 stealth.py 的 create_stealth_context 中配置

## 常见问题

**Q: 抖音/小红书搜索返回空结果？**
A: Cookie 可能已过期，运行 `update_cookie.bat` 重新获取

**Q: 出现 461 错误？**
A: 小红书的反爬机制，项目已通过同会话模式解决

**Q: LLM 精筛报错？**
A: 检查 config.py 中的 LLM_API_KEY 是否正确配置

**Q: 如何提高抓取速度？**
A: 将 DEFAULT_SPEED 改为 "fast" 或 "normal"，但有被风控风险

## 更新日志

### v1.0 (2026-02)

- 初始版本
- 支持 B站、抖音、小红书三平台
- 三层筛选系统
- Cookie 自动获取
- LLM 分析任务（情感/摘要/分类/话题相关性）
- Gradio GUI 界面
- 四维统计分析
