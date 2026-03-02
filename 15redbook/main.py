"""
小红书英语教育内容生成器 - 主程序

工作流程：
1. 开始 -> 输入 category, style, phrase_count
2. 选题生成 (LLM) -> 输出 topic_json
3. 文案生成 (LLM) -> 输出 content_json
4. HTML渲染 -> 输出 cover_html, slide_htmls
5. 图片生成 -> 输出 cover_image, slide_images
6. 结束 -> 返回所有结果
"""

import json
import argparse
import sys
import io
from datetime import datetime
from pathlib import Path
from typing import Optional

# 设置UTF-8编码输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from llm_client import generate_topic, generate_content
from html_renderer import render_content
from image_generator import generate_images
from obsidian_exporter import export_to_obsidian
from xhs_publisher import publish_to_xiaohongshu, test_cookie


class RedbookGenerator:
    """小红书内容生成器"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        category: str = "随机",
        style: str = "轻松幽默",
        phrase_count: int = 5,
        custom_topic: Optional[str] = None,
        save_html: bool = True,
        save_json: bool = True,
        export_obsidian: bool = True,
        obsidian_vault: Optional[str] = None,
        auto_publish: bool = False,
        is_private: bool = False
    ) -> dict:
        """
        生成完整的小红书内容

        Args:
            category: 分类（随机/餐饮美食/交通出行等）
            style: 风格
            phrase_count: 短语数量
            custom_topic: 自定义主题（可选，如果提供则跳过选题生成）
            save_html: 是否保存HTML文件
            save_json: 是否保存JSON文件
            export_obsidian: 是否导出到Obsidian
            obsidian_vault: Obsidian vault路径（可选）
            auto_publish: 是否自动发布到小红书
            is_private: 是否私密发布（用于测试）

        Returns:
            包含所有生成结果的字典
        """
        # 生成批次ID
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_dir = self.output_dir / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)

        print(f"[1/5] 开始生成内容 - 批次ID: {batch_id}")

        # Step 1: 选题生成（或使用自定义主题）
        if custom_topic:
            print(f"      使用自定义主题: {custom_topic}")
            print("[2/5] 正在基于自定义主题生成选题...")
            topic_json, topic_reasoning = generate_topic(
                category="自定义",
                phrase_count=phrase_count,
                custom_topic=custom_topic
            )
        else:
            print(f"      分类: {category}, 风格: {style}, 短语数: {phrase_count}")
            print("[2/5] 正在生成选题...")
            topic_json, topic_reasoning = generate_topic(category, phrase_count)

        print(f"      选题: {topic_json.get('topic', '未知')}")

        # Step 2: 文案生成
        print("[3/5] 正在生成文案...")
        content_json, content_reasoning = generate_content(topic_json)
        print(f"      标题: {content_json.get('title', '未知')}")

        # Step 3: HTML渲染
        print("[4/5] 正在渲染HTML...")
        cover_html, slide_htmls, caption = render_content(content_json)
        print(f"      封面HTML: {len(cover_html)} 字符")
        print(f"      内容页: {len(slide_htmls)} 页")

        # Step 4: 生成图片
        print("[5/5] 正在生成图片...")
        cover_image, slide_images = generate_images(
            cover_html,
            slide_htmls,
            str(batch_dir),
            ""
        )
        print(f"      封面图片: {cover_image}")
        print(f"      内容页图片: {len(slide_images)} 张")

        # 保存文件
        if save_json:
            # 保存选题JSON
            with open(batch_dir / "topic.json", 'w', encoding='utf-8') as f:
                json.dump(topic_json, f, ensure_ascii=False, indent=2)

            # 保存内容JSON
            with open(batch_dir / "content.json", 'w', encoding='utf-8') as f:
                json.dump(content_json, f, ensure_ascii=False, indent=2)

            # 保存文案
            with open(batch_dir / "caption.txt", 'w', encoding='utf-8') as f:
                f.write(caption)
                f.write("\n\n")
                f.write(" ".join(content_json.get('tags', [])))

        if save_html:
            # 保存封面HTML
            with open(batch_dir / "cover.html", 'w', encoding='utf-8') as f:
                f.write(cover_html)

            # 保存内容页HTML
            for i, html in enumerate(slide_htmls, 1):
                with open(batch_dir / f"slide_{i}.html", 'w', encoding='utf-8') as f:
                    f.write(html)

        print(f"\n生成完成！所有文件已保存到: {batch_dir}")

        # Step 5: 导出到Obsidian
        obsidian_path = None
        if export_obsidian:
            try:
                print("\n[6/6] 正在导出到Obsidian...")
                all_images = [cover_image] + list(slide_images)
                obsidian_path = export_to_obsidian(
                    batch_id=batch_id,
                    topic_json=topic_json,
                    content_json=content_json,
                    image_paths=all_images,
                    source_dir=batch_dir,
                    vault_path=obsidian_vault
                )
                print(f"      已导出到: {obsidian_path}")
            except Exception as e:
                print(f"      Obsidian导出失败: {e}")
                print("      请检查config.yaml中的obsidian.vault_path配置")

        # Step 6: 自动发布到小红书
        publish_result = None
        if auto_publish:
            try:
                print("\n[7/7] 正在发布到小红书...")
                all_images = [str(cover_image)] + [str(p) for p in slide_images]

                # 准备标题（去掉emoji，不超过20字）
                title = content_json.get('title', '')
                # 移除emoji
                title_clean = ''.join(c for c in title if ord(c) < 0x1F600 or ord(c) > 0x1F9FF)
                if len(title_clean) > 20:
                    title_clean = title_clean[:20]

                publish_result = publish_to_xiaohongshu(
                    title=title_clean,
                    content=caption,
                    image_paths=all_images,
                    tags=content_json.get('tags', []),
                    is_private=is_private
                )
                print(f"      发布成功！")
                if publish_result:
                    print(f"      笔记ID: {publish_result.get('note_id', '未知')}")
            except Exception as e:
                print(f"      发布失败: {e}")
                print("      请检查config.yaml中的xiaohongshu.cookie配置")

        return {
            "batch_id": batch_id,
            "topic_json": topic_json,
            "content_json": content_json,
            "cover_html": cover_html,
            "slide_htmls": slide_htmls,
            "caption": caption,
            "cover_image": str(cover_image),
            "slide_images": [str(p) for p in slide_images],
            "output_dir": str(batch_dir),
            "obsidian_path": str(obsidian_path) if obsidian_path else None,
            "publish_result": publish_result
        }


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="小红书英语教育内容生成器")
    parser.add_argument(
        "-c", "--category",
        default="随机",
        help="分类 (随机/餐饮美食/交通出行/购物消费/职场办公/社交聊天/旅行住宿/医疗健康/租房生活/校园学习/娱乐休闲)"
    )
    parser.add_argument(
        "-s", "--style",
        default="轻松幽默",
        help="风格"
    )
    parser.add_argument(
        "-n", "--phrase-count",
        type=int,
        default=5,
        help="知识点数量 (默认: 5)"
    )
    parser.add_argument(
        "-t", "--topic",
        default=None,
        help="自定义主题（如：公交车、咖啡店点单）"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="输出目录"
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="不保存HTML文件"
    )
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="不保存JSON文件"
    )
    parser.add_argument(
        "--no-obsidian",
        action="store_true",
        help="不导出到Obsidian"
    )
    parser.add_argument(
        "--vault",
        default=None,
        help="Obsidian vault路径（覆盖配置文件）"
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="自动发布到小红书"
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="私密发布（用于测试，仅自己可见）"
    )
    parser.add_argument(
        "--test-cookie",
        action="store_true",
        help="测试小红书Cookie是否有效"
    )

    args = parser.parse_args()

    # 测试Cookie
    if args.test_cookie:
        test_cookie()
        return

    generator = RedbookGenerator(args.output)
    result = generator.generate(
        category=args.category,
        style=args.style,
        phrase_count=args.phrase_count,
        custom_topic=args.topic,
        save_html=not args.no_html,
        save_json=not args.no_json,
        export_obsidian=not args.no_obsidian,
        obsidian_vault=args.vault,
        auto_publish=args.publish,
        is_private=args.private
    )

    # 打印摘要
    print("\n" + "=" * 50)
    print("生成摘要")
    print("=" * 50)
    print(f"选题: {result['topic_json'].get('topic', '未知')}")
    print(f"标题: {result['content_json'].get('title', '未知')}")
    print(f"封面: {result['cover_image']}")
    print(f"内容页: {len(result['slide_images'])} 张")
    print(f"输出目录: {result['output_dir']}")
    if result.get('obsidian_path'):
        print(f"Obsidian笔记: {result['obsidian_path']}")
    if result.get('publish_result'):
        print(f"小红书发布: 成功")


if __name__ == "__main__":
    main()
