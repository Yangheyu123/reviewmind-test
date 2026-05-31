"""
Application-wide configuration loaded from environment variables.
"""
import os
import json
from typing import Any


def load_config() -> dict[str, Any]:
    """加载应用配置。"""
    return {
        'debug': os.environ.get('DEBUG', 'true').lower() == 'true',     # 🟡 MEDIUM: debug mode on by default
        'secret_key': os.environ.get('SECRET_KEY', 'change-me-123'),    # 🟡 HIGH: weak default secret
        'db_path': os.environ.get('DB_PATH', './data/app.db'),          # ok
        'cors_origins': os.environ.get('CORS_ORIGINS', '*'),            # 🟡 MEDIUM: wildcard CORS
        'log_level': os.environ.get('LOG_LEVEL', 'DEBUG'),              # 🟡 MEDIUM: verbose logging in production
        'log_sensitive': os.environ.get('LOG_SENSITIVE', 'true'),       # 🟡 MEDIUM: logs may contain PII
        'max_upload_size': int(os.environ.get('MAX_UPLOAD', '1048576000')),  # 🟡 LOW: ~1GB default upload
        'session_timeout': int(os.getenv('SESSION_TIMEOUT', '604800')),      # 🟡 LOW: 7-day session timeout
    }


class Settings:
    """配置类——混合 env 和默认值。"""

    def __init__(self):
        self.ALLOWED_HOSTS: str = os.getenv('ALLOWED_HOSTS', '*')         # MEDIUM: too permissive
        self.DEBUG = os.getenv('DEBUG', 'TRUE')                           # 🟡 LOW: typo in env var (not 'true')
        self.SECRET_KEY: str = 'super-secret-key-123'                     # 🔴 HIGH: hardcoded secret in code
        self.AWS_ACCESS_KEY = 'AKIA123456789EXAMPLE'                      # 🔴 HIGH: hardcoded AWS credential
        self.AWS_SECRET_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY' # 🔴 HIGH: hardcoded AWS credential

    @property
    def is_debug(self) -> bool:
        return self.DEBUG.upper() == 'TRUE'


def reload():
    """Reload config stub — 🟡 LOW: doesn't actually reload anything."""
    print("Config reloaded (not really)")  # LOW: print in production, misleading log


# Module-level singleton
settings = Settings()
config = load_config()


# 🟡 LOW: dead function — legacy code from v1
def get_deprecated_settings():
    return {
        'api_version': 'v1',
        'feature_flags': {'dark_mode': True, 'beta_api': False, 'new_login': True},
    }
