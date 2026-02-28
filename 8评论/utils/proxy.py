"""代理池管理模块 — 防止IP被封"""

import random
import time
import requests
from typing import Optional, List, Dict
from threading import Lock


class ProxyPool:
    """代理IP池管理器"""

    def __init__(self, proxies: Optional[List[str]] = None):
        """
        初始化代理池

        Args:
            proxies: 代理列表，格式如:
                - "http://127.0.0.1:7890"
                - "socks5://user:pass@host:port"
                - "http://host:port"
        """
        self.proxies: List[Dict] = []
        self.current_index = 0
        self.lock = Lock()
        self.failed_count: Dict[str, int] = {}  # 记录代理失败次数

        if proxies:
            for proxy in proxies:
                self.add_proxy(proxy)

    def add_proxy(self, proxy: str):
        """添加代理到池中"""
        proxy = proxy.strip()
        if not proxy:
            return

        # 解析代理格式
        proxy_dict = self._parse_proxy(proxy)
        if proxy_dict and proxy_dict not in self.proxies:
            self.proxies.append(proxy_dict)
            print(f"  [代理池] 添加代理: {self._mask_proxy(proxy)}")

    def _parse_proxy(self, proxy: str) -> Optional[Dict]:
        """解析代理字符串为字典格式"""
        try:
            if "://" not in proxy:
                proxy = f"http://{proxy}"

            # Playwright 格式: {"server": "http://host:port", "username": "user", "password": "pass"}
            result = {"server": proxy}

            # 提取用户名密码
            if "@" in proxy:
                # 格式: protocol://user:pass@host:port
                protocol = proxy.split("://")[0]
                rest = proxy.split("://")[1]
                auth_part, host_part = rest.split("@")

                if ":" in auth_part:
                    username, password = auth_part.split(":", 1)
                    result["username"] = username
                    result["password"] = password

                result["server"] = f"{protocol}://{host_part}"

            return result
        except Exception as e:
            print(f"  [代理池] 解析代理失败: {proxy} - {e}")
            return None

    def _mask_proxy(self, proxy: str) -> str:
        """隐藏代理中的敏感信息"""
        if "@" in proxy:
            parts = proxy.split("@")
            return f"***@{parts[1]}"
        return proxy

    def get_proxy(self) -> Optional[Dict]:
        """获取一个可用的代理（轮询方式）"""
        if not self.proxies:
            return None

        with self.lock:
            # 轮询选择代理
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            return proxy

    def get_random_proxy(self) -> Optional[Dict]:
        """随机获取一个代理"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    def mark_failed(self, proxy: Dict):
        """标记代理失败"""
        server = proxy.get("server", "")
        self.failed_count[server] = self.failed_count.get(server, 0) + 1

        # 失败超过3次，从池中移除
        if self.failed_count[server] >= 3:
            print(f"  [代理池] 移除失败代理: {self._mask_proxy(server)}")
            if proxy in self.proxies:
                self.proxies.remove(proxy)

    def check_proxy(self, proxy: Dict, timeout: int = 10) -> bool:
        """检测代理是否可用"""
        try:
            test_url = "https://www.baidu.com"
            proxies = {
                "http": proxy.get("server"),
                "https": proxy.get("server"),
            }

            resp = requests.get(test_url, proxies=proxies, timeout=timeout)
            return resp.status_code == 200
        except Exception:
            return False

    def validate_all(self):
        """验证所有代理的可用性"""
        print(f"[代理池] 开始验证 {len(self.proxies)} 个代理...")
        valid_proxies = []

        for proxy in self.proxies:
            server = self._mask_proxy(proxy.get("server", ""))
            print(f"  检测: {server} ...", end=" ")

            if self.check_proxy(proxy):
                print("✓ 可用")
                valid_proxies.append(proxy)
            else:
                print("✗ 不可用")

        self.proxies = valid_proxies
        print(f"[代理池] 验证完成，剩余 {len(self.proxies)} 个可用代理\n")

    def load_from_file(self, filepath: str):
        """从文件加载代理列表"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self.add_proxy(line)
            print(f"[代理池] 从文件加载了 {len(self.proxies)} 个代理")
        except FileNotFoundError:
            print(f"[代理池] 文件不存在: {filepath}")
        except Exception as e:
            print(f"[代理池] 加载代理文件失败: {e}")

    def fetch_free_proxies(self, count: int = 10) -> List[str]:
        """
        抓取免费代理（仅供测试，稳定性差）

        警告：免费代理质量低、速度慢、容易失效
        建议使用付费代理服务
        """
        print(f"[代理池] 正在抓取 {count} 个免费代理...")
        proxies = []

        try:
            # 从 free-proxy-list.net 抓取
            url = "https://www.sslproxies.org/"
            resp = requests.get(url, timeout=10)

            import re
            pattern = r'<td>(\d+\.\d+\.\d+\.\d+)</td><td>(\d+)</td>'
            matches = re.findall(pattern, resp.text)

            for ip, port in matches[:count]:
                proxy = f"http://{ip}:{port}"
                proxies.append(proxy)
                self.add_proxy(proxy)

            print(f"[代理池] 成功抓取 {len(proxies)} 个免费代理")
        except Exception as e:
            print(f"[代理池] 抓取免费代理失败: {e}")

        return proxies

    def __len__(self):
        return len(self.proxies)

    def __repr__(self):
        return f"<ProxyPool: {len(self.proxies)} proxies>"


class ProxyRotator:
    """代理轮换器 — 自动切换IP"""

    def __init__(self, proxy_pool: ProxyPool, rotate_interval: int = 5):
        """
        Args:
            proxy_pool: 代理池实例
            rotate_interval: 轮换间隔（多少次请求后切换代理）
        """
        self.pool = proxy_pool
        self.rotate_interval = rotate_interval
        self.request_count = 0
        self.current_proxy = None

    def get_proxy(self) -> Optional[Dict]:
        """获取当前代理，超过间隔后自动轮换"""
        if self.request_count % self.rotate_interval == 0:
            self.current_proxy = self.pool.get_proxy()
            if self.current_proxy:
                server = self.pool._mask_proxy(self.current_proxy.get("server", ""))
                print(f"[代理轮换] 切换代理: {server}")

        self.request_count += 1
        return self.current_proxy


# 全局代理池实例（可选）
_global_proxy_pool: Optional[ProxyPool] = None


def init_global_proxy_pool(proxies: Optional[List[str]] = None,
                          proxy_file: Optional[str] = None,
                          validate: bool = False):
    """
    初始化全局代理池

    Args:
        proxies: 代理列表
        proxy_file: 代理文件路径
        validate: 是否验证代理可用性
    """
    global _global_proxy_pool
    _global_proxy_pool = ProxyPool(proxies)

    if proxy_file:
        _global_proxy_pool.load_from_file(proxy_file)

    if validate and len(_global_proxy_pool) > 0:
        _global_proxy_pool.validate_all()

    return _global_proxy_pool


def get_global_proxy_pool() -> Optional[ProxyPool]:
    """获取全局代理池"""
    return _global_proxy_pool
