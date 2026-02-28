"""
图表生成模块
"""
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List


def create_time_trend_chart(time_stats: Dict[str, Any]) -> go.Figure:
    """创建时间趋势图"""
    daily_counts = time_stats.get('daily_counts', [])

    if not daily_counts:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", x=0.5, y=0.5, showarrow=False)
        return fig

    dates = [item['date'] for item in daily_counts]
    counts = [item['count'] for item in daily_counts]
    likes = [item['likes'] for item in daily_counts]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=dates,
        y=counts,
        name='评论数',
        marker_color='rgb(55, 83, 109)'
    ))

    fig.add_trace(go.Scatter(
        x=dates,
        y=likes,
        name='点赞数',
        yaxis='y2',
        line=dict(color='rgb(255, 127, 14)', width=2)
    ))

    fig.update_layout(
        title='发言趋势',
        xaxis_title='日期',
        yaxis=dict(title='评论数', side='left'),
        yaxis2=dict(title='点赞数', side='right', overlaying='y'),
        legend=dict(x=0.01, y=0.99),
        hovermode='x unified',
    )

    return fig


def create_platform_pie_chart(platform_stats: Dict[str, Any]) -> go.Figure:
    """创建平台分布饼图"""
    distribution = platform_stats.get('distribution', [])

    if not distribution:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", x=0.5, y=0.5, showarrow=False)
        return fig

    labels = [item['platform'] for item in distribution]
    values = [item['comment_count'] for item in distribution]

    # 平台名称映射
    name_map = {
        'bilibili': 'B站',
        'douyin': '抖音',
        'xiaohongshu': '小红书',
    }
    labels = [name_map.get(l, l) for l in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textinfo='label+percent',
        marker=dict(colors=['#FB7299', '#00D8FF', '#FE2C55'])
    )])

    fig.update_layout(title='平台评论分布')

    return fig


def create_engagement_bar_chart(engagement_stats: Dict[str, Any]) -> go.Figure:
    """创建点赞分布柱状图"""
    like_distribution = engagement_stats.get('like_distribution', {})

    if not like_distribution:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", x=0.5, y=0.5, showarrow=False)
        return fig

    categories = list(like_distribution.keys())
    counts = list(like_distribution.values())

    fig = go.Figure(data=[go.Bar(
        x=categories,
        y=counts,
        marker_color='rgb(102, 178, 255)',
        text=counts,
        textposition='auto',
    )])

    fig.update_layout(
        title='点赞数分布',
        xaxis_title='点赞区间',
        yaxis_title='评论数量',
    )

    return fig


def create_user_ranking_table(user_stats: Dict[str, Any]) -> List[Dict]:
    """创建用户排行表格数据"""
    users = user_stats.get('active_users', [])[:20]

    # 平台名称映射
    name_map = {
        'bilibili': 'B站',
        'douyin': '抖音',
        'xiaohongshu': '小红书',
    }

    return [
        {
            '用户名': u['username'],
            '平台': name_map.get(u['platform'], u['platform']),
            '发言数': u['post_count'],
            '总点赞': u['total_likes'],
            '平均点赞': u['avg_likes'],
            'KOL': '✓' if u['is_kol'] else '',
        }
        for u in users
    ]


def create_top_content_table(engagement_stats: Dict[str, Any]) -> List[Dict]:
    """创建热门内容表格数据"""
    contents = engagement_stats.get('top_contents', [])

    name_map = {
        'bilibili': 'B站',
        'douyin': '抖音',
        'xiaohongshu': '小红书',
    }

    return [
        {
            '平台': name_map.get(c['platform'], c['platform']),
            '标题': c['title'][:30] + '...' if len(c['title']) > 30 else c['title'],
            '点赞': c['likes'],
            '抓取评论': c['comments'],
        }
        for c in contents
    ]
