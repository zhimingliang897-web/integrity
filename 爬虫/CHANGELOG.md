# 版本迭代日志

## v4 — 2026-01-31 (当前)

代码审查，修复 P0/P1 问题。

- 修复: `get_video_info` 返回 cid，下载时不再重复请求 `/view` 接口
- 修复: 下载改用 `.tmp` 临时文件，完成后 rename，中断时自动清理
- 优化: API timeout 从 10s 提升到 15s
- 优化: `_get` 增加指数退避重试（默认重试 2 次，间隔 1s/2s）
- 清理: 删除旧 `bilibili_demo.py`
- 新增: REVIEW.md 代码审查文档、CHANGELOG.md 版本日志

## v3 — 2026-01-31

拆分为三个独立脚本，增加反封策略。

- 拆分: `bilibili_client.py` (共享客户端) + `bilibili_search.py` (搜索) + `bilibili_download.py` (下载)
- 反封: UA 池轮换、随机延迟 1-3s、单次请求上限 60、文件大小上限 100MB
- 搜索结果按 `时间戳_关键词` 独立文件夹存储
- 下载脚本支持 BV 号和搜索目录两种输入方式
- 删除旧 `bilibili_demo.py`

## v2 — 2026-01-31

在 demo 基础上增加分类保存和媒体下载。

- 数据按类型分目录: search/ video/ comment/ popular/ cover/ media/
- 新增封面图下载（带 Referer 防盗链）
- 新增 360p 视频下载（fnval=1 请求 mp4 流，跳过 >50MB）
- 新增 README

## v1 — 2026-01-31

初始 demo，单文件 `bilibili_demo.py`。

- 搜索视频、获取详情、评论、热门榜单
- 解决 412 问题（启动时获取匿名 Cookie）
- Windows GBK 终端兼容（替换 Unicode 特殊字符）
