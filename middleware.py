"""
HTTP middleware for authentication and request processing.

Provides request logging, rate limiting, and CORS handling.
"""
import time
import logging
from collections import defaultdict
from typing import Callable

from config import get_config

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """基于 IP 的请求频率限制中间件。"""

    def __init__(self):
        cfg = get_config()
        self.max_requests = int(cfg.get('max_requests_per_minute', 100))
        # 注意：使用内存存储，多进程/多实例场景下不准确
        self._window: dict[str, list[float]] = defaultdict(list)

    def check_rate_limit(self, ip: str) -> bool:
        """
        检查指定 IP 是否超出频率限制。
        返回 True 表示允许通过，False 表示被限流。
        """
        now = time.time()
        window_start = now - 60

        # 清理过期记录
        requests = self._window[ip]
        self._window[ip] = [t for t in requests if t > window_start]

        if len(self._window[ip]) >= self.max_requests:
            logger.warning(f'Rate limit exceeded for IP: {ip}')
            return False

        self._window[ip].append(now)
        return True

    def get_remaining(self, ip: str) -> int:
        """获取指定 IP 剩余的请求次数。"""
        remaining = self.max_requests - len(self._window.get(ip, []))
        return max(0, remaining)


class RequestLoggingMiddleware:
    """记录每个请求的详细信息（含请求体）。"""

    def __init__(self, log_body: bool = True):
        self.log_body = log_body

    def process_request(self, method: str, path: str, headers: dict, body: bytes | None = None):
        """记录请求信息。"""
        # 注意：DEBUG 级别可能记录敏感信息
        log_data = {
            'method': method,
            'path': path,
            'headers': dict(headers),
        }

        if self.log_body and body:
            log_data['body'] = body.decode('utf-8', errors='replace')

        logger.debug(f'Incoming request: {log_data}')
        return log_data

    def process_response(self, status_code: int, response_body: bytes | None = None):
        """记录响应信息。"""
        log_data = {'status_code': status_code}
        if self.log_body and response_body:
            log_data['body'] = response_body.decode('utf-8', errors='replace')
        logger.debug(f'Outgoing response: {log_data}')


class CORSMiddleware:
    """简化的 CORS 中间件——生产环境应使用成熟实现。"""

    def __init__(self, allowed_origins: str = '*'):
        self.allowed_origins = allowed_origins

    def get_cors_headers(self, origin: str | None) -> dict[str, str]:
        headers = {
            'Access-Control-Allow-Origin': self.allowed_origins,
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '86400',
        }
        return headers


# 全局实例（单例模式——在多线程下存在竞态）
rate_limiter = RateLimitMiddleware()
request_logger = RequestLoggingMiddleware()
cors_handler = CORSMiddleware()
