"""
PostgreSQL 数据库连接与表结构管理模块。

职责：
- 管理数据库连接（psycopg 3.x）
- 提供上下文管理器实现自动提交/回滚
- 应用启动时自动创建 pgvector 扩展和相关数据表

数据表说明：
- documents：存储上传文档的元数据（文件名、大小、分块策略等）
- document_chunks：存储文档分块文本、向量嵌入（pgvector）和 JSONB 元数据
  通过外键关联 documents 表，删除文档时自动级联删除对应分块
"""

import logging
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row  # 查询结果以字典形式返回

from app.config import settings

logger = logging.getLogger(__name__)

# 缓存 vector 类型所在的 schema（首次连接时查询，之后复用）
_vector_schema: str | None = None

# 创建 pgvector 扩展（需单独执行，确保 vector 类型在建表前已注册）
_CREATE_EXTENSION_SQL = "CREATE EXTENSION IF NOT EXISTS vector;"

# 建表和索引 SQL（不包含 CREATE EXTENSION，避免同事务中 vector 类型未注册的问题）
_INIT_SQL = """
-- 文档元数据表：记录每个上传文档的基本信息和处理参数
CREATE TABLE IF NOT EXISTS documents (
    doc_id          UUID PRIMARY KEY,            -- 文档唯一标识
    collection    VARCHAR(128) DEFAULT 'default', -- 知识库名称（支持多知识库）
    file_name       VARCHAR(512) NOT NULL,       -- 原始文件名
    file_type       VARCHAR(32),                 -- 文件类型（如 .pdf, .docx）
    file_size       INTEGER DEFAULT 0,           -- 文件大小（字节）
    total_segments  INTEGER DEFAULT 0,           -- 解析出的段落/页面数
    total_chunks    INTEGER DEFAULT 0,           -- 分块总数
    total_characters INTEGER DEFAULT 0,          -- 文本总字符数
    chunk_strategy  VARCHAR(64),                 -- 使用的分块策略名称
    chunk_size      INTEGER,                     -- 分块大小参数
    chunk_overlap   INTEGER,                     -- 分块重叠参数
    sliding_window  INTEGER DEFAULT 0,           -- 滑动窗口大小（0表示不使用）
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()  -- 上传时间
);

-- 如果collection字段不存在，则添加
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='documents' AND column_name='collection') THEN
        ALTER TABLE documents ADD COLUMN collection VARCHAR(128) DEFAULT 'default';
    END IF;
END $$;

-- 如果sliding_window字段不存在，则添加
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='documents' AND column_name='sliding_window') THEN
        ALTER TABLE documents ADD COLUMN sliding_window INTEGER DEFAULT 0;
    END IF;
END $$;

-- 文档分块表：存储文本块、向量嵌入和元数据
CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id    UUID PRIMARY KEY,                 -- 分块唯一标识
    doc_id      UUID NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,  -- 所属文档ID，级联删除
    text        TEXT NOT NULL,                    -- 分块文本内容
    embedding   vector({embedding_dim}),          -- 向量嵌入（维度由配置决定）
    parent_text TEXT,                             -- 父分块文本（父子分块策略使用）
    metadata    JSONB DEFAULT '{{}}'::jsonb,      -- 额外元数据（来源、页码等）
    chunk_index INTEGER DEFAULT 0                 -- 分块在文档中的序号
);

-- 按知识库查询文档的索引
CREATE INDEX IF NOT EXISTS idx_documents_collection ON documents(collection);

-- 按文档ID查询分块的索引
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON document_chunks(doc_id);

-- 向量相似度检索索引（IVFFlat，余弦距离）
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
""".format(embedding_dim=settings.embedding_dim)


def _get_vector_schema() -> str:
    """
    查询 vector 类型所在的 schema 名称（带缓存）。

    pgvector 扩展可能安装在非 public schema（如用户默认 schema），
    需要动态查找并将其加入 search_path，否则 vector 类型不可见。

    注意：此函数直接使用 psycopg.connect 创建原始连接，
    不调用 get_connection()，避免循环依赖。
    """
    global _vector_schema
    if _vector_schema is not None:
        return _vector_schema

    conn = psycopg.connect(settings.database_url, row_factory=dict_row)
    try:
        conn.autocommit = True
        row = conn.execute(
            "SELECT n.nspname FROM pg_type t "
            "JOIN pg_namespace n ON t.typnamespace = n.oid "
            "WHERE t.typname = 'vector' LIMIT 1"
        ).fetchone()
        _vector_schema = row["nspname"] if row else None
        if _vector_schema:
            logger.info("检测到 vector 类型位于 schema: %s", _vector_schema)
            return _vector_schema
        # vector 类型尚不存在（扩展未安装），返回 public 但不缓存
        return "public"
    finally:
        conn.close()


def get_connection() -> psycopg.Connection:
    """
    创建一个新的数据库连接。

    自动将 vector 类型所在的 schema 加入 search_path，
    确保所有 SQL 操作都能正确解析 vector 类型。

    返回:
        psycopg.Connection: 配置了字典行工厂和正确 search_path 的连接对象。
    """
    conn = psycopg.connect(settings.database_url, row_factory=dict_row)
    conn.autocommit = False
    # 动态设置 search_path，兼容 pgvector 安装在非 public schema 的环境
    schema = _get_vector_schema()
    if schema != "public":
        conn.execute(f"SET search_path TO {schema}, public;")
    return conn


@contextmanager
def get_db():
    """
    数据库连接上下文管理器。

    自动处理事务的提交和回滚：
    - 正常退出时自动 commit
    - 发生异常时自动 rollback 并重新抛出
    - 无论成功与否都会关闭连接

    用法:
        with get_db() as conn:
            conn.execute("INSERT INTO ...", params)
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database() -> None:
    """
    初始化数据库表结构。

    在应用启动时调用，自动创建 pgvector 扩展和数据表（如果不存在）。
    该操作是幂等的，重复调用不会报错。

    注意：
    - CREATE EXTENSION 和 CREATE TABLE 使用两个独立的数据库连接，
      因为 psycopg3 的类型缓存在连接建立时就已固定。
    - 动态查找 vector 类型所在的 schema 并加入 search_path，
      兼容扩展安装在非 public schema 的环境。
    """
    # 第一步：创建 pgvector 扩展（使用独立连接）
    conn = psycopg.connect(settings.database_url, autocommit=True)
    try:
        conn.execute(_CREATE_EXTENSION_SQL)
        logger.info("pgvector 扩展已就绪")
    except Exception as e:
        logger.error("pgvector 扩展创建失败: %s", e)
        raise
    finally:
        conn.close()

    # 第二步：查找 vector 类型所在 schema，设置 search_path 后建表
    vector_schema = _get_vector_schema()
    logger.info("vector 类型位于 schema: %s", vector_schema)

    conn = psycopg.connect(settings.database_url, autocommit=True, row_factory=dict_row)
    try:
        # 将 vector 类型所在 schema 加入 search_path
        conn.execute(f"SET search_path TO {vector_schema}, public;")
        conn.execute(_INIT_SQL)
        logger.info("数据库表结构初始化完成")
    except Exception as e:
        logger.error("数据库表结构初始化失败: %s", e)
        raise
    finally:
        conn.close()


def reset_database() -> None:
    """
    重置数据库：删除并重建所有表。

    适用场景：
    - 切换 Embedding 模型导致向量维度变化时（如从 2048 维切换到 1024 维）
    - 需要彻底清空所有数据并重建表结构时

    注意：此操作会删除所有已存储的文档和向量数据，不可恢复。
    """
    # 第一步：确保扩展存在（独立连接）
    conn = get_connection()
    try:
        conn.autocommit = True
        conn.execute(_CREATE_EXTENSION_SQL)
    except Exception as e:
        logger.error("pgvector 扩展创建失败: %s", e)
        raise
    finally:
        conn.close()

    # 第二步：查找 vector schema 并重建表
    vector_schema = _get_vector_schema()
    logger.info("vector 类型位于 schema: %s", vector_schema)

    conn = get_connection()
    try:
        conn.autocommit = True
        conn.execute(f"SET search_path TO {vector_schema}, public;")
        conn.execute("DROP TABLE IF EXISTS document_chunks;")
        conn.execute("DROP TABLE IF EXISTS documents;")
        conn.execute(_INIT_SQL)
        logger.info("数据库表已重置，向量维度: %d", settings.embedding_dim)
    except Exception as e:
        logger.error("数据库重置失败: %s", e)
        raise
    finally:
        conn.close()
