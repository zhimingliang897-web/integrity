#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从浏览器获取 Cookie，保存为 yt-dlp 能用的格式
支持 Chrome、Edge（Windows）

用法: python get_cookies.py
"""

import os
import sys
import sqlite3
import shutil
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).parent
OUT  = HERE / "cookies.txt"

# ── 常见视频网站域名 ──────────────────────────────────────────
VIDEO_DOMAINS = [
    "bilibili.com",
    "youtube.com",
    "youtu.be",
    "douyin.com",
    "weibo.com",
    "weibo.cn",
    "iqiyi.com",
    "youku.com",
    "v.qq.com",
    "mgtv.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com",
    "xiaohongshu.com",
    "xhs.link",
    "ntu.edu.sg",
    "ntu.edu.tw",
    "panopto.com",
    "kaltura.com",
]


def get_chrome_cookie_db() -> Path | None:
    """查找 Chrome/Edge 的 Cookie 数据库路径"""
    candidates = [
        # Chrome
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/User Data/Default/Network/Cookies",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/User Data/Default/Cookies",
        # Edge
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Edge/User Data/Default/Network/Cookies",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Edge/User Data/Default/Cookies",
    ]
    for p in candidates:
        if p.exists():
            print(f"  找到 Cookie 数据库: {p}")
            return p
    return None


def read_cookies_from_db(db_path: Path) -> list[dict]:
    """从 SQLite 数据库读取 Cookie（需要关闭 Chrome）"""
    # 复制数据库（避免被 Chrome 锁定）
    tmp = Path(tempfile.mktemp(suffix=".db"))
    try:
        shutil.copy2(db_path, tmp)
    except PermissionError:
        print("  ✗ Cookie 文件被锁定，请先关闭 Chrome/Edge 后重试")
        return []

    cookies = []
    try:
        conn = sqlite3.connect(tmp)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # 不同版本的 Chrome 字段名略有不同
        try:
            cur.execute("""
                SELECT host_key, name, value, path, expires_utc, is_secure,
                       encrypted_value
                FROM cookies
            """)
        except sqlite3.OperationalError:
            cur.execute("""
                SELECT host_key, name, value, path, expires_utc, is_secure
                FROM cookies
            """)

        for row in cur.fetchall():
            host = row["host_key"]
            # 只保留视频域名的 Cookie
            if not any(d in host for d in VIDEO_DOMAINS):
                continue

            value = row["value"]
            # 如果 value 为空但有 encrypted_value，尝试解密
            if not value and "encrypted_value" in row.keys() and row["encrypted_value"]:
                value = try_decrypt(row["encrypted_value"])

            # Chrome 时间戳从 1601-01-01 开始（微秒），转为 Unix 时间戳
            expires = row["expires_utc"]
            if expires > 0:
                # Chrome: 微秒数，从1601-01-01
                expires_unix = (expires - 11644473600000000) // 1000000
            else:
                expires_unix = 0

            cookies.append({
                "domain":  host,
                "path":    row["path"] or "/",
                "secure":  bool(row["is_secure"]),
                "expires": expires_unix,
                "name":    row["name"],
                "value":   value or "",
            })

        conn.close()
    except Exception as e:
        print(f"  ✗ 读取 Cookie 失败: {e}")
    finally:
        tmp.unlink(missing_ok=True)

    return cookies


def try_decrypt(encrypted: bytes) -> str:
    """尝试解密 Chrome 加密的 Cookie（Windows DPAPI）"""
    try:
        import win32crypt
        decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
        return decrypted[1].decode("utf-8", errors="replace")
    except Exception:
        pass
    return ""


def write_netscape_format(cookies: list[dict], out: Path):
    """写入 Netscape Cookie 格式（yt-dlp 使用）"""
    lines = ["# Netscape HTTP Cookie File\n",
             f"# 由 get_cookies.py 生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"]

    for c in cookies:
        domain = c["domain"]
        include_sub = "TRUE" if domain.startswith(".") else "FALSE"
        path    = c["path"]
        secure  = "TRUE" if c["secure"] else "FALSE"
        expires = str(c["expires"])
        name    = c["name"]
        value   = c["value"]
        lines.append(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

    out.write_text("".join(lines), encoding="utf-8")


def yt_dlp_export(browser: str = "chrome"):
    """用 yt-dlp 内置的 --cookies-from-browser 方式导出（推荐，无需关闭浏览器）"""
    domains = " ".join(VIDEO_DOMAINS[:5])  # 示例几个
    print(f"\n  尝试用 yt-dlp 直接从 {browser} 导出 Cookie...")
    import subprocess
    result = subprocess.run(
        [
            sys.executable, "-m", "yt_dlp",
            "--cookies-from-browser", browser,
            "--cookies", str(OUT),
            "--skip-download",
            "https://www.bilibili.com",  # 随便一个 URL 触发导出
        ],
        capture_output=True, text=True
    )
    if OUT.exists() and OUT.stat().st_size > 20:
        return True
    return False


def main():
    print("=" * 50)
    print("  Cookie 获取工具")
    print("=" * 50)
    print(f"\n  Cookie 将保存到: {OUT}")
    print(f"  涵盖 {len(VIDEO_DOMAINS)} 个视频网站域名\n")

    # 方法1：yt-dlp 内置导出（最简单，不需要关闭浏览器）
    print("方法1: 用 yt-dlp 内置功能导出（无需关闭浏览器）")
    for browser in ["chrome", "edge", "firefox"]:
        print(f"  正在尝试从 {browser} 导出...")
        try:
            if yt_dlp_export(browser):
                size = OUT.stat().st_size
                print(f"\n  ✓ 成功！已保存 {size} 字节到 cookies.txt")
                print(f"  现在可以运行 python main.py <URL> 下载视频了")
                return
        except Exception as e:
            print(f"  ✗ {browser} 失败: {e}")

    # 方法2：直接读 SQLite 数据库
    print("\n方法2: 直接读取浏览器 Cookie 数据库")
    print("  ⚠️  请先完全关闭 Chrome/Edge 再继续")
    input("  关闭后按回车...")

    db = get_chrome_cookie_db()
    if not db:
        print("\n  ✗ 未找到 Chrome/Edge Cookie 数据库")
        print("  请手动从浏览器导出 cookies.txt 文件，放到此目录")
        return

    cookies = read_cookies_from_db(db)
    if not cookies:
        print("\n  ✗ 未读取到 Cookie，可能需要安装 pywin32: pip install pywin32")
        return

    write_netscape_format(cookies, OUT)
    print(f"\n  ✓ 已保存 {len(cookies)} 条 Cookie 到 cookies.txt")
    print("  现在可以运行 python main.py <URL> 下载视频了")


if __name__ == "__main__":
    main()
