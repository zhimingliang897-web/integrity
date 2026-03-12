# 21视频下载器

一个强大的本地视频下载工具，支持B站（bilibili）、NTU课程网站等多种视频平台下载，无时间限制，无数量限制。

## 功能特性

- ✅ **Web图形界面** - 可视化操作，无需命令行
- ✅ **Chrome浏览器插件** - 一键发送当前页面视频到下载器
- ✅ 支持B站视频下载（最高支持1080P+）
- ✅ 支持NTU课程网站视频下载
- ✅ 支持绝大多数主流视频网站
- ✅ 无时间限制（突破插件2小时限制）
- ✅ 无数量限制（支持批量下载）
- ✅ 自动合并视频和音频流
- ✅ 支持Cookie认证下载高清视频
- ✅ 实时显示下载进度

## 项目结构

```
21视频下载/
├── core/                   # 核心下载模块
│   ├── __init__.py
│   └── downloader.py
├── web/                    # Web GUI服务
│   ├── app.py              # FastAPI后端
│   ├── static/             # 静态资源
│   └── templates/          # HTML模板
├── extension/              # Chrome浏览器插件
│   ├── manifest.json
│   ├── popup.html/js
│   ├── background.js
│   ├── content.js
│   └── icons/
├── downloads/              # 视频下载保存目录
├── main.py                # CLI主程序（备用）
├── requirements.txt        # Python依赖
├── environment.yml        # Conda环境配置
└── README.md              # 本文档
```

## 快速开始

### 方式一：使用Web界面（推荐）

```bash
# 1. 进入项目目录
cd 21视频下载

# 2. 创建并激活Conda环境
conda env create -f environment.yml
conda activate 21_video_env

# 3. 安装系统依赖
# macOS:
brew install ffmpeg

# 4. 启动Web服务
python web/app.py
```

启动成功后，浏览器访问：**http://127.0.0.1:8000**

### 方式二：使用命令行

```bash
# 激活环境后
python main.py
```

## Cookie配置（重要！）

部分视频网站（如B站高清视频、NTU课程网站）需要登录才能下载。

### Web界面配置

1. 打开 http://127.0.0.1:8000
2. 在左侧"配置"面板中粘贴Cookie内容
3. 点击"保存配置"

### 获取Cookie文件

1. 安装浏览器插件：**Get cookies.txt LOCALLY** 或 **Cookie-Editor**
2. 登录需要下载视频的网站（B站或NTU）
3. 导出Cookie（选择Netscape格式）
4. 保存为 `cookies.txt` 或直接粘贴到Web界面

## Chrome浏览器插件安装

### 1. 生成插件图标

插件需要PNG格式图标，运行以下命令生成：

```bash
# 在项目目录运行
python -c "
from PIL import Image, ImageDraw
import os

sizes = [16, 48, 128]
colors = [(102, 126, 234), (118, 75, 162)]

for size in sizes:
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 画渐变背景圆形
    r = size // 2
    for i in range(r):
        ratio = i / r
        color = tuple(int(colors[0][j] + (colors[1][j] - colors[0][j]) * ratio) for j in range(3))
        draw.ellipse([i, i, size-i, size-i], fill=color + (255,))
    
    # 画下载图标
    cx, cy = size // 2, size // 2
    padding = size // 5
    points = [
        (cx - padding, cy - padding//2),
        (cx - padding, cy + padding),
        (cx + padding, cy + padding),
        (cx + padding, cy - padding//2)
    ]
    draw.polygon(points, fill=(255, 255, 255, 255))
    
    img.save(f'extension/icons/icon{size}.png')

print('图标生成完成！')
"
```

如果提示没有PIL库，请先安装：
```bash
pip install Pillow
```

### 2. 安装插件

1. 打开Chrome浏览器，访问 `chrome://extensions/`
2. 开启右上角的"开发者模式"
3. 点击"加载已解压的扩展程序"
4. 选择项目中的 `extension` 文件夹

### 3. 使用插件

1. 确保Web服务正在运行（`python web/app.py`）
2. 打开B站或NTU课程视频页面
3. 点击浏览器右上角的插件图标
4. 点击"发送到下载器"

或在视频页面直接点击右下角出现的悬浮按钮。

## 支持的网站

| 网站 | 支持情况 | 说明 |
|------|----------|------|
| B站 (bilibili) | ✅ 完全支持 | 支持大会员1080P+ |
| NTU课程网站 | ✅ 支持 | 需要Cookie认证 |
| YouTube | ✅ 支持 | 需要Cookie（如需高清） |
| 通用HLS流 | ✅ 支持 | .m3u8链接 |
| 其他网站 | ✅ 大部分支持 | yt-dlp支持900+网站 |

## API接口

如果需要自定义集成，可以直接调用API：

```bash
# 健康检查
curl http://127.0.0.1:8000/health

# 添加下载任务
curl -X POST http://127.0.0.1:8000/api/add_task \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.bilibili.com/video/xxx"}'

# 获取所有任务
curl http://127.0.0.1:8000/api/tasks

# 取消任务
curl -X POST http://127.0.0.1:8000/api/tasks/{task_id}/cancel
```

## 常见问题

### Q: 下载失败，提示"Unable to extract data"

A: 可能是网站更新了反爬措施，尝试更新yt-dlp：
```bash
pip install --upgrade yt-dlp
```

### Q: B站视频只有480P画质

A: 需要登录B站账号并导出Cookie，具体见上文"Cookie配置"部分。

### Q: NTU视频下载失败

A: 
1. 确认已正确配置cookies.txt
2. 确认Cookie未过期（重新登录导出）
3. 确认有访问该课程的权限

###Q: 插件提示"服务离线"

A: 请确保Web服务正在运行：
```bash
python web/app.py
```

### Q: 下载速度慢

A: 
1. 可以尝试使用代理
2. 某些视频网站本身有速度限制

## 技术原理

本项目基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 开发：

- yt-dlp 是 youtube-dl 的强大分支
- 支持超过900个视频网站
- 自动处理视频/音频流合并
- 支持Cookie注入认证

Web界面使用 **FastAPI** + **TailwindCSS** 构建。

## 许可证

仅供个人学习使用，请遵守相关网站的服务条款。

## 更新日志

### v1.1 (2026-03-12)
- 新增Web图形界面
- 新增Chrome浏览器插件
- 支持一键发送页面视频到下载器
- 实时显示下载进度

### v1.0 (2026-03-12)
- 初始版本发布
- 支持B站、NTU等视频网站
- 批量下载功能
- Cookie认证支持
