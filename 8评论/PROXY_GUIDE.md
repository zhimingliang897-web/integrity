# 🛡️ IP代理使用指南

防止抓取时被封IP的完整解决方案。

---

## 📋 目录

- [为什么需要代理](#为什么需要代理)
- [快速开始](#快速开始)
- [代理配置](#代理配置)
- [使用方法](#使用方法)
- [代理服务推荐](#代理服务推荐)
- [常见问题](#常见问题)

---

## 🤔 为什么需要代理

在抓取评论时，平台可能会检测到：
- ✅ **同一IP短时间内频繁请求** → 触发风控，封禁IP
- ✅ **浏览器指纹识别** → 识别出自动化工具
- ✅ **Cookie失效** → 需要重新登录

**解决方案：**
1. **代理IP** - 隐藏真实IP，防止被封（本指南）
2. **浏览器反检测** - 隐藏自动化特征（已集成在 `stealth.py`）
3. **速度控制** - 降低请求频率（使用 `speed` 参数）

---

## 🚀 快速开始

### 1. 准备代理

#### 方式A：本地代理（推荐测试）

如果你有 **Clash、V2Ray、Shadowsocks** 等工具：

```bash
# Clash 默认端口
http://127.0.0.1:7890

# V2Ray SOCKS5
socks5://127.0.0.1:1080
```

#### 方式B：付费代理（推荐生产）

购买代理服务（见下方推荐），获取代理地址：

```bash
# 快代理
http://订单号:密钥@proxy.kuaidaili.com:端口

# 阿布云
http://用户名:密码@proxy.abuyun.com:9020
```

### 2. 创建代理配置文件

复制模板文件：

```bash
cp proxies.txt.example proxies.txt
```

编辑 `proxies.txt`，添加你的代理：

```txt
# 每行一个代理
http://127.0.0.1:7890
http://username:password@proxy.example.com:8080
socks5://127.0.0.1:1080
```

### 3. 使用代理抓取

```python
from utils.proxy import ProxyPool
from scrapers.douyin import DouyinScraper

# 创建代理池
pool = ProxyPool()
pool.load_from_file("proxies.txt")

# 可选：验证代理可用性
pool.validate_all()

# 使用代理抓取
scraper = DouyinScraper(
    cookie="你的Cookie",
    speed="normal",
    proxy_pool=pool  # 传入代理池
)

comments = scraper.fetch_comments(
    url="https://www.douyin.com/video/7xxxxxxxxxxxxxxxxx",
    max_count=100
)
```

---

## ⚙️ 代理配置

### 支持的代理格式

| 类型 | 格式 | 示例 |
|------|------|------|
| HTTP | `http://host:port` | `http://127.0.0.1:7890` |
| HTTPS | `https://host:port` | `https://proxy.example.com:8080` |
| SOCKS5 | `socks5://host:port` | `socks5://127.0.0.1:1080` |
| 带认证的HTTP | `http://user:pass@host:port` | `http://admin:123456@proxy.com:8080` |
| 带认证的SOCKS5 | `socks5://user:pass@host:port` | `socks5://admin:123456@proxy.com:1080` |

### 配置文件说明

`proxies.txt` 文件格式：

```txt
# 这是注释，以 # 开头

# HTTP 代理
http://127.0.0.1:7890

# 带用户名密码的代理
http://username:password@proxy.example.com:8080

# SOCKS5 代理
socks5://127.0.0.1:1080

# 空行会被忽略

```

---

## 💡 使用方法

### 方法1：从文件加载（推荐）

```python
from utils.proxy import ProxyPool
from scrapers.douyin import DouyinScraper

pool = ProxyPool()
pool.load_from_file("proxies.txt")
pool.validate_all()  # 验证代理可用性

scraper = DouyinScraper(cookie="...", proxy_pool=pool)
comments = scraper.fetch_comments(url, max_count=100)
```

### 方法2：代码中直接定义

```python
from utils.proxy import ProxyPool

proxies = [
    "http://127.0.0.1:7890",
    "http://user:pass@proxy.com:8080",
]

pool = ProxyPool(proxies)
scraper = DouyinScraper(cookie="...", proxy_pool=pool)
```

### 方法3：全局代理池

```python
from utils.proxy import init_global_proxy_pool, get_global_proxy_pool

# 初始化（只需一次）
init_global_proxy_pool(proxy_file="proxies.txt", validate=True)

# 在任何地方使用
pool = get_global_proxy_pool()
scraper = DouyinScraper(cookie="...", proxy_pool=pool)
```

### 方法4：代理轮换器

定期切换代理，避免单个IP频繁请求：

```python
from utils.proxy import ProxyPool, ProxyRotator

pool = ProxyPool()
pool.load_from_file("proxies.txt")

# 每5次请求切换一次代理
rotator = ProxyRotator(pool, rotate_interval=5)

for url in urls:
    proxy = rotator.get_proxy()
    # 使用 proxy 抓取
```

### 方法5：不使用代理

```python
# 不传 proxy_pool 参数，直接抓取
scraper = DouyinScraper(cookie="...")
comments = scraper.fetch_comments(url, max_count=100)
```

---

## 🏆 代理服务推荐

### 付费代理（稳定可靠）

| 服务商 | 特点 | 价格参考 | 推荐度 |
|--------|------|----------|--------|
| **[快代理](https://www.kuaidaili.com/)** | IP池大、稳定性高 | ¥5/天起 | ⭐⭐⭐⭐⭐ |
| **[阿布云](https://www.abuyun.com/)** | 动态代理、按流量计费 | ¥0.6/MB | ⭐⭐⭐⭐ |
| **[芝麻代理](https://www.zhimaruanjian.com/)** | 性价比高 | ¥3/天起 | ⭐⭐⭐⭐ |
| **[讯代理](https://www.xdaili.cn/)** | 高匿代理 | ¥5/天起 | ⭐⭐⭐ |

### 免费代理（仅供测试）

⚠️ **警告：免费代理质量差、速度慢、成功率低**

抓取免费代理：

```python
from utils.proxy import ProxyPool

pool = ProxyPool()
pool.fetch_free_proxies(count=10)  # 抓取10个免费代理
pool.validate_all()  # 验证可用性（大多不可用）

print(f"可用代理数: {len(pool)}")
```

**免费代理来源：**
- https://www.sslproxies.org/
- https://free-proxy-list.net/
- https://www.proxy-list.download/

---

## ❓ 常见问题

### Q1: 代理连接失败怎么办？

**A:** 检查以下几点：
1. 代理地址格式是否正确
2. 代理服务是否正常运行（如 Clash 是否开启）
3. 代理端口是否正确
4. 网络是否能访问代理服务器

测试代理：

```python
pool = ProxyPool()
pool.add_proxy("http://127.0.0.1:7890")
pool.validate_all()  # 自动测试代理可用性
```

### Q2: 使用代理后还是被封IP？

**A:** 可能原因：
1. **代理质量差** - 使用付费代理
2. **请求频率过高** - 调整 `speed` 参数：
   ```python
   scraper = DouyinScraper(speed="safe")  # 使用最慢速度
   ```
3. **Cookie失效** - 更新Cookie
4. **代理IP被平台封禁** - 更换代理池

### Q3: 如何验证代理是否生效？

**A:** 查看终端输出，会显示：

```
[代理] 使用代理: ***@proxy.example.com:8080
```

或者检查网络请求的源IP（可用 https://httpbin.org/ip 测试）。

### Q4: 代理池中的代理会自动轮换吗？

**A:** 默认每次请求轮询使用代理池中的代理。使用 `ProxyRotator` 可以设置切换频率：

```python
rotator = ProxyRotator(pool, rotate_interval=5)  # 每5次请求切换
```

### Q5: 免费代理为什么不可用？

**A:** 免费代理存在以下问题：
- ⚠️ 稳定性差，随时失效
- ⚠️ 速度慢，延迟高
- ⚠️ 可能被平台封禁
- ⚠️ 安全性低，可能泄露数据

**建议：** 仅用于测试，生产环境使用付费代理。

### Q6: 使用本地代理（Clash/V2Ray）安全吗？

**A:**
- ✅ 安全性高（流量加密）
- ✅ 速度快（本地转发）
- ❌ 只有单个出口IP，容易被识别
- 💡 **建议：** 结合速度控制，降低请求频率

---

## 🎯 最佳实践

1. **组合策略：**
   ```python
   scraper = DouyinScraper(
       cookie="你的Cookie",
       speed="safe",         # 慢速抓取
       proxy_pool=pool       # 使用代理池
   )
   ```

2. **错误处理：**
   ```python
   try:
       comments = scraper.fetch_comments(url, max_count=100)
   except Exception as e:
       print(f"抓取失败: {e}")
       # 更换代理或降低速度
   ```

3. **定期更新代理池：**
   - 定期检查代理可用性
   - 移除失效代理
   - 补充新代理

4. **监控抓取状态：**
   - 观察终端输出
   - 检查是否触发验证码
   - 监控成功率

---

## 📚 相关文件

- `utils/proxy.py` - 代理池核心模块
- `utils/stealth.py` - 浏览器反检测模块
- `example_proxy_usage.py` - 使用示例代码
- `proxies.txt.example` - 代理配置模板

---

## 🤝 支持

遇到问题？
1. 查看本文档的 [常见问题](#常见问题) 部分
2. 检查代理配置是否正确
3. 验证代理可用性：`pool.validate_all()`

---

**祝你抓取顺利！** 🚀
