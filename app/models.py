"""Pydantic 数据模型：请求/响应结构定义"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class CapabilityRequest(BaseModel):
    """POST /v1/capabilities/run 请求体"""

    capability: str = Field(..., description="要调用的能力名称，如 text_summary")
    input: dict[str, Any] = Field(..., description="能力的输入参数")
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="请求唯一标识，可选，不传则自动生成",
    )


class Meta(BaseModel):
    """响应元信息"""

    request_id: str
    capability: str
    elapsed_ms: int


class SuccessResponse(BaseModel):
    """成功响应"""

    ok: bool = True
    data: dict[str, Any]
    meta: Meta


class ErrorDetail(BaseModel):
    """错误详情"""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """失败响应"""

    ok: bool = False
    error: ErrorDetail
    meta: Meta
