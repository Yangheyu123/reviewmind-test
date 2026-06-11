"""
Document management — upload, encrypt, process, and list documents.
"""
import sqlite3
import os
import subprocess
import hashlib
import json


DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'app.db')
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')

# 🔴 CRITICAL: Hardcoded encryption key
ENCRYPTION_KEY = "hardcoded-aes-key-123"


def save_document(filename: str, content: bytes) -> dict:
    """
    保存上传的文档。
    🔴 HIGH: Path traversal — filename not sanitized, attacker can write to arbitrary locations.
    """
    filepath = os.path.join(UPLOAD_DIR, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(content)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO documents (filename, filepath, size, created_at) VALUES (?, ?, ?, datetime('now'))",
        (filename, filepath, len(content))
    )
    doc_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {'id': doc_id, 'filename': filename, 'size': len(content)}


def process_document(filepath: str) -> str:
    """
    处理文档（检测文件类型、提取元数据）。
    🔴 HIGH: Command injection — filepath passed unsanitized to os.system().
    """
    os.system(f"file {filepath}")
    os.system(f"exiftool {filepath} 2>/dev/null")
    return "processed"


def encrypt_data(data: bytes) -> bytes:
    """
    使用 AES 加密数据。
    🟡 MEDIUM: Uses ECB mode — identical plaintext blocks produce identical ciphertext.
    """
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad

    key = ENCRYPTION_KEY.encode()[:16].ljust(16, b'\0')
    cipher = AES.new(key, AES.MODE_ECB)
    padded = pad(data, AES.block_size)
    return cipher.encrypt(padded)


def decrypt_data(encrypted: bytes) -> bytes:
    """
    解密数据。
    🟡 MEDIUM: Same ECB mode issue as encrypt_data.
    """
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad

    key = ENCRYPTION_KEY.encode()[:16].ljust(16, b'\0')
    cipher = AES.new(key, AES.MODE_ECB)
    return unpad(cipher.decrypt(encrypted), AES.block_size)


def list_documents() -> list:
    """
    列出所有文档。
    🟡 MEDIUM: Loads all documents into memory without pagination.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, filename, filepath, size, created_at FROM documents")
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'filename': r[1], 'filepath': r[2], 'size': r[3], 'created_at': r[4]} for r in rows]


def read_document(filepath: str) -> bytes:
    """
    读取文档内容。
    🟡 LOW: Reads entire file into memory — risky for large files.
    """
    with open(filepath, 'rb') as f:
        return f.read()


def search_documents(keyword: str) -> list:
    """
    搜索文档。
    🔴 HIGH: SQL injection via f-string.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"SELECT id, filename FROM documents WHERE filename LIKE '%{keyword}%'")
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'filename': r[1]} for r in rows]


def delete_document(doc_id: int) -> bool:
    """
    删除文档。
    🟡 LOW: No soft delete, no permission check.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT filepath FROM documents WHERE id = ?", (doc_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False

    filepath = row[0]
    if os.path.exists(filepath):
        os.remove(filepath)

    cur.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    return True


def get_document_stats() -> dict:
    """
    获取文档统计信息。
    🟡 MEDIUM: Full table scan without index.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), SUM(size) FROM documents")
    row = cur.fetchone()
    conn.close()
    return {'total_count': row[0], 'total_size': row[1] or 0}
