"""
Gradio GUI 界面 - 社媒辅助搜索引擎
"""
import gradio as gr
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Any, Generator
import time

from core.engine import SearchEngine
from storage import Database
from stats import StatsAnalyzer
from stats.charts import (
    create_time_trend_chart,
    create_platform_pie_chart,
    create_engagement_bar_chart,
    create_user_ranking_table,
)
from storage.export import export_session_report
from platforms import BilibiliPlatform, DouyinPlatform, XiaohongshuPlatform
from llm import LLMClient
import config


def get_scraper(platform: str):
    """获取平台爬虫实例"""
    if platform == 'bilibili':
        return BilibiliPlatform(cookie=config.BILIBILI_COOKIE)
    elif platform == 'douyin':
        return DouyinPlatform(cookie=config.DOUYIN_COOKIE)
    elif platform == 'xiaohongshu':
        return XiaohongshuPlatform(cookie=config.XIAOHONGSHU_COOKIE)
    else:
        raise ValueError(f"未知平台: {platform}")


# 全局引擎实例
engine = None
stats_analyzer = None
llm_client = None

# 当前会话数据（用于问答）
current_session_data = {
    "session_id": None,
    "keyword": "",
    "contents": [],
    "comments": [],
}


def init_engine():
    """初始化引擎"""
    global engine, stats_analyzer, llm_client
    if engine is None:
        db = Database(config.DB_PATH)
        engine = SearchEngine(db=db)
        stats_analyzer = StatsAnalyzer(db)
    if llm_client is None:
        llm_client = LLMClient()


def do_search_with_progress(keyword: str, platforms: List[str],
                            max_search: int, max_comments: int,
                            speed: str) -> Generator:
    """执行搜索（带进度显示）- 使用 yield 实时更新"""
    global current_session_data
    init_engine()

    empty_df = pd.DataFrame()

    if not keyword.strip():
        yield "请输入搜索关键词", empty_df, empty_df, None, None
        return

    if not platforms:
        platforms = ['bilibili', 'douyin', 'xiaohongshu']

    # 进度日志
    progress_logs = []

    def add_log(msg):
        progress_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        return "\n".join(progress_logs[-25:])

    yield add_log(f"开始搜索: {keyword}"), empty_df, empty_df, None, None
    yield add_log(f"平台: {', '.join(_platform_name(p) for p in platforms)}"), empty_df, empty_df, None, None

    try:
        # 阶段1: 多平台搜索
        yield add_log("【阶段1/4】多平台搜索中..."), empty_df, empty_df, None, None

        all_contents = []
        for platform in platforms:
            yield add_log(f"  搜索 {_platform_name(platform)}..."), empty_df, empty_df, None, None

            try:
                scraper = get_scraper(platform)
                contents = scraper.search(keyword, max_results=max_search)
                all_contents.extend(contents)
                yield add_log(f"  {_platform_name(platform)} 找到 {len(contents)} 条内容"), empty_df, empty_df, None, None
            except Exception as e:
                yield add_log(f"  {_platform_name(platform)} 搜索失败: {e}"), empty_df, empty_df, None, None

        if not all_contents:
            yield add_log("未找到任何内容，搜索结束"), empty_df, empty_df, None, None
            return

        yield add_log(f"搜索完成，共 {len(all_contents)} 条内容"), empty_df, empty_df, None, None

        # 阶段2: Layer1 规则筛选
        yield add_log("【阶段2/4】规则粗筛中..."), empty_df, empty_df, None, None
        layer1_passed, _ = engine.layer1.filter(all_contents)
        yield add_log(f"粗筛通过: {len(layer1_passed)}/{len(all_contents)}"), empty_df, empty_df, None, None

        # 阶段3: Layer2 LLM 精筛
        yield add_log("【阶段3/4】LLM 精筛中..."), empty_df, empty_df, None, None
        if llm_client.is_configured() and layer1_passed:
            try:
                layer2_passed, _ = engine.layer2.filter(layer1_passed, keyword)
                yield add_log(f"精筛通过: {len(layer2_passed)}/{len(layer1_passed)}"), empty_df, empty_df, None, None
            except Exception as e:
                layer2_passed = layer1_passed
                yield add_log(f"精筛出错，跳过: {e}"), empty_df, empty_df, None, None
        else:
            layer2_passed = layer1_passed
            if not llm_client.is_configured():
                yield add_log("跳过精筛（LLM 未配置）"), empty_df, empty_df, None, None

        # 阶段4: 评论抓取
        yield add_log("【阶段4/4】抓取评论中..."), empty_df, empty_df, None, None
        all_comments = []
        target_contents = layer2_passed if layer2_passed else layer1_passed[:5]

        for i, content in enumerate(target_contents, 1):
            title_short = content.title[:25] + '...' if len(content.title or '') > 25 else content.title
            yield add_log(f"  [{i}/{len(target_contents)}] {title_short}"), empty_df, empty_df, None, None

            try:
                scraper = get_scraper(content.platform)
                comments = scraper.get_comments(content.content_id, url=content.url, max_count=max_comments)
                all_comments.extend(comments)
                yield add_log(f"    获取 {len(comments)} 条评论"), empty_df, empty_df, None, None
            except Exception as e:
                yield add_log(f"    评论抓取失败: {e}"), empty_df, empty_df, None, None

            # 控制速度
            delay = config.SPEED_PRESETS.get(speed, (1, 2))[0]
            time.sleep(delay)

        yield add_log(f"评论抓取完成，共 {len(all_comments)} 条"), empty_df, empty_df, None, None

        # 保存到数据库
        yield add_log("保存数据中..."), empty_df, empty_df, None, None

        # 生成会话ID
        session_id = f"s_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        engine.db.create_session(session_id, keyword, platforms)

        # 准备内容数据
        contents_data = []
        for content in all_contents:
            content_dict = content.to_dict() if hasattr(content, 'to_dict') else {
                'platform': content.platform,
                'content_id': content.content_id,
                'title': content.title,
                'url': content.url,
                'author': content.author,
                'description': getattr(content, 'description', ''),
                'likes': content.likes,
                'comments': content.comment_count,
                'views': content.views,
                'publish_time': content.publish_time,
            }
            content_dict['layer1_pass'] = content in layer1_passed
            content_dict['layer2_pass'] = content in layer2_passed
            content_dict['layer2_score'] = getattr(content, 'relevance_score', None)
            contents_data.append(content_dict)

        engine.db.insert_contents(session_id, contents_data)

        # 准备评论数据
        comments_data = []
        for comment in all_comments:
            comment_dict = comment.to_dict() if hasattr(comment, 'to_dict') else {
                'content_id': comment.content_id,
                'platform': comment.platform,
                'comment_id': comment.comment_id,
                'username': comment.username,
                'text': comment.text,
                'likes': comment.likes,
                'create_time': comment.publish_time,
                'ip_location': comment.ip_location,
            }
            comments_data.append(comment_dict)

        engine.db.insert_comments(session_id, comments_data)

        # 更新会话统计
        engine.db.update_session_stats(
            session_id,
            total_contents=len(all_contents),
            layer1_passed=len(layer1_passed),
            layer2_passed=len(layer2_passed),
            total_comments=len(all_comments),
        )

        # 更新全局数据（用于问答）
        current_session_data["session_id"] = session_id
        current_session_data["keyword"] = keyword
        current_session_data["contents"] = all_contents
        current_session_data["comments"] = all_comments

        # 准备显示数据
        contents_df = pd.DataFrame([
            {
                '平台': _platform_name(c.platform),
                '标题': c.title[:40] + '...' if len(c.title or '') > 40 else c.title,
                '作者': c.author,
                '粗筛': '✓' if c in layer1_passed else '✗',
                '精筛': '✓' if c in layer2_passed else '✗',
            }
            for c in all_contents
        ])

        comments_df = pd.DataFrame([
            {
                '用户': c.username,
                '内容': c.text[:60] + '...' if len(c.text or '') > 60 else c.text,
                '点赞': c.likes,
                '平台': _platform_name(c.platform),
            }
            for c in all_comments[:100]
        ])

        # 统计图表
        try:
            stats = stats_analyzer.analyze(session['session_id'], '7d')
            time_chart = create_time_trend_chart(stats['time'])
            platform_chart = create_platform_pie_chart(stats['platform'])
        except:
            time_chart = None
            platform_chart = None

        final_status = (
            f"搜索完成!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"内容总数: {len(all_contents)}\n"
            f"粗筛通过: {len(layer1_passed)}\n"
            f"精筛通过: {len(layer2_passed)}\n"
            f"评论总数: {len(all_comments)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"会话ID: {session['session_id']}\n"
            f"可在「数据问答」标签页提问"
        )

        yield final_status, contents_df, comments_df, time_chart, platform_chart

    except Exception as e:
        yield add_log(f"搜索失败: {str(e)}"), empty_df, empty_df, None, None


def do_chat(question: str, history: List[List[str]]) -> Tuple[List[List[str]], str]:
    """数据问答"""
    init_engine()

    if not question.strip():
        return history, ""

    if not current_session_data["comments"]:
        history.append([question, "暂无数据，请先在「搜索」标签页进行搜索"])
        return history, ""

    if not llm_client.is_configured():
        history.append([question, "LLM 未配置，请在 config.py 中设置 LLM_API_KEY"])
        return history, ""

    # 构建评论上下文
    comments = current_session_data["comments"]
    keyword = current_session_data["keyword"]

    context_lines = []
    total_chars = 0
    max_chars = 20000

    for c in comments[:200]:
        line = f"- [{c.username}] {c.text}"
        if total_chars + len(line) > max_chars:
            break
        context_lines.append(line)
        total_chars += len(line)

    context_text = "\n".join(context_lines)

    # 调用 LLM
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    f"你是一个社交媒体数据分析助手。用户正在研究话题「{keyword}」。\n"
                    "你需要基于提供的评论数据回答用户问题。\n"
                    "回答要具体、有洞察，如果数据中没有相关信息要明确说明。\n"
                    "用中文回答，简洁清晰。"
                ),
            },
            {
                "role": "user",
                "content": f"以下是从各平台抓取的 {len(context_lines)} 条评论:\n\n{context_text}\n\n用户问题: {question}",
            },
        ]
        answer = llm_client.chat(messages, temperature=0.5)
    except Exception as e:
        answer = f"调用 LLM 失败: {e}"

    history.append([question, answer])
    return history, ""


def load_history_session(history_selection: str) -> Tuple:
    """加载历史会话"""
    global current_session_data
    init_engine()

    empty_df = pd.DataFrame()

    if not history_selection:
        return empty_df, empty_df, None, None, "请选择历史记录"

    session_id = history_selection.split(' - ')[0]

    try:
        results = engine.get_session_results(session_id)

        if not results:
            return empty_df, empty_df, None, None, "会话不存在"

        # 更新全局数据（用于问答）
        current_session_data["session_id"] = session_id
        current_session_data["keyword"] = results['session'].get('keyword', '') if results.get('session') else ''

        # 将 dict 转换为类似对象用于问答
        class CommentObj:
            def __init__(self, d):
                self.username = d.get('username', '')
                self.text = d.get('text', '')

        current_session_data["comments"] = [CommentObj(c) for c in results['comments']]

        contents_df = pd.DataFrame([
            {
                '平台': _platform_name(c['platform']),
                '标题': c['title'][:40] + '...' if len(c['title'] or '') > 40 else c['title'],
                '作者': c['author'],
                '粗筛': '✓' if c['layer1_pass'] else '✗',
                '精筛': '✓' if c['layer2_pass'] else '✗',
            }
            for c in results['contents']['all']
        ])

        comments_df = pd.DataFrame([
            {
                '用户': c['username'],
                '内容': c['text'][:60] + '...' if len(c['text'] or '') > 60 else c['text'],
                '点赞': c['likes'],
                '平台': _platform_name(c['platform']),
            }
            for c in results['comments'][:100]
        ])

        try:
            stats = stats_analyzer.analyze(session_id, '7d')
            time_chart = create_time_trend_chart(stats['time'])
            platform_chart = create_platform_pie_chart(stats['platform'])
        except:
            time_chart = None
            platform_chart = None

        status = f"已加载会话: {session_id}\n评论: {len(results['comments'])} 条\n可在「数据问答」标签页提问"

        return contents_df, comments_df, time_chart, platform_chart, status

    except Exception as e:
        return empty_df, empty_df, None, None, f"加载失败: {str(e)}"


def export_report(history_selection: str) -> str:
    """导出报告"""
    init_engine()

    if not history_selection:
        return "请先选择会话"

    session_id = history_selection.split(' - ')[0]

    try:
        filepath = export_session_report(engine.db, session_id)
        return f"已导出: {filepath}"
    except Exception as e:
        return f"导出失败: {str(e)}"


def refresh_history() -> gr.update:
    """刷新历史记录列表"""
    init_engine()
    try:
        history = engine.get_history(20)
        choices = [
            f"{h['session_id']} - {h['keyword']} ({h['created_at'][:10]})"
            for h in history
        ]
        return gr.update(choices=choices)
    except:
        return gr.update(choices=[])


def _platform_name(platform: str) -> str:
    """平台名称映射"""
    return {
        'bilibili': 'B站',
        'douyin': '抖音',
        'xiaohongshu': '小红书',
    }.get(platform, platform)


def create_app():
    """创建 Gradio 应用"""

    with gr.Blocks(
        title="社媒辅助搜索引擎",
        theme=gr.themes.Soft(),
        css="""
        .contain { max-width: 1400px; margin: auto; }
        .progress-box textarea { font-family: monospace !important; font-size: 13px !important; }
        """
    ) as app:

        gr.Markdown("# 社媒辅助搜索引擎")
        gr.Markdown("搜索 B站、抖音、小红书 → 智能筛选 → 数据问答")

        with gr.Tabs():
            # ============ Tab 1: 搜索 ============
            with gr.Tab("搜索"):
                with gr.Row():
                    with gr.Column(scale=3):
                        keyword_input = gr.Textbox(
                            label="搜索关键词",
                            placeholder="输入要搜索的话题，如：春招AI岗位简历",
                            lines=1,
                        )
                    with gr.Column(scale=2):
                        platform_select = gr.CheckboxGroup(
                            choices=["bilibili", "douyin", "xiaohongshu"],
                            value=["bilibili", "douyin", "xiaohongshu"],
                            label="搜索平台",
                        )

                with gr.Row():
                    max_search = gr.Slider(1, 20, value=5, step=1, label="每平台搜索数")
                    max_comments = gr.Slider(10, 200, value=50, step=10, label="每内容评论数")
                    speed_select = gr.Dropdown(
                        choices=["fast", "normal", "slow", "safe"],
                        value="safe",
                        label="速度档位",
                    )
                    search_btn = gr.Button("开始搜索", variant="primary", size="lg")

                # 进度显示区
                progress_box = gr.Textbox(
                    label="搜索进度",
                    lines=15,
                    interactive=False,
                    elem_classes=["progress-box"],
                )

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 内容列表")
                        content_table = gr.Dataframe(
                            headers=['平台', '标题', '作者', '粗筛', '精筛'],
                            interactive=False,
                            wrap=True,
                        )
                    with gr.Column():
                        gr.Markdown("### 评论数据")
                        comment_table = gr.Dataframe(
                            headers=['用户', '内容', '点赞', '平台'],
                            interactive=False,
                            wrap=True,
                        )

                with gr.Row():
                    time_chart = gr.Plot(label="时间趋势")
                    platform_chart = gr.Plot(label="平台分布")

            # ============ Tab 2: 数据问答 ============
            with gr.Tab("数据问答"):
                gr.Markdown("### 基于搜索结果的智能问答")
                gr.Markdown("搜索完成后，可以在这里对抓取的数据进行提问分析")

                chatbot = gr.Chatbot(
                    label="对话",
                    height=450,
                )

                with gr.Row():
                    chat_input = gr.Textbox(
                        label="输入问题",
                        placeholder="例如：用户对这个话题的主要看法是什么？负面评价集中在哪些方面？",
                        lines=2,
                        scale=4,
                    )
                    chat_btn = gr.Button("发送", variant="primary", scale=1)

                clear_chat_btn = gr.Button("清空对话")

                gr.Markdown("""
                **提问示例：**
                - 用户对这个话题的主要观点是什么？
                - 负面评价主要集中在哪些方面？
                - 有哪些有价值的建议或反馈？
                - 总结一下用户最关心的问题
                - 有没有提到具体的数据或案例？
                - 哪些用户的观点比较有代表性？
                """)

            # ============ Tab 3: 历史记录 ============
            with gr.Tab("历史记录"):
                with gr.Row():
                    history_dropdown = gr.Dropdown(
                        label="选择历史会话",
                        choices=[],
                        interactive=True,
                        scale=3,
                    )
                    refresh_btn = gr.Button("刷新列表", scale=1)
                    load_btn = gr.Button("加载", variant="primary", scale=1)
                    export_btn = gr.Button("导出报告", scale=1)

                history_status = gr.Textbox(label="状态", interactive=False, lines=3)

                with gr.Row():
                    history_content_table = gr.Dataframe(
                        headers=['平台', '标题', '作者', '粗筛', '精筛'],
                        interactive=False,
                        wrap=True,
                    )
                    history_comment_table = gr.Dataframe(
                        headers=['用户', '内容', '点赞', '平台'],
                        interactive=False,
                        wrap=True,
                    )

                with gr.Row():
                    history_time_chart = gr.Plot(label="时间趋势")
                    history_platform_chart = gr.Plot(label="平台分布")

        # ============ 事件绑定 ============

        # 搜索（带进度）
        search_btn.click(
            fn=do_search_with_progress,
            inputs=[keyword_input, platform_select, max_search, max_comments, speed_select],
            outputs=[progress_box, content_table, comment_table, time_chart, platform_chart],
        )

        # 数据问答
        chat_btn.click(
            fn=do_chat,
            inputs=[chat_input, chatbot],
            outputs=[chatbot, chat_input],
        )

        chat_input.submit(
            fn=do_chat,
            inputs=[chat_input, chatbot],
            outputs=[chatbot, chat_input],
        )

        clear_chat_btn.click(
            fn=lambda: ([], ""),
            outputs=[chatbot, chat_input],
        )

        # 历史记录
        refresh_btn.click(
            fn=refresh_history,
            outputs=[history_dropdown],
        )

        load_btn.click(
            fn=load_history_session,
            inputs=[history_dropdown],
            outputs=[history_content_table, history_comment_table, history_time_chart, history_platform_chart, history_status],
        )

        export_btn.click(
            fn=export_report,
            inputs=[history_dropdown],
            outputs=[history_status],
        )

        # 启动时刷新历史
        app.load(fn=refresh_history, outputs=[history_dropdown])

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name=config.GUI_HOST,
        server_port=config.GUI_PORT,
        share=False,
    )
