"""
HTML转图片模块 - 使用Playwright将HTML渲染为PNG图片
"""

import asyncio
from pathlib import Path
from typing import List, Optional
import yaml


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class ImageGenerator:
    """HTML转图片生成器"""

    def __init__(self, output_dir: Optional[str] = None):
        config = load_config()
        self.width = config['image']['width']
        self.height = config['image']['height']
        self.format = config['image']['format']
        self.output_dir = Path(output_dir or config['image']['output_dir'])
        self.output_dir = Path(__file__).parent / self.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def _html_to_image_async(self, html_content: str, output_path: Path) -> Path:
        """
        异步将HTML转换为图片

        Args:
            html_content: HTML内容
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                viewport={'width': self.width, 'height': self.height}
            )

            # 设置HTML内容
            await page.set_content(html_content)

            # 等待渲染完成
            await page.wait_for_load_state('networkidle')

            # 截图
            await page.screenshot(
                path=str(output_path),
                type=self.format,
                full_page=False
            )

            await browser.close()

        return output_path

    def html_to_image(self, html_content: str, output_path: Path) -> Path:
        """
        将HTML转换为图片（同步包装）

        Args:
            html_content: HTML内容
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        return asyncio.run(self._html_to_image_async(html_content, output_path))

    def generate_cover_image(self, cover_html: str, filename: str = "cover.png") -> Path:
        """
        生成封面图片

        Args:
            cover_html: 封面HTML
            filename: 文件名

        Returns:
            输出文件路径
        """
        output_path = self.output_dir / filename
        return self.html_to_image(cover_html, output_path)

    def generate_slide_images(self, slide_htmls: List[str], prefix: str = "slide") -> List[Path]:
        """
        生成所有内容页图片

        Args:
            slide_htmls: 内容页HTML列表
            prefix: 文件名前缀

        Returns:
            输出文件路径列表
        """
        paths = []
        for i, html in enumerate(slide_htmls, 1):
            output_path = self.output_dir / f"{prefix}_{i}.png"
            self.html_to_image(html, output_path)
            paths.append(output_path)
        return paths

    async def generate_all_async(
        self,
        cover_html: str,
        slide_htmls: List[str],
        batch_id: str = ""
    ) -> tuple[Path, List[Path]]:
        """
        异步批量生成所有图片（更高效）

        Args:
            cover_html: 封面HTML
            slide_htmls: 内容页HTML列表
            batch_id: 批次ID（用于区分不同批次）

        Returns:
            tuple: (封面图片路径, 内容页图片路径列表)
        """
        from playwright.async_api import async_playwright

        prefix = f"{batch_id}_" if batch_id else ""

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                viewport={'width': self.width, 'height': self.height}
            )

            # 生成封面
            cover_path = self.output_dir / f"{prefix}cover.png"
            await page.set_content(cover_html)
            await page.wait_for_load_state('networkidle')
            await page.screenshot(path=str(cover_path), type=self.format)

            # 生成内容页
            slide_paths = []
            for i, html in enumerate(slide_htmls, 1):
                slide_path = self.output_dir / f"{prefix}slide_{i}.png"
                await page.set_content(html)
                await page.wait_for_load_state('networkidle')
                await page.screenshot(path=str(slide_path), type=self.format)
                slide_paths.append(slide_path)

            await browser.close()

        return cover_path, slide_paths

    def generate_all(
        self,
        cover_html: str,
        slide_htmls: List[str],
        batch_id: str = ""
    ) -> tuple[Path, List[Path]]:
        """
        同步批量生成所有图片

        Args:
            cover_html: 封面HTML
            slide_htmls: 内容页HTML列表
            batch_id: 批次ID

        Returns:
            tuple: (封面图片路径, 内容页图片路径列表)
        """
        return asyncio.run(self.generate_all_async(cover_html, slide_htmls, batch_id))


# 便捷函数
def generate_images(
    cover_html: str,
    slide_htmls: List[str],
    output_dir: Optional[str] = None,
    batch_id: str = ""
) -> tuple[Path, List[Path]]:
    """
    生成所有图片

    Args:
        cover_html: 封面HTML
        slide_htmls: 内容页HTML列表
        output_dir: 输出目录
        batch_id: 批次ID

    Returns:
        tuple: (封面图片路径, 内容页图片路径列表)
    """
    generator = ImageGenerator(output_dir)
    return generator.generate_all(cover_html, slide_htmls, batch_id)


if __name__ == "__main__":
    # 测试
    test_html = '''<!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                width: 1080px;
                height: 1440px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                font-family: sans-serif;
            }
            h1 { color: white; font-size: 72px; }
        </style>
    </head>
    <body>
        <h1>测试图片生成</h1>
    </body>
    </html>'''

    generator = ImageGenerator()
    path = generator.generate_cover_image(test_html, "test.png")
    print(f"测试图片已生成: {path}")
