"""
统计分析模块
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from storage import Database
import config


class StatsAnalyzer:
    """统计分析器"""

    def __init__(self, db: Database):
        self.db = db

    def analyze(self, session_id: str = None,
                time_range: str = None) -> Dict[str, Any]:
        """
        执行全维度统计分析

        Args:
            session_id: 会话ID，None则为全局统计
            time_range: 时间范围 "24h" / "7d" / "30d" / "2026-01-01,2026-02-01"

        Returns:
            统计结果字典
        """
        time_range = time_range or config.STATS_CONFIG.get('default_time_range', '7d')
        start_time, end_time = self._parse_time_range(time_range)

        return {
            'time_range': {
                'start': start_time.isoformat() if start_time else None,
                'end': end_time.isoformat() if end_time else None,
                'label': time_range,
            },
            'time': self.time_stats(session_id, start_time, end_time),
            'platform': self.platform_stats(session_id),
            'engagement': self.engagement_stats(session_id),
            'user': self.user_stats(session_id),
        }

    def time_stats(self, session_id: str = None,
                   start_time: datetime = None,
                   end_time: datetime = None) -> Dict[str, Any]:
        """
        时间维度统计

        - 每小时/每天发言数量趋势
        - 高峰时段识别
        """
        raw_stats = self.db.get_time_stats(session_id, start_time, end_time)

        if not raw_stats:
            return {
                'hourly_counts': [],
                'daily_counts': [],
                'peak_hour': None,
                'peak_day': None,
                'total': 0,
            }

        # 按小时统计
        hourly_counts = [
            {
                'time': row['hour'],
                'count': row['count'],
                'likes': row['total_likes'] or 0,
            }
            for row in raw_stats
        ]

        # 聚合为按天统计
        daily_map = {}
        for row in raw_stats:
            day = row['hour'][:10] if row['hour'] else 'unknown'
            if day not in daily_map:
                daily_map[day] = {'count': 0, 'likes': 0}
            daily_map[day]['count'] += row['count']
            daily_map[day]['likes'] += row['total_likes'] or 0

        daily_counts = [
            {'date': day, 'count': data['count'], 'likes': data['likes']}
            for day, data in sorted(daily_map.items())
        ]

        # 找高峰时段
        peak_hour = max(hourly_counts, key=lambda x: x['count'])['time'] if hourly_counts else None
        peak_day = max(daily_counts, key=lambda x: x['count'])['date'] if daily_counts else None

        return {
            'hourly_counts': hourly_counts,
            'daily_counts': daily_counts,
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'total': sum(row['count'] for row in raw_stats),
        }

    def platform_stats(self, session_id: str = None) -> Dict[str, Any]:
        """
        平台维度统计

        - 各平台内容数/评论数分布
        - 平台互动率对比
        """
        raw_stats = self.db.get_platform_stats(session_id)

        distribution = []
        total_comments = 0
        total_likes = 0

        for row in raw_stats:
            total_comments += row['comment_count']
            total_likes += row['total_likes'] or 0

            distribution.append({
                'platform': row['platform'],
                'content_count': row['content_count'],
                'comment_count': row['comment_count'],
                'total_likes': row['total_likes'] or 0,
                'avg_likes': round(row['avg_likes'] or 0, 1),
            })

        # 计算占比
        for item in distribution:
            item['comment_ratio'] = round(
                item['comment_count'] / total_comments * 100, 1
            ) if total_comments > 0 else 0

        return {
            'distribution': distribution,
            'total_comments': total_comments,
            'total_likes': total_likes,
        }

    def engagement_stats(self, session_id: str = None) -> Dict[str, Any]:
        """
        热度维度统计

        - 点赞分布
        - 热门内容 Top10
        """
        top_contents = self.db.get_top_contents(session_id, limit=10)

        # 点赞分布区间
        comments = self.db.get_comments(session_id)
        like_distribution = {
            '0': 0,
            '1-10': 0,
            '11-50': 0,
            '51-100': 0,
            '100+': 0,
        }

        for c in comments:
            likes = c.get('likes', 0)
            if likes == 0:
                like_distribution['0'] += 1
            elif likes <= 10:
                like_distribution['1-10'] += 1
            elif likes <= 50:
                like_distribution['11-50'] += 1
            elif likes <= 100:
                like_distribution['51-100'] += 1
            else:
                like_distribution['100+'] += 1

        return {
            'top_contents': [
                {
                    'content_id': row['content_id'],
                    'platform': row['platform'],
                    'title': row['title'] or '',
                    'likes': row['likes'],
                    'comments': row['scraped_comments'],
                }
                for row in top_contents
            ],
            'like_distribution': like_distribution,
            'total_engagement': sum(c.get('likes', 0) for c in comments),
        }

    def user_stats(self, session_id: str = None) -> Dict[str, Any]:
        """
        用户维度统计

        - 活跃用户排行
        - KOL 识别
        """
        raw_stats = self.db.get_user_stats(session_id, limit=50)

        kol_threshold_avg = config.STATS_CONFIG.get('kol_avg_likes', 50)
        kol_threshold_total = config.STATS_CONFIG.get('kol_total_likes', 500)

        users = []
        kol_count = 0

        for row in raw_stats:
            avg_likes = row['avg_likes'] or 0
            total_likes = row['total_likes'] or 0

            is_kol = avg_likes >= kol_threshold_avg or total_likes >= kol_threshold_total

            if is_kol:
                kol_count += 1

            users.append({
                'username': row['username'],
                'platform': row['platform'],
                'post_count': row['post_count'],
                'total_likes': total_likes,
                'avg_likes': round(avg_likes, 1),
                'max_likes': row['max_likes'] or 0,
                'is_kol': is_kol,
            })

        return {
            'active_users': users,
            'kol_count': kol_count,
            'total_users': len(users),
        }

    def _parse_time_range(self, time_range: str) -> tuple:
        """解析时间范围"""
        now = datetime.now()

        if time_range == '24h':
            return now - timedelta(hours=24), now
        elif time_range == '7d':
            return now - timedelta(days=7), now
        elif time_range == '30d':
            return now - timedelta(days=30), now
        elif ',' in time_range:
            parts = time_range.split(',')
            start = datetime.fromisoformat(parts[0].strip())
            end = datetime.fromisoformat(parts[1].strip())
            return start, end
        else:
            return now - timedelta(days=7), now
