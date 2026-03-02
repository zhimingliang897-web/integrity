"""
Obsidian导出模块 - 将生成的内容导出为Obsidian笔记格式
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
import yaml


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class ObsidianExporter:
    """Obsidian导出器"""

    def __init__(self, vault_path: Optional[str] = None):
        config = load_config()
        obsidian_config = config.get('obsidian', {})

        self.vault_path = Path(vault_path) if vault_path else Path(obsidian_config.get('vault_path', ''))
        self.queue_folder = obsidian_config.get('queue_folder', '01_发布队列')
        self.attachments_folder = obsidian_config.get('attachments_folder', 'attachments')

    def export(
        self,
        batch_id: str,
        topic_json: dict,
        content_json: dict,
        image_paths: list,
        source_dir: Path
    ) -> Path:
        """
        导出内容到Obsidian

        Args:
            batch_id: 批次ID
            topic_json: 选题JSON
            content_json: 内容JSON
            image_paths: 图片路径列表 [cover, slide_1, ...]
            source_dir: 源文件目录

        Returns:
            导出的Markdown文件路径
        """
        if not self.vault_path or not self.vault_path.exists():
            raise ValueError(f"Obsidian vault路径无效: {self.vault_path}")

        # 创建发布队列目录
        queue_dir = self.vault_path / self.queue_folder
        queue_dir.mkdir(parents=True, exist_ok=True)

        # 创建附件目录
        attachments_dir = self.vault_path / self.attachments_folder / batch_id
        attachments_dir.mkdir(parents=True, exist_ok=True)

        # 复制图片到附件目录
        image_names = []
        for img_path in image_paths:
            img_path = Path(img_path)
            if img_path.exists():
                dest = attachments_dir / img_path.name
                shutil.copy2(img_path, dest)
                # Obsidian使用相对路径
                image_names.append(f"{self.attachments_folder}/{batch_id}/{img_path.name}")

        # 生成Markdown内容
        md_content = self._generate_markdown(
            batch_id=batch_id,
            topic_json=topic_json,
            content_json=content_json,
            image_names=image_names
        )

        # 保存Markdown文件
        title_safe = content_json.get('title', batch_id).replace('/', '-').replace('\\', '-')
        # 移除emoji以避免文件名问题
        title_safe = ''.join(c for c in title_safe if ord(c) < 128 or c in '中文日韩').strip()
        if not title_safe:
            title_safe = batch_id

        md_filename = f"{batch_id}_{topic_json.get('category', '未分类')}.md"
        md_path = queue_dir / md_filename

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return md_path

    def _generate_markdown(
        self,
        batch_id: str,
        topic_json: dict,
        content_json: dict,
        image_names: list
    ) -> str:
        """生成Markdown内容"""

        # YAML frontmatter
        frontmatter = {
            'status': '待发布',
            'category': topic_json.get('category', ''),
            'topic': topic_json.get('topic', ''),
            'difficulty': topic_json.get('difficulty', ''),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'batch_id': batch_id,
            'tags': ['小红书', '英语教学', topic_json.get('category', '')]
        }

        # 构建slides摘要
        slides_summary = []
        for slide in content_json.get('slides', []):
            slides_summary.append(
                f"{slide.get('slide_number', '')}️⃣ {slide.get('wrong_cn', '')} → \"{slide.get('correct_en', '')}\""
            )

        # 获取tags
        tags = content_json.get('tags', [])
        tags_str = ' '.join(tags)

        # 图片清单
        image_list = []
        if image_names:
            image_list.append(f"- [ ] **封面图**: `{Path(image_names[0]).name}`")
            for i, img in enumerate(image_names[1:], 1):
                image_list.append(f"- [ ] **知识点{i}**: `{Path(img).name}`")

        # 组装Markdown
        md = f"""---
{yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False).strip()}
---

# 📱 小红书标题
{content_json.get('title', '')}

# ✍️ 正文文案
{content_json.get('caption', '')}

---
{chr(10).join(slides_summary)}

{tags_str}

# 🖼️ 图片清单（发布顺序）
{chr(10).join(image_list)}

# 📝 详细内容

## 封面信息
- **大标题**: {content_json.get('cover', {}).get('main_title', '')}
- **副标题**: {content_json.get('cover', {}).get('sub_title', '')}
- **emoji**: {content_json.get('cover', {}).get('emoji_icon', '')}

## 知识点详情
"""
        # 添加每个slide的详细信息
        for slide in content_json.get('slides', []):
            dialogue = slide.get('dialogue', {})
            md += f"""
### {slide.get('slide_number', '')}. {slide.get('scene_title', '')}
- ❌ **中式英语**: {slide.get('wrong_cn', '')} → {slide.get('wrong_en', '')}
- ✅ **地道表达**: {slide.get('correct_en', '')} ({slide.get('correct_cn', '')})
- 💬 **对话**:
  - A: {dialogue.get('a', '')} ({dialogue.get('a_cn', '')})
  - B: {dialogue.get('b', '')} ({dialogue.get('b_cn', '')})
- 💡 **小贴士**: {slide.get('tip', '')}
"""

        # 添加图片预览
        md += "\n# 🖼️ 图片预览\n"
        for img in image_names:
            md += f"![[{img}]]\n\n"

        # 添加发布备注
        md += """
# 🤖 发布备注
> 请按顺序上传文件夹内的 6 张 PNG 图片（1封面 + 5知识点）
> 复制上方标题和正文到小红书发布界面
"""

        return md


def export_to_obsidian(
    batch_id: str,
    topic_json: dict,
    content_json: dict,
    image_paths: list,
    source_dir: Path,
    vault_path: Optional[str] = None
) -> Path:
    """
    便捷函数：导出到Obsidian

    Args:
        batch_id: 批次ID
        topic_json: 选题JSON
        content_json: 内容JSON
        image_paths: 图片路径列表
        source_dir: 源文件目录
        vault_path: Obsidian vault路径（可选，优先使用配置文件）

    Returns:
        导出的Markdown文件路径
    """
    exporter = ObsidianExporter(vault_path)
    return exporter.export(batch_id, topic_json, content_json, image_paths, source_dir)


if __name__ == "__main__":
    # 测试
    print("请在config.yaml中配置obsidian.vault_path后使用")
