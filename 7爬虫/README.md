# B站爬虫

通过 B站公开 API 实现搜索、视频详情、评论抓取，以及封面图和视频下载。

## 文件结构

```
e:\爬虫\
├── bilibili_client.py      # 共享客户端 (API封装 + 反封策略)
├── bilibili_search.py      # 搜索脚本 (搜索 + 详情 + 评论)
├── bilibili_download.py    # 下载脚本 (封面图 + 视频)
├── README.md
└── data/                   # 所有抓取结果 (自动生成)
    └── 20260131_153000_英语学习/   # 每次搜索一个独立文件夹
        ├── search.csv      # 搜索结果列表
        ├── videos.json     # 视频详情 + 评论
        └── media/          # 下载的封面图和视频
            ├── BVxxx.jpg
            └── BVxxx.mp4
```

每次搜索自动创建 `时间戳_关键词` 文件夹，保证唯一性。

## 三个脚本

### 1. bilibili_client.py — 共享客户端

所有 API 调用和反封策略都封装在 `BilibiliClient` 类中，被搜索和下载脚本共同使用。

**封装的 API:**

| 方法 | API | 说明 |
|---|---|---|
| `search_video()` | `/x/web-interface/search/type` | 搜索视频 |
| `get_video_info()` | `/x/web-interface/view` | 视频详情 |
| `get_comments()` | `/x/v2/reply/main` | 评论 |
| `get_popular()` | `/x/web-interface/popular` | 全站热门 |
| `get_play_url()` | `/x/player/playurl` | 视频流地址 |
| `download_file()` | 直接下载 | 带进度条的文件下载 |

**反封策略:**

| 策略 | 实现 |
|---|---|
| 随机延迟 | 每次请求间隔 1~3 秒，模拟人类操作 |
| User-Agent 池 | 5 个不同浏览器指纹，每 10 次请求轮换 |
| 匿名 Cookie | 启动时自动访问 bilibili.com 获取 buvid3 |
| 请求限速 | 单次运行最多 60 个 API 请求 |
| 失败重试 | 指数退避重试 2 次（间隔 1s、2s），API timeout 15 秒 |
| 安全下载 | 下载到 .tmp 临时文件，完成后 rename，中断不残留 |
| 文件大小限制 | 视频超过 100MB 自动跳过 |

### 2. bilibili_search.py — 搜索脚本

搜索关键词，获取视频详情和评论，保存到独立文件夹。

```bat
set PY=E:\anaconda_laptop\envs\torch_cu111\python.exe

:: 默认搜索 "Python爬虫"
%PY% bilibili_search.py

:: 自定义关键词
%PY% bilibili_search.py "英语学习"
```

**流程:**
```
搜索关键词 → 返回 10 条视频
  → 逐个获取视频详情 (标题/播放量/点赞/标签...)
  → 逐个获取热门评论 (top 5)
  → 保存 search.csv + videos.json
```

### 3. bilibili_download.py — 下载脚本

下载视频的封面图和 360p 视频文件。支持两种用法:

```bat
:: 方式1: 指定 BV 号
%PY% bilibili_download.py BV1xxx BV2xxx

:: 方式2: 指定搜索结果目录 (自动读取 videos.json 中的 BV 号)
%PY% bilibili_download.py data\20260131_153000_英语学习\
```

方式2 会把文件下载到该目录的 `media/` 子文件夹中。

## 原理

B站是前后端分离架构，页面用 Vue 渲染，数据全走 `api.bilibili.com` 的 REST API。
用 F12 → Network → Fetch/XHR 就能看到所有 API 请求。

**关键点:**

- 需要先访问 `bilibili.com` 拿到匿名 Cookie（`buvid3`），否则搜索接口返回 412
- 下载图片/视频必须带 `Referer: https://www.bilibili.com/`，否则 403（防盗链）
- 未登录只能拿 360p 视频，720p 及以上需要登录 Cookie
- 高清视频是音视频分离的 DASH 格式，需要 ffmpeg 合并；本脚本用 `fnval=1` 请求整合的 mp4 流
- 超过 100MB 的视频自动跳过

## 典型工作流

```bat
set PY=E:\anaconda_laptop\envs\torch_cu111\python.exe

:: 1. 搜索
%PY% bilibili_search.py "英语学习"

:: 2. 查看结果 (打开 CSV 或 JSON)
:: data\20260131_153000_英语学习\search.csv

:: 3. 下载搜索结果中的视频
%PY% bilibili_download.py data\20260131_153000_英语学习\
```

## 依赖

```bat
%PY% -m pip install requests
```

只需要 requests，无其他依赖。
