"""
PostgreSQL + pgvector 向量存储模块。

职责：
- 将文档分块及其向量嵌入存储到 PostgreSQL 的 document_chunks 表
- 基于余弦相似度进行向量检索（使用 pgvector 的 <=> 算子）
- 提供按文档ID删除和统计功能

检索原理：
  pgvector 的 <=> 算子返回余弦距离（0~2），
  相似度 = 1 - 距离，值越接近 1 表示越相似。
"""

import json
import logging
import uuid
from typing import Any

import psycopg
from pgvector.psycopg import register_vector  # 注册 pgvector 类型到 psycopg

from app.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)


class VectorStore:
    """
    基于 PostgreSQL + pgvector 的向量存储。

    将文档分块和向量嵌入存储在 PostgreSQL 中，
    利用 pgvector 扩展实现高效的余弦相似度检索。
    """

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or settings.database_url
        self._vector_registered = False  # 标记是否已注册 pgvector 类型

    def _ensure_vector_type(self, conn: psycopg.Connection) -> None:
        """在当前连接上注册 pgvector 类型（只需注册一次）。"""
        if not self._vector_registered:
            register_vector(conn)
            self._vector_registered = True

    def add_documents(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        doc_id: str | None = None,
        parent_texts: list[str | None] | None = None,
    ) -> list[str]:
        """
        将文档分块写入向量存储。

        参数:
            texts: 分块文本列表。
            embeddings: 对应的向量列表（与 texts 一一对应）。
            metadatas: 对应的元数据字典列表（来源、页码等）。
            doc_id: 所属文档的唯一标识。
            parent_texts: 父分块文本列表（父子分块策略下使用，用于检索时提供更完整上下文）。

        返回:
            新创建的分块 ID 列表。
        """
        chunk_ids = []

        with get_db() as conn:
            self._ensure_vector_type(conn)

            insert_sql = """
                INSERT INTO document_chunks
                    (chunk_id, doc_id, text, embedding, parent_text, metadata, chunk_index)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            for i, (text, embedding, metadata) in enumerate(
                zip(texts, embeddings, metadatas)
            ):
                chunk_id = str(uuid.uuid4())
                chunk_ids.append(chunk_id)

                # 获取父分块文本（如果存在）
                parent_text = None
                if parent_texts and i < len(parent_texts):
                    parent_text = parent_texts[i]

                # 元数据序列化为 JSON 字符串存入 JSONB 列
                meta_json = json.dumps(metadata, ensure_ascii=False)

                conn.execute(
                    insert_sql,
                    (chunk_id, doc_id, text, embedding, parent_text, meta_json, i),
                )

        logger.info("已写入 %d 个分块到 PostgreSQL (doc_id=%s)", len(chunk_ids), doc_id)
        return chunk_ids

    def search(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
        doc_id_filter: str | None = None,
        collections: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        基于余弦相似度检索最相关的文档分块。

        参数:
            query_embedding: 查询文本的向量表示。
            top_k: 返回的最相似结果数量，默认使用配置中的 top_k。
            doc_id_filter: 可选的文档ID过滤，仅在指定文档范围内检索。
            collections: 可选的知识库列表过滤，为None则检索所有知识库。

        返回:
            结果列表，每项包含:
            - text: 分块文本
            - parent_text: 父分块文本（可能为 None）
            - score: 余弦相似度得分（0~1）
            - metadata: 元数据字典
        """
        top_k = top_k or settings.top_k
        results = []

        with get_db() as conn:
            self._ensure_vector_type(conn)

            if doc_id_filter:
                # 带文档ID过滤的检索
                search_sql = """
                    SELECT text, parent_text, metadata,
                           1 - (embedding <=> %s::vector) AS score
                    FROM document_chunks dc
                    JOIN documents d ON dc.doc_id = d.doc_id
                    WHERE dc.doc_id = %s
                    ORDER BY dc.embedding <=> %s::vector
                    LIMIT %s
                """
                rows = conn.execute(
                    search_sql,
                    (query_embedding, doc_id_filter, query_embedding, top_k),
                ).fetchall()
            elif collections:
                # 按知识库列表过滤检索
                if len(collections) == 1:
                    # 单个知识库
                    search_sql = """
                        SELECT text, parent_text, metadata,
                               1 - (embedding <=> %s::vector) AS score
                        FROM document_chunks dc
                        JOIN documents d ON dc.doc_id = d.doc_id
                        WHERE d.collection = %s
                        ORDER BY dc.embedding <=> %s::vector
                        LIMIT %s
                    """
                    rows = conn.execute(
                        search_sql,
                        (query_embedding, collections[0], query_embedding, top_k),
                    ).fetchall()
                else:
                    # 多个知识库
                    placeholders = ", ".join(["%s"] * len(collections))
                    search_sql = f"""
                        SELECT text, parent_text, metadata,
                               1 - (embedding <=> %s::vector) AS score
                        FROM document_chunks dc
                        JOIN documents d ON dc.doc_id = d.doc_id
                        WHERE d.collection IN ({placeholders})
                        ORDER BY dc.embedding <=> %s::vector
                        LIMIT %s
                    """
                    params = [query_embedding] + list(collections) + [query_embedding, top_k]
                    rows = conn.execute(search_sql, params).fetchall()
            else:
                # 全局检索
                search_sql = """
                    SELECT text, parent_text, metadata,
                           1 - (embedding <=> %s::vector) AS score
                    FROM document_chunks
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                rows = conn.execute(
                    search_sql,
                    (query_embedding, query_embedding, top_k),
                ).fetchall()

            for row in rows:
                # metadata 从 JSONB 读出后可能是字符串或字典
                meta = row["metadata"]
                if isinstance(meta, str):
                    meta = json.loads(meta)

                results.append(
                    {
                        "text": row["text"],
                        "parent_text": row["parent_text"],
                        "score": float(row["score"]),
                        "metadata": meta,
                    }
                )

        return results

    def delete_by_doc_id(self, doc_id: str) -> None:
        """
        删除指定文档的所有分块。

        注意：由于外键设置了 ON DELETE CASCADE，
        通常删除 documents 表记录时会自动级联删除，
        此方法作为显式清理使用。
        """
        with get_db() as conn:
            conn.execute(
                "DELETE FROM document_chunks WHERE doc_id = %s", (doc_id,)
            )
        logger.info("已删除文档 %s 的所有分块", doc_id)

    def get_table_stats(self) -> dict[str, Any]:
        """获取向量存储表的统计信息（文档数和分块数）。"""
        with get_db() as conn:
            doc_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM documents"
            ).fetchone()["cnt"]

            chunk_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM document_chunks"
            ).fetchone()["cnt"]

        return {
            "table": "document_chunks",
            "documents_count": doc_count,
            "chunks_count": chunk_count,
            "status": "active",
        }


# ---- 全局单例 ----
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """获取或创建向量存储的全局单例。"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
