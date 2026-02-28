"""
SQLite 数据库操作封装
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from .models import create_tables


class Database:
    """数据库操作类"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # 初始化数据库
        with self.get_connection() as conn:
            create_tables(conn)

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ============================================================
    # 会话操作
    # ============================================================

    def create_session(self, session_id: str, keyword: str, platforms: List[str]) -> str:
        """创建搜索会话"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, keyword, platforms)
                VALUES (?, ?, ?)
            """, (session_id, keyword, json.dumps(platforms)))
            conn.commit()
        return session_id

    def update_session_stats(self, session_id: str,
                             total_contents: int = None,
                             layer1_passed: int = None,
                             layer2_passed: int = None,
                             total_comments: int = None):
        """更新会话统计数据"""
        updates = []
        values = []
        if total_contents is not None:
            updates.append("total_contents = ?")
            values.append(total_contents)
        if layer1_passed is not None:
            updates.append("layer1_passed = ?")
            values.append(layer1_passed)
        if layer2_passed is not None:
            updates.append("layer2_passed = ?")
            values.append(layer2_passed)
        if total_comments is not None:
            updates.append("total_comments = ?")
            values.append(total_comments)

        if updates:
            values.append(session_id)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE sessions SET {', '.join(updates)}
                    WHERE session_id = ?
                """, values)
                conn.commit()

    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def get_recent_sessions(self, limit: int = 20) -> List[Dict]:
        """获取最近的会话列表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def mark_session_saved(self, session_id: str, saved: bool = True, notes: str = None):
        """标记会话为已保存"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions SET is_saved = ?, notes = ?
                WHERE session_id = ?
            """, (saved, notes, session_id))
            conn.commit()

    # ============================================================
    # 内容操作
    # ============================================================

    def insert_contents(self, session_id: str, contents: List[Dict]):
        """批量插入内容"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for c in contents:
                cursor.execute("""
                    INSERT OR REPLACE INTO contents
                    (session_id, platform, content_id, title, url, author, description,
                     likes, comments, views, shares, publish_time,
                     layer1_pass, layer1_reason, layer2_pass, layer2_score, layer2_reason, layer2_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    c.get('platform'),
                    c.get('content_id'),
                    c.get('title'),
                    c.get('url'),
                    c.get('author'),
                    c.get('description'),
                    c.get('likes', 0),
                    c.get('comments', 0),
                    c.get('views', 0),
                    c.get('shares', 0),
                    c.get('publish_time'),
                    c.get('layer1_pass', False),
                    c.get('layer1_reason'),
                    c.get('layer2_pass', False),
                    c.get('layer2_score'),
                    c.get('layer2_reason'),
                    c.get('layer2_type'),
                ))
            conn.commit()

    def get_contents(self, session_id: str,
                     layer1_only: bool = False,
                     layer2_only: bool = False) -> List[Dict]:
        """获取内容列表"""
        conditions = ["session_id = ?"]
        params = [session_id]

        if layer1_only:
            conditions.append("layer1_pass = 1")
        if layer2_only:
            conditions.append("layer2_pass = 1")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM contents
                WHERE {' AND '.join(conditions)}
                ORDER BY likes DESC
            """, params)
            return [dict(row) for row in cursor.fetchall()]

    # ============================================================
    # 评论操作
    # ============================================================

    def insert_comments(self, session_id: str, comments: List[Dict]):
        """批量插入评论"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for c in comments:
                cursor.execute("""
                    INSERT OR REPLACE INTO comments
                    (session_id, content_id, platform, comment_id,
                     username, text, likes, replies, create_time, ip_location,
                     relevance, key_info)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    c.get('content_id'),
                    c.get('platform'),
                    c.get('comment_id'),
                    c.get('username'),
                    c.get('text'),
                    c.get('likes', 0),
                    c.get('replies', 0),
                    c.get('create_time'),
                    c.get('ip_location'),
                    c.get('relevance'),
                    c.get('key_info'),
                ))
            conn.commit()

    def get_comments(self, session_id: str,
                     content_id: str = None,
                     limit: int = None) -> List[Dict]:
        """获取评论列表"""
        conditions = ["session_id = ?"]
        params = [session_id]

        if content_id:
            conditions.append("content_id = ?")
            params.append(content_id)

        sql = f"""
            SELECT * FROM comments
            WHERE {' AND '.join(conditions)}
            ORDER BY likes DESC
        """
        if limit:
            sql += f" LIMIT {limit}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    # ============================================================
    # 保存操作
    # ============================================================

    def save_items(self, session_id: str, item_type: str,
                   item_ids: List[str], tags: List[str] = None, notes: str = None):
        """保存用户选择的条目"""
        tags_json = json.dumps(tags) if tags else None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for item_id in item_ids:
                cursor.execute("""
                    INSERT OR REPLACE INTO saved
                    (session_id, item_type, item_id, tags, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, item_type, item_id, tags_json, notes))
            conn.commit()

    def get_saved_items(self, session_id: str = None,
                        item_type: str = None) -> List[Dict]:
        """获取已保存的条目"""
        conditions = []
        params = []

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)
        if item_type:
            conditions.append("item_type = ?")
            params.append(item_type)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM saved {where_clause}
                ORDER BY saved_at DESC
            """, params)
            return [dict(row) for row in cursor.fetchall()]

    # ============================================================
    # 统计查询
    # ============================================================

    def get_time_stats(self, session_id: str = None,
                       start_time: datetime = None,
                       end_time: datetime = None) -> List[Dict]:
        """按时间统计评论数"""
        conditions = []
        params = []

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)
        if start_time:
            conditions.append("create_time >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("create_time <= ?")
            params.append(end_time.isoformat())

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT
                    strftime('%Y-%m-%d %H:00', create_time) as hour,
                    COUNT(*) as count,
                    SUM(likes) as total_likes
                FROM comments
                {where_clause}
                GROUP BY hour
                ORDER BY hour
            """, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_platform_stats(self, session_id: str = None) -> List[Dict]:
        """按平台统计"""
        conditions = []
        params = []

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT
                    platform,
                    COUNT(DISTINCT content_id) as content_count,
                    COUNT(*) as comment_count,
                    SUM(likes) as total_likes,
                    AVG(likes) as avg_likes
                FROM comments
                {where_clause}
                GROUP BY platform
            """, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_user_stats(self, session_id: str = None, limit: int = 50) -> List[Dict]:
        """用户活跃度统计"""
        conditions = []
        params = []

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT
                    username,
                    platform,
                    COUNT(*) as post_count,
                    SUM(likes) as total_likes,
                    AVG(likes) as avg_likes,
                    MAX(likes) as max_likes
                FROM comments
                {where_clause}
                GROUP BY username, platform
                HAVING post_count >= 1
                ORDER BY total_likes DESC
                LIMIT ?
            """, params + [limit])
            return [dict(row) for row in cursor.fetchall()]

    def get_top_contents(self, session_id: str = None, limit: int = 10) -> List[Dict]:
        """热门内容排行"""
        conditions = []
        params = []

        if session_id:
            conditions.append("c.session_id = ?")
            params.append(session_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT
                    c.content_id,
                    c.platform,
                    c.title,
                    c.likes,
                    c.comments as comment_count,
                    COUNT(cm.id) as scraped_comments
                FROM contents c
                LEFT JOIN comments cm ON c.content_id = cm.content_id AND c.session_id = cm.session_id
                {where_clause}
                GROUP BY c.content_id
                ORDER BY c.likes DESC
                LIMIT ?
            """, params + [limit])
            return [dict(row) for row in cursor.fetchall()]
