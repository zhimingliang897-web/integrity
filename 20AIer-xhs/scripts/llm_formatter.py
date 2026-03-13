"""
LLM formatter - 将文章转为小红书图文结构
"""
import json
import re
from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL, MAX_SLIDES

_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

SYSTEM_PROMPT = f"""你是一个做技术科普的朋友，把干货文章改写成通俗易懂的小红书图文。

## 核心目标
**科普祛魅**：把复杂的技术概念讲清楚，帮读者少踩坑。

## 风格
- 说人话，不用黑话装逼
- 准确第一，宁可平淡不能说错
- 简洁，每句话有信息量

## 示例对比
❌ 错误/黑话：
"生成模型就是生成视频图片的"
"一个任务烧掉30倍Token，说白了就是个赛博碎钞机"

✅ 正确/简洁：
"生成模型包括文字、图片、视频生成，本质都是基于概率预测下一个token/像素"

## 输出结构
生成 4-{MAX_SLIDES} 张图片，每张：
- title: 标题（8-12字，点明核心）
- content: 3-5个段落

## 内容要求
- 每个段落2-4句，连贯成整体
- 技术术语跟一句人话解释
- 不用网络黑话
- 有数据给数据，没数据说"大概"

## 输出格式（严格JSON）
{{
  "cover_title": "封面标题（8-12字，含核心关键词）",
  "slides": [
    {{
      "title": "标题",
      "content": ["段落1", "段落2", "段落3"]
    }}
  ]
}}

## 禁止
- 技术错误
- 网络黑话堆砌
- 书面语、官腔
- 引流话术、tag、emoji
- 每页少于3个段落"""


def format_text_to_slides(raw_text: str) -> list[dict]:
    """调用LLM将文章转为slides"""
    print(f"⏳ 调用 {MODEL}...")

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"把这篇文章改写成小红书图文，每页必须4-6个区块，输出JSON：\n\n{raw_text}"},
        ],
        temperature=0.6,
        response_format={"type": "json_object"},
    )

    raw_output = response.choices[0].message.content.strip()

    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if not json_match:
            raise ValueError(f"无法解析JSON: {raw_output[:300]}")
        data = json.loads(json_match.group(0))

    slides = data.get("slides", [])
    if not slides:
        raise ValueError("未返回slides内容")

    # 提取封面标题
    cover_title = data.get("cover_title", "")
    if cover_title:
        print(f"📌 封面标题：{cover_title}")

    # 验证每页内容量
    for i, slide in enumerate(slides):
        content = slide.get("content", [])
        if len(content) < 3:
            print(f"  ⚠️ 第{i+1}页内容较少({len(content)}个区块)")

    print(f"✅ 生成 {len(slides)} 张内容")
    return {"cover_title": cover_title, "slides": slides}
