"""
rag-demo - Application Entry Point.

Responsible for FastAPI application initialization, route mounting, and database initialization.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import chat, document
from app.core.database import init_database

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理。

    启动时自动初始化数据库表结构（创建 pgvector 扩展和数据表）。
    """
    logger.info("正在初始化 PostgreSQL 数据库表结构...")
    init_database()
    logger.info("数据库准备就绪。")
    yield


# Create FastAPI application
app = FastAPI(
    title="rag-demo",
    description="Enterprise Retrieval-Augmented Generation Knowledge Base System",
    version="1.0.0",
    lifespan=lifespan,
)

# 挂载 API 路由
app.include_router(document.router)  # 文档管理路由
app.include_router(chat.router)      # 对话查询路由


# ---- 健康检查 ----


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "rag-demo"}
