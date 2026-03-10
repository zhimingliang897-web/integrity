"""
Token消耗对比工具 - Gradio Web版
================================

主入口文件，负责组装和启动应用

功能：
- 一键对比多语言、多模型的Token消耗
- 翻译对照验证
- 历史记录与数据分析
- 准确率评分与花费展示

模块结构：
- config.py      : 配置信息（API密钥、模型配置、价格等）
- api.py         : API调用（调用接口、成本计算）
- utils.py       : 工具函数（翻译、历史管理、数据格式化）
- ui_components.py: UI组件（各个标签页的定义）
"""

import gradio as gr

from config import APP_CONFIG, THEME, CSS
from ui_components import (
    create_header,
    create_comparison_tab,
    create_history_tab,
    create_analytics_tab,
    create_settings_tab,
)


def create_app() -> gr.Blocks:
    """
    创建完整的Gradio应用

    Returns:
        Gradio Blocks应用实例
    """
    with gr.Blocks(title=APP_CONFIG["title"]) as app:

        # 页面头部
        create_header()

        # 标签页
        with gr.Tabs():
            with gr.Tab("一键对比"):
                create_comparison_tab()

            with gr.Tab("历史记录"):
                create_history_tab()

            with gr.Tab("数据分析"):
                create_analytics_tab()

            with gr.Tab("设置"):
                create_settings_tab()

        # 页脚
        gr.Markdown(f"""
        <div style="text-align: center; color: #999; margin-top: 30px; padding: 20px;">
            {APP_CONFIG['title']} v{APP_CONFIG['version']} | 基于Gradio构建
        </div>
        """)

    return app


def main():
    """主函数：创建并启动应用"""
    app = create_app()

    # Gradio 6.0: theme和css移到launch()
    theme = gr.themes.Soft(
        primary_hue=THEME["primary_hue"],
        secondary_hue=THEME["secondary_hue"],
        neutral_hue=THEME["neutral_hue"],
        font=THEME["font"]
    )

    app.launch(
        server_name=APP_CONFIG["server_name"],
        server_port=APP_CONFIG["server_port"],
        share=False,
        show_error=True,
        theme=theme,
        css=CSS,
        inbrowser=True  # 自动打开浏览器
    )


if __name__ == "__main__":
    main()
