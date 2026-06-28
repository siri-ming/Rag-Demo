"""
Application Global Configuration Module.

Manages all configuration items via Pydantic Settings, supporting .env files and environment variable injection.
Configuration items cover: Bailian (Alibaba Cloud DashScope) models, PostgreSQL database, file upload, document chunking, LLM parameters, retrieval parameters, etc.
"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings

# 项目根目录（pyproject.toml 所在目录）
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用配置类，所有字段均可通过环境变量或 .env 文件覆盖。"""

    # ---- 百炼（阿里云 DashScope）模型配置 ----
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")  # 百炼 API 密钥（必填）
    dashscope_base_url: str = os.getenv(
        "DASHSCOPE_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )  # DashScope OpenAI 兼容接口地址
    dashscope_llm_model: str = os.getenv("DASHSCOPE_LLM_MODEL", "qwen-plus")  # 对话模型名称
    dashscope_embedding_model: str = os.getenv(
        "DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v3"
    )  # 向量嵌入模型

    # ---- PostgreSQL 数据库配置 ----
    # 连接字符串格式: postgresql://用户名:密码@主机:端口/数据库名
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/rag_db",
    )

    # ---- 文件上传配置 ----
    upload_dir: str = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))  # 上传文件存储目录
    max_upload_size: int = 50 * 1024 * 1024  # 单文件最大上传大小，默认 50MB

    # ---- 文档分块配置（默认值，前端可覆盖）----
    chunk_size: int = 500  # 每个分块的目标字符数（默认值）
    chunk_overlap: int = 50  # 相邻分块的重叠字符数（默认值）
    default_chunk_strategy: str = "recursive"  # 默认分块策略：fixed / recursive / parent_child
    sliding_window: int = 0  # 滑动窗口大小（0表示不使用）

    # ---- LLM 生成配置 ----
    llm_temperature: float = 0.7  # 生成温度，值越高输出越随机
    llm_max_tokens: int = 2048  # 单次生成的最大 token 数

    # ---- Embedding 向量配置 ----
    # 百炼 text-embedding-v3 模型默认输出 1024 维向量，需与数据库 vector 列维度一致
    embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "1024"))

    # ---- 检索配置 ----
    top_k: int = 5  # 向量检索返回的最相关文档块数量

    class Config:
        """Pydantic Settings 内部配置。"""

        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"


# 全局配置单例
settings = Settings()

# 启动时自动创建必要的目录
os.makedirs(settings.upload_dir, exist_ok=True)
