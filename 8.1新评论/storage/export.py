"""
数据导出功能
"""
import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict

import config


def export_to_csv(data: List[Dict], filename: str, output_dir: str = None) -> str:
    """导出为 CSV 文件"""
    output_dir = output_dir or config.EXPORTS_DIR
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, filename)
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    return filepath


def export_to_excel(data: Dict[str, List[Dict]], filename: str, output_dir: str = None) -> str:
    """导出为 Excel 文件（多 sheet）"""
    output_dir = output_dir or config.EXPORTS_DIR
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, filename)

    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        for sheet_name, sheet_data in data.items():
            df = pd.DataFrame(sheet_data)
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    return filepath


def export_session_report(db, session_id: str, output_dir: str = None) -> str:
    """导出完整会话报告"""
    output_dir = output_dir or config.EXPORTS_DIR
    os.makedirs(output_dir, exist_ok=True)

    session = db.get_session(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")

    keyword = session['keyword']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 准备数据
    data = {
        '内容列表': db.get_contents(session_id),
        '精筛内容': db.get_contents(session_id, layer2_only=True),
        '评论数据': db.get_comments(session_id),
        '用户统计': db.get_user_stats(session_id),
    }

    # 导出 Excel
    filename = f"report_{keyword}_{timestamp}.xlsx"
    filepath = export_to_excel(data, filename, output_dir)

    return filepath


def backup_raw_data(session_id: str, contents: List[Dict], comments: List[Dict],
                    output_dir: str = None) -> str:
    """备份原始数据为 CSV"""
    output_dir = output_dir or os.path.join(config.EXPORTS_DIR, 'backups')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 备份内容
    if contents:
        content_file = os.path.join(output_dir, f"{session_id}_contents_{timestamp}.csv")
        pd.DataFrame(contents).to_csv(content_file, index=False, encoding='utf-8-sig')

    # 备份评论
    if comments:
        comment_file = os.path.join(output_dir, f"{session_id}_comments_{timestamp}.csv")
        pd.DataFrame(comments).to_csv(comment_file, index=False, encoding='utf-8-sig')

    return output_dir
