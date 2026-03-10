"""
工具函数模块
============
翻译、数据处理等通用工具函数
"""

import requests
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

from config import TRANSLATION_MAP


def translate_to_english(text: str) -> str:
    """
    将中文翻译成英文

    Args:
        text: 中文文本

    Returns:
        英文翻译
    """
    # 优先使用预设翻译
    if text in TRANSLATION_MAP:
        return TRANSLATION_MAP[text]

    # 使用免费翻译API
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": "zh-CN|en"}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("responseStatus") == 200:
                return data["responseData"]["translatedText"]
    except Exception:
        pass

    return f"[翻译] {text}"


class HistoryManager:
    """历史记录管理器"""

    def __init__(self):
        self.data: List[Dict] = []

    def add(self, record: Dict) -> None:
        """添加记录"""
        self.data.append(record)

    def clear(self) -> None:
        """清空记录"""
        self.data = []

    def filter(self, model_filter: str = "全部", language_filter: str = "全部") -> List[Dict]:
        """
        筛选记录

        Args:
            model_filter: 模型筛选条件
            language_filter: 语言筛选条件

        Returns:
            筛选后的记录列表
        """
        filtered = self.data

        if model_filter != "全部":
            filtered = [r for r in filtered if r.get("model_name") == model_filter]

        if language_filter != "全部":
            filtered = [r for r in filtered if r.get("language") == language_filter]

        return filtered

    def get_statistics(self, filtered: Optional[List[Dict]] = None) -> Dict:
        """
        计算统计数据

        Args:
            filtered: 筛选后的数据（可选）

        Returns:
            统计数据字典
        """
        data = filtered if filtered is not None else self.data

        total = len(data)
        cost = sum(r.get("cost", 0) for r in data)
        ratings = [r.get("accuracy_rating", 0) for r in data if r.get("accuracy_rating", 0) > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        return {
            "total": total,
            "cost": cost,
            "avg_rating": avg_rating
        }

    def to_table_data(self, filtered: Optional[List[Dict]] = None) -> List[List]:
        """
        转换为表格数据

        Args:
            filtered: 筛选后的数据（可选）

        Returns:
            表格数据列表
        """
        data = filtered if filtered is not None else self.data

        return [
            [
                r.get("timestamp", "")[:19],
                r.get("model_name", ""),
                r.get("language", ""),
                r.get("question", "")[:30] + "..." if len(r.get("question", "")) > 30 else r.get("question", ""),
                r.get("prompt_tokens", 0),
                r.get("completion_tokens", 0),
                r.get("total_tokens", 0),
                f"${r.get('cost', 0):.6f}",
                r.get("accuracy_rating", 0)
            ]
            for r in data
        ]

    def export_csv(self, output_dir: str) -> Optional[str]:
        """
        导出为CSV文件

        Args:
            output_dir: 输出目录

        Returns:
            CSV文件路径
        """
        if not self.data:
            return None

        df = pd.DataFrame(self.data)
        csv_path = os.path.join(output_dir, "history_export.csv")
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        return csv_path


def format_result_markdown(result: Dict) -> str:
    """
    将结果格式化为Markdown

    Args:
        result: 结果字典

    Returns:
        Markdown格式字符串
    """
    return f"""
### {result['model_name']} ({result['language']})

**输入Token**: {result['prompt_tokens']} | **输出Token**: {result['completion_tokens']} |
**花费**: ${result['cost']:.6f} | **延迟**: {result['latency_ms']}ms

---

{result['full_response']}

---
"""


def create_result_record(
    model_id: str,
    model_name: str,
    language: str,
    question: str,
    usage: Dict,
    cost: float,
    response: str
) -> Dict:
    """
    创建结果记录

    Args:
        model_id: 模型ID
        model_name: 模型名称
        language: 语言
        question: 问题
        usage: 使用量
        cost: 成本
        response: 响应文本

    Returns:
        结果记录字典
    """
    return {
        "model_id": model_id,
        "model_name": model_name,
        "language": language,
        "question": question,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "cost": cost,
        "latency_ms": usage.get("latency_ms", 0),
        "response": response[:500] if len(response) > 500 else response,
        "full_response": response,
        "accuracy_rating": 0,
        "timestamp": datetime.now().isoformat()
    }
