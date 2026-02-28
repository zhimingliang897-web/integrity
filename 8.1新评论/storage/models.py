"""
SQLite 数据库表结构定义
"""

# 搜索会话表
CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    keyword TEXT NOT NULL,
    platforms TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- 统计数据
    total_contents INTEGER DEFAULT 0,
    layer1_passed INTEGER DEFAULT 0,
    layer2_passed INTEGER DEFAULT 0,
    total_comments INTEGER DEFAULT 0,

    -- 用户操作
    is_saved BOOLEAN DEFAULT 0,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_keyword ON sessions(keyword);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at);
"""

# 内容表（视频/笔记/帖子）
CREATE_CONTENTS = """
CREATE TABLE IF NOT EXISTS contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    content_id TEXT NOT NULL,

    title TEXT,
    url TEXT,
    author TEXT,
    description TEXT,

    -- 互动数据
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,

    publish_time DATETIME,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- 筛选结果
    layer1_pass BOOLEAN DEFAULT 0,
    layer1_reason TEXT,
    layer2_pass BOOLEAN DEFAULT 0,
    layer2_score REAL,
    layer2_reason TEXT,
    layer2_type TEXT,

    UNIQUE(session_id, platform, content_id)
);

CREATE INDEX IF NOT EXISTS idx_contents_session ON contents(session_id);
CREATE INDEX IF NOT EXISTS idx_contents_platform ON contents(platform);
CREATE INDEX IF NOT EXISTS idx_contents_publish ON contents(publish_time);
"""

# 评论表
CREATE_COMMENTS = """
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    content_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    comment_id TEXT NOT NULL,

    username TEXT,
    text TEXT,
    likes INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    create_time DATETIME,
    ip_location TEXT,

    -- 分析结果
    relevance TEXT,
    key_info TEXT,

    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(session_id, platform, comment_id)
);

CREATE INDEX IF NOT EXISTS idx_comments_session ON comments(session_id);
CREATE INDEX IF NOT EXISTS idx_comments_content ON comments(content_id);
CREATE INDEX IF NOT EXISTS idx_comments_time ON comments(create_time);
CREATE INDEX IF NOT EXISTS idx_comments_user ON comments(username);
"""

# 用户保存的结果
CREATE_SAVED = """
CREATE TABLE IF NOT EXISTS saved (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    item_type TEXT NOT NULL,
    item_id TEXT NOT NULL,

    tags TEXT,
    notes TEXT,
    saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(session_id, item_type, item_id)
);

CREATE INDEX IF NOT EXISTS idx_saved_session ON saved(session_id);
"""

# 所有建表语句
ALL_TABLES = [
    CREATE_SESSIONS,
    CREATE_CONTENTS,
    CREATE_COMMENTS,
    CREATE_SAVED,
]


def create_tables(conn):
    """创建所有表"""
    cursor = conn.cursor()
    for sql in ALL_TABLES:
        cursor.executescript(sql)
    conn.commit()
