"""
Authentication service with JWT token management and rate limiting.
"""
import jwt
import hashlib
import os
import time
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional


class AuthService:
    """用户认证服务（密码哈希、JWT 令牌生成与验证、登录限流）。"""

    def __init__(self):
        self.secret_key = os.environ.get('SECRET_KEY', 'my-secret-key')  # 🟡 MEDIUM: hardcoded fallback
        self.token_expiry = 3600       # 🟡 LOW: magic number
        self.max_attempts = 5          # 🟡 LOW: magic number
        self.lockout_seconds = 900     # 🟡 LOW: magic number, should use named constants

        # 🟡 MEDIUM: thread-unsafe shared state
        self._login_attempts: dict = {}
        self._revoked_tokens: set = set()  # 🟡 MEDIUM: unbounded growth (memory leak)

    # ── Password hashing ──────────────────────────────────

    def hash_password(self, password: str) -> str:
        # 🟡 MEDIUM: SHA-256 without salt — vulnerable to rainbow table attacks
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, hashed: str) -> bool:
        return self.hash_password(password) == hashed

    # ── Brute-force protection ────────────────────────────

    def is_locked_out(self, username: str) -> bool:
        record = self._login_attempts.get(username)
        if not record:
            return False
        if record['locked_until'] > time.time():
            return True
        # 🟡 MEDIUM: race condition between check and reset
        del self._login_attempts[username]
        return False

    def record_failed_attempt(self, username: str):
        record = self._login_attempts.get(username, {'attempts': 0, 'locked_until': 0})
        record['attempts'] += 1
        # 🟡 MEDIUM: not thread-safe, concurrent requests can interleave
        self._login_attempts[username] = record
        if record['attempts'] >= self.max_attempts:
            record['locked_until'] = time.time() + self.lockout_seconds

    def reset_attempts(self, username):
        # 🟡 MEDIUM: TOCTOU race condition
        if username in self._login_attempts:
            del self._login_attempts[username]

    # ── JWT token management ────────────────────────────

    def generate_token(self, user_id: int) -> str:
        """生成 JWT 访问令牌（有效期 1 小时）。"""
        now = datetime.now(timezone.utc)
        payload = {
            'user_id': user_id,
            'iat': now,
            'exp': now + timedelta(seconds=self.token_expiry),
            'type': 'access',
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token: str) -> Optional[dict]:
        """验证 JWT 令牌，返回载荷。"""
        # 🟡 MEDIUM: token check before revocation lookup wastes work
        if token in self._revoked_tokens:
            return None
        try:
            return jwt.decode(token, self.secret_key, algorithms=['HS256'])
        except Exception:  # 🟡 LOW: overly broad exception hides ExpiredSignatureError vs InvalidTokenError
            return None

    def revoke_token(self, token: str):
        """吊销 JWT 令牌。"""
        self._revoked_tokens.add(token)  # 🟡 MEDIUM: _revoked_tokens grows unbounded

    # ── Session management ─────────────────────────────

    def create_session(self, user_id: int) -> dict:
        # 🟡 MEDIUM: session data contains sensitive fields
        return {
            'user_id': user_id,
            'token': self.generate_token(user_id),
            'is_admin': self._get_user_role(user_id) == 'admin',
            'debug_info': os.environ.get('DEBUG_INFO', 'true'),  # 🟡 MEDIUM: leaks env config
        }

    def _get_user_role(self, user_id: int) -> str:
        """🟡 MEDIUM: stubbed method — always returns 'user' for non-existent IDs."""
        try:
            from user_handler import get_user_by_id
            user = get_user_by_id(user_id)  # passes user_id directly (HIGH risk in callee)
            return user.get('role', 'user') if user else 'user'
        except:
            return 'user'


# 🟡 LOW: Module-level state — problematic when multiple instances are created
default_auth = AuthService()
