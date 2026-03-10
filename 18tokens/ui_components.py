"""
UI组件模块
==========
所有Gradio UI组件的定义和事件处理
"""

import gradio as gr
import pandas as pd
import plotly.express as px
import os

from config import MODELS, MODEL_CHOICES, LANGUAGE_CHOICES, DASHSCOPE_API_KEY, OPENAI_API_KEY
from api import call_api, calculate_cost, get_model_name
from utils import (
    translate_to_english,
    HistoryManager,
    format_result_markdown,
    create_result_record,
)


# 全局历史记录管理器
history_manager = HistoryManager()
current_comparison_results = []


# ==================== 页面头部 ====================
def create_header():
    """创建页面头部"""
    return gr.Markdown("""
    # Token消耗对比工具

    <div style="text-align: center; color: #666; margin-bottom: 20px;">
        一键对比不同语言和模型下的Token消耗、响应质量与成本
    </div>
    """, elem_id="header")


# ==================== 一键对比标签页 ====================
def create_comparison_tab():
    """创建一键对比标签页"""

    with gr.Row():
        # 左侧：输入设置
        with gr.Column(scale=1):
            gr.Markdown("### 输入设置")

            question_input = gr.Textbox(
                label="问题内容",
                placeholder="请输入您想测试的问题...",
                value="北京今天天气怎么样",
                lines=3
            )

            language_radio = gr.Radio(
                label="输入语言",
                choices=LANGUAGE_CHOICES,
                value="中文"
            )

            model_checkboxes = gr.CheckboxGroup(
                label="选择模型（可多选）",
                choices=MODEL_CHOICES,
                value=["阿里云百炼: qwen-plus"]
            )

            image_input = gr.Image(
                label="上传图片（仅图片中文模式）",
                type="filepath",
                visible=False
            )

            compare_btn = gr.Button(
                "一键对比",
                variant="primary",
                size="lg"
            )

            # 翻译验证区
            gr.Markdown("### 翻译对照")
            with gr.Row():
                with gr.Column():
                    original_text = gr.Textbox(
                        label="原始问题（中文）",
                        interactive=False,
                        lines=2
                    )
                with gr.Column():
                    translated_text = gr.Textbox(
                        label="翻译问题（英文）",
                        interactive=True,
                        lines=2,
                        placeholder="请检查翻译是否正确..."
                    )

            translate_btn = gr.Button("更新翻译", size="sm")

        # 右侧：结果展示
        with gr.Column(scale=2):
            gr.Markdown("### 对比结果")

            # 统计卡片
            with gr.Row():
                avg_cost_card = gr.Markdown("**平均花费**: $0.0000")
                avg_tokens_card = gr.Markdown("**平均Token**: 0")
                best_cost_card = gr.Markdown("**最低花费**: $0.0000")

            # 结果表格
            results_table = gr.Dataframe(
                headers=["模型", "语言", "输入Token", "输出Token", "总Token", "花费($)", "延迟(ms)", "评分"],
                datatype=["str", "str", "number", "number", "number", "number", "number", "number"],
                interactive=True,
                wrap=True,
                max_height=400
            )

            # 响应内容
            gr.Markdown("### 详细响应内容")
            with gr.Accordion("点击展开/收起所有响应", open=False):
                responses_display = gr.Markdown("**请运行对比后查看结果**")

    # ========== 事件处理 ==========
    def update_translation(question, language):
        """更新翻译"""
        if language == "中文":
            return question, translate_to_english(question)
        elif language == "英文":
            return question, question
        return question, "[图片模式]"

    def on_language_change(language):
        """语言切换时更新图片输入可见性"""
        return gr.update(visible=(language == "图片中文"))

    def run_comparison(question, language, selected_models, image_path):
        """执行对比"""
        global current_comparison_results

        results = []
        responses_html = []

        # 准备不同语言的问题
        if language == "中文":
            content_cn = f"请用中文回答：{question}"
            content_en = f"Please answer in Chinese: {translate_to_english(question)}"
        elif language == "英文":
            content_cn = f"Please answer in English: {question}"
            content_en = f"Please answer in English: {question}"
        else:
            content_cn = None
            content_en = None

        for model_full in selected_models:
            provider, model_id = model_full.split(": ")

            # 确定内容和模式
            if language == "图片中文":
                content = image_path
                is_image = True
                display_lang = "图片中文"
            else:
                content = content_cn if "英文" not in language else content_en
                is_image = False
                display_lang = language

            # 调用API
            usage, response = call_api(model_id, content, is_image)
            cost = calculate_cost(model_id, usage)
            model_name = get_model_name(model_id)

            # 创建记录
            result = create_result_record(
                model_id, model_name, display_lang, question, usage, cost, response
            )
            results.append(result)
            history_manager.add(result)

            responses_html.append(format_result_markdown(result))

        current_comparison_results = results

        # 构建表格数据
        table_data = [
            [r["model_name"], r["language"], r["prompt_tokens"], r["completion_tokens"],
             r["total_tokens"], f"${r['cost']:.6f}", r["latency_ms"], r["accuracy_rating"]]
            for r in results
        ]

        # 计算统计
        if results:
            avg_cost = sum(r["cost"] for r in results) / len(results)
            avg_tokens = sum(r["total_tokens"] for r in results) / len(results)
            best_cost = min(r["cost"] for r in results)
            stats = [
                f"**平均花费**: ${avg_cost:.6f}",
                f"**平均Token**: {avg_tokens:.0f}",
                f"**最低花费**: ${best_cost:.6f}"
            ]
        else:
            stats = ["**平均花费**: $0", "**平均Token**: 0", "**最低花费**: $0"]

        responses_md = "\n\n".join(responses_html) if responses_html else "**请运行对比后查看结果**"

        return table_data, stats[0], stats[1], stats[2], responses_md

    # 绑定事件
    translate_btn.click(update_translation, [question_input, language_radio], [original_text, translated_text])
    language_radio.change(on_language_change, [language_radio], [image_input])
    compare_btn.click(
        run_comparison,
        [question_input, language_radio, model_checkboxes, image_input],
        [results_table, avg_cost_card, avg_tokens_card, best_cost_card, responses_display]
    )
    question_input.change(update_translation, [question_input, language_radio], [original_text, translated_text])

    return {
        "question_input": question_input,
        "language_radio": language_radio,
        "model_checkboxes": model_checkboxes,
        "image_input": image_input,
        "compare_btn": compare_btn,
        "results_table": results_table,
    }


# ==================== 历史记录标签页 ====================
def create_history_tab():
    """创建历史记录标签页"""

    gr.Markdown("### 历史记录")

    with gr.Row():
        with gr.Column(scale=2):
            history_table = gr.Dataframe(
                headers=["时间", "模型", "语言", "问题", "输入Token", "输出Token", "总Token", "花费($)", "评分"],
                datatype=["str", "str", "str", "str", "number", "number", "number", "number", "number"],
                interactive=True,
                wrap=True,
                max_height=500
            )

            with gr.Row():
                clear_history_btn = gr.Button("清空历史", variant="stop")
                export_history_btn = gr.Button("导出CSV")

        with gr.Column(scale=1):
            gr.Markdown("### 筛选条件")

            all_model_names = ["全部"] + [get_model_name(m["id"]) for p in MODELS.values() for m in p]
            filter_model = gr.Dropdown(label="按模型筛选", choices=all_model_names, value="全部")
            filter_language = gr.Dropdown(label="按语言筛选", choices=["全部"] + LANGUAGE_CHOICES, value="全部")
            filter_btn = gr.Button("筛选")

            gr.Markdown("### 统计概览")
            total_runs = gr.Markdown("**总测试次数**: 0")
            total_cost = gr.Markdown("**总花费**: $0.000000")
            avg_rating = gr.Markdown("**平均评分**: 0.0")

    def update_history_table(model_filter, language_filter):
        """更新历史表格"""
        filtered = history_manager.filter(model_filter, language_filter)
        table_data = history_manager.to_table_data(filtered)
        stats = history_manager.get_statistics(filtered)

        return (
            table_data,
            f"**总测试次数**: {stats['total']}",
            f"**总花费**: ${stats['cost']:.6f}",
            f"**平均评分**: {stats['avg_rating']:.1f}"
        )

    def clear_history():
        """清空历史"""
        history_manager.clear()
        return [], "**总测试次数**: 0", "**总花费**: $0.000000", "**平均评分**: 0.0"

    def export_csv():
        """导出CSV"""
        return history_manager.export_csv(os.path.dirname(__file__))

    filter_btn.click(update_history_table, [filter_model, filter_language], [history_table, total_runs, total_cost, avg_rating])
    clear_history_btn.click(clear_history, outputs=[history_table, total_runs, total_cost, avg_rating])
    export_history_btn.click(export_csv, outputs=gr.File(label="下载CSV"))

    return history_table


# ==================== 数据分析标签页 ====================
def create_analytics_tab():
    """创建数据分析标签页"""

    gr.Markdown("### 数据分析")

    with gr.Row():
        with gr.Column():
            gr.Markdown("#### Token消耗对比")
            token_chart = gr.Plot()

        with gr.Column():
            gr.Markdown("#### 成本对比")
            cost_chart = gr.Plot()

    with gr.Row():
        with gr.Column():
            gr.Markdown("#### 语言效率对比")
            lang_chart = gr.Plot()

        with gr.Column():
            gr.Markdown("#### 模型响应时间")
            latency_chart = gr.Plot()

    def update_charts():
        """更新图表"""
        if not history_manager.data:
            empty_df = pd.DataFrame({"模型": [], "Token数": [], "花费": [], "语言": [], "延迟": []})
            fig1 = px.bar(empty_df, x="模型", y="Token数", title="暂无数据")
            fig2 = px.bar(empty_df, x="模型", y="花费", title="暂无数据")
            fig3 = px.bar(empty_df, x="语言", y="Token数", title="暂无数据")
            fig4 = px.bar(empty_df, x="模型", y="延迟", title="暂无数据")
            return fig1, fig2, fig3, fig4

        df = pd.DataFrame(history_manager.data)

        # Token对比
        fig1 = px.bar(
            df, x="model_name", y="total_tokens", color="language",
            title="各模型Token消耗对比", barmode="group",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig1.update_layout(plot_bgcolor="rgba(240,240,240,0.5)", paper_bgcolor="white")

        # 成本对比
        fig2 = px.bar(
            df, x="model_name", y="cost", color="language",
            title="各模型成本对比", barmode="group",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig2.update_layout(plot_bgcolor="rgba(240,240,240,0.5)", paper_bgcolor="white")

        # 语言效率
        lang_stats = df.groupby("language").agg({"total_tokens": "mean", "cost": "mean"}).reset_index()
        fig3 = px.bar(
            lang_stats, x="language", y="total_tokens",
            title="不同语言平均Token消耗", color="language",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig3.update_layout(plot_bgcolor="rgba(240,240,240,0.5)", paper_bgcolor="white")

        # 响应时间
        fig4 = px.bar(
            df, x="model_name", y="latency_ms",
            title="各模型响应时间", color="model_name",
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        fig4.update_layout(plot_bgcolor="rgba(240,240,240,0.5)", paper_bgcolor="white")

        return fig1, fig2, fig3, fig4

    refresh_btn = gr.Button("刷新图表")
    refresh_btn.click(update_charts, outputs=[token_chart, cost_chart, lang_chart, latency_chart])

    return {"token_chart": token_chart, "cost_chart": cost_chart, "lang_chart": lang_chart, "latency_chart": latency_chart}


# ==================== 设置标签页 ====================
def create_settings_tab():
    """创建设置标签页"""

    gr.Markdown("### API设置")

    with gr.Row():
        with gr.Column():
            gr.Markdown("#### 阿里云百炼")
            dashscope_key = gr.Textbox(
                label="DashScope API Key",
                value=DASHSCOPE_API_KEY[:10] + "...",
                type="password",
                interactive=True
            )

        with gr.Column():
            gr.Markdown("#### OpenAI")
            openai_key = gr.Textbox(
                label="OpenAI API Key",
                value=OPENAI_API_KEY[:10] + "...",
                type="password",
                interactive=True
            )

    gr.Markdown("### 模型价格配置（每1K tokens）")

    with gr.Accordion("点击展开/收起价格详情", open=False):
        price_info = """
        | 模型 | 输入价格($) | 输出价格($) |
        |------|------------|------------|
        | qwen-turbo | 0.001 | 0.002 |
        | qwen-plus | 0.004 | 0.012 |
        | qwen-max | 0.02 | 0.06 |
        | qwen-vl-plus | 0.005 | 0.015 |
        | gpt-4o-mini | 0.00015 | 0.0006 |
        | gpt-4o | 0.0025 | 0.01 |
        | gpt-4-turbo | 0.01 | 0.03 |
        """
        gr.Markdown(price_info)

    gr.Markdown("### 使用说明")
    gr.Markdown("""
    1. **一键对比**: 在对比页面选择问题和模型，点击"一键对比"按钮
    2. **翻译验证**: 提交前检查英文翻译是否正确
    3. **评分**: 在结果表格中可以给响应质量打分（1-5分）
    4. **历史**: 所有测试都会保存到历史记录中
    5. **分析**: 在数据分析页面查看图表统计
    """)

    save_btn = gr.Button("保存设置", variant="primary")

    return {"dashscope_key": dashscope_key, "openai_key": openai_key, "save_btn": save_btn}
