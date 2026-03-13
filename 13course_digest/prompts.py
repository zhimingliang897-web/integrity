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


def build_dl_classify_prompt(files: list[dict]) -> str:
    """
    为 dl 模式构建“资料角色识别” Prompt。

    Args:
        files: 形如 {"path": "...", "ext": ".pdf", "kind": "document", "preview": "..."} 的列表
    """
    items = []
    for f in files:
        items.append(
            f"- path: {f['path']}\n"
            f"  ext: {f.get('ext', '')}\n"
            f"  kind: {f.get('kind', '')}\n"
            f"  preview: |\n"
            + "\n".join(f"    {line}" for line in (f.get('preview') or '').splitlines()[:80])
        )
    files_block = "\n".join(items)

    return f"""
你是一名资深课程设计与考试教研专家，负责帮学生整理一个课程文件夹中的各种资料。
请阅读下方每个文件的基本信息和内容预览，为每个文件识别其在课程中的“角色”。

## 可用角色类别（role 字段）
- course_overview: 课程简介、课程介绍、syllabus 封面等总览性说明
- course_requirements: 教学大纲、学习目标、作业/平时成绩构成等“平时学习要求”
- exam_requirements: 期中/期末考试说明、考试范围、题型、评分标准、作弊说明等
- lecture_slides: 课堂 PPT、讲义、板书整理等“授课内容”
- past_exams: 往年试卷、sample exam、quiz/midterm/final 题目
- reference: 论文、书籍章节、补充阅读材料
- other: 其他与考试不直接相关或难以判断的内容

## 需要你做的事
1. 对每个文件给出一个最合适的 role。
2. 如能从该文件中看出“考试政策/考试要求”，请在 exam_policy_notes 中用 1-3 句话摘录关键信息（中文）。
3. 给出一个 1-5 的置信度（confidence），5 表示非常确定。

## 输入文件列表（YAML 形式，仅供阅读理解，不要求原样返回）
{files_block}

## 输出格式（严格返回 JSON，便于程序解析）
一个 JSON 数组，每个元素形如：
{{
  "path": "相对路径，与输入 path 完全一致",
  "role": "course_overview|course_requirements|exam_requirements|lecture_slides|past_exams|reference|other",
  "confidence": 1-5,
  "exam_policy_notes": "如该文件包含考试时间/范围/题型/成绩构成等说明，则在此用中文简要摘录；否则用空字符串"
}}
"""


def build_dl_study_guide_prompt(course_context: dict) -> str:
    """
    为 dl 模式构建“复习指南” Prompt。

    course_context 为 Python dict，将在此转为纯文本。
    """
    course_name = course_context.get("course_name", "本课程")
    overview = course_context.get("course_overview", "")
    syllabus = course_context.get("course_requirements", "")
    lecture_summary = course_context.get("lecture_summary", "")
    key_topics = course_context.get("key_topics", "")

    return f"""
你是一名专业的大学课程学习规划导师，现在需要根据一个课程的所有资料，为学生制定一份完整的 **复习指南**。

## 课程基本信息
课程名称：{course_name}

### 课程简介 / 课程目标（来自课程说明/教学大纲）
{overview or "（无明确课程简介，按一般 STEM 课程默认假设）"}

### 课程要求 / 学习目标（来自教学大纲）
{syllabus or "（未提供详细课程要求）"}

### 授课内容摘要（来自讲义/视频等）
{lecture_summary or "（系统仅提供了原始资料，你可以根据常见课程结构来组织内容）"}

### 系统提取的关键主题/术语（如有）
{key_topics or "（暂未做结构化提取，可按你理解总结）"}

## 你的任务
请输出一份面向“期中/期末考试复习”的指南，内容包括：

1. **整体复习策略**
   - 本课程大概分为哪些模块/章节？
   - 每个模块的大致作用和难度如何？

2. **分章节复习路径**
   - 按模块/章节列出学习顺序。
   - 分为【必学】【重要】【可了解】三个等级。
   - 每个章节给出：需要掌握的核心概念、关键公式/方法、典型应用。

3. **时间规划建议**
   - 假设学生距离考试还有 2-3 周，请给出每周/每天的复习安排建议。

4. **配套资料使用建议**
   - 如何利用 PPT / 讲义 / 论文 / 往年题来复习？
   - 哪些资料更适合快速浏览，哪些更适合精读？

请用 **中文** 输出，结构清晰，使用 Markdown 标题和列表。
"""


def build_dl_exam_guide_prompt(course_context: dict) -> str:
    """
    为 dl 模式构建“考试指南” Prompt。
    """
    course_name = course_context.get("course_name", "本课程")
    exam_raw = course_context.get("exam_raw_text", "")
    past_exams_text = course_context.get("past_exams_text", "")
    exam_policy_notes = course_context.get("exam_policy_notes", "")
    key_topics = course_context.get("key_topics", "")

    return f"""
你是一名考试命题与备考辅导专家，现在需要根据一个课程的考试相关资料，为学生生成一份 **考试指南**。

## 课程名称
{course_name}

## 已知考试说明 / 成绩构成 / 题型信息（原始摘录）
（来自 syllabus、exam requirements 文档等）
{exam_raw or "（系统未能找到专门的考试说明文档）"}

### 系统自动摘录的考试政策提示（可能来自多份文件）
{exam_policy_notes or "（暂无明确考试政策摘录）"}

## 往年试卷 / 样题原始文本（如有）
{past_exams_text or "（系统未能找到往年试卷）"}

## 系统推断的关键主题（来自教学资料）
{key_topics or "（你可以结合常见课程内容自行推断重点考点）"}

## 你的任务
请输出一份面向“考前 1-3 周”的考试指南，内容包括：

1. **考试基本信息总结**
   - 考试形式（开卷/闭卷、线上/线下）
   - 考试时长、题型构成（选择题/简答/计算/证明/编程等）
   - 各部分分值比例、平时成绩与考试成绩的权重

2. **高频考点与分值分布预测**
   - 列出 10-20 个高频考点，并用⭐标注重要性（⭐⭐⭐/⭐⭐/⭐）。
   - 对每类题型（如选择题、简答题、证明题）给出常考内容和典型问题类型。

3. **不同时间段的备考策略**
   - 考前 2-3 周：应该完成哪些任务？
   - 考前 1 周：如何查漏补缺？
   - 考前 1 天：如何高效浏览/背诵？

4. **做题与回顾建议**
   - 如果有往年试卷：如何选择题目练习、如何分析错题？
   - 如果缺少往年题：如何自己构造类似题目进行演练？

请用 **中文** 输出，使用清晰的 Markdown 标题和列表，语气务实、具体。
"""
