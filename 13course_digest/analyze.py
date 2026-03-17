"""
analyze.py - LLM 分析模块

支持两种 API:
- 阿里巴巴百炼 API (千问 qwen-plus) - 通过 DashScope
- Groq API (Llama) - 备用

分块处理长视频，最终汇总为完整的单节课学习指南。
"""

import os
import time

import config
import prompts

# 尝试导入 API 客户端
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import dashscope
    from dashscope import Generation
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False


def _call_qwen(system: str, user: str, retries: int = 3) -> str:
    """
    调用千问 API (阿里巴巴百炼)

    Args:
        system: 系统提示词
        user: 用户消息内容
        retries: 最大重试次数

    Returns:
        str: LLM 返回的文本内容
    """
    if not DASHSCOPE_AVAILABLE:
        raise ImportError("请安装 dashscope: pip install dashscope")
    
    if not config.DASHSCOPE_API_KEY:
        raise ValueError("DASHSCOPE_API_KEY 未设置，请在 config.yaml 中配置")
    
    # 设置 API Key
    dashscope.api_key = config.DASHSCOPE_API_KEY
    
    for attempt in range(1, retries + 1):
        try:
            response = Generation.call(
                model=config.QWEN_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
                result_format="message",
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                raise Exception(f"API Error: {response.code} - {response.message}")
                
        except Exception as e:
            print(f"[analyze] 千问 API 请求失败（第{attempt}次）: {e}")
            if attempt < retries:
                time.sleep(5 * attempt)
    
    raise RuntimeError("千问 API 多次请求失败，请检查 API Key 或网络连接")


def _call_groq(system: str, user: str, retries: int = 3) -> str:
    """
    调用 Groq API (备用方案)

    Args:
        system: 系统提示词
        user: 用户消息内容
        retries: 最大重试次数

    Returns:
        str: LLM 返回的文本内容
    """
    if not GROQ_AVAILABLE:
        raise ImportError("请安装 groq: pip install groq")
    
    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY 未设置，请在环境变量中配置")
    
    client = Groq(api_key=config.GROQ_API_KEY)
    
    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[analyze] Groq API 请求失败（第{attempt}次）: {e}")
            if attempt < retries:
                time.sleep(5 * attempt)
    raise RuntimeError("Groq API 多次请求失败，请检查 API Key 或网络连接")


def _call_llm(system: str, user: str, retries: int = 3) -> str:
    """
    根据配置选择合适的 LLM API

    Args:
        system: 系统提示词
        user: 用户消息内容
        retries: 最大重试次数

    Returns:
        str: LLM 返回的文本内容
    """
    if config.API_PROVIDER == "dashscope" or config.API_PROVIDER == "qwen":
        return _call_qwen(system, user, retries)
    elif config.API_PROVIDER == "groq":
        return _call_groq(system, user, retries)
    else:
        # 默认使用千问
        return _call_qwen(system, user, retries)


def analyze_lecture(
    chunks: list[str],
    lecture_name: str,
    syllabus: str = "",
    past_exams: str = "",
    ppt_text: str = "",
    paper_text: str = "",
) -> str:
    """
    对单节课的所有转录块进行分析，输出完整学习指南。

    流程：
    1. 逐块调用 LLM 分析（每块约 CHUNK_MINUTES 分钟）
    2. 将所有块的分析结果汇总为最终学习指南

    Args:
        chunks: transcribe.segments_to_chunks() 返回的文本块列表
        lecture_name: 课程名称，如 "Lecture 3"
        syllabus: 考试大纲文本（可选）
        past_exams: 往年真题文本（可选）
        ppt_text: PPT 提取的文本（可选）
        paper_text: 论文文本（可选）

    Returns:
        str: 完整的 Markdown 格式学习指南
    """
    # 检查 API 可用性
    if config.API_PROVIDER in ["dashscope", "qwen"]:
        if not config.DASHSCOPE_API_KEY:
            raise ValueError("DASHSCOPE_API_KEY 未设置，请在 config.yaml 中配置")
    elif config.API_PROVIDER == "groq":
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY 未设置，请在环境变量中配置")

    system = prompts.build_system_prompt()
    chunk_results: list[str] = []

    provider_name = "千问" if config.API_PROVIDER in ["dashscope", "qwen"] else "Groq"
    print(f"[analyze] 使用 {provider_name} API ({config.QWEN_MODEL if config.API_PROVIDER in ['dashscope', 'qwen'] else config.GROQ_MODEL})")
    print(f"[analyze] {lecture_name}：共 {len(chunks)} 个片段，开始逐块分析...")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"[analyze] 分析片段 {i}/{len(chunks)}...")
        user = prompts.build_chunk_prompt(chunk, lecture_name, syllabus, past_exams, ppt_text, paper_text)
        result = _call_llm(system, user)
        chunk_results.append(result)
        # 避免请求过快，稍作等待
        if i < len(chunks):
            time.sleep(1)

    print(f"[analyze] 汇总 {lecture_name} 的学习指南...")
    summary_user = prompts.build_summary_prompt(chunk_results, lecture_name)
    final_guide = _call_llm(system, summary_user)

    return final_guide
