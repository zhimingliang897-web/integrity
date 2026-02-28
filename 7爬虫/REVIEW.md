# 代码审查 & 优化建议

## 一、已修复的问题

### ~~1. get_video_cid 重复请求~~ (v4 已修复)

`get_video_info` 返回值已包含 `cid` 字段，下载时直接用 `info["cid"]`，不再单独调 `get_video_cid`。

### ~~2. 下载中断无法续传~~ (v4 已修复)

`download_file` 现在先下载到 `.tmp` 临时文件，完成后 rename。中断时自动清理临时文件，不会残留不完整文件。

### ~~3. 请求超时偏短~~ (v4 已修复)

API timeout 从 10 秒提升到 15 秒。

### ~~4. 无重试机制~~ (v4 已修复)

`_get` 方法增加指数退避重试（默认 2 次），失败后等待 1s、2s 再重试。

---

## 二、待处理问题

### 1. 评论全部返回 0 条

搜索脚本里对每个视频都获取了评论，但实测很多返回 0 条。
原因：B站评论接口 `/x/v2/reply/main` 对匿名请求限制较严，部分视频需要登录才能获取评论。
当前代码没有提示这个限制，用户可能以为是 bug。

**建议:** 在输出中提示未登录限制，或增加可选的 Cookie 登录支持。

### 2. 搜索结果无去重

多次搜索同一关键词会创建多个文件夹（时间戳不同），数据完全重复。
虽然时间戳保证唯一性，但积累后会浪费空间。

**建议:** 搜索前检查最近是否有相同关键词的结果（比如同一天内），提示用户是否跳过。

---

## 三、后续优化建议

### 1. 日志系统 (P2)

当前用 `print()` 输出所有信息，没有日志级别区分，也无法回溯。

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bilibili.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("bilibili")
```

### 2. 配置文件 (P2)

当前所有参数硬编码在代码里。可以抽出一个 `config.json`：

```json
{
  "delay_min": 1.0,
  "delay_max": 3.0,
  "max_requests": 60,
  "max_download_mb": 100,
  "search_page_size": 10,
  "comment_count": 5,
  "api_timeout": 15
}
```

### 3. 登录 Cookie 支持 (P3)

当前只能匿名访问，视频最高 360p，部分评论拿不到。
支持从浏览器导入 Cookie 可以解锁更多内容。

### 4. 并发下载 (P3)

封面图体积小，可以用线程池 3 并发下载。视频不建议并发太多。

### 5. 数据分析脚本 (P3)

加一个 `bilibili_analyze.py`：统计播放量/点赞量分布，生成排行。

---

## 四、优先级总览

| 优先级 | 改动 | 状态 |
|:---:|---|:---:|
| P0 | 修复 cid 重复请求 | v4 已修复 |
| P0 | 下载用临时文件 | v4 已修复 |
| P1 | 加重试机制 (指数退避) | v4 已修复 |
| P1 | 提升 API timeout 到 15s | v4 已修复 |
| P2 | 配置文件 | 待做 |
| P2 | 日志系统 | 待做 |
| P3 | Cookie 登录 | 待做 |
| P3 | 并发下载 | 待做 |
| P3 | 数据分析 | 待做 |
