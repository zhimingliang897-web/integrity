"""
图片 -> 提示词生成器

批量读取图片并调用视觉模型，输出两类英文提示词：
1) dalle_style: 自然语言描述
2) sd_style: 逗号分隔标签
"""

import argparse
import base64
import concurrent.futures
import os
import sys
import time
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("需要安装 openai 库：pip install openai")
    sys.exit(1)


DEFAULT_INPUT_DIR = "raw"
DEFAULT_OUTPUT_DIR = "prompts"
DEFAULT_MODE = "both"
DEFAULT_WORKERS = 5
DEFAULT_PROVIDER = "dashscope"
DEFAULT_MODEL_DASHSCOPE = "qwen3-vl-flash-2026-01-22"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

PROVIDER_SETTINGS = {
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "env_key": "DASHSCOPE_API_KEY",
    },
    "volcengine": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "env_key": "VOLC_API_KEY",
    },
}

SYSTEM_PROMPT_DALLE = """你是一个专业的 AI 绘画提示词工程师。请分析这张图片，生成一段适用于 DALL-E 3 / Midjourney 的英文提示词。

要求：
1. 使用连贯英文句子，不要堆砌碎片化关键词。
2. 描述主体外观、动作、表情与关键细节。
3. 描述光照、色彩、背景与整体风格。
4. 保持简洁精准，不要输出无关解释。
5. 只输出提示词正文。"""

SYSTEM_PROMPT_SD = """你是一个专业的 Stable Diffusion 提示词助手。请分析这张图片，生成适用于 SD WebUI / ComfyUI 的英文提示词（Tags）。

要求：
1. 使用英文 tags，并以逗号分隔。
2. 优先使用 Danbooru 风格标签。
3. 覆盖质量、风格、主体、背景、光影等信息。
4. 只输出 tags，不要输出解释。"""

STYLE_PROMPTS = {
    "dalle": SYSTEM_PROMPT_DALLE,
    "sd": SYSTEM_PROMPT_SD,
}

MODE_STYLES = {
    "dalle": ("dalle",),
    "sd": ("sd",),
    "both": ("dalle", "sd"),
}

MIME_BY_EXTENSION = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


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


def parse_args():
    parser = argparse.ArgumentParser(description="图片提示词生成工具")
    parser.add_argument("--input", "-i", default=DEFAULT_INPUT_DIR, help="图片输入目录")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_DIR, help="提示词输出目录")
    parser.add_argument(
        "--mode",
        "-m",
        choices=["dalle", "sd", "both"],
        default=DEFAULT_MODE,
        help="输出类型：dalle / sd / both",
    )
    parser.add_argument("--workers", "-w", type=positive_int, default=DEFAULT_WORKERS, help="并发线程数")
    parser.add_argument("--provider", choices=["dashscope", "volcengine"], default=DEFAULT_PROVIDER, help="API 提供商")
    parser.add_argument(
        "--model",
        help=f"模型名称；dashscope 默认 {DEFAULT_MODEL_DASHSCOPE}，volcengine 建议填写 Endpoint ID",
    )
    parser.add_argument("--key", "-k", help="API Key（可替代环境变量）")
    return parser.parse_args()


def resolve_path(path_value, script_dir):
    path = Path(path_value)
    if not path.is_absolute():
        path = script_dir / path
    return path


def resolve_provider_config(provider, input_key, input_model):
    settings = PROVIDER_SETTINGS[provider]
    api_key = input_key or os.environ.get(settings["env_key"])
    if not api_key:
        raise ValueError(f"未找到 API Key。请使用 --key 或设置环境变量 {settings['env_key']}")

    if provider == "dashscope":
        model = input_model or DEFAULT_MODEL_DASHSCOPE
    else:
        model = input_model
        if not model:
            raise ValueError("volcengine 模式必须通过 --model 指定 Endpoint ID（例如 ep-xxxxx）")

    return api_key, settings["base_url"], model


def collect_images(input_root):
    images = [p for p in input_root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    return sorted(images, key=lambda p: str(p).lower())


def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_mime_type(image_path):
    return MIME_BY_EXTENSION.get(image_path.suffix.lower(), "image/png")


def normalize_message_content(content):
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    text_parts.append(text)
        return "\n".join(text_parts).strip()
    return str(content).strip()


def call_vision_model(client, model, system_prompt, base64_image, mime_type):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}},
                    {"type": "text", "text": "Describe this image for AI generation."},
                ],
            },
        ],
    )
    content = response.choices[0].message.content
    text = normalize_message_content(content)
    if not text:
        raise RuntimeError("模型返回空内容")
    return text


def process_single_image(client, image_path, input_root, mode, model):
    image_name = image_path.name
    rel_path = image_path.parent.relative_to(input_root)

    try:
        base64_image = encode_image(image_path)
        mime_type = get_mime_type(image_path)
        results = {}

        for style in MODE_STYLES[mode]:
            prompt_text = call_vision_model(
                client=client,
                model=model,
                system_prompt=STYLE_PROMPTS[style],
                base64_image=base64_image,
                mime_type=mime_type,
            )
            results[style] = prompt_text

        return image_name, rel_path, results, None
    except Exception as exc:
        return image_name, rel_path, None, str(exc)


def save_result(output_root, style, rel_path, image_name, text):
    target_dir = output_root / f"{style}_style" / rel_path
    target_dir.mkdir(parents=True, exist_ok=True)
    output_file = target_dir / f"{Path(image_name).stem}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    configure_windows_encoding()
    args = parse_args()

    script_dir = Path(__file__).resolve().parent
    input_path = resolve_path(args.input, script_dir)
    output_path = resolve_path(args.output, script_dir)

    if not input_path.exists() or not input_path.is_dir():
        print(f"错误：输入目录不存在 -> {input_path}")
        return

    try:
        api_key, base_url, model = resolve_provider_config(args.provider, args.key, args.model)
    except ValueError as exc:
        print(f"错误：{exc}")
        sys.exit(1)

    images = collect_images(input_path)
    if not images:
        print(f"警告：在目录中未找到支持的图片文件 -> {input_path}")
        return

    print("[开始] 图片 -> 提示词")
    print(f"[配置] 输入目录: {input_path.resolve()}")
    print(f"[配置] 输出目录: {output_path.resolve()}")
    print(f"[配置] Provider: {args.provider}")
    print(f"[配置] Model: {model}")
    print(f"[配置] Mode: {args.mode}")
    print(f"[配置] Workers: {args.workers}")
    print(f"[扫描] 共找到 {len(images)} 张图片")
    print("-" * 60)

    client = OpenAI(api_key=api_key, base_url=base_url)
    success_count = 0
    fail_count = 0
    start_time = time.time()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(process_single_image, client, img_path, input_path, args.mode, model)
                for img_path in images
            ]

            for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
                image_name, rel_path, results, error = future.result()
                display_name = str(rel_path / image_name)

                if error:
                    print(f"[{index}/{len(images)}] FAIL {display_name}: {error}")
                    fail_count += 1
                    continue

                for style, prompt_text in results.items():
                    save_result(output_path, style, rel_path, image_name, prompt_text)

                print(f"[{index}/{len(images)}] OK   {display_name}")
                success_count += 1
    except KeyboardInterrupt:
        print("\n用户中断，任务已停止")
        sys.exit(130)

    duration = time.time() - start_time
    print("-" * 60)
    print(f"[完成] 耗时: {duration:.2f}s")
    print(f"[统计] 成功: {success_count} | 失败: {fail_count}")
    print(f"[输出] {output_path.resolve()}")


if __name__ == "__main__":
    main()
