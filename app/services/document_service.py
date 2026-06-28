"""
文档处理编排服务模块。

负责将文档处理的全流程串联起来：
上传 → 解析 → 分块 → 向量化 → 存储（PostgreSQL）

同时提供文档管理功能（列表、查询、删除、清空全部、统计）。
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.chunkers import get_chunker, get_available_strategies
from app.config import settings
from app.core.database import get_db
from app.core.embedding import get_embedding_service
from app.core.vectorstore import get_vector_store
from app.parsers import get_parser, get_supported_extensions
from app.api.schemas import convert_db_value

logger = logging.getLogger(__name__)


class DocumentService:
    """
    文档处理编排服务。

    负责：
    - 文档处理流水线（解析→分块→向量化→存储）
    - 文档元数据管理（增删查列表）
    - 清空全部知识库
    - 系统统计信息
    """

    def process_document(
        self,
        file_path: str | Path,
        collection: str = "default",
        chunk_strategy: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        sliding_window: int | None = None,
    ) -> dict[str, Any]:
        """
        处理单个上传文件，走完整流水线。

        参数:
            file_path: 文件路径。
            collection: 知识库名称，默认为"default"。
            chunk_strategy: 分块策略名称（fixed / recursive / parent_child），为空则使用默认。
            chunk_size: 分块大小，为空则使用配置默认值。
            chunk_overlap: 分块重叠，为空则使用配置默认值。
            sliding_window: 滑动窗口大小，为0或None表示不使用。

        返回:
            文档元数据字典，包含 doc_id、文件名、分块数等。
        """
        file_path = Path(file_path)
        doc_id = str(uuid.uuid4())

        # ---- 第一步：解析文档 ----
        logger.info("开始解析文档: %s", file_path.name)
        parser = get_parser(file_path)
        documents = parser.parse(file_path)

        if not documents:
            raise ValueError(f"未能从文件 {file_path.name} 中提取到任何文本内容")

        total_chars = sum(doc.char_count for doc in documents)
        logger.info("解析完成: %d 个段落/页面, 共 %d 字符", len(documents), total_chars)

        # ---- 第二步：文档分块 ----
        strategy = chunk_strategy or settings.default_chunk_strategy
        c_size = chunk_size or settings.chunk_size
        c_overlap = chunk_overlap or settings.chunk_overlap
        s_window = sliding_window if sliding_window is not None else settings.sliding_window

        chunker = get_chunker(strategy, chunk_size=c_size, chunk_overlap=c_overlap)
        chunks = chunker.chunk(documents)

        logger.info("分块完成: %d 个分块, 策略=%s, 滑动窗口=%d", len(chunks), strategy, s_window)

        # ---- 第三步：向量化 ----
        embedding_svc = get_embedding_service()
        texts = [c.text for c in chunks]
        embeddings = embedding_svc.embed_batch(texts)

        # ---- 第四步：保存文档元数据到 PostgreSQL（必须先于分块插入）----
        uploaded_at = datetime.now(timezone.utc)
        doc_meta = {
            "doc_id": doc_id,
            "collection": collection,
            "file_name": file_path.name,
            "file_type": file_path.suffix.lower(),
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "total_segments": len(documents),
            "total_chunks": len(chunks),
            "total_characters": total_chars,
            "chunk_strategy": strategy,
            "chunk_size": c_size,
            "chunk_overlap": c_overlap,
            "sliding_window": s_window,
            "uploaded_at": uploaded_at.isoformat(),
        }

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO documents
                    (doc_id, collection, file_name, file_type, file_size,
                     total_segments, total_chunks, total_characters,
                     chunk_strategy, chunk_size, chunk_overlap, sliding_window, uploaded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    doc_id,
                    collection,
                    file_path.name,
                    file_path.suffix.lower(),
                    doc_meta["file_size"],
                    len(documents),
                    len(chunks),
                    total_chars,
                    strategy,
                    c_size,
                    c_overlap,
                    s_window,
                    uploaded_at,
                ),
            )

        # ---- 第五步：存入向量数据库（此时 documents 表中已有记录）----
        vectorstore = get_vector_store()
        metadatas = [c.metadata for c in chunks]
        parent_texts = [c.parent_text for c in chunks]

        vectorstore.add_documents(
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            doc_id=doc_id,
            parent_texts=parent_texts,
        )

        logger.info("文档处理成功: %s (doc_id=%s)", file_path.name, doc_id)
        return doc_meta

    def list_documents(self, collection: str | None = None) -> list[dict[str, Any]]:
        """从 PostgreSQL 获取所有已上传文档的列表（按上传时间倒序）。
        
        参数:
            collection: 可选的知识库名称过滤，为None则返回所有知识库的文档。
        """
        with get_db() as conn:
            if collection:
                rows = conn.execute(
                    """
                    SELECT doc_id, collection, file_name, file_type, file_size,
                           total_segments, total_chunks, total_characters,
                           chunk_strategy, chunk_size, chunk_overlap, sliding_window, uploaded_at
                    FROM documents
                    WHERE collection = %s
                    ORDER BY uploaded_at DESC
                    """,
                    (collection,)
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT doc_id, collection, file_name, file_type, file_size,
                           total_segments, total_chunks, total_characters,
                           chunk_strategy, chunk_size, chunk_overlap, sliding_window, uploaded_at
                    FROM documents
                    ORDER BY uploaded_at DESC
                    """
                ).fetchall()

        results = []
        for row in rows:
            doc = dict(row)
            # 使用统一的转换函数处理所有字段
            for key, value in doc.items():
                doc[key] = convert_db_value(value)
            results.append(doc)

        return results

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """根据 doc_id 获取单个文档的元数据，不存在则返回 None。"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE doc_id = %s", (doc_id,)
            ).fetchone()

            if row is None:
                return None

            doc = dict(row)
            # 使用统一的转换函数处理所有字段
            for key, value in doc.items():
                doc[key] = convert_db_value(value)
            return doc

    def delete_document(self, doc_id: str) -> bool:
        """
        删除文档及其关联分块和上传的文件。

        利用外键 ON DELETE CASCADE，删除 documents 记录时
        会自动级联删除 document_chunks 中的对应分块。

        返回:
            True 表示文档存在且已删除，False 表示文档不存在。
        """
        with get_db() as conn:
            # 删除前先查询文件名（用于日志记录和删除文件）
            row = conn.execute(
                "SELECT file_name FROM documents WHERE doc_id = %s", (doc_id,)
            ).fetchone()

            if row is None:
                return False

            file_name = row["file_name"]
            
            # 删除文档记录，分块通过外键级联自动删除
            conn.execute("DELETE FROM documents WHERE doc_id = %s", (doc_id,))

        # 删除上传的文件
        upload_dir = Path(settings.upload_dir)
        file_path = upload_dir / file_name
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info("已删除上传文件: %s", file_name)
            except Exception as e:
                logger.warning("删除文件失败 %s: %s", file_name, str(e))

        logger.info("已删除文档: %s (doc_id=%s)", file_name, doc_id)
        return True

    def clear_all(self) -> dict[str, Any]:
        """
        清空整个知识库：删除所有文档记录、向量分块和上传的文件。

        使用 TRUNCATE 配合 CASCADE 快速清空两张表，
        比逐条 DELETE 效率高得多。

        返回:
            包含删除统计信息的字典（删除的文档数和分块数）。
        """
        with get_db() as conn:
            # 先获取所有文档的文件名（用于删除文件）
            rows = conn.execute(
                "SELECT file_name FROM documents"
            ).fetchall()
            
            # 统计待删除的数量
            doc_count = len(rows)
            chunk_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM document_chunks"
            ).fetchone()["cnt"]

            # 删除上传的文件
            upload_dir = Path(settings.upload_dir)
            deleted_files = 0
            for row in rows:
                file_path = upload_dir / row["file_name"]
                if file_path.exists():
                    try:
                        file_path.unlink()
                        deleted_files += 1
                        logger.info("已删除上传文件: %s", row["file_name"])
                    except Exception as e:
                        logger.warning("删除文件失败 %s: %s", row["file_name"], str(e))

            # TRUNCATE 快速清空两张表（CASCADE 确保先清子表再清父表）
            conn.execute("TRUNCATE TABLE document_chunks, documents CASCADE")

        logger.info(
            "已清空知识库: 删除 %d 篇文档, %d 个分块, %d 个文件", 
            doc_count, chunk_count, deleted_files
        )
        return {
            "deleted_documents": doc_count,
            "deleted_chunks": chunk_count,
            "deleted_files": deleted_files,
        }

    def get_stats(self) -> dict[str, Any]:
        """获取系统统计信息（文档数、分块数、支持的格式和策略等）。"""
        vectorstore = get_vector_store()

        try:
            table_stats = vectorstore.get_table_stats()
        except Exception:
            table_stats = {"chunks_count": 0, "status": "unavailable"}

        with get_db() as conn:
            total_docs = conn.execute(
                "SELECT COUNT(*) AS cnt FROM documents"
            ).fetchone()["cnt"]

        return {
            "total_documents": total_docs,
            "supported_extensions": get_supported_extensions(),
            "available_strategies": get_available_strategies(),
            "collection": table_stats,
        }

    def list_collections(self) -> list[dict[str, Any]]:
        """获取所有知识库列表及其统计信息。"""
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT 
                    collection,
                    COUNT(*) AS document_count,
                    (SELECT COUNT(*) FROM document_chunks dc 
                     JOIN documents d ON dc.doc_id = d.doc_id 
                     WHERE d.collection = docs.collection) AS chunk_count
                FROM documents docs
                GROUP BY collection
                ORDER BY collection
                """
            ).fetchall()

        results = []
        for row in rows:
            results.append({
                "name": row["collection"],
                "document_count": row["document_count"],
                "chunk_count": row["chunk_count"],
            })
        
        return results

    def get_document_chunks(self, doc_id: str) -> list[dict[str, Any]]:
        """获取指定文档的所有分块详情。"""
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT chunk_id, text, metadata, chunk_index, parent_text
                FROM document_chunks
                WHERE doc_id = %s
                ORDER BY chunk_index ASC
                """,
                (doc_id,)
            ).fetchall()

        results = []
        for row in rows:
            meta = row["metadata"]
            if isinstance(meta, str):
                import json
                meta = json.loads(meta)
            
            results.append({
                "chunk_id": str(row["chunk_id"]),
                "text": row["text"],
                "chunk_index": row["chunk_index"],
                "metadata": meta,
                "parent_text": row.get("parent_text"),  # 父分块文本
            })
        
        return results


# ---- 全局单例 ----
_document_service: DocumentService | None = None


def get_document_service() -> DocumentService:
    """获取或创建文档服务的全局单例。"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
