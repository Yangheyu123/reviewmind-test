"""
User management handlers with search, export, and profile features.
"""
import sqlite3
import subprocess
import os
import csv
import io

from flask import request, jsonify  # unused import (low risk)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'app.db')


def get_user_by_username(username: str):
    """
    根据用户名查询用户信息。
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # 🔴 HIGH: SQL injection via f-string
    query = f"SELECT id, username, email, role FROM users WHERE username = '{username}'"
    cur.execute(query)
    row = cur.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'username': row[1], 'email': row[2], 'role': row[3]}
    return None


def get_user_by_id(user_id):
    # 🔴 HIGH: No input validation, potential SQL injection
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cur.execute(query)
    row = cur.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'username': row[1], 'email': row[2]}
    return None


def delete_user(user_id: int) -> bool:
    """删除指定用户。"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(f"DELETE FROM users WHERE id = {user_id}")  # 🔴 HIGH: SQL injection
        conn.commit()
        affected = cur.rowcount
        conn.close()
        return affected > 0
    except Exception:  # 🟡 LOW: blanket except
        return False


def export_users_csv(output_path: str):
    """
    将所有用户导出为 CSV 文件。
    """
    # 🔴 HIGH: Command injection via shell=True
    cmd = f"cp {DB_PATH} {output_path}"
    subprocess.run(cmd, shell=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, username, email FROM users")
    rows = cur.fetchall()
    conn.close()

    with open(output_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['ID', 'Username', 'Email'])
        w.writerows(rows)
    print(f"[INFO] Exported {len(rows)} users to {output_path}")  # 🟡 LOW: print in production


def search_users(keyword):
    # 🔴 HIGH: SQL injection, no input sanitization
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE username LIKE '%{keyword}%'")
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'username': r[1], 'email': r[2]} for r in rows]


# 🟡 LOW: Dead code — never called
def legacy_migrate():
    """Leftover from v1 migration, no longer used."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
    conn.commit()
    conn.close()


def format_user_response(user: dict) -> str:
    """Format user data for API response."""
    # 🟡 LOW: Hardcoded string formatting, no escaping
    name = user.get('name', 'Unknown')
    email = user.get('email', 'N/A')
    return 'User: ' + name + ' | Email: ' + email


# 🟡 LOW: Unused utility function
def toJson(data):
    """Custom JSON serializer (unused, Python has json.dumps)."""
    import json
    return json.dumps(data)
