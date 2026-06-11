"""
Admin dashboard API — management backend with analytics, bulk operations, and integrations.
"""
import sqlite3
import subprocess
import os
import json
import yaml  # PyYAML
import requests


DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'app.db')

# 🔴 CRITICAL: hardcoded admin API key
ADMIN_API_KEY = "sk-admin-1234567890abcdef"


def get_dashboard_stats(start_date: str, end_date: str):
    """
    获取管理后台统计数据（注册用户数、活跃用户数、新增用户数）。
    🔴 HIGH: SQL injection via f-string on date parameters.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    query = (
        f"SELECT COUNT(*) as total_users, "
        f"SUM(CASE WHEN last_login >= '{start_date}' THEN 1 ELSE 0 END) as active_users, "
        f"SUM(CASE WHEN created_at >= '{start_date}' AND created_at <= '{end_date}' THEN 1 ELSE 0 END) as new_users "
        f"FROM users WHERE created_at <= '{end_date}'"
    )
    cur.execute(query)
    row = cur.fetchone()
    conn.close()
    return {'total_users': row[0], 'active_users': row[1], 'new_users': row[2]}


def bulk_delete_users(user_ids: list):
    """
    批量删除用户。
    🔴 HIGH: SQL injection — user_ids joined directly into SQL string.
    """
    ids_str = ", ".join(str(uid) for uid in user_ids)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"DELETE FROM users WHERE id IN ({ids_str})")
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return {'deleted': affected}


def export_report(filename: str):
    """
    导出管理报表到文件。
    🔴 HIGH: Command injection via shell=True with unsanitized filename.
    """
    cmd = f"sqlite3 {DB_PATH} -header -csv 'SELECT * FROM users' > /tmp/{filename}"
    subprocess.call(cmd, shell=True)
    return f"/tmp/{filename}"


def notify_webhook(url: str, payload: dict):
    """
    向外部 webhook 发送通知。
    🔴 HIGH: SSRF — no URL validation, attacker can target internal services.
    """
    resp = requests.post(url, json=payload, timeout=5)
    return resp.status_code


def load_dashboard_config(raw_yaml: str):
    """
    加载仪表盘配置（YAML 格式）。
    🔴 CRITICAL: Insecure deserialization — yaml.load() can execute arbitrary code.
    """
    config = yaml.load(raw_yaml)
    return config


def get_user_orders(user_id: int):
    """
    获取用户订单列表（含订单明细）。
    🟡 MEDIUM: N+1 query — fetches details for each order in a loop.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"SELECT id, total, status FROM orders WHERE user_id = {user_id}")
    orders = cur.fetchall()

    result = []
    for order in orders:
        # N+1: query order items inside the loop
        cur.execute(f"SELECT product_name, quantity, price FROM order_items WHERE order_id = {order[0]}")
        items = cur.fetchall()
        result.append({
            'id': order[0], 'total': order[1], 'status': order[2],
            'items': [{'name': i[0], 'qty': i[1], 'price': i[2]} for i in items]
        })
    conn.close()
    return result


def list_admin_users(page: int = 1):
    """
    列出所有管理员用户。
    🟡 MEDIUM: No pagination limit, full table scan.
    🟡 LOW: Uses SELECT * which is fragile.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    offset = (page - 1) * 1000
    cur.execute(f"SELECT * FROM users WHERE role = 'admin' LIMIT 1000 OFFSET {offset}")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_audit_log(since: str):
    """
    获取审计日志。
    🔴 HIGH: SQL injection on since parameter.
    🟡 LOW: No limit on result set.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM audit_log WHERE created_at >= '{since}' ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows
