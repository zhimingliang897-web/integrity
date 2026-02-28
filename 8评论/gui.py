from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

import config


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = (BASE_DIR / getattr(config, "OUTPUT_DIR", "output")).resolve()
PLATFORMS = ["bilibili", "douyin", "xiaohongshu"]
SPEEDS = ["fast", "normal", "slow", "safe"]

DEFAULT_SPEED = getattr(config, "DEFAULT_SPEED", "safe")
DEFAULT_MAX_SEARCH = int(getattr(config, "TOPIC_MAX_SEARCH", 5))
DEFAULT_MAX_COMMENTS = int(getattr(config, "TOPIC_MAX_COMMENTS", 50))
DEFAULT_MODEL = getattr(config, "LLM_MODEL", "deepseek-v3.1")

# 从配置中获取模型和API地址列表
AVAILABLE_MODELS = getattr(config, "AVAILABLE_MODELS", ["deepseek-v3.1", "qwen-plus", "gpt-3.5-turbo"])
AVAILABLE_API_URLS = getattr(config, "AVAILABLE_API_URLS", ["https://dashscope.aliyuncs.com/compatible-mode/v1"])


def has_streamlit_context() -> bool:
    """Return True when script is executed by `streamlit run`."""
    try:
        import streamlit.runtime as runtime
    except Exception:  # noqa: BLE001
        return False
    return runtime.exists()


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def list_datasets() -> list[Path]:
    ensure_output_dir()
    files = [p for p in OUTPUT_DIR.rglob("*") if p.suffix.lower() in {".csv", ".xlsx"}]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(BASE_DIR))
    except ValueError:
        return str(path)


def load_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".xlsx":
        return pd.read_excel(path)

    last_err: Exception | None = None
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception as err:  # noqa: BLE001
            last_err = err
    raise RuntimeError(f"读取文件失败: {path} ({last_err})")


def build_context(df: pd.DataFrame, max_comments: int = 300, max_chars: int = 30000) -> tuple[str, int]:
    if "content" not in df.columns:
        return "", 0

    lines: list[str] = []
    used = 0
    total_chars = 0

    for raw in df["content"].dropna().astype(str):
        text = raw.strip()
        if not text:
            continue

        line = f"- {text}"
        if total_chars + len(line) + 1 > max_chars:
            break

        lines.append(line)
        total_chars += len(line) + 1
        used += 1

        if used >= max_comments:
            break

    return "\n".join(lines), used


def run_cli(args: list[str], log_placeholder: Any) -> tuple[int, str]:
    cmd = [sys.executable, "main.py", *args]
    preview = subprocess.list2cmdline(cmd)
    st.caption(f"执行命令: `{preview}`")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    process = subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    logs: list[str] = []
    if process.stdout is not None:
        for line in process.stdout:
            line = line.rstrip("\n")
            logs.append(line)
            log_placeholder.code("\n".join(logs[-300:]) or "(无输出)", language="text")

    code = process.wait()
    if not logs:
        log_placeholder.code("(无输出)", language="text")

    return code, "\n".join(logs)


def run_and_render(args: list[str], title: str) -> bool:
    with st.expander(f"{title}日志", expanded=True):
        placeholder = st.empty()
        code, _ = run_cli(args, placeholder)

    if code == 0:
        st.success(f"✅ {title}完成")
        return True

    st.error(f"❌ {title}失败，退出码: {code}")
    return False


def init_session_state() -> None:
    """初始化会话状态中的配置项"""
    # API配置
    if "llm_base_url" not in st.session_state:
        st.session_state.llm_base_url = getattr(config, "LLM_BASE_URL", "")
    if "llm_api_key" not in st.session_state:
        st.session_state.llm_api_key = getattr(config, "LLM_API_KEY", "")
    if "llm_model" not in st.session_state:
        st.session_state.llm_model = getattr(config, "LLM_MODEL", "deepseek-v3.1")
    # 自定义API URL开关
    if "use_custom_api_url" not in st.session_state:
        st.session_state.use_custom_api_url = False
    # 自定义模型开关
    if "use_custom_model" not in st.session_state:
        st.session_state.use_custom_model = False


def render_sidebar() -> None:
    with st.sidebar:
        # 标题
        st.header("环境信息")
        st.write(f"项目目录: `{BASE_DIR}`")
        st.write(f"输出目录: `{OUTPUT_DIR}`")
        st.write(f"默认速度: `{DEFAULT_SPEED}`")

        st.divider()

        # LLM 配置区域
        st.header("🤖 LLM 配置")

        # API地址配置
        st.subheader("API 配置")

        # 是否使用自定义API地址
        use_custom = st.toggle("自定义API地址", value=st.session_state.get("use_custom_api_url", False), key="toggle_custom_url")
        st.session_state.use_custom_api_url = use_custom

        if use_custom:
            # 自定义API地址输入
            base_url = st.text_input(
                "API Base URL",
                value=st.session_state.get("llm_base_url", ""),
                placeholder="https://api.openai.com/v1",
                key="custom_base_url",
            )
            st.session_state.llm_base_url = base_url
        else:
            # 从预设列表选择API地址
            api_url_options = [""] + AVAILABLE_API_URLS
            current_url = st.session_state.get("llm_base_url", "")
            try:
                default_idx = api_url_options.index(current_url) if current_url in api_url_options else 0
            except ValueError:
                default_idx = 0

            selected_url = st.selectbox(
                "选择API服务商",
                api_url_options,
                index=default_idx,
                key="select_api_url",
            )
            st.session_state.llm_base_url = selected_url

        # API Key配置
        api_key = st.text_input(
            "API Key",
            value=st.session_state.get("llm_api_key", ""),
            type="password",
            placeholder="输入您的API Key",
            key="api_key_input",
        )
        st.session_state.llm_api_key = api_key

        st.divider()

        # 模型选择
        st.subheader("模型选择")

        # 是否使用自定义模型
        use_custom_model = st.toggle("自定义模型名称", value=st.session_state.get("use_custom_model", False), key="toggle_custom_model")
        st.session_state.use_custom_model = use_custom_model

        if use_custom_model:
            # 自定义模型名称输入
            model = st.text_input(
                "模型名称",
                value=st.session_state.get("llm_model", DEFAULT_MODEL),
                placeholder="例如: gpt-3.5-turbo",
                key="custom_model_input",
            )
            st.session_state.llm_model = model
        else:
            # 从预设列表选择模型
            model_options = AVAILABLE_MODELS
            current_model = st.session_state.get("llm_model", DEFAULT_MODEL)
            try:
                default_idx = model_options.index(current_model) if current_model in model_options else 0
            except ValueError:
                default_idx = 0

            selected_model = st.selectbox(
                "选择模型",
                model_options,
                index=default_idx,
                key="select_model",
            )
            st.session_state.llm_model = selected_model

        # 显示当前配置摘要
        st.divider()
        with st.expander("当前配置摘要", expanded=False):
            st.write(f"**API地址**: `{st.session_state.llm_base_url or '未配置'}`")
            st.write(f"**API Key**: `{'*' * 8}{st.session_state.llm_api_key[-4:] if st.session_state.llm_api_key else '未配置'}`")
            st.write(f"**模型**: `{st.session_state.llm_model}`")

        st.divider()

        if st.button("刷新页面", width="stretch"):
            st.rerun()


def render_scrape_section() -> None:
    st.subheader("1) 抓取评论")
    tab_topic, tab_single = st.tabs(["话题抓取", "单条抓取"])

    with tab_topic:
        col1, col2 = st.columns(2)
        keyword = col1.text_input("关键词", placeholder="例如：新加坡旅游攻略", key="topic_keyword")
        platforms = col2.multiselect("平台", PLATFORMS, default=PLATFORMS, key="topic_platforms")

        col3, col4, col5 = st.columns(3)
        max_search = col3.number_input(
            "每平台最大搜索数",
            min_value=1,
            max_value=50,
            value=DEFAULT_MAX_SEARCH,
            step=1,
            key="topic_max_search",
        )
        max_comments = col4.number_input(
            "每条最大评论数",
            min_value=1,
            max_value=5000,
            value=DEFAULT_MAX_COMMENTS,
            step=1,
            key="topic_max_comments",
        )
        default_speed_idx = SPEEDS.index(DEFAULT_SPEED) if DEFAULT_SPEED in SPEEDS else 1
        speed = col5.selectbox("速度档位", SPEEDS, index=default_speed_idx, key="topic_speed")

        topic_output = st.text_input(
            "输出目录（可选）",
            value="",
            placeholder="留空使用 config.OUTPUT_DIR",
            key="topic_output",
        )

        if st.button("开始话题抓取", type="primary", key="topic_run_btn"):
            if not keyword.strip():
                st.error("请先输入关键词")
                return
            if not platforms:
                st.error("请至少选择一个平台")
                return

            args = [
                "topic",
                "-k",
                keyword.strip(),
                "-p",
                ",".join(platforms),
                "-ms",
                str(max_search),
                "-mc",
                str(max_comments),
                "-s",
                speed,
            ]
            if topic_output.strip():
                args.extend(["-o", topic_output.strip()])

            if run_and_render(args, "话题抓取"):
                st.rerun()

    with tab_single:
        col1, col2 = st.columns(2)
        platform = col1.selectbox("平台", PLATFORMS, index=0, key="single_platform")
        max_comments = col2.number_input(
            "最大评论数",
            min_value=1,
            max_value=10000,
            value=100,
            step=1,
            key="single_max_comments",
        )

        col3, col4 = st.columns(2)
        speed = col3.selectbox(
            "速度档位",
            SPEEDS,
            index=SPEEDS.index(DEFAULT_SPEED) if DEFAULT_SPEED in SPEEDS else 1,
            key="single_speed",
        )
        single_output = col4.text_input(
            "输出目录（可选）",
            value="",
            placeholder="留空使用 config.OUTPUT_DIR",
            key="single_output",
        )

        url = st.text_input(
            "视频/帖子链接或ID",
            placeholder="例如: BV1xx411c7mD 或 https://v.douyin.com/...",
            key="single_url",
        )

        if st.button("开始单条抓取", type="primary", key="single_run_btn"):
            if not url.strip():
                st.error("请先输入链接或ID")
                return

            args = [
                "scrape",
                "-p",
                platform,
                "-u",
                url.strip(),
                "-m",
                str(max_comments),
                "-s",
                speed,
            ]
            if single_output.strip():
                args.extend(["-o", single_output.strip()])

            if run_and_render(args, "单条抓取"):
                st.rerun()


def render_analyze_section(datasets: list[Path]) -> None:
    st.subheader("2) 批量分析 (analyze)")
    if not datasets:
        st.info("当前没有可分析文件，请先抓取评论。")
        return

    selected = st.selectbox(
        "选择待分析文件",
        datasets,
        format_func=rel_path,
        key="analyze_dataset",
    )

    task = st.selectbox(
        "分析任务",
        ["all", "sentiment", "summary", "filter", "classify"],
        index=0,
        key="analyze_task",
    )

    criteria = ""
    categories = ""

    if task in {"filter", "all"}:
        criteria = st.text_input(
            "筛选条件（filter/all 可选）",
            value="",
            placeholder="例如：关于续航问题的用户反馈",
            key="analyze_criteria",
        )
    if task in {"classify", "all"}:
        categories = st.text_input(
            "分类标签（classify/all 可选）",
            value="",
            placeholder="例如：好评,差评,建议,提问,闲聊",
            key="analyze_categories",
        )

    analyze_output = st.text_input(
        "分析输出目录（可选）",
        value="",
        placeholder="留空使用 config.OUTPUT_DIR",
        key="analyze_output",
    )

    if st.button("开始分析", type="primary", key="analyze_run_btn"):
        if task == "filter" and not criteria.strip():
            st.error("filter 任务需要填写筛选条件")
            return
        if task == "classify" and not categories.strip():
            st.error("classify 任务需要填写分类标签")
            return

        args = [
            "analyze",
            "-i",
str(selected),
            "-t",
            task,
        ]

        if criteria.strip():
            args.extend(["-c", criteria.strip()])
        if categories.strip():
            args.extend(["--categories", categories.strip()])
        if analyze_output.strip():
            args.extend(["-o", analyze_output.strip()])

        if run_and_render(args, "评论分析"):
            st.rerun()


def render_chat_section(datasets: list[Path]) -> None:
    st.subheader("3) 数据问答")
    if not datasets:
        st.info("当前没有可用数据，请先抓取评论。")
        return

    selected = st.selectbox(
        "选择问答数据集",
        datasets,
        format_func=rel_path,
        key="chat_dataset",
    )

    try:
        df = load_table(selected)
    except Exception as err:  # noqa: BLE001
        st.error(str(err))
        return

    st.caption(f"数据规模: {len(df)} 行, {len(df.columns)} 列")
    with st.expander("数据预览", expanded=False):
        st.dataframe(df.head(50), width="stretch")

    if "content" not in df.columns:
        st.warning("该文件不含 `content` 列，无法问答。")
        return

    context_text, used = build_context(df)
    st.caption(f"问答上下文已加载 {used} 条评论")

    # 使用侧边栏配置
    base_url = st.session_state.llm_base_url.strip()
    api_key = st.session_state.llm_api_key.strip()
    model = st.session_state.llm_model.strip()

    chat_key = f"chat_history::{selected}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    if st.button("清空当前数据集对话", key="chat_clear_btn"):
        st.session_state[chat_key] = []
        st.rerun()

    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input("输入问题，例如：负面评价主要集中在哪些点？")
    if not user_query:
        return

    st.session_state[chat_key].append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    if not base_url or not api_key:
        err_text = "LLM 配置不完整：请在左侧边栏填写 API Base URL 和 API Key"
        with st.chat_message("assistant"):
            st.error(err_text)
        st.session_state[chat_key].append({"role": "assistant", "content": err_text})
        return

    with st.chat_message("assistant"):
        with st.spinner("分析中..."):
            try:
                from analyzer.client import LLMClient

                client = LLMClient(base_url=base_url, api_key=api_key, model=model or DEFAULT_MODEL)
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "你是评论数据分析助手。仅基于提供的评论内容回答问题。"
                            "优先给出可执行洞察，结论要具体。"
                            "若评论中没有足够信息，明确说明。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"评论数据如下:\n{context_text}\n\n用户问题: {user_query}",
                    },
                ]
                answer = client.chat(messages)
            except Exception as err:  # noqa: BLE001
                answer = f"调用 LLM 失败: {err}"

            st.markdown(answer)
            st.session_state[chat_key].append({"role": "assistant", "content": answer})


def main() -> None:
    st.set_page_config(
        page_title="评论抓取与分析 GUI",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 初始化会话状态
    init_session_state()

    st.title("评论抓取与分析 GUI")
    st.markdown("在一个页面里完成 `抓取 -> 分析 -> 问答`。")

    render_sidebar()
    render_scrape_section()

    st.divider()
    datasets = list_datasets()
    render_analyze_section(datasets)

    st.divider()
    render_chat_section(datasets)


if __name__ == "__main__":
    if has_streamlit_context():
        main()
    else:
        cmd = [sys.executable, "-m", "streamlit", "run", "gui.py"]
        print("检测到直接运行 `python gui.py`，正在切换为 Streamlit 启动方式...")
        raise SystemExit(subprocess.call(cmd, cwd=str(BASE_DIR)))
