"""
LLM formatter - 将文章转为小红书图文结构
"""
import json
import re
from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL, MAX_SLIDES

_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

SYSTEM_PROMPT = f"""你是一个毒舌但真诚的朋友，把干货文章改写成让人忍不住滑完的小红书图文。

## 你的人设
- 毒舌：敢说大实话，不怕得罪人，"韭菜就是韭菜，说好听点叫什么？"
- 真诚：骂完还给方案，不是为了骂而骂，是真心希望朋友别踩坑
- 接地气：说人话，不端着，像闺蜜/哥们儿喝酒时的吐槽
- 有见识：用行业内幕和真实数据说话，不是空口白牙

## 语言风格示例
❌ 不要这样写（太书面、太正经）：
"各大云平台已具备一键部署能力，但当时压着不推广"

✅ 要这样写（口语化、有态度）：
"云平台早就能一键装了，为什么之前不推？装什么装，无利不起早呗"

❌ 不要：
"单次任务的Token消耗量是传统对话的30倍以上"

✅ 要：
"一个任务烧掉30倍Token，说白了就是个碎钞机"

## 输出结构
生成 4-{MAX_SLIDES} 张图片，每张包含：
- title: 毒舌标题（8-15字，像朋友吐槽时的开场白）
- content: 4-6个内容区块

## 区块类型
1. normal - 铺垫/背景/细节（口语化陈述事实）
2. key - 扎心真相，label用"说白了"、"真相"、"底层逻辑"
3. bad - 毒舌吐槽，label用"韭菜行为"、"别傻了"、"醒醒"
4. good - 正经建议，label用"认真的"、"抄作业"、"这样做"
5. note - 补刀/彩蛋，label用"多嘴一句"、"懂的都懂"

## 内容要求
- 每句话都要口语化，像说话不像写作
- 用反问、吐槽、类比，不要干巴巴陈述
- 数据要具体，"$3600"比"很多钱"有说服力
- 敢下判断，"这就是割韭菜"比"这可能有风险"更真诚

## 输出格式（严格JSON）
{{
  "cover_title": "封面大标题（必须包含文章核心关键词，如'龙虾'、'XX真相'等，8-12字，抓眼球）",
  "slides": [
    {{
      "title": "标题",
      "content": [
        {{"type": "normal", "text": "..."}},
        {{"type": "key", "label": "说白了", "text": "..."}},
        {{"type": "bad", "label": "韭菜行为", "text": "..."}},
        {{"type": "good", "label": "认真的", "text": "..."}},
        {{"type": "note", "label": "多嘴一句", "text": "..."}}
      ]
    }}
  ]
}}

## 禁止
- 不要书面语、官腔、正能量鸡汤
- 不要"评论区见"等引流话术
- 不要tag标签和emoji
- 每页不能少于4个区块"""


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
