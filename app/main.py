"""FastAPI 应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.exceptions import AppError, app_error_handler, generic_error_handler
from app.logger import get_logger, setup_logging
from app.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = get_logger(__name__)
    logger.info("AI Capability Service starting up...")
    yield
    logger.info("AI Capability Service shutting down.")


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="AI Capability Service",
        description="统一模型能力调用后端服务，支持 text_summary、sentiment_analysis 等 capability。",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS（可按需限制 origins）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 全局异常处理
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # 注册路由
    app.include_router(router)

    return app


app = create_app()
