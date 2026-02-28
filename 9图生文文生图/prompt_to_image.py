"""
提示词 -> 图片生成器

批量读取 .txt 提示词文件并生成图片，支持：
1) DashScope（qwen-image / wanx）
2) Volcengine（OpenAI 兼容接口）
"""

import argparse
import concurrent.futures
import json
import os
import sys
import threading
import time
from pathlib import Path

import requests

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


DEFAULT_INPUT_DIR = "prompts"
DEFAULT_OUTPUT_DIR = "generated"
DEFAULT_PROVIDER = "dashscope"
DEFAULT_SIZE = "1024x1024"
DEFAULT_WORKERS = 1
DEFAULT_INTERVAL = 3.0

DEFAULT_MODEL_DASHSCOPE = "qwen-image-max"
VOLCENGINE_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DASHSCOPE_QWEN_IMAGE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
DASHSCOPE_PROMPT_LIMIT = 800


class RequestLimiter:
    """全局请求限速器，避免并发下触发过快请求。"""

    def __init__(self, interval_seconds):
        self.interval = max(interval_seconds, 0.0)
        self._lock = threading.Lock()
        self._next_allowed_at = 0.0

    def wait(self):
        if self.interval <= 0:
            return

        while True:
            with self._lock:
                now = time.monotonic()
                if now >= self._next_allowed_at:
                    self._next_allowed_at = now + self.interval
                    return
                sleep_seconds = self._next_allowed_at - now
            time.sleep(sleep_seconds)


def configure_windows_encoding():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("必须是整数") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("必须大于 0")
    return parsed


def non_negative_float(value):
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("必须是数字") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("不能小于 0")
    return parsed


def parse_args():
    parser = argparse.ArgumentParser(description="提示词生图工具")
    parser.add_argument("--input", "-i", default=DEFAULT_INPUT_DIR, help="提示词目录（递归扫描 .txt）")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_DIR, help="图片输出目录")
    parser.add_argument("--provider", "-p", choices=["dashscope", "volcengine"], default=DEFAULT_PROVIDER, help="API 提供商")
    parser.add_argument("--model", "-m", help=f"模型名称；dashscope 默认 {DEFAULT_MODEL_DASHSCOPE}")
    parser.add_argument("--size", "-s", default=DEFAULT_SIZE, help="图片尺寸，例如 1024x1024")
    parser.add_argument("--workers", "-w", type=positive_int, default=DEFAULT_WORKERS, help="并发线程数")
    parser.add_argument("--interval", type=non_negative_float, default=DEFAULT_INTERVAL, help="请求最小间隔（秒）")
    parser.add_argument("--key", "-k", help="API Key（可替代环境变量）")
    return parser.parse_args()


def resolve_path(path_value, script_dir):
    path = Path(path_value)
    if not path.is_absolute():
        path = script_dir / path
    return path


def read_prompt(prompt_path):
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError as exc:
        raise RuntimeError(f"读取提示词失败: {exc}") from exc


def download_image(url, save_path):
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
    except requests.RequestException as exc:
        return False, str(exc)

    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(response.content)
    return True, None


def to_dashscope_size(size):
    return size.replace("x", "*")


def extract_qwen_image_url(result):
    try:
        content = result["output"]["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"解析 qwen-image 返回失败: {result}") from exc

    if isinstance(content, dict):
        content = [content]

    if not isinstance(content, list):
        raise RuntimeError(f"qwen-image 返回 content 格式异常: {content}")

    for item in content:
        if not isinstance(item, dict):
            continue
        image = item.get("image")
        if isinstance(image, str) and image:
            return image
        image_url = item.get("image_url")
        if isinstance(image_url, str) and image_url:
            return image_url
        if isinstance(image_url, dict):
            url = image_url.get("url")
            if isinstance(url, str) and url:
                return url
        url = item.get("url")
        if isinstance(url, str) and url:
            return url

    raise RuntimeError(f"未在 qwen-image 返回中找到图片 URL: {result}")


def generate_qwen_image(api_key, model, prompt, size):
    payload = {
        "model": model,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ]
        },
        "parameters": {
            "size": to_dashscope_size(size),
            "n": 1,
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    response = requests.post(DASHSCOPE_QWEN_IMAGE_URL, headers=headers, json=payload, timeout=120)
    try:
        result = response.json()
    except ValueError as exc:
        raw_preview = response.text[:500]
        raise RuntimeError(f"DashScope 返回非 JSON（状态码 {response.status_code}）：{raw_preview}") from exc

    if response.status_code != 200:
        raise RuntimeError(f"DashScope 错误（{response.status_code}）：{json.dumps(result, ensure_ascii=False)}")

    return extract_qwen_image_url(result)


def generate_wanx_image(api_key, model, prompt, size):
    try:
        import dashscope
        from dashscope import ImageSynthesis
    except ImportError as exc:
        raise RuntimeError("使用 wanx 模型需要安装 dashscope：pip install dashscope") from exc

    dashscope.api_key = api_key
    response = ImageSynthesis.call(
        model=model,
        prompt=prompt,
        n=1,
        size=to_dashscope_size(size),
    )

    if response.status_code != 200:
        raise RuntimeError(f"DashScope 错误: {response.code} - {response.message}")
    if not response.output or not response.output.results:
        raise RuntimeError("DashScope 返回结果为空")
    if not response.output.results[0].url:
        raise RuntimeError("DashScope 返回 URL 为空")
    return response.output.results[0].url


def generate_dashscope_image(api_key, model, prompt, size):
    if model.startswith("qwen-image"):
        return generate_qwen_image(api_key, model, prompt, size)
    return generate_wanx_image(api_key, model, prompt, size)


def generate_volcengine_image(client, model, prompt, size):
    response = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
        quality="standard",
        n=1,
    )
    if not response.data:
        raise RuntimeError("Volcengine 返回结果为空")
    image_url = response.data[0].url
    if not image_url:
        raise RuntimeError("Volcengine 返回 URL 为空")
    return image_url


def normalize_prompt(prompt_text, provider):
    if provider == "dashscope" and len(prompt_text) > DASHSCOPE_PROMPT_LIMIT:
        return prompt_text[:DASHSCOPE_PROMPT_LIMIT], True
    return prompt_text, False


def process_single_prompt(provider, client_or_key, prompt_path, input_root, output_root, model, size, limiter):
    rel_path = prompt_path.parent.relative_to(input_root)
    save_path = output_root / rel_path / f"{prompt_path.stem}.png"
    display_name = str(rel_path / f"{prompt_path.stem}.png")

    if save_path.exists():
        return display_name, "SKIP", None

    try:
        prompt_text = read_prompt(prompt_path)
    except RuntimeError as exc:
        return display_name, None, str(exc)

    if not prompt_text:
        return display_name, None, "空提示词"

    prompt_text, truncated = normalize_prompt(prompt_text, provider)

    try:
        limiter.wait()
        if provider == "dashscope":
            image_url = generate_dashscope_image(client_or_key, model, prompt_text, size)
        else:
            image_url = generate_volcengine_image(client_or_key, model, prompt_text, size)
    except Exception as exc:
        return display_name, None, str(exc)

    downloaded, download_error = download_image(image_url, save_path)
    if not downloaded:
        return display_name, None, f"下载失败: {download_error}"

    status = "OK"
    if truncated:
        status = "OK (prompt 截断到 800 字符)"
    return display_name, status, None


def resolve_provider(provider, input_key, input_model):
    if provider == "dashscope":
        api_key = input_key or os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("未找到 DashScope API Key。请使用 --key 或设置 DASHSCOPE_API_KEY")
        model = input_model or DEFAULT_MODEL_DASHSCOPE
        return api_key, model

    api_key = input_key or os.environ.get("VOLC_API_KEY")
    if not api_key:
        raise ValueError("未找到 Volcengine API Key。请使用 --key 或设置 VOLC_API_KEY")
    if not input_model:
        raise ValueError("volcengine 模式必须通过 --model 指定 Endpoint ID（例如 ep-xxxxx）")
    if OpenAI is None:
        raise ValueError("volcengine 模式需要 openai 库：pip install openai")

    client = OpenAI(api_key=api_key, base_url=VOLCENGINE_BASE_URL)
    return client, input_model


def main():
    configure_windows_encoding()
    args = parse_args()

    script_dir = Path(__file__).resolve().parent
    input_path = resolve_path(args.input, script_dir)
    output_path = resolve_path(args.output, script_dir)

    if not input_path.exists() or not input_path.is_dir():
        print(f"错误：输入目录不存在 -> {input_path}")
        return

    prompt_files = sorted(input_path.rglob("*.txt"), key=lambda p: str(p).lower())
    if not prompt_files:
        print(f"警告：未找到 .txt 提示词文件 -> {input_path}")
        return

    try:
        client_or_key, model = resolve_provider(args.provider, args.key, args.model)
    except ValueError as exc:
        print(f"错误：{exc}")
        sys.exit(1)

    print("[开始] 提示词 -> 图片")
    print(f"[配置] 输入目录: {input_path.resolve()}")
    print(f"[配置] 输出目录: {output_path.resolve()}")
    print(f"[配置] Provider: {args.provider}")
    print(f"[配置] Model: {model}")
    print(f"[配置] Size: {args.size}")
    print(f"[配置] Workers: {args.workers}")
    print(f"[配置] Interval: {args.interval}s")
    print(f"[扫描] 共找到 {len(prompt_files)} 个提示词文件")
    print("-" * 60)

    limiter = RequestLimiter(args.interval)
    success_count = 0
    skip_count = 0
    fail_count = 0
    start_time = time.time()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(
                    process_single_prompt,
                    args.provider,
                    client_or_key,
                    prompt_path,
                    input_path,
                    output_path,
                    model,
                    args.size,
                    limiter,
                )
                for prompt_path in prompt_files
            ]

            for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
                display_name, status, error = future.result()
                if error:
                    print(f"[{index}/{len(prompt_files)}] FAIL {display_name}: {error}")
                    fail_count += 1
                    continue

                if status == "SKIP":
                    print(f"[{index}/{len(prompt_files)}] SKIP {display_name}")
                    skip_count += 1
                    continue

                print(f"[{index}/{len(prompt_files)}] {status} {display_name}")
                success_count += 1
    except KeyboardInterrupt:
        print("\n用户中断，任务已停止")
        sys.exit(130)

    duration = time.time() - start_time
    print("-" * 60)
    print(f"[完成] 耗时: {duration:.2f}s")
    print(f"[统计] 成功: {success_count} | 跳过: {skip_count} | 失败: {fail_count}")
    print(f"[输出] {output_path.resolve()}")


if __name__ == "__main__":
    main()
