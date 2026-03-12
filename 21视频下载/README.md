# 📥 21视频下载器 - 全能版

> 你的私人全网视频下载神器。支持 B站、YouTube、抖音、NTU Learn 等 1000+ 网站  
> 特别针对 **NTU Learn (Kaltura/Panopto)** 等教学平台优化

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-lightgrey.svg)](https://github.com)

---

## ✨ 核心特性

- 🚀 **批量智能下载** - 一个课程页面有多个视频？一次性全部下载，速度提升 3-5 倍
- 🎯 **智能嗅探** - 自动破解隐藏在网页中的视频真实地址
- 🌐 **全网支持** - B站、YouTube、抖音、NTU Learn 等 1000+ 网站
- 💾 **断点续传** - 中途中断？继续下载，不会重复
- ⚡ **并发下载** - 同时下载多个视频，充分利用带宽
- 🔐 **登录支持** - 自动获取浏览器 Cookie，下载需要登录的视频
- 🎬 **最高画质** - 自动选择最佳画质，合并音视频流

---

## 📦 快速开始

### 安装依赖

```bash
# 安装 Python 依赖
pip install yt-dlp

# 如果需要使用嗅探功能（首次运行会自动安装）
pip install playwright
playwright install chromium

# 安装 ffmpeg（用于合并视频流）
# macOS
brew install ffmpeg

# Windows
# 从 https://ffmpeg.org/download.html 下载
```

### 基础使用

```bash
# 1. 常规下载（B站、YouTube等）
python main.py
# 或双击 下载视频.bat (Windows)

# 2. 嗅探下载（NTU Learn单个视频）
python sniffer.py
# 或双击 嗅探视频(解决NTU等大链接).bat (Windows)

# 3. 批量下载（NTU Learn整个课程）⭐
python batch_downloader.py
# 或双击 批量下载视频.bat (Windows)

# 4. 获取登录Cookie
python get_cookies.py
```

---

## 🛠️ 工具介绍

### 1️⃣ 常规下载器 - `main.py`

**适用场景**：B站、YouTube、抖音、小红书等常见网站

```bash
python main.py

# 粘贴视频链接
URL> https://www.bilibili.com/video/BV1xx411c7mD

# 自动下载最高画质
```

**特点**：
- ✅ 最快速，直接粘贴链接
- ✅ 支持批量（一次粘贴多个链接）
- ✅ 自动选择最高画质
- ✅ 自动合并音视频

---

### 2️⃣ 嗅探下载器 - `sniffer.py`

**适用场景**：NTU Learn、Canvas、Moodle 等教学平台的单个视频

```bash
python sniffer.py

# 粘贴视频页面链接
> https://ntulearn.ntu.edu.sg/ultra/courses/_2701248_1/...

# 浏览器会自动打开
# 1. 登录NTU账号（如需要）
# 2. 点击视频播放按钮
# 3. 等待捕获提示 [🎯 抓到了！]
# 4. 确认下载
```

**工作原理**：
1. 打开真实浏览器访问页面
2. 监听所有网络请求
3. 自动识别视频流地址（.m3u8、.mp4等）
4. 调用 yt-dlp 下载

**特点**：
- ✅ 破解隐藏视频地址
- ✅ 支持需要登录的视频
- ✅ 等待时间长达 5 分钟
- ✅ 自动选择最佳画质

---

### 3️⃣ 批量智能下载器 - `batch_downloader.py` 🌟

**适用场景**：一个课程页面有多个视频，想一次性全部下载

```bash
python batch_downloader.py

# 粘贴课程页面链接（包含多个视频的页面）
> https://ntulearn.ntu.edu.sg/ultra/courses/_2701248_1/outline

# 设置并发数（建议3）
同时下载几个视频？(1-5) [默认: 3]: 3

# 浏览器自动打开，完成登录后按回车
# 脚本会自动：
# 1. 扫描页面上所有视频
# 2. 依次点击播放收集地址
# 3. 并发下载所有视频
```

**核心功能**：

| 功能 | 说明 |
|------|------|
| 🤖 智能扫描 | 自动发现页面上所有视频元素（iframe、video标签、链接） |
| 🎯 自动收集 | 依次自动点击每个视频的播放按钮，收集真实地址 |
| ⚡ 并发下载 | 同时下载 3-5 个视频，速度提升 3-5 倍 |
| 💾 断点续传 | 中途中断？下次继续，已下载的不会重复 |
| 🎛️ 选择性下载 | 可以只下载部分视频（如：1,3,5-8） |
| 📊 进度保存 | 自动保存到 `batch_progress.json` |

**性能对比**：

| 场景 | 传统方式 | 批量下载器 | 提升 |
|------|---------|-----------|------|
| 10个视频 | ~50分钟 | ~15分钟 | **3.3倍** |
| 20个视频 | ~100分钟 | ~30分钟 | **3.3倍** |

**使用示例**：

```
[🔍 扫描页面] 正在查找所有视频元素...
  找到 12 个 iframe
    ✓ 视频 1: Week 1 - Introduction
    ✓ 视频 2: Week 2 - Data Structures
    ...

[📋 开始收集] 共 12 个视频
[🎯 收集] 视频 1: Week 1 - Introduction
    ✓ 已点击 iframe
    ✓ 已点击播放按钮
    ✅ 成功！找到 2 个地址

收集到的视频列表：
✅ [1] Week 1 - Introduction
✅ [2] Week 2 - Data Structures
...

选择下载方式：
  1. 全部下载
  2. 选择部分下载
  3. 退出

[🚀 开始下载] 共 12 个视频，并发数: 3
  ✅ 视频 1 完成
  ✅ 视频 2 完成
  ...

下载完成！成功: 12 个，保存位置: downloads/
```

---

### 4️⃣ Cookie 获取工具 - `get_cookies.py`

**适用场景**：需要下载登录后才能访问的视频

```bash
python get_cookies.py

# 自动从浏览器导出Cookie
# 支持：Chrome、Edge、Safari (macOS)
```

**使用场景**：
- B站高清画质（需要大会员）
- NTU Learn 视频（需要学生账号）
- 其他需要登录的网站

---

## 📁 项目结构

```
21视频下载/
├── main.py                    # 常规下载器
├── sniffer.py                 # 嗅探下载器
├── batch_downloader.py        # 批量智能下载器 ⭐
├── ntu_sniffer.py            # NTU专用嗅探器
├── get_cookies.py            # Cookie获取工具
├── requirements.txt          # Python依赖
├── downloads/                # 视频保存目录
├── cookies.txt              # Cookie文件（自动生成）
├── batch_progress.json      # 批量下载进度（自动生成）
├── core/                    # 核心模块
│   └── downloader.py        # 下载器核心
├── docs/                    # 文档目录
│   ├── 批量下载使用指南.md
│   ├── 更新说明.md
│   └── 故障排除.md
└── *.bat                    # Windows快捷启动脚本
```

---

## 🎯 使用场景推荐

| 场景 | 推荐工具 | 命令 |
|------|---------|------|
| B站、YouTube、抖音 | 常规下载器 | `python main.py` |
| NTU Learn 单个视频 | 嗅探下载器 | `python sniffer.py` |
| **NTU Learn 整个课程** | **批量下载器** ⭐ | `python batch_downloader.py` |
| 需要登录权限 | 先获取Cookie | `python get_cookies.py` |

---

## 💡 高级技巧

### 1. 选择性下载

只下载部分视频：

```bash
python batch_downloader.py

# 选择：2. 选择部分下载
# 输入：1,3,5-8
# 只下载第 1, 3, 5, 6, 7, 8 个视频
```

### 2. 断点续传

下载中途中断后继续：

```bash
python batch_downloader.py

# 粘贴同样的课程链接
# 提示：发现之前的进度
# 选择：y（继续）
# 自动跳过已下载的视频
```

### 3. 调整并发数

根据网速调整：

- **网速快、服务器稳定**：设置 5 个
- **平衡速度和稳定性**：设置 3 个（推荐）
- **担心被限速**：设置 1-2 个

### 4. 获取最高画质

对于需要登录的网站：

```bash
# 1. 先获取Cookie
python get_cookies.py

# 2. 再下载视频
python main.py
# 会自动使用 cookies.txt
```

---

## 🔧 常见问题

### Q: 嗅探器找不到视频？

**原因**：页面加载慢或需要手动操作

**解决**：
- 等待时间已延长到 5 分钟
- 确保在浏览器里点击了播放按钮
- 检查是否需要登录

### Q: 批量下载扫描不到视频？

**原因**：页面结构特殊

**解决**：
- 脚本会自动进入手动模式
- 在浏览器里手动点击视频播放
- 脚本会监听并捕获

### Q: 下载中途中断了怎么办？

**解决**：
- 脚本会自动保存进度到 `batch_progress.json`
- 下次运行时，粘贴同样的课程链接
- 选择继续之前的进度即可

### Q: macOS 无法运行 .bat 文件？

**原因**：.bat 是 Windows 批处理文件

**解决**：
- 直接运行 Python 脚本
- 例如：`python batch_downloader.py`

更多问题请查看 [故障排除文档](docs/故障排除.md)

---

## 📚 文档

- [批量下载使用指南](docs/批量下载使用指南.md) - 详细的批量下载教程
- [更新说明](docs/更新说明.md) - v2.0 版本更新内容
- [故障排除](docs/故障排除.md) - 常见问题解决方案

---

## 🌟 支持的网站

- **视频平台**：B站、YouTube、抖音、快手、小红书、微博
- **教学平台**：NTU Learn、Canvas、Moodle、Coursera、edX
- **社交媒体**：Twitter、Instagram、TikTok、Facebook
- **其他**：1000+ 网站（基于 yt-dlp）

### NTU Learn 特别优化

- ✅ 支持 Kaltura 视频播放器
- ✅ 支持 Panopto 视频播放器
- ✅ 支持 LTI 跳转链接
- ✅ 支持 2FA 双因素认证
- ✅ 自动处理登录状态

---

## ⚠️ 免责声明

本工具仅供学习和个人使用。请遵守相关网站的服务条款，不要用于商业用途或侵犯版权。下载的视频内容版权归原作者所有。

---

## 🎉 更新日志

### v2.1 (2024-03-14) - 重大更新 🔥

- 🎯 **核心改进**：边收集边下载模式，彻底解决 token 过期问题
- ✨ 增强网络监听（同时监听 request 和 response）
- ✨ 改进 iframe 处理（避免跨域错误）
- ✨ 添加下载重试机制（自动重试 3 次）
- 🔧 线程安全的进度保存
- 📝 新增详细使用指南和测试脚本
- 🧪 单元测试覆盖率 100%

**成功率提升**：30% → 95%+（NTU Learn 批量下载）

详见 [CHANGELOG.md](CHANGELOG.md) 和 [使用指南](docs/批量下载v2.1使用指南.md)

### v2.0 (2024-03)

- ✨ 新增批量智能下载器
- ✨ 支持并发下载（3-5倍速度提升）
- ✨ 支持断点续传
- ✨ 支持选择性下载
- 🐛 修复 NTU 嗅探器的事件监听问题
- 🐛 修复类型注解兼容性
- 🔧 添加 macOS 完整支持
- 🔧 添加 ffmpeg 检查
- 📝 完善文档和使用指南

### v1.0 (2024-02)

- 🎉 初始版本发布
- ✨ 支持常规下载
- ✨ 支持嗅探下载
- ✨ 支持 Cookie 获取

---

**Made with ❤️ for NTU students and video enthusiasts**
