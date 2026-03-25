"""自定义异常类及全局错误处理器"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.logger import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """应用级别异常基类"""

    def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class CapabilityNotFoundError(AppError):
    def __init__(self, capability: str):
        super().__init__(
            code="CAPABILITY_NOT_FOUND",
            message=f"Capability '{capability}' is not supported.",
            status_code=404,
            details={"capability": capability},
        )


class InvalidInputError(AppError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            code="INVALID_INPUT",
            message=message,
            status_code=422,
            details=details or {},
        )


class ModelAPIError(AppError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            code="MODEL_API_ERROR",
            message=message,
            status_code=502,
            details=details or {},
        )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """处理所有 AppError 子类，返回标准错误格式"""
    logger.warning("AppError: code=%s message=%s", exc.code, exc.message)
    # capability 和 request_id 由 router 层统一封装，此处仅返回裸错误
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "ok": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底处理所有未预期异常"""
    logger.exception("Unexpected error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "details": {},
            },
        },
    )
