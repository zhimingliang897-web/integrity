"""
小红书内容生成器 - 图形界面
使用Gradio构建Web UI
"""

import gradio as gr
import yaml
import json
from pathlib import Path
from datetime import datetime
import shutil


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_config(config: dict):
    """保存配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


# 分类列表
CATEGORIES = [
    "随机",
    "餐饮美食", "交通出行", "购物消费", "职场办公", "社交聊天",
    "旅行住宿", "医疗健康", "租房生活", "校园学习", "娱乐休闲"
]

# 可用模型列表
MODELS = {
    "dashscope": ["qwen-turbo", "qwen-plus", "qwen-max"],
    "openai": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
}


def get_output_dir() -> Path:
    """获取输出目录"""
    return Path(__file__).parent / "output"


def get_current_settings():
    """获取当前设置"""
    config = load_config()
    return {
        "api_key": config.get('api', {}).get('api_key', ''),
        "model": config.get('api', {}).get('model', 'qwen-plus'),
        "provider": config.get('api', {}).get('provider', 'dashscope'),
        "vault_path": config.get('obsidian', {}).get('vault_path', ''),
    }


def save_settings(api_key, model, provider, vault_path):
    """保存设置"""
    config = load_config()

    if 'api' not in config:
        config['api'] = {}
    config['api']['api_key'] = api_key
    config['api']['model'] = model
    config['api']['provider'] = provider

    if provider == 'dashscope':
        config['api']['base_url'] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    else:
        config['api']['base_url'] = "https://api.openai.com/v1"

    if 'obsidian' not in config:
        config['obsidian'] = {}
    config['obsidian']['vault_path'] = vault_path

    save_config(config)
    return "设置已保存"


def refresh_cookie_action():
    """刷新Cookie"""
    try:
        from cookie_manager import refresh_cookie
        cookie = refresh_cookie()
        if cookie:
            return "Cookie刷新成功", cookie[:50] + "..." if len(cookie) > 50 else cookie
        else:
            return "Cookie刷新失败，请重试", ""
    except Exception as e:
        return f"错误: {str(e)}", ""


def validate_cookie_action():
    """验证Cookie格式"""
    try:
        from cookie_manager import CookieManager
        import re

        manager = CookieManager()
        cookie = manager.get_saved_cookie()

        if not cookie or len(cookie) < 50:
            return "Cookie为空，请点击刷新Cookie"

        def extract(cookie_str, key):
            match = re.search(rf'{key}=([^;]+)', cookie_str)
            return match.group(1) if match else ""

        a1 = extract(cookie, 'a1')
        web_session = extract(cookie, 'web_session')

        if a1 and web_session:
            return f"Cookie有效\na1: {a1[:15]}...\nweb_session: {web_session[:15]}..."
        elif a1:
            return "Cookie缺少web_session，可能无法发布"
        else:
            return "Cookie格式无效：缺少必要字段"
    except Exception as e:
        return f"验证失败: {str(e)}"


def scan_content_list():
    """扫描输出目录获取内容列表"""
    output_dir = get_output_dir()
    if not output_dir.exists():
        return []

    contents = []
    for batch_dir in sorted(output_dir.iterdir(), reverse=True):
        if not batch_dir.is_dir():
            continue

        content_file = batch_dir / "content.json"
        if not content_file.exists():
            continue

        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                content = json.load(f)

            # 检查发布状态
            status_file = batch_dir / "publish_status.json"
            status = "待发布"
            publish_info = {}
            if status_file.exists():
                with open(status_file, 'r', encoding='utf-8') as f:
                    publish_info = json.load(f)
                    status = "已发布" if publish_info.get('published') else "待发布"

            # 统计图片数量
            image_count = len(list(batch_dir.glob("slide_*.png"))) + (1 if (batch_dir / "cover.png").exists() else 0)

            contents.append({
                "batch_id": batch_dir.name,
                "title": content.get('title', '未知标题'),
                "status": status,
                "image_count": image_count,
                "path": str(batch_dir),
                "publish_info": publish_info
            })
        except Exception:
            continue

    return contents


def format_content_table():
    """格式化内容列表为表格数据"""
    contents = scan_content_list()
    if not contents:
        return [["暂无内容", "", "", ""]]

    table_data = []
    for c in contents[:20]:  # 最多显示20条
        status_icon = "🟢" if c["status"] == "已发布" else "🟡"
        table_data.append([
            c["batch_id"],
            c["title"][:25] + "..." if len(c["title"]) > 25 else c["title"],
            f"{status_icon} {c['status']}",
            f"{c['image_count']}张"
        ])
    return table_data


def get_content_detail(batch_id):
    """获取指定内容的详细信息"""
    if not batch_id or batch_id == "暂无内容":
        return "", "", None, [], ""

    output_dir = get_output_dir() / batch_id
    if not output_dir.exists():
        return "目录不存在", "", None, [], ""

    try:
        # 读取content.json
        content_file = output_dir / "content.json"
        if content_file.exists():
            with open(content_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
            title = content.get('title', '')
            caption = content.get('caption', '')
        else:
            title = ""
            caption = ""

        # 封面图片
        cover_path = output_dir / "cover.png"
        cover = str(cover_path) if cover_path.exists() else None

        # 内容页图片
        slides = []
        for i in range(1, 20):
            slide_path = output_dir / f"slide_{i}.png"
            if slide_path.exists():
                slides.append(str(slide_path))
            else:
                break

        return title, caption, cover, slides, str(output_dir)
    except Exception as e:
        return f"读取失败: {e}", "", None, [], ""


def generate_content(category, custom_topic, phrase_count, export_obsidian, progress=gr.Progress()):
    """生成内容"""
    try:
        from main import RedbookGenerator

        progress(0, desc="初始化...")
        generator = RedbookGenerator()

        progress(0.2, desc="正在生成选题...")
        progress(0.4, desc="正在生成文案...")
        progress(0.6, desc="正在渲染卡片...")
        progress(0.8, desc="正在生成图片...")

        topic_input = custom_topic.strip() if custom_topic.strip() else None

        result = generator.generate(
            category=category if not topic_input else "自定义",
            custom_topic=topic_input,
            phrase_count=int(phrase_count),
            export_obsidian=export_obsidian,
            auto_publish=False,
            is_private=True
        )

        progress(1.0, desc="完成")

        # 准备输出
        topic = result['topic_json'].get('topic', '未知')
        title = result['content_json'].get('title', '未知')
        caption = result['caption']
        cover_image = result['cover_image']
        slide_images = result['slide_images']
        output_dir = result['output_dir']
        batch_id = result['batch_id']

        status = f"生成成功\n批次: {batch_id}\n选题: {topic}"
        if result.get('obsidian_path'):
            status += f"\nObsidian: 已导出"

        # 更新列表
        table_data = format_content_table()

        return (
            status,
            title,
            caption,
            cover_image,
            slide_images,
            output_dir,
            batch_id,
            table_data
        )

    except Exception as e:
        import traceback
        error_msg = f"生成失败: {str(e)}\n{traceback.format_exc()}"
        return error_msg, "", "", None, [], "", "", format_content_table()


def publish_content(title, caption, output_dir, is_private):
    """发布内容到小红书"""
    if not output_dir:
        return "请先生成或选择内容", format_content_table()

    try:
        from xhs_publisher import publish_to_xiaohongshu

        output_path = Path(output_dir)
        if not output_path.exists():
            return f"输出目录不存在: {output_dir}", format_content_table()

        # 收集图片
        images = []
        cover = output_path / "cover.png"
        if cover.exists():
            images.append(str(cover))

        for i in range(1, 20):
            slide = output_path / f"slide_{i}.png"
            if slide.exists():
                images.append(str(slide))
            else:
                break

        if not images:
            return "未找到图片文件", format_content_table()

        # 处理标题
        title_clean = ''.join(c for c in title if ord(c) < 0x1F600 or ord(c) > 0x1F9FF)
        pub_title = title_clean[:20] if len(title_clean) > 20 else title_clean

        # 发布
        result = publish_to_xiaohongshu(
            title=pub_title,
            content=caption,
            image_paths=images,
            is_private=is_private
        )

        if result:
            # 保存发布状态
            status_file = output_path / "publish_status.json"
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "published": True,
                    "note_id": result.get('note_id', ''),
                    "is_private": is_private,
                    "publish_time": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            mode = "私密" if is_private else "公开"
            return f"发布成功\n笔记ID: {result.get('note_id', '未知')}\n模式: {mode}", format_content_table()
        else:
            return "发布失败，请检查Cookie是否有效", format_content_table()

    except Exception as e:
        import traceback
        return f"发布失败: {str(e)}\n{traceback.format_exc()}", format_content_table()


def delete_content(batch_id):
    """删除指定内容"""
    if not batch_id or batch_id == "暂无内容":
        return "请先选择内容", format_content_table()

    output_dir = get_output_dir() / batch_id
    if output_dir.exists():
        try:
            shutil.rmtree(output_dir)
            return f"已删除: {batch_id}", format_content_table()
        except Exception as e:
            return f"删除失败: {e}", format_content_table()
    else:
        return "目录不存在", format_content_table()


def on_table_select(evt: gr.SelectData):
    """表格选择事件处理"""
    if evt.value and evt.value != "暂无内容":
        row_index = evt.index[0]
        contents = scan_content_list()
        if row_index < len(contents):
            batch_id = contents[row_index]["batch_id"]
            title, caption, cover, slides, output_dir = get_content_detail(batch_id)
            return title, caption, cover, slides, output_dir, batch_id
    return "", "", None, [], "", ""


def create_ui():
    """创建Gradio界面"""

    settings = get_current_settings()

    with gr.Blocks(title="小红书内容生成器", css="""
        .status-box { font-size: 14px; }
        .compact-row { gap: 8px; }
    """) as app:
        gr.Markdown("# 小红书英语内容生成器")
        gr.Markdown("AI自动生成小红书英语教育内容，支持一键发布")

        with gr.Tabs():
            # ===== 生成内容标签页 =====
            with gr.TabItem("生成内容"):
                with gr.Row():
                    # 左侧：参数设置
                    with gr.Column(scale=1):
                        gr.Markdown("### 生成参数")

                        category_input = gr.Dropdown(
                            choices=CATEGORIES,
                            value="随机",
                            label="选择分类"
                        )

                        custom_topic_input = gr.Textbox(
                            value="",
                            label="自定义主题（可选）",
                            placeholder="如：公交车、咖啡店点单、投诉服务...",
                            lines=2,
                            info="填写后将忽略上方分类"
                        )

                        phrase_count_input = gr.Number(
                            value=5,
                            label="知识点数量",
                            minimum=3,
                            maximum=15,
                            step=1,
                            info="建议3-8个，太多影响阅读体验"
                        )

                        export_obsidian_input = gr.Checkbox(
                            value=True,
                            label="导出到Obsidian"
                        )

                        generate_btn = gr.Button(
                            "开始生成",
                            variant="primary",
                            size="lg"
                        )

                        status_output = gr.Textbox(
                            label="生成状态",
                            lines=4,
                            interactive=False
                        )

                    # 右侧：结果预览
                    with gr.Column(scale=2):
                        gr.Markdown("### 预览与编辑")

                        title_output = gr.Textbox(
                            label="标题（可编辑）",
                            interactive=True
                        )

                        caption_output = gr.Textbox(
                            label="正文（可编辑）",
                            lines=6,
                            interactive=True
                        )

                        # 隐藏状态
                        output_dir_state = gr.State(value="")
                        batch_id_state = gr.State(value="")

                        # 发布控制
                        gr.Markdown("### 发布")
                        with gr.Row():
                            is_private_input = gr.Checkbox(value=True, label="私密发布")
                            publish_btn = gr.Button("发布到小红书", variant="secondary")

                        publish_status = gr.Textbox(
                            label="发布状态",
                            lines=2,
                            interactive=False
                        )

                # 图片预览
                gr.Markdown("### 图片预览")
                with gr.Row():
                    cover_output = gr.Image(label="封面", height=300)
                    slides_output = gr.Gallery(
                        label="内容页",
                        columns=4,
                        height=300,
                        object_fit="contain"
                    )

            # ===== 内容管理标签页 =====
            with gr.TabItem("内容管理"):
                gr.Markdown("### 已生成内容")
                gr.Markdown("点击表格行查看详情，可发布或删除")

                refresh_list_btn = gr.Button("刷新列表", size="sm")

                content_table = gr.Dataframe(
                    headers=["批次ID", "标题", "状态", "图片"],
                    value=format_content_table(),
                    interactive=False,
                    row_count=(10, "fixed")
                )

                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 选中内容")
                        selected_batch = gr.Textbox(label="批次ID", interactive=False)
                        selected_title = gr.Textbox(label="标题", interactive=True)
                        selected_caption = gr.Textbox(label="正文", lines=5, interactive=True)
                        selected_dir = gr.State(value="")

                        with gr.Row():
                            manage_private = gr.Checkbox(value=True, label="私密发布")
                            manage_publish_btn = gr.Button("发布", variant="primary")
                            manage_delete_btn = gr.Button("删除", variant="stop")

                        manage_status = gr.Textbox(label="操作状态", interactive=False)

                    with gr.Column(scale=2):
                        gr.Markdown("### 图片预览")
                        selected_cover = gr.Image(label="封面", height=250)
                        selected_slides = gr.Gallery(
                            label="内容页",
                            columns=4,
                            height=250,
                            object_fit="contain"
                        )

            # ===== 设置标签页 =====
            with gr.TabItem("设置"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### API设置")

                        provider_input = gr.Dropdown(
                            choices=list(MODELS.keys()),
                            value=settings['provider'],
                            label="API提供商"
                        )

                        model_input = gr.Dropdown(
                            choices=MODELS.get(settings['provider'], []),
                            value=settings['model'],
                            label="模型"
                        )

                        api_key_input = gr.Textbox(
                            value=settings['api_key'],
                            label="API Key",
                            type="password"
                        )

                        def update_models(provider):
                            models = MODELS.get(provider, [])
                            return gr.Dropdown(choices=models, value=models[0] if models else "")

                        provider_input.change(
                            fn=update_models,
                            inputs=[provider_input],
                            outputs=[model_input]
                        )

                    with gr.Column():
                        gr.Markdown("### Obsidian设置")
                        vault_path_input = gr.Textbox(
                            value=settings['vault_path'],
                            label="Vault路径"
                        )

                        gr.Markdown("### 小红书Cookie")
                        cookie_status = gr.Textbox(
                            value="点击验证检查Cookie状态",
                            label="Cookie状态",
                            interactive=False
                        )

                        with gr.Row():
                            validate_cookie_btn = gr.Button("验证Cookie")
                            refresh_cookie_btn = gr.Button("刷新Cookie")

                        validate_cookie_btn.click(
                            fn=validate_cookie_action,
                            outputs=[cookie_status]
                        )

                        refresh_cookie_btn.click(
                            fn=refresh_cookie_action,
                            outputs=[cookie_status, gr.Textbox(visible=False)]
                        )

                gr.Markdown("---")

                with gr.Row():
                    save_btn = gr.Button("保存设置", variant="primary")
                    save_status = gr.Textbox(label="", interactive=False, scale=3)

                save_btn.click(
                    fn=save_settings,
                    inputs=[api_key_input, model_input, provider_input, vault_path_input],
                    outputs=[save_status]
                )

            # ===== 帮助标签页 =====
            with gr.TabItem("帮助"):
                gr.Markdown("""
                ## 使用说明

                ### 快速开始

                1. **配置API Key** - 在设置页面填入阿里千问或OpenAI的API Key
                2. **获取Cookie** - 点击"刷新Cookie"，在打开的浏览器中登录小红书
                3. **生成内容** - 选择分类或输入自定义主题，点击"开始生成"
                4. **发布** - 预览无误后点击"发布到小红书"

                ### 分类说明

                | 分类 | 示例场景 |
                |------|---------|
                | 餐饮美食 | 点餐、咖啡店、餐厅结账 |
                | 交通出行 | 打车、地铁、问路 |
                | 购物消费 | 商场购物、退换货 |
                | 职场办公 | 会议、邮件、同事交流 |
                | 社交聊天 | 聊天、约会、派对 |
                | 旅行住宿 | 酒店入住、景点咨询 |
                | 医疗健康 | 看病、药店买药 |
                | 租房生活 | 租房、水电缴费 |
                | 校园学习 | 课堂、图书馆 |
                | 娱乐休闲 | 电影、健身房 |

                ### 常见问题

                **Q: Cookie多久过期？**
                约1-2周，过期后重新刷新即可

                **Q: 发布失败怎么办？**
                1. 检查Cookie是否有效
                2. 标题不要超过20字
                3. 建议先私密发布测试

                **Q: 知识点数量多少合适？**
                建议5-8个，太少内容单薄，太多影响阅读体验
                """)

        # ===== 事件绑定 =====

        # 生成按钮
        generate_btn.click(
            fn=generate_content,
            inputs=[
                category_input,
                custom_topic_input,
                phrase_count_input,
                export_obsidian_input
            ],
            outputs=[
                status_output,
                title_output,
                caption_output,
                cover_output,
                slides_output,
                output_dir_state,
                batch_id_state,
                content_table
            ]
        )

        # 发布按钮（生成页面）
        publish_btn.click(
            fn=publish_content,
            inputs=[
                title_output,
                caption_output,
                output_dir_state,
                is_private_input
            ],
            outputs=[publish_status, content_table]
        )

        # 刷新列表
        refresh_list_btn.click(
            fn=format_content_table,
            outputs=[content_table]
        )

        # 表格选择
        content_table.select(
            fn=on_table_select,
            outputs=[
                selected_title,
                selected_caption,
                selected_cover,
                selected_slides,
                selected_dir,
                selected_batch
            ]
        )

        # 管理页面发布
        manage_publish_btn.click(
            fn=publish_content,
            inputs=[
                selected_title,
                selected_caption,
                selected_dir,
                manage_private
            ],
            outputs=[manage_status, content_table]
        )

        # 删除内容
        manage_delete_btn.click(
            fn=delete_content,
            inputs=[selected_batch],
            outputs=[manage_status, content_table]
        )

    return app


def main():
    """启动GUI"""
    app = create_ui()
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True
    )


if __name__ == "__main__":
    main()
