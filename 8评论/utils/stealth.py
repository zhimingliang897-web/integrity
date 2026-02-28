"""Playwright 反检测工具 — 用于绕过抖音/小红书等平台的 bot 检测"""

# 浏览器启动参数：禁用自动化特征
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-infobars",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-accelerated-2d-canvas",
    "--disable-gpu",
    "--lang=zh-CN,zh",
]

# 在页面加载前注入的 JS，隐藏 Playwright/Selenium 自动化痕迹
STEALTH_JS = """
() => {
    // 1. 覆盖 navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
    });

    // 2. 覆盖 navigator.plugins（模拟真实浏览器插件）
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
            { name: 'Native Client', filename: 'internal-nacl-plugin' },
        ],
    });

    // 3. 覆盖 navigator.languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['zh-CN', 'zh', 'en-US', 'en'],
    });

    // 4. 修改 chrome.runtime 以通过检测
    window.chrome = {
        runtime: {
            connect: () => {},
            sendMessage: () => {},
        },
    };

    // 5. 覆盖 permissions query
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters);

    // 6. 覆盖 WebGL 渲染器信息
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) return 'Intel Inc.';
        if (parameter === 37446) return 'Intel Iris OpenGL Engine';
        return getParameter.call(this, parameter);
    };

    // 7. 移除 Playwright 注入的属性
    delete window.__playwright;
    delete window.__pw_manual;
    delete window.__PW_inspect;

    // 8. 覆盖 navigator.platform
    Object.defineProperty(navigator, 'platform', {
        get: () => 'Win32',
    });

    // 9. 设置合理的 hardwareConcurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8,
    });

    // 10. 设置合理的 deviceMemory
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => 8,
    });
}
"""


def create_stealth_context(playwright_instance, cookie_str: str = "", domain: str = "",
                           headless: bool = True, proxy: dict = None):
    """
    创建带反检测的浏览器上下文

    Args:
        playwright_instance: sync_playwright() 返回的实例
        cookie_str: Cookie 字符串
        domain: Cookie 所属域名，如 ".douyin.com"
        headless: 是否无头模式（False 时更难被检测）
        proxy: 代理配置，格式: {"server": "http://host:port", "username": "user", "password": "pass"}

    Returns:
        (browser, context) 元组
    """
    # 优先尝试使用 real Chrome（指纹更真实）
    browser = None
    for channel in ["chrome", None]:
        try:
            launch_args = {
                "headless": headless,
                "args": BROWSER_ARGS,
            }
            if channel:
                launch_args["channel"] = channel
            browser = playwright_instance.chromium.launch(**launch_args)
            break
        except Exception:
            continue

    if browser is None:
        browser = playwright_instance.chromium.launch(
            headless=headless,
            args=BROWSER_ARGS,
        )

    # 构建浏览器上下文参数
    context_options = {
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "viewport": {"width": 1920, "height": 1080},
        "locale": "zh-CN",
        "timezone_id": "Asia/Shanghai",
        "color_scheme": "dark",
    }

    # 添加代理配置
    if proxy:
        context_options["proxy"] = proxy
        proxy_display = proxy.get("server", "").replace(proxy.get("username", ""), "***") if "username" in proxy else proxy.get("server", "")
        print(f"  [代理] 使用代理: {proxy_display}")

    context = browser.new_context(**context_options)

    # 注入 stealth 脚本（在每个新页面加载前自动执行）
    context.add_init_script(STEALTH_JS)

    # 注入 Cookie
    if cookie_str and domain:
        cookies = []
        for item in cookie_str.split("; "):
            if "=" in item:
                name, value = item.split("=", 1)
                cookies.append({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": domain,
                    "path": "/",
                })
        if cookies:
            context.add_cookies(cookies)

    return browser, context
