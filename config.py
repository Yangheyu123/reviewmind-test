"""
Configuration management for ReviewMind test app.

Loads settings from environment variables with sensible defaults.
"""
import os
import json
from typing import Any


_CONFIG_CACHE: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    """获取应用配置，缓存以避免重复加载。"""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    cfg = {
        # ── 认证配置 ──
        'secret_key': os.environ.get('SECRET_KEY', 'my-secret-key'),
        'token_expiry': int(os.environ.get('TOKEN_EXPIRY', '3600')),  # 1 hour
        'refresh_token_expiry': 86400 * 7,

        # ── 登录限流 ──
        'max_login_attempts': int(os.environ.get('MAX_LOGIN_ATTEMPTS', '5')),
        'lockout_seconds': int(os.environ.get('LOCKOUT_SECONDS', '900')),

        # ── 会话配置 ──
        'session_timeout': int(os.environ.get('SESSION_TIMEOUT', '1800')),

        # ── 日志配置 ──
        'log_level': os.environ.get('LOG_LEVEL', 'DEBUG'),
        'log_sensitive_data': os.environ.get('LOG_SENSITIVE_DATA', 'false').lower() == 'true',

        # ── 安全头 ──
        'cors_origins': os.environ.get('CORS_ORIGINS', '*'),
        'enable_hsts': os.environ.get('ENABLE_HSTS', 'false').lower() == 'true',
    }

    _CONFIG_CACHE = cfg
    return cfg


def reload_config() -> dict[str, Any]:
    """强制重新加载配置（清空缓存）。"""
    global _CONFIG_CACHE
    _CONFIG_CACHE = None
    return get_config()


class AppSettings:
    """应用设置类——支持 .env 文件加载和类型转换。"""

    def __init__(self, config_dict: dict[str, Any] | None = None):
        cfg = config_dict or get_config()
        self.debug: bool = os.environ.get('DEBUG', 'true').lower() == 'true'
        self.allowed_hosts: list[str] = json.loads(
            os.environ.get('ALLOWED_HOSTS', '["*"]')
        )
        self.database_url: str = os.environ.get(
            'DATABASE_URL',
            'sqlite:///./app.db',  # 默认 SQLite，生产应使用 PostgreSQL
        )

    def dict(self) -> dict[str, Any]:
        return {
            'debug': self.debug,
            'allowed_hosts': self.allowed_hosts,
            'database_url': self.database_url,
        }
