"""Authentication service with refresh token and rate limiting support."""
import jwt
import hashlib
import os
import time
import threading
from datetime import datetime, timedelta, timezone
from config import get_config


class AuthService:
    """认证服务：支持密码哈希、JWT 令牌、刷新令牌与登录限流。"""

    def __init__(self):
        cfg = get_config()
        self.secret_key = os.environ.get('SECRET_KEY', 'my-secret-key')
        self.token_expiry = int(os.environ.get('TOKEN_EXPIRY', '3600'))
        self.refresh_token_expiry = cfg.get('refresh_token_expiry', 86400 * 7)
        self.max_attempts = cfg.get('max_login_attempts', 5)
        self.lockout_seconds = cfg.get('lockout_seconds', 900)

        # 登录尝试记录：username -> {'attempts': int, 'locked_until': float}
        self._login_attempts: dict[str, dict] = {}
        self._lock = threading.Lock()

        # 已吊销的令牌（内存集合，重启丢失）
        self._revoked_tokens: set[str] = set()

    # ── 密码哈希 ──────────────────────────────────────────

    def hash_password(self, password: str) -> str:
        """对密码进行 SHA-256 哈希。"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码是否匹配哈希。"""
        return self.hash_password(password) == hashed

    # ── 登录限流 ──────────────────────────────────────────

    def is_locked_out(self, username: str) -> bool:
        """检查用户是否因多次失败登录被锁定。"""
        record = self._login_attempts.get(username)
        if not record:
            return False
        if record['locked_until'] > time.time():
            return True
        # 锁定已过期，重置计数
        with self._lock:
            self._login_attempts.pop(username, None)
        return False

    def record_failed_attempt(self, username: str) -> int:
        """记录一次失败登录。返回剩余尝试次数，0 表示已锁定。"""
        with self._lock:
            now = time.time()
            record = self._login_attempts.get(username)
            if not record:
                record = {'attempts': 0, 'locked_until': 0}
                self._login_attempts[username] = record
            record['attempts'] += 1
            remaining = max(0, self.max_attempts - record['attempts'])
            if remaining == 0:
                record['locked_until'] = now + self.lockout_seconds
            return remaining

    def reset_login_attempts(self, username: str) -> None:
        """登录成功后重置失败计数。"""
        with self._lock:
            self._login_attempts.pop(username, None)

    # ── JWT 令牌 ──────────────────────────────────────────

    def generate_token(self, user_id: int) -> str:
        """生成访问令牌（15 分钟过期）。"""
        now = datetime.now(timezone.utc)
        payload = {
            'user_id': user_id,
            'iat': now,
            'exp': now + timedelta(seconds=self.token_expiry),
            'type': 'access',
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def generate_refresh_token(self, user_id: int) -> str:
        """生成刷新令牌（7 天过期）。"""
        now = datetime.now(timezone.utc)
        payload = {
            'user_id': user_id,
            'iat': now,
            'exp': now + timedelta(seconds=self.refresh_token_expiry),
            'type': 'refresh',
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def refresh_access_token(self, refresh_token: str) -> str | None:
        """用刷新令牌换取新的访问令牌。"""
        try:
            payload = jwt.decode(
                refresh_token, self.secret_key, algorithms=['HS256']
            )
            if payload.get('type') != 'refresh':
                return None
            return self.generate_token(payload['user_id'])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def verify_token(self, token: str) -> dict | None:
        """验证访问令牌并返回载荷。"""
        if token in self._revoked_tokens:
            return None
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def revoke_token(self, token: str) -> None:
        """吊销一个令牌（放入黑名单）。"""
        self._revoked_tokens.add(token)

    def cleanup_expired_tokens(self) -> int:
        """清理过期令牌（此实现仅清空黑名单，实际应持久化）。"""
        count = len(self._revoked_tokens)
        self._revoked_tokens.clear()
        return count
