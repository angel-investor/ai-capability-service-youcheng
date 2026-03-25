"""路由层：POST /v1/capabilities/run"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.capabilities.sentiment_analysis import SentimentAnalysisCapability
from app.capabilities.text_summary import TextSummaryCapability
from app.exceptions import AppError, CapabilityNotFoundError
from app.logger import get_logger, request_id_var
from app.models import CapabilityRequest

logger = get_logger(__name__)

router = APIRouter()

# 注册所有 capability，新增时仅需在此添加
CAPABILITY_REGISTRY: dict[str, Any] = {
    "text_summary": TextSummaryCapability(),
    "sentiment_analysis": SentimentAnalysisCapability(),
}


@router.post("/v1/capabilities/run")
async def run_capability(request: CapabilityRequest) -> JSONResponse:
    """统一能力调用接口"""

    # 将 request_id 注入日志上下文
    request_id_var.set(request.request_id)
    start_ms = time.time()

    logger.info("Received capability='%s'", request.capability)

    def meta(elapsed_ms: int) -> dict:
        return {
            "request_id": request.request_id,
            "capability": request.capability,
            "elapsed_ms": elapsed_ms,
        }

    def error_response(exc: AppError) -> JSONResponse:
        elapsed = int((time.time() - start_ms) * 1000)
        logger.warning("AppError code=%s message=%s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "ok": False,
                "error": {"code": exc.code, "message": exc.message, "details": exc.details},
                "meta": meta(elapsed),
            },
        )

    # 查找 capability（在 router 内处理，确保响应带 meta）
    handler = CAPABILITY_REGISTRY.get(request.capability)
    if handler is None:
        return error_response(CapabilityNotFoundError(request.capability))

    try:
        data = await handler.run(request.input)
        elapsed = int((time.time() - start_ms) * 1000)
        logger.info("Completed capability='%s' elapsed_ms=%d", request.capability, elapsed)
        return JSONResponse(
            status_code=200,
            content={"ok": True, "data": data, "meta": meta(elapsed)},
        )
    except AppError as exc:
        return error_response(exc)
