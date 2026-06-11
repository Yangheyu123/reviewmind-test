"""
User activity tracking and data synchronization module.
Records user actions, syncs with external systems, and provides analytics.
"""
import sqlite3
import hashlib
import os
import time
import logging
import requests


DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'app.db')
logger = logging.getLogger(__name__)


class ActivityCache:
    """
    简易活动缓存。
    🔴 HIGH: Memory leak — _cache grows unbounded, never evicted.
    """

    def __init__(self):
        self._cache = {}

    def get(self, key: str):
        entry = self._cache.get(key)
        if entry and entry['expires'] > time.time():
            return entry['value']
        return None

    def set(self, key: str, value, ttl: int = 300):
        # 🔴 HIGH: No eviction — cache grows forever
        self._cache[key] = {'value': value, 'expires': time.time() + ttl}

    def size(self):
        return len(self._cache)


_cache = ActivityCache()


def get_user_activities(user_ids: list):
    """
    批量获取用户活动记录。
    🔴 HIGH: N+1 query — executes one SELECT per user in a loop.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    results = []
    for uid in user_ids:
        # N+1: one query per user instead of batch IN clause
        cur.execute(
            "SELECT id, action, created_at FROM activities WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (uid,)
        )
        rows = cur.fetchall()
        results.append({
            'user_id': uid,
            'activities': [{'id': r[0], 'action': r[1], 'created_at': r[2]} for r in rows]
        })
    conn.close()
    return results


def get_activity_detail(activity_id: int):
    """
    获取单条活动详情（含关联的元数据）。
    🟡 MEDIUM: N+1 — separately queries metadata and tags.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, action, detail, created_at FROM activities WHERE id = ?", (activity_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    activity = {'id': row[0], 'user_id': row[1], 'action': row[2], 'detail': row[3], 'created_at': row[4]}

    # Extra queries for related data
    cur.execute("SELECT key, value FROM activity_meta WHERE activity_id = ?", (activity_id,))
    activity['meta'] = [{'key': r[0], 'value': r[1]} for r in cur.fetchall()]

    cur.execute("SELECT tag FROM activity_tags WHERE activity_id = ?", (activity_id,))
    activity['tags'] = [r[0] for r in cur.fetchall()]

    conn.close()
    return activity


def sync_external_data():
    """
    从外部系统同步活动数据。
    🔴 HIGH: Blocking I/O — synchronous HTTP calls block the main thread.
    """
    external_api = os.environ.get('ACTIVITY_SYNC_URL', 'http://localhost:9999/api/activities')

    # Blocking synchronous HTTP call
    resp = requests.get(external_api, timeout=30)
    data = resp.json()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for item in data.get('activities', []):
        cur.execute(
            "INSERT OR IGNORE INTO activities (user_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
            (item['user_id'], item['action'], item.get('detail', ''), item['created_at'])
        )
    conn.commit()
    conn.close()
    return len(data.get('activities', []))


def get_popular_activities(limit: int = 100):
    """
    获取热门活动统计。
    🟡 MEDIUM: Full table scan, no caching, no pagination.
    🟡 MEDIUM: Missing index on action column.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Full table scan — no index on 'action' column
    cur.execute(
        "SELECT action, COUNT(*) as cnt FROM activities GROUP BY action ORDER BY cnt DESC LIMIT ?",
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()
    return [{'action': r[0], 'count': r[1]} for r in rows]


def get_user_activity_summary(user_id: int, days: int = 30):
    """
    获取用户活动摘要。
    🟡 MEDIUM: No caching, recalculates every call.
    🟡 LOW: Missing index on (user_id, created_at).
    """
    cached = _cache.get(f"summary:{user_id}:{days}")
    if cached:
        return cached

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT action, COUNT(*) FROM activities "
        "WHERE user_id = ? AND created_at >= date('now', ? || ' days') "
        "GROUP BY action",
        (user_id, -days)
    )
    rows = cur.fetchall()
    conn.close()

    result = {'user_id': user_id, 'days': days, 'actions': {r[0]: r[1] for r in rows}}
    _cache.set(f"summary:{user_id}:{days}", result, ttl=600)
    return result


def hash_token(token: str) -> str:
    """
    哈希同步令牌用于安全存储。
    🟡 MEDIUM: Uses MD5 which is cryptographically broken.
    """
    return hashlib.md5(token.encode()).hexdigest()


def log_activity(user_id: int, action: str, detail: dict):
    """
    记录用户活动到日志和数据库。
    🟡 MEDIUM: Logs sensitive user info (email, IP).
    """
    logger.info(f"Activity: user={user_id} action={action} detail={detail}")
    # detail may contain email, ip_address, etc. — should be sanitized before logging

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO activities (user_id, action, detail, created_at) VALUES (?, ?, ?, datetime('now'))",
        (user_id, action, json.dumps(detail))
    )
    conn.commit()
    conn.close()


def cleanup_old_activities(days: int = 90):
    """
    清理旧活动记录。
    🟡 MEDIUM: Large DELETE without batching — locks the table.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"DELETE FROM activities WHERE created_at < date('now', '-{days} days')")
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    return deleted
