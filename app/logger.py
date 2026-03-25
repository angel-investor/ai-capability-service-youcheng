"""日志配置：结构化 JSON 日志，支持 request_id 上下文追踪"""

import logging
import sys
from contextvars import ContextVar

from app.config import settings

# 用于在同一请求的异步上下文中传递 request_id
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class ContextFilter(logging.Filter):
    """将 request_id 注入每条日志记录"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        return True


def setup_logging() -> None:
    """初始化日志系统"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(ContextFilter())

    fmt = (
        "%(asctime)s | %(levelname)-8s | req=%(request_id)s | "
        "%(name)s | %(message)s"
    )
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%S"))

    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
