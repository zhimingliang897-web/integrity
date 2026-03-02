"""
HTML渲染器 - 生成小红书风格的封面和内容页HTML
"""

from typing import List
from jinja2 import Template

# 封面HTML模板
COVER_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            width: 1080px;
            height: 1440px;
            font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 80px;
        }
        .emoji-icon {
            font-size: 120px;
            margin-bottom: 60px;
            filter: drop-shadow(0 10px 30px rgba(0,0,0,0.2));
        }
        .main-title {
            font-size: 96px;
            font-weight: 800;
            color: white;
            text-align: center;
            text-shadow: 0 4px 20px rgba(0,0,0,0.3);
            margin-bottom: 40px;
            letter-spacing: 8px;
        }
        .sub-title {
            font-size: 48px;
            font-weight: 500;
            color: rgba(255,255,255,0.95);
            text-align: center;
            background: rgba(255,255,255,0.2);
            padding: 20px 50px;
            border-radius: 50px;
            backdrop-filter: blur(10px);
        }
        .badge {
            position: absolute;
            top: 60px;
            right: 60px;
            background: #ff6b6b;
            color: white;
            padding: 15px 35px;
            border-radius: 30px;
            font-size: 32px;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(255,107,107,0.4);
        }
        .watermark {
            position: absolute;
            bottom: 50px;
            font-size: 28px;
            color: rgba(255,255,255,0.6);
        }
    </style>
</head>
<body>
    <div class="badge">实用英语</div>
    <div class="emoji-icon">{{ emoji_icon }}</div>
    <div class="main-title">{{ main_title }}</div>
    <div class="sub-title">{{ sub_title }}</div>
    <div class="watermark">学英语 | 每日一学</div>
</body>
</html>'''

# 内容页HTML模板
SLIDE_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            width: 1080px;
            height: 1440px;
            font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background: linear-gradient(180deg, #f8f9ff 0%, #e8ecff 100%);
            padding: 60px;
            display: flex;
            flex-direction: column;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
        }
        .slide-number {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 80px;
            height: 80px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            font-weight: 700;
        }
        .scene-title {
            font-size: 42px;
            font-weight: 700;
            color: #333;
            flex: 1;
            margin-left: 30px;
        }
        .comparison-box {
            background: white;
            border-radius: 30px;
            padding: 50px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
        }
        .wrong-section {
            margin-bottom: 40px;
            padding-bottom: 40px;
            border-bottom: 2px dashed #eee;
        }
        .section-label {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 20px;
        }
        .wrong-label {
            color: #e74c3c;
        }
        .correct-label {
            color: #27ae60;
        }
        .chinese-text {
            font-size: 32px;
            color: #666;
            margin-bottom: 15px;
        }
        .english-text {
            font-size: 40px;
            font-weight: 600;
        }
        .wrong-english {
            color: #e74c3c;
            text-decoration: line-through;
            text-decoration-thickness: 3px;
        }
        .correct-english {
            color: #27ae60;
        }
        .correct-meaning {
            font-size: 28px;
            color: #888;
            margin-top: 10px;
        }
        .dialogue-box {
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            border-radius: 25px;
            padding: 40px;
            margin-bottom: 30px;
            border-left: 6px solid #667eea;
        }
        .dialogue-title {
            font-size: 28px;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .dialogue-line {
            margin-bottom: 20px;
        }
        .dialogue-en {
            font-size: 34px;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
        }
        .dialogue-cn {
            font-size: 26px;
            color: #888;
        }
        .tip-box {
            background: linear-gradient(135deg, #fff9e6 0%, #fff3cc 100%);
            border-radius: 20px;
            padding: 30px 40px;
            display: flex;
            align-items: flex-start;
            gap: 20px;
        }
        .tip-icon {
            font-size: 36px;
        }
        .tip-text {
            font-size: 28px;
            color: #666;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="slide-number">{{ slide_number }}</div>
        <div class="scene-title">{{ scene_title }}</div>
    </div>

    <div class="comparison-box">
        <div class="wrong-section">
            <div class="section-label wrong-label">
                <span>&#10060;</span> 中式英语
            </div>
            <div class="chinese-text">{{ wrong_cn }}</div>
            <div class="english-text wrong-english">{{ wrong_en }}</div>
        </div>

        <div class="correct-section">
            <div class="section-label correct-label">
                <span>&#9989;</span> 地道表达
            </div>
            <div class="english-text correct-english">{{ correct_en }}</div>
            <div class="correct-meaning">{{ correct_cn }}</div>
        </div>
    </div>

    <div class="dialogue-box">
        <div class="dialogue-title">
            <span>&#128172;</span> 实战对话
        </div>
        <div class="dialogue-line">
            <div class="dialogue-en">{{ dialogue_a }}</div>
            <div class="dialogue-cn">{{ dialogue_a_cn }}</div>
        </div>
        <div class="dialogue-line">
            <div class="dialogue-en">{{ dialogue_b }}</div>
            <div class="dialogue-cn">{{ dialogue_b_cn }}</div>
        </div>
    </div>

    <div class="tip-box">
        <div class="tip-icon">&#128161;</div>
        <div class="tip-text">{{ tip }}</div>
    </div>
</body>
</html>'''


class HTMLRenderer:
    """HTML渲染器"""

    def __init__(self):
        self.cover_template = Template(COVER_TEMPLATE)
        self.slide_template = Template(SLIDE_TEMPLATE)

    def render_cover(self, content_json: dict) -> str:
        """
        渲染封面HTML

        Args:
            content_json: 内容JSON

        Returns:
            封面HTML字符串
        """
        cover = content_json.get('cover', {})
        return self.cover_template.render(
            emoji_icon=cover.get('emoji_icon', '📚'),
            main_title=cover.get('main_title', '学英语'),
            sub_title=cover.get('sub_title', '每日一学')
        )

    def render_slide(self, slide: dict) -> str:
        """
        渲染单个内容页HTML

        Args:
            slide: 内容页数据

        Returns:
            内容页HTML字符串
        """
        dialogue = slide.get('dialogue', {})
        return self.slide_template.render(
            slide_number=slide.get('slide_number', 1),
            scene_title=slide.get('scene_title', ''),
            wrong_cn=slide.get('wrong_cn', ''),
            wrong_en=slide.get('wrong_en', ''),
            correct_en=slide.get('correct_en', ''),
            correct_cn=slide.get('correct_cn', ''),
            dialogue_a=dialogue.get('a', ''),
            dialogue_a_cn=dialogue.get('a_cn', ''),
            dialogue_b=dialogue.get('b', ''),
            dialogue_b_cn=dialogue.get('b_cn', ''),
            tip=slide.get('tip', '')
        )

    def render_all(self, content_json: dict) -> tuple[str, List[str], str]:
        """
        渲染所有HTML

        Args:
            content_json: 完整的内容JSON

        Returns:
            tuple: (封面HTML, 内容页HTML列表, 文案caption)
        """
        cover_html = self.render_cover(content_json)

        slide_htmls = []
        for slide in content_json.get('slides', []):
            slide_html = self.render_slide(slide)
            slide_htmls.append(slide_html)

        caption = content_json.get('caption', '')

        return cover_html, slide_htmls, caption


# 便捷函数
def render_content(content_json: dict) -> tuple[str, List[str], str]:
    """渲染内容为HTML"""
    renderer = HTMLRenderer()
    return renderer.render_all(content_json)


if __name__ == "__main__":
    # 测试
    test_content = {
        "title": "星巴克点单英语",
        "cover": {
            "main_title": "星巴克点单",
            "sub_title": "5句地道英语轻松搞定",
            "emoji_icon": "☕"
        },
        "slides": [
            {
                "slide_number": 1,
                "scene_title": "点一杯拿铁",
                "wrong_cn": "我想要一杯咖啡",
                "wrong_en": "I want a coffee",
                "correct_en": "Can I get a latte?",
                "correct_cn": "我能要一杯拿铁吗？",
                "dialogue": {
                    "a": "A: Hi, can I get a grande latte?",
                    "a_cn": "嗨，我能要一杯大杯拿铁吗？",
                    "b": "B: Sure! For here or to go?",
                    "b_cn": "好的！在这喝还是带走？"
                },
                "tip": "老外点单很少说 I want，更常用 Can I get 或 I'll have"
            }
        ],
        "caption": "测试文案"
    }

    cover_html, slide_htmls, caption = render_content(test_content)
    print("封面HTML长度:", len(cover_html))
    print("内容页数量:", len(slide_htmls))
    print("文案:", caption)
