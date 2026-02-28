"""
Open platform website in a real browser window, let user log in manually,
then extract cookies and update config.py automatically.

Example:
    python scripts/refresh_cookie.py --platform douyin
    python scripts/refresh_cookie.py --platform xiaohongshu --no-update
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

PLATFORM_META: dict[str, dict[str, object]] = {
    "douyin": {
        "url": "https://www.douyin.com/",
        "cookie_var": "DOUYIN_COOKIE",
        "domain_keywords": ["douyin.com", "bytedance.com"],
    },
    "xiaohongshu": {
        "url": "https://www.xiaohongshu.com/",
        "cookie_var": "XIAOHONGSHU_COOKIE",
        "domain_keywords": ["xiaohongshu.com", "xhslink.com"],
    },
    "bilibili": {
        "url": "https://www.bilibili.com/",
        "cookie_var": "BILIBILI_COOKIE",
        "domain_keywords": ["bilibili.com"],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh platform cookie and update config.py")
    parser.add_argument(
        "--platform",
        "-p",
        choices=sorted(PLATFORM_META.keys()),
        required=True,
        help="Target platform",
    )
    parser.add_argument(
        "--config",
        default=str(CONFIG_PATH),
        help="Path to config.py (default: ./config.py)",
    )
    parser.add_argument(
        "--no-update",
        action="store_true",
        help="Do not update config.py, only print/save cookie",
    )
    parser.add_argument(
        "--save-path",
        default="",
        help="Optional file path to save the cookie text",
    )
    return parser.parse_args()


def dedupe_cookie_pairs(cookie_pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for name, value in cookie_pairs:
        if name in seen:
            continue
        seen.add(name)
        result.append((name, value))
    return result


def build_cookie_header(cookies: list[dict], domain_keywords: list[str]) -> str:
    domain_keywords = [k.lower() for k in domain_keywords]

    filtered = [
        c
        for c in cookies
        if any(k in (c.get("domain", "") or "").lower() for k in domain_keywords)
    ]
    source = filtered if filtered else cookies

    pairs = dedupe_cookie_pairs([(c["name"], c["value"]) for c in source if c.get("name") and c.get("value")])
    return "; ".join(f"{name}={value}" for name, value in pairs)


def update_config_cookie(config_path: Path, cookie_var: str, cookie_value: str) -> None:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    text = config_path.read_text(encoding="utf-8")
    new_line = f"{cookie_var} = {json.dumps(cookie_value, ensure_ascii=False)}"

    # Replace existing variable assignment line if present, otherwise append.
    pattern = re.compile(rf"^{re.escape(cookie_var)}\s*=.*$", flags=re.MULTILINE)
    if pattern.search(text):
        updated = pattern.sub(new_line, text, count=1)
    else:
        suffix = "" if text.endswith("\n") else "\n"
        updated = f"{text}{suffix}\n{new_line}\n"

    backup_path = config_path.with_suffix(config_path.suffix + ".bak")
    backup_path.write_text(text, encoding="utf-8")
    config_path.write_text(updated, encoding="utf-8")

    print(f"[OK] Updated {cookie_var} in: {config_path}")
    print(f"[OK] Backup created: {backup_path}")


def run_capture(platform: str) -> str:
    meta = PLATFORM_META[platform]
    url = str(meta["url"])
    domain_keywords = list(meta["domain_keywords"])

    print(f"\nOpening browser for platform: {platform}")
    print(f"URL: {url}")
    print("1) Please log in manually in the opened browser window.")
    print("2) After login succeeds and homepage loads, return here and press Enter.")
    print("3) Browser will close automatically after cookie extraction.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
        input("Press Enter to capture cookies...")

        cookies = context.cookies()
        browser.close()

    cookie_header = build_cookie_header(cookies, domain_keywords)
    if not cookie_header:
        raise RuntimeError("No cookie captured. Please confirm you completed login.")
    return cookie_header


def main() -> int:
    args = parse_args()
    platform = args.platform
    cookie_var = str(PLATFORM_META[platform]["cookie_var"])
    config_path = Path(args.config).resolve()

    try:
        cookie_header = run_capture(platform)
    except Exception as err:  # noqa: BLE001
        print(f"[ERROR] Capture failed: {err}")
        return 1

    preview = cookie_header[:120] + ("..." if len(cookie_header) > 120 else "")
    print(f"[OK] Cookie captured, length={len(cookie_header)}")
    print(f"[Preview] {preview}")

    if args.save_path:
        save_path = Path(args.save_path).resolve()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(cookie_header, encoding="utf-8")
        print(f"[OK] Saved cookie text: {save_path}")

    if args.no_update:
        print("[INFO] --no-update set, skipped config.py update.")
        return 0

    try:
        update_config_cookie(config_path=config_path, cookie_var=cookie_var, cookie_value=cookie_header)
    except Exception as err:  # noqa: BLE001
        print(f"[ERROR] Update config failed: {err}")
        return 1

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
