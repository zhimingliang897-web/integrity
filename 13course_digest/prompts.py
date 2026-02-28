"""
prompts.py - LLM Prompt 模板管理

所有发给 Groq/LLM 的提示词集中在此，便于调优和维护。
与业务逻辑解耦：analyze.py 只负责调用 API，此文件负责"说什么"。
"""


def build_system_prompt() -> str:
    """
    构建系统提示词：定义 LLM 的角色和行为准则。

    Returns:
        str: 系统提示词内容
    """
    return (
        "You are an expert academic tutor helping a student prepare for a STEM exam. "
        "Your goal is to analyze lecture transcripts and identify what the student "
        "MUST study versus what can be safely skipped. "
        "Always reference specific timestamps when pointing to lecture content. "
        "Be concise and exam-focused. Output in Chinese (except for technical terms)."
    )


def build_chunk_prompt(
    chunk_text: str,
    lecture_name: str,
    syllabus: str,
    past_exams: str,
    ppt_text: str,
    paper_text: str = "",
) -> str:
    """
    构建单段转录文本的分析 Prompt。

    Args:
        chunk_text: 带时间戳的转录片段（如 "[00:05:00] Professor explains..."）
        lecture_name: 课程名称，如 "Lecture 3"
        syllabus: 考试大纲全文
        past_exams: 往年真题全文
        ppt_text: 本节课 PPT 提取的文字内容
        paper_text: 论文内容的文字提取

    Returns:
        str: 完整的 user prompt
    """
    return f"""
## 任务
分析以下 {lecture_name} 的转录片段，输出考试导向的学习要点。

## 参考材料

### 考试大纲（Syllabus）
{syllabus or '（未提供）'}

### 往年真题
{past_exams or '（未提供）'}

### 补充论文材料 (Papers)
{paper_text or '（未提供）'}

### 本节 PPT 内容
{ppt_text or '（未提供）'}

## 转录片段（含时间戳）
{chunk_text}

## 输出格式（严格按此结构输出）

### 本段内容概述
（1-2句话说明这段讲了什么）

### 必学考点
（每条格式：⭐数量 [开始时间-结束时间] 主题 → 需要掌握XXX → 考试可能以XXX形式考）
（⭐⭐⭐=高频考点，⭐⭐=重要，⭐=了解即可）

### 可跳过内容
（格式：[时间段] 原因：xxx）

### 与往年真题的关联
（如有对应，注明"20XX年第X题 → 对应[时间]讲的XXX"）

### 本段关键术语
（术语: 一句话解释）
"""


def build_cv_analysis_prompt(all_texts: str) -> str:
    """第一部分：全课程考点深度分析"""
    return f"""
你是一位计算机视觉专家。请根据以下 7 节课的资料内容，输出：
## 第一部分：全课程考点深度分析
1. 识别跨章节的高频考点（列表形式）。
2. 总结核心算法（CNN, Transformers, Autoencoder, VAE, YOLO, Faster R-CNN, Swin）的优缺点、适用场景和关键公式。
3. 给出每个知识点的“考试关注度”（⭐⭐⭐）。

## 课程资料内容：
{all_texts}
"""

def build_cv_questions_part1_prompt(all_texts: str) -> str:
    """第二部分：模拟备考练习题 (MCQ 1-20)"""
    return f"""
你是一位计算机视觉专家。请根据以下资料设计 **20 道单项选择题 (MCQ 1-20)**。
要求：
1. 涵盖前几章的基础概念与计算。
2. 每道题必须包含：【正确答案】、【详细知识点分析】、【解题思路/题解】。
3. 重点术语保留英文。

## 课程资料内容：
{all_texts}
"""

def build_cv_questions_part2_prompt(all_texts: str) -> str:
    """第三部分：模拟备考练习题 (MCQ 21-40 + 6 Fill-in)"""
    return f"""
你是一位计算机视觉专家。请根据以下资料设计：
1. **20 道单项选择题 (MCQ 21-40)**：涵盖检测、分割及高级模型。
2. **6 道填空题**：考察公式参数、术语或架构名称。
要求：
1. 每道题必须包含：【正确答案】、【详细知识点分析】、【解题思路/题解】。
2. 重点术语保留英文。

## 课程资料内容：
{all_texts}
"""


def build_summary_prompt(all_guides: list[str], lecture_name: str) -> str:
    """
    构建单节课汇总 Prompt：将多个片段分析整合为完整学习指南。

    Args:
        all_guides: 各片段分析结果的列表
        lecture_name: 课程名称

    Returns:
        str: 汇总 prompt
    """
    combined = "\n\n---\n\n".join(all_guides)
    return f"""
以下是 {lecture_name} 各片段的分析结果，请整合为一份完整的学习指南。
去除重复内容，按重要性重新排序考点，保留所有时间戳引用。

{combined}

## 输出格式

# {lecture_name} 学习指南

## 本节内容概览

## 必学考点（按重要性排序）

## 可跳过内容

## 与往年真题对应

## 本节关键术语表
"""
