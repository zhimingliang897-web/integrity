# 社交媒体评论抓取 & 分析工具

支持 **B站、抖音、小红书** 三个平台的评论抓取，并通过 LLM 对评论进行智能分析（筛选、情感分析、摘要、分类），导出为 CSV/Excel。

🔥 **最新更新 (2026-02-12)**:
*   **小红书**: 架构升级为 **同会话搜索+抓取** 模式，有效解决笔记详情页跳转失败 (461) 问题。
*   **抖音**: 增加首页预热与搜索框模拟输入，大幅降低验证码触发率。
*   **精准过滤**: 所有平台采用 **严格关键词过滤** 策略，自动剔除推荐流中的无关内容，确保搜索结果的相关性。
*   **反爬虫**: 全面启用 `headless=False` (有头模式) + 随机延时策略，模拟真人操作。

---

## 快速开始

### 1.环境准备

```bash
pip install -r requirements.txt

# 安装 Playwright 浏览器驱动
pip install playwright
python -m playwright install chromium
```

如有条件，建议安装 **Google Chrome** 浏览器，程序会优先调用真实的 Chrome 以降低指纹特征。

### 2.配置 Cookie (关键!)

抖音和小红书必须提供 Cookie 才能抓取。请在 `config.py` 中配置：

建议先从模板复制（仅首次）：

```bash
cp config.example.py config.py
```

1.  用浏览器打开 [douyin.com](https://www.douyin.com) 或 [xiaohongshu.com](https://www.xiaohongshu.com) 并登录。
2.  按 `F12` 打开开发者工具 -> `Network` (网络) 标签。
3.  刷新页面，点击任意请求 (如 `user/me` 或 `search`)。
4.  在 `Request Headers` (请求头) 中找到 `Cookie`，复制全部内容。
5.  粘贴到 `config.py` 的 `DOUYIN_COOKIE` 或 `XIAOHONGSHU_COOKIE` 变量中。

### 3.运行一站式话题分析

输入关键词，自动完成 `搜索 -> 抓取 -> 分析 -> 报告` 全流程：

```bash
# 搜索三个平台，默认每平台5个内容，每内容50条评论
python main.py topic -k "iPhone 16 电池续航"

# 只搜小红书，安全模式 (速度较慢但稳定)
python main.py topic -k "新加坡旅游攻略" -p xiaohongshu -s safe

# 自定义数量: 每平台搜 10 个内容，每个抓 100 条评论
python main.py topic -k "减肥食谱" -ms 10 -mc 100
```

### 4.启动图形界面 (GUI)

```bash
pip install -r requirements.txt
streamlit run gui.py
```

Windows 也可直接双击 `start_gui.bat`。

### 5.一键刷新 Cookie（自动写入 config.py）

```bash
# 抖音
python scripts/refresh_cookie.py -p douyin

# 小红书
python scripts/refresh_cookie.py -p xiaohongshu

# B站
python scripts/refresh_cookie.py -p bilibili
```

流程:
1. 脚本自动打开浏览器  
2. 你手动登录目标平台  
3. 回终端按回车  
4. 脚本自动提取 Cookie 并更新 `config.py`（同时生成 `config.py.bak` 备份）

Windows 可直接双击 `update_cookie.bat` 选择平台执行。

---

## 核心功能命令详解

### 1. 话题分析 (topic)

全自动流程，适合调研。

| 参数 | 说明 |
| :--- | :--- |
| `-k` | **(必填)** 话题关键词 |
| `-p` | 平台: `bilibili`, `douyin`, `xiaohongshu` (默认全部) |
| `-ms` | 每个平台最大搜索结果数 (默认 5) |
| `-mc` | 每个视频/帖子最大抓取评论数 (默认 50) |
| `-s` | 速度/安全档位: `fast`, `normal`, `slow`, **`safe`** (推荐) |

### 2. 单篇抓取 (scrape)

抓取指定视频/笔记的评论。

```bash
# 小红书 (支持短链接)
python main.py scrape -p xiaohongshu -u "https://www.xiaohongshu.com/explore/64a1..."

# 抖音
python main.py scrape -p douyin -u "https://v.douyin.com/..."

# B站 (速度极快)
python main.py scrape -p bilibili -u "BV1xx411c7mD"
```

### 3. 评论分析 (analyze)

使用 LLM 分析已抓取的 CSV 文件。

```bash
# 自动执行所有分析任务 (情感、摘要、筛选、分类)
python main.py analyze -i output/topic/xxx_raw.csv --task all

# 仅筛选特定内容的评论
python main.py analyze -i output/xxx.csv --task filter --criteria "关于价格的讨论"
```

---

## 架构与原理

### 项目结构

```
评论/
├── main.py                   # CLI 入口
├── config.py                 # 配置文件 (Cookie, LLM Key)
├── searchers/                # 搜索模块 (Playwright)
│   ├── douyin.py             # 抖音搜索 (预热+模拟输入)
│   └── xiaohongshu.py        # 小红书搜索+抓取 (同会话模式)
├── scrapers/                 # 评论抓取模块
│   ├── bilibili.py           # B站 (API)
│   ├── douyin.py             # 抖音 (Playwright 拦截)
│   └── xiaohongshu.py        # 小红书 (Playwright 独立模式 scrape 专用)
├── topic/
│   └── pipeline.py           # 话题分析流水线
├── utils/
│   ├── stealth.py            # 浏览器反检测模块
│   └── proxy.py              # 代理池管理模块 (防封IP)
├── proxies.txt.example       # 代理配置模板
├── example_proxy_usage.py    # 代理使用示例
└── PROXY_GUIDE.md            # 代理使用完整指南
```

### 推荐整理方式（先做这 3 件事）

1. 保持“源码和产物分离”：源码留在 `analyzer/`、`scrapers/`、`searchers/`、`topic/`，运行结果只放 `output/`。  
2. 保持“模板和私有配置分离”：提交 `config.example.py`，本机使用 `config.py`。  
3. 保持“调试和正式代码分离”：临时调试脚本统一放到 `scripts/debug_archive/`，稳定后再迁移到正式模块。

项目已提供：
- `.gitignore`（忽略缓存、产物和本地敏感文件）
- `config.example.py`（无敏感信息配置模板）
- `PROJECT_LAYOUT.md`（完整整理建议）

### 抓取策略

1.  **B站**:
    *   使用公开 API，无签名验证，速度快，无需 Cookie (但登录后可看更多)。

2.  **抖音**:
    *   **搜索**: 启动 Playwright 浏览器，先访问首页建立会话，然后在搜索框输入关键词并回车 (模拟真人)。
    *   **评论**: 拦截浏览器网络请求，自动处理 `X-Bogus` 签名验证。

3.  **小红书** (重点):
    *   **难点**: 严格的服务端反爬，新开浏览器会话访问笔记详情页会导致 `461` 错误 (被重定向回首页)。
    *   **解决方案**: 采用 **"同会话 DOM 点击"** 策略。搜索完成后，**不关闭浏览器**，直接在当前搜索结果页点击笔记卡片 (模拟真人点击)，使笔记以弹窗形式打开，在此过程中拦截评论 API 数据。
    *   **注意**: 此过程需要完整的浏览器环境，因此速度较慢，请保持耐心。

---

## 🛡️ 防封IP策略 (代理支持)

为了避免频繁抓取导致IP被封禁，本工具已集成**代理池**功能。

### 快速使用

1. **创建代理配置文件：**
   ```bash
   cp proxies.txt.example proxies.txt
   # 编辑 proxies.txt，添加你的代理地址
   ```

2. **在代码中使用：**
   ```python
   from utils.proxy import ProxyPool
   from scrapers.douyin import DouyinScraper

   pool = ProxyPool()
   pool.load_from_file("proxies.txt")
   pool.validate_all()  # 验证代理可用性

   scraper = DouyinScraper(
       cookie="你的Cookie",
       speed="normal",
       proxy_pool=pool  # 传入代理池
   )
   ```

### 支持的代理类型

- ✅ HTTP/HTTPS 代理
- ✅ SOCKS5 代理
- ✅ 带用户名密码认证的代理
- ✅ 本地代理（Clash/V2Ray）
- ✅ 付费代理服务

### 代理配置格式

```txt
# proxies.txt
http://127.0.0.1:7890
http://username:password@proxy.example.com:8080
socks5://127.0.0.1:1080
```

### 完整指南

查看 **[PROXY_GUIDE.md](PROXY_GUIDE.md)** 了解：
- 代理服务推荐
- 详细配置方法
- 使用示例代码
- 常见问题解答

---

## 常见问题

**Q: 小红书/抖音抓取失败，提示 "Cookie 无效" 或 "重定向"?**
A: Cookie 已过期或被平台标记。请重新在浏览器登录，获取新的 Cookie 更新到 `config.py`。建议使用 Chrome 隐身模式登录获取。

**Q: 浏览器一闪而过?**
A: 这是正常的。但在调试模式或 `headless=False` (默认) 下，你会看到浏览器自动操作的过程。**请勿手动干预浏览器窗口**。

**Q: 抓取速度太慢?**
A: 为了安全。抖音和小红书对频率限制极严。建议使用 `-s safe` 模式 (间隔 5-10 秒)，虽然慢但能稳定抓取，避免封号。

**Q: 为什么不使用 API 直接请求?**
A: 抖音和小红书 API 均有复杂的加密签名 (WebId, X-Bogus, X-s 等) 和设备指纹验证。使用浏览器自动化 (Playwright) 是最稳定且维护成本最低的方案。

**Q: IP被封了怎么办?**
A: 使用代理IP池！本工具已支持代理功能，步骤：
1. 准备代理（本地Clash/V2Ray 或购买付费代理）
2. 创建 `proxies.txt` 配置文件
3. 在代码中传入 `proxy_pool` 参数
详见 [PROXY_GUIDE.md](PROXY_GUIDE.md) 完整指南。
