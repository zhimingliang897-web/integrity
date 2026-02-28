"""
自动获取平台 Cookie 工具

打开平台网站的浏览器窗口，用户手动登录后自动提取 Cookie 并更新 config.py

使用方法:
    python scripts/refresh_cookie.py --platform douyin
    python scripts/refresh_cookie.py --platform xiaohongshu
    python scripts/refresh_cookie.py --platform bilibili
    python scripts/refresh_cookie.py -p douyin --no-update  # 只打印不更新配置
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config.py"

# 平台配置元信息
PLATFORM_META: dict[str, dict[str, object]] = {
    "douyin": {
        "url": "https://www.douyin.com/",
        "cookie_var": "DOUYIN_COOKIE",
        "domain_keywords": ["douyin.com", "bytedance.com"],
        "display_name": "抖音",
    },
    "xiaohongshu": {
        "url": "https://www.xiaohongshu.com/",
        "cookie_var": "XIAOHONGSHU_COOKIE",
        "domain_keywords": ["xiaohongshu.com", "xhslink.com"],
        "display_name": "小红书",
    },
    "bilibili": {
        "url": "https://www.bilibili.com/",
        "cookie_var": "BILIBILI_COOKIE",
        "domain_keywords": ["bilibili.com"],
        "display_name": "B站",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="自动获取平台Cookie并更新config.py"
    )
    parser.add_argument(
        "--platform", "-p",
        choices=sorted(PLATFORM_META.keys()),
        required=True,
        help="目标平台: douyin, xiaohongshu, bilibili",
    )
    parser.add_argument(
        "--config",
        default=str(CONFIG_PATH),
        help=f"配置文件路径 (默认: {CONFIG_PATH})",
    )
    parser.add_argument(
        "--no-update",
        action="store_true",
        help="不更新config.py，只打印Cookie",
    )
    parser.add_argument(
        "--save-path",
        default="",
        help="可选：保存Cookie到指定文件",
    )
    return parser.parse_args()


def dedupe_cookie_pairs(cookie_pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """去重Cookie键值对，保留第一个出现的"""
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for name, value in cookie_pairs:
        if name in seen:
            continue
        seen.add(name)
        result.append((name, value))
    return result


def build_cookie_header(cookies: list[dict], domain_keywords: list[str]) -> str:
    """从浏览器Cookie列表构建HTTP Cookie头字符串"""
    domain_keywords = [k.lower() for k in domain_keywords]

    # 只保留目标域名的Cookie
    filtered = [
        c for c in cookies
        if any(k in (c.get("domain", "") or "").lower() for k in domain_keywords)
    ]
    source = filtered if filtered else cookies

    # 构建 name=value 格式
    pairs = dedupe_cookie_pairs([
        (c["name"], c["value"])
        for c in source
        if c.get("name") and c.get("value")
    ])
    return "; ".join(f"{name}={value}" for name, value in pairs)


def update_config_cookie(config_path: Path, cookie_var: str, cookie_value: str) -> None:
    """更新config.py中的Cookie变量"""
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    text = config_path.read_text(encoding="utf-8")
    new_line = f'{cookie_var} = {json.dumps(cookie_value, ensure_ascii=False)}'

    # 替换已存在的变量赋值行，否则追加
    pattern = re.compile(rf"^{re.escape(cookie_var)}\s*=.*$", flags=re.MULTILINE)
    if pattern.search(text):
        updated = pattern.sub(new_line, text, count=1)
    else:
        suffix = "" if text.endswith("\n") else "\n"
        updated = f"{text}{suffix}\n{new_line}\n"

    # 创建备份
    backup_path = config_path.with_suffix(config_path.suffix + ".bak")
    backup_path.write_text(text, encoding="utf-8")
    config_path.write_text(updated, encoding="utf-8")

    print(f"[OK] 已更新 {cookie_var} 到: {config_path}")
    print(f"[OK] 备份已创建: {backup_path}")


def run_capture(platform: str) -> str:
    """打开浏览器让用户登录，然后捕获Cookie"""
    meta = PLATFORM_META[platform]
    url = str(meta["url"])
    display_name = str(meta["display_name"])
    domain_keywords = list(meta["domain_keywords"])

    print(f"\n{'='*50}")
    print(f"正在打开 {display_name} 登录页面")
    print(f"{'='*50}")
    print(f"URL: {url}")
    print()
    print("操作步骤:")
    print("  1) 在打开的浏览器窗口中手动登录")
    print("  2) 登录成功后，确保页面已完全加载")
    print("  3) 返回此窗口，按回车键继续")
    print("  4) 浏览器会自动关闭并提取Cookie")
    print()

    with sync_playwright() as p:
        # 使用有头浏览器，让用户可以手动登录
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        # 注入反检测脚本
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        page.goto(url, wait_until="domcontentloaded", timeout=120000)

        input("登录完成后按回车键继续...")

        # 提取Cookie
        cookies = context.cookies()
        browser.close()

    cookie_header = build_cookie_header(cookies, domain_keywords)
    if not cookie_header:
        raise RuntimeError("未能捕获到Cookie，请确认已完成登录")

    return cookie_header


def main() -> int:
    args = parse_args()
    platform = args.platform
    meta = PLATFORM_META[platform]
    cookie_var = str(meta["cookie_var"])
    display_name = str(meta["display_name"])
    config_path = Path(args.config).resolve()

    print(f"\n[INFO] 目标平台: {display_name} ({platform})")

    try:
        cookie_header = run_capture(platform)
    except KeyboardInterrupt:
        print("\n[INFO] 用户取消操作")
        return 1
    except Exception as err:
        print(f"[ERROR] Cookie获取失败: {err}")
        return 1

    # 显示预览
    preview = cookie_header[:100] + ("..." if len(cookie_header) > 100 else "")
    print(f"\n[OK] Cookie获取成功!")
    print(f"[INFO] 长度: {len(cookie_header)} 字符")
    print(f"[Preview] {preview}")

    # 可选保存到文件
    if args.save_path:
        save_path = Path(args.save_path).resolve()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(cookie_header, encoding="utf-8")
        print(f"[OK] Cookie已保存到: {save_path}")

    # 更新配置文件
    if args.no_update:
        print("[INFO] --no-update 已设置，跳过配置文件更新")
        print(f"\n完整Cookie:\n{cookie_header}")
        return 0

    try:
        update_config_cookie(
            config_path=config_path,
            cookie_var=cookie_var,
            cookie_value=cookie_header
        )
    except Exception as err:
        print(f"[ERROR] 更新配置文件失败: {err}")
        return 1

    print("\n完成!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
