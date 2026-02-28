# XZ图片网爬虫项目文档

## 一、项目概述

该项目是一套针对**XZ图片网（0xzn.com）**的自动化图片采集工具，使用Playwright浏览器引擎实现对目标网站的自动化访问和图片抓取。项目支持多分类并行下载、断点续爬、代理轮换等企业级功能，适用于大规模图片数据集的采集场景。

### 1.1 项目定位

本项目的定位是一个功能完善的图片批量采集工具，适用于以下场景：图片数据集收集、Cosplay照片整理、网络美图归档等。需要强调的是，本工具仅供个人学习研究使用，请勿用于商业目的或大规模非法采集。

### 1.2 技术架构

项目采用模块化设计，包含以下核心组件：**xz_scraper.py**是主爬虫程序，负责整个采集流程的控制，包括浏览器初始化、页面导航、数据提取、文件下载等；**xz_config.py**是配置文件，集中管理所有可调整参数，包括速度档位、安全限制、代理配置等；**xz_proxy.py**是代理池管理模块，提供代理加载、验证、轮换等功能，有效防止IP被封禁。

---

## 二、文件结构

```
E:\integrity\7爬虫\xz_图片\
├── xz_config.py          # 【配置】配置文件（2.4KB，59行）
├── xz_scraper.py        # 【核心】主爬虫程序（48.6KB，1236行）
├── xz_proxy.py          # 【模块】代理池管理（8.3KB，246行）
├── proxies.txt          # 【可选】代理列表文件
└── data/               # 数据输出目录
    ├── xz_images/      # 下载的图片存放目录
    │   ├── cosplay/
    │   ├── 机构美女图片/
    │   └── 网红美女/
    ├── xz_progress.json           # 进度记录（主）
    └── xz_progress_秀人网.json   # 各分类独立进度文件
```

### 2.1 各文件职责

**xz_config.py**集中管理所有配置项：目标网站URL、输出目录路径、速度档位参数、安全限制设置、代理配置选项、下载参数设置。任何参数调整都应修改此文件。

**xz_scraper.py**是程序入口和核心逻辑：实现五阶段工作流程（扫描→统计→汇总→选择→下载）；实现浏览器自动化操作；实现图片URL提取和下载；实现断点续爬功能；支持命令行参数解析和多开并行。

**xz_proxy.py**提供代理池功能：ProxyPool类负责代理列表管理和验证；ProxyRotator类负责代理自动轮换；支持从文件加载代理；支持代理可用性检测。

---

## 三、功能说明

### 3.1 核心功能列表

| 功能模块 | 功能描述 | 状态 |
|----------|----------|------|
| 分类扫描 | 自动扫描网站所有分类 | ✅ 正常 |
| 数量统计 | 统计每个分类的图集数量和分页 | ✅ 正常 |
| 交互选择 | 图形化界面选择要下载的分类 | ✅ 正常 |
| 图片下载 | 批量下载图集中的所有图片 | ✅ 正常 |
| 断点续爬 | 中断后可继续，支持多进程 | ✅ 正常 |
| 多开并行 | 支持多CMD窗口同时运行 | ✅ 正常 |
| 代理支持 | 单一代理或代理池轮换 | ✅ 正常 |
| 反检测 | Playwright+stealth模式 | ❌ 缺失依赖 |

### 3.2 五阶段工作流程

**阶段一：扫描分类**

程序启动后自动访问目标网站首页，通过多种CSS选择器匹配导航链接，提取所有分类的名称和URL。去重后会显示所有发现的分类供用户选择。

**阶段二：统计数量**

逐个访问每个分类的第一页，尝试获取分页导航中的总页码信息，结合当前页的图集数量，估算出每个分类的总图集数量。

**阶段三：展示汇总**

以表格形式展示所有分类的统计信息，包括：分类名称、预估图集数量、总页数、已下载数量。便于用户了解整体情况后做出选择。

**阶段四：交互选择**

用户可以通过以下方式选择要下载的分类：输入`all`下载全部分类；输入`1,3,5`下载指定编号的分类；输入`1-5`下载编号范围内的分类；输入`q`退出程序。

**阶段五：爬取下载**

遍历选中分类的所有页面，提取每个图集的标题和链接，然后逐个访问图集页面，通过滚动触发懒加载，提取所有图片URL并下载保存。

### 3.3 速度档位

| 档位 | 页面请求间隔 | 图片请求间隔 | 适用场景 |
|------|-------------|--------------|----------|
| fast | 1-3秒 | 0.3-0.8秒 | 网络环境好、快速采集 |
| normal | 3-6秒 | 0.5-1.5秒 | 默认选项，平衡速度与安全 |
| slow | 5-10秒 | 1-3秒 | 网络一般或站点较敏感 |
| safe | 8-15秒 | 2-5秒 | 最大限度降低检测风险 |

### 3.4 安全保护机制

程序内置多重保护机制确保采集行为合理可控：

**请求限速**：单次运行最多500次请求，超过后自动停止，用户重新运行可继续下载。

**错误处理**：连续失败3次后暂停60-120秒再继续，避免因暂时性问题导致程序终止。

**定期休息**：每处理20个图集强制休息30-60秒，模拟人类操作节奏。

**超时设置**：页面加载超时30秒，图片下载超时60秒，避免因网络问题导致程序卡死。

---

## 四、使用方法

### 4.1 交互模式（推荐新手）

```bash
cd E:\integrity\7爬虫\xz_图片
python xz_scraper.py
```

程序启动后会依次执行五阶段流程，在选择分类阶段会显示类似下方的交互界面：

```
============================================================
  请选择要下载的分类
============================================================
  输入方式:
    all       — 下载全部分类
    1,3,5     — 下载编号 1、3、5 的分类
    1-5       — 下载编号 1 到 5 的分类
    q         — 退出

  请输入选择: 
```

### 4.2 扫描模式

只扫描分类和数量，不执行下载，便于查看分类信息后使用并行命令：

```bash
python xz_scraper.py --scan
```

输出示例：

```
============================================================
  阶段1: 扫描网站分类
============================================================

[扫描] 发现 15 个分类:
  1. 秀人网 → https://www.0xzn.com/xrnw
  2. 语画界 → https://www.0xzn.com/yhj
  ...

============================================================
  分类汇总
============================================================
    #  分类名称      图集数(估)     页数
  ---  ----------  ----------  ------
    1  秀人网           5000      250
    2  语画界           3500      175
  ...

============================================================
  并行下载命令示例（每个CMD窗口一个）:
============================================================
  python xz_scraper.py --category "秀人网"
  python xz_scraper.py --category "语画界"
  
  # 限制每分类100个: --max-albums 100
  # 改速度档: --speed safe
```

### 4.3 命令行指定模式

通过参数直接指定要下载的分类，跳过交互选择：

```bash
# 下载单个分类
python xz_scraper.py --category "秀人网"

# 下载多个分类
python xz_scraper.py --category "爱尤物,模范学院"

# 限制每个分类最多下载数量
python xz_scraper.py --category "语画界" --max-albums 100

# 限制所有分类总共下载数量
python xz_scraper.py --category "秀人网" --max-albums 50
```

### 4.4 调整速度档位

```bash
# 使用快速模式（可能容易被检测）
python xz_scraper.py --speed fast

# 使用安全模式（慢但稳定）
python xz_scraper.py --speed safe
```

### 4.5 使用代理

当IP被封禁时，可通过代理解决：

```bash
# 使用单一代理
python xz_scraper.py --proxy "http://127.0.0.1:7890"

# 使用代理池（需配置proxies.txt）
python xz_scraper.py  # 代理池默认启用
```

支持的代理格式：

```bash
http://127.0.0.1:7890           # HTTP代理（Clash默认）
socks5://127.0.0.1:1080         # SOCKS5代理（SS/V2ray）
http://user:pass@host:port       # 带认证的代理
```

### 4.6 进度管理

```bash
# 查看当前进度（通过输出目录的进度文件）
# 进度文件位置：data/xz_progress_*.json

# 清除进度重新开始
python xz_scraper.py --reset-progress
```

### 4.7 并行多开

在多个CMD窗口中分别运行不同分类，可大幅提升采集效率：

```bash
# 窗口1：下载秀人网
python xz_scraper.py --category "秀人网"

# 窗口2：下载语画界，限制100个
python xz_scraper.py --category "语画界" --max-albums 100

# 窗口3：下载爱尤物和模范学院
python xz_scraper.py --category "爱尤物,模范学院"
```

---

## 五、流程图

### 5.1 整体架构流程

```mermaid
graph TB
    subgraph 用户层
        A[用户执行命令] --> B{参数类型}
        B -->|交互模式| C[无参数运行]
        B -->|--scan| D[扫描模式]
        B -->|--category| E[指定分类模式]
    end
    
    subgraph 主程序[xz_scraper.py]
        C --> F[五阶段流程]
        D --> F
        E --> G[解析参数]
        G --> F
    end
    
    subgraph 核心模块
        F --> H[浏览器初始化]
        H --> I[分类扫描]
        I --> J[数量统计]
        J --> K[交互选择]
        K --> L[批量下载]
    end
    
    subgraph 代理模块[xz_proxy.py]
        L --> M{使用代理}
        M -->|是| N[代理池轮换]
        M -->|否| O[直接请求]
    end
    
    subgraph 输出层
        N --> P[下载图片]
        O --> P
        P --> Q[保存到本地]
        Q --> R[记录进度]
    end
    
    style F fill:#e1f5fe
    style H fill:#e1f5fe
    style P fill:#fff3e0
```

### 5.2 五阶段工作流程

```mermaid
flowchart TD
    A[开始] --> B[阶段1: 扫描分类]
    B --> C[访问首页提取导航链接]
    C --> D[阶段2: 统计数量]
    D --> E[逐个访问分类获取页码]
    E --> F[阶段3: 展示汇总]
    F --> G[显示分类表格]
    G --> H{运行模式}
    H -->|交互模式| I[用户交互选择]
    H -->|命令行模式| J[解析参数选择]
    I --> K[阶段4: 确认选择]
    J --> K
    K --> L[阶段5: 批量下载]
    L --> M[遍历分类页面]
    M --> N[遍历图集页面]
    N --> O[提取图片URL]
    O --> P[下载保存]
    P --> Q{还有更多?}
    Q -->|是| M
    Q -->|否| R[结束]
    
    style B fill:#e3f2fd
    style D fill:#e3f2fd
    style F fill:#e3f2fd
    style L fill:#fff3e0
```

### 5.3 图片下载流程

```mermaid
flowchart TD
    A[获取图集URL] --> B[访问图集页面]
    B --> C[滚动触发懒加载]
    C --> D[提取所有图片URL]
    D --> E{多页图集?}
    E -->|是| F[查找下一页按钮]
    F --> G[访问下一页]
    G --> C
    E -->|否| H[开始逐个下载]
    
    H --> I{遍历图片URL}
    I --> J{文件已存在?}
    J -->|是| K[跳过]
    J -->|否| L[下载图片]
    L --> M[添加延迟]
    M --> I
    
    I -->|全部完成| N[标记完成]
    N --> O[保存进度]
    
    style L fill:#fff3e0
    style O fill:#e8f5e9
```

### 5.4 断点续爬机制

```mermaid
flowchart LR
    A[程序启动] --> B{存在进度文件?}
    B -->|是| C[加载已完成列表]
    B -->|否| D[创建新进度文件]
    C --> E[遍历图集]
    D --> E
    
    E --> F{图集已完成?}
    F -->|是| G[跳过]
    F -->|否| H[下载图集]
    H --> I[成功]
    I --> J[记录到进度]
    J --> E
    
    G --> K{还有更多?}
    K -->|是| E
    K -->|否| L[程序结束]
    
    style C fill:#e8f5e9
    style J fill:#e8f5e9
```

---

## 六、配置文件说明

### 6.1 xz_config.py 完整配置项

```python
# ========== 路径配置 ==========
BASE_DIR = Path(__file__).parent          # 程序所在目录
OUTPUT_DIR = BASE_DIR / "data" / "xz_images"  # 图片输出目录
PROGRESS_FILE = BASE_DIR / "data" / "xz_progress.json"  # 进度文件

# ========== 目标网站 ==========
SITE_URL = "https://www.0xzn.com"

# ========== 浏览器配置 ==========
HEADLESS = False  # False=显示浏览器窗口，True=无头模式

# ========== 速度档位 ==========
SPEED_PROFILES = {
    "fast":   {"page_delay": (1, 3),   "img_delay": (0.3, 0.8)},
    "normal": {"page_delay": (3, 6),   "img_delay": (0.5, 1.5)},
    "slow":   {"page_delay": (5, 10),  "img_delay": (1, 3)},
    "safe":   {"page_delay": (8, 15),  "img_delay": (2, 5)},
}
DEFAULT_SPEED = "normal"

# ========== 安全限制 ==========
MAX_REQUESTS_PER_RUN = 500      # 单次运行最大请求数
MAX_CONSECUTIVE_ERRORS = 3      # 连续失败N次暂停
ERROR_PAUSE_DURATION = (60, 120)  # 出错暂停秒数
PAUSE_EVERY_N_ALBUMS = 20       # 每N个图集强制休息
PAUSE_DURATION = (30, 60)       # 强制休息秒数
REQUEST_TIMEOUT = 30000         # 页面加载超时（毫秒）
DOWNLOAD_TIMEOUT = 60           # 图片下载超时（秒）

# ========== 代理配置 ==========
PROXY = "http://127.0.0.1:7890"  # 单一代理
USE_PROXY_POOL = True             # 启用代理池
PROXY_FILE = "proxies.txt"        # 代理列表文件
PROXY_VALIDATE = False            # 启动时验证代理
PROXY_ROTATE_INTERVAL = 10        # 每N个图集切换代理

# ========== 下载配置 ==========
SKIP_EXISTING = True              # 跳过已下载文件
MAX_IMAGE_SIZE_MB = 50            # 单张图片大小上限
DOWNLOAD_CHUNK_SIZE = 256 * 1024  # 下载分块大小
```

### 6.2 常用配置调整

**调整速度（推荐）**：

如果被检测到，建议调整为`safe`档位，修改`DEFAULT_SPEED = "safe"`。

**调整代理**：

如果没有代理软件，修改`USE_PROXY_POOL = False`和`PROXY = ""`。

**调整下载量**：

修改`MAX_REQUESTS_PER_RUN`可调整单次运行的最大请求数。

---

## 七、环境依赖

### 7.1 Python环境

```bash
# Python版本要求
Python 3.8 或更高版本

# 必需安装的库
pip install requests
pip install playwright
playwright install chromium  # 安装Chromium浏览器
```

### 7.2 外部依赖

**Playwright浏览器**：必须运行`playwright install chromium`安装Chromium，这是浏览器自动化的核心。

**代理软件**（可选）：如需使用代理，需要先启动代理软件（Clash、SS、V2ray等）。

### 7.3 代理配置示例

**Clash for Windows**：

```bash
# 默认HTTP端口
PROXY = "http://127.0.0.1:7890"
```

**V2rayN**：

```bash
# 默认HTTP端口
PROXY = "http://127.0.0.1:10809"
```

**Shadowsocks**：

```bash
# 默认SOCKS5端口
PROXY = "socks5://127.0.0.1:1080"
```

### 7.4 代理池配置（进阶）

在`proxies.txt`文件中每行添加一个代理：

```text
# 格式1: 简单代理
http://127.0.0.1:7890

# 格式2: 带认证
http://username:password@host:port

# 格式3: SOCKS5
socks5://127.0.0.1:1080
```

---

## 八、问题汇总与解决

### 8.1 严重问题：缺少依赖模块 ❌

**问题描述**：

程序第47-48行尝试导入不存在的模块：

```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "评论"))
from utils.stealth import create_stealth_context, STEALTH_JS, BROWSER_ARGS
```

代码注释说明该模块应位于`E:\integrity\7爬虫\评论\utils\stealth.py`，但该路径实际上不存在。

**问题影响**：

程序运行时会报`ModuleNotFoundError`错误，无法启动。

**解决方案**：

需要创建缺失的stealth模块，或修改导入路径。具体解决方案需根据实际需求确定。

### 8.2 常见问题

**问题：浏览器启动失败**

表现：提示`playwright`相关错误。

解决：运行`playwright install chromium`安装浏览器。

**问题：代理连接失败**

表现：提示代理无法连接。

解决：检查代理软件是否已启动，端口是否正确。

**问题：图片下载失败**

表现：部分图片下载失败或超时。

解决：网络不稳定可能导致，降低速度档位可改善。

**问题：被目标网站检测**

表现：页面返回异常或无法访问。

解决：使用代理池轮换IP，或使用`--speed safe`降低速度。

---

## 九、输出示例

### 9.1 目录结构

```
xz_图片\data\xz_images\
├── cosplay\
│   ├── [N0.第12016期]Shika小鹿鹿 逸仙 [9P]\
│   │   ├── 001.jpg
│   │   ├── 002.jpg
│   │   └── ...
│   └── ...
├── 机构美女图片\
│   └── ...
└── 网红美女\
    └── ...
```

### 9.2 进度文件格式

```json
{
  "completed_albums": [
    "https://www.0xzn.com/xxx/123.html",
    "https://www.0xzn.com/xxx/456.html"
  ],
  "failed_albums": [
    "https://www.0xzn.com/xxx/789.html"
  ]
}
```

---

## 十、命令行参数汇总

| 参数 | 说明 | 示例 |
|------|------|------|
| --speed | 速度档位 | --speed safe |
| --headless | 无头模式 | --headless |
| --scan | 只扫描不下载 | --scan |
| --category | 指定分类 | --category "秀人网" |
| --max-albums | 每分类上限 | --max-albums 100 |
| --proxy | 指定代理 | --proxy "http://..." |
| --reset-progress | 清除进度 | --reset-progress |

---

## 十一、注意事项

### 11.1 使用限制

本工具仅供个人学习研究使用，请勿用于商业目的或大规模采集。批量采集可能对目标网站造成压力，也可能违反网站的服务条款。采集的内容请勿用于侵权用途。

### 11.2 建议

首次使用时建议使用`--scan`参数查看分类信息。使用代理可以有效防止IP被封。建议使用`normal`或`slow`速度档位。大规模采集时使用多开并行，每个CMD窗口运行不同分类。

### 11.3 数据存储

图片默认保存在`xz_图片\data\xz_images\`目录下。进度文件保存在`xz_图片\data\`目录下。定期备份进度文件以防丢失。

---

*文档版本：1.0*
*更新时间：2026-02-19*
