import sqlite3
from datetime import datetime
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_posts (
            post_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            published_date TEXT,
            text TEXT,
            is_deleted BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_post(user_id, post_id, text):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO user_posts (post_id, user_id, published_date, text) VALUES (?, ?, ?, ?)",
        (post_id, user_id, datetime.now().isoformat(), text[:500])
    )
    conn.commit()
    conn.close()

def get_user_posts(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    posts = conn.execute(
        "SELECT post_id, published_date, text FROM user_posts WHERE user_id = ? AND is_deleted = 0 ORDER BY published_date DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(p) for p in posts]

def delete_user_post(user_id, post_id):
    conn = sqlite3.connect(DB_PATH)
    post = conn.execute("SELECT * FROM user_posts WHERE post_id = ? AND user_id = ?", (post_id, user_id)).fetchone()
    if post:
        conn.execute("UPDATE user_posts SET is_deleted = 1 WHERE post_id = ?", (post_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def get_post_author(post_id):
    conn = sqlite3.connect(DB_PATH)
    post = conn.execute("SELECT user_id FROM user_posts WHERE post_id = ?", (post_id,)).fetchone()
    conn.close()
    return post[0] if post else None
