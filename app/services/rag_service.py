"""
RAG（检索增强生成）编排服务模块。

负责将 RAG 全流程串联起来：
用户提问 → 向量化 → 向量检索 → 构建上下文 → LLM 生成回答

支持流式和非流式两种输出模式。
"""

import logging
from collections.abc import Generator
from typing import Any

from app.config import settings
from app.core.embedding import get_embedding_service
from app.core.llm import get_llm_service
from app.core.vectorstore import get_vector_store

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG 检索增强生成服务。

    负责：
    - 用户问题的向量化
    - 向量数据库相似度检索
    - 检索结果上下文构建
    - LLM 回答生成（支持流式/非流式）
    """

    def _build_context(self, results: list[dict[str, Any]]) -> str:
        """
        将检索结果构建为 LLM 可用的上下文文本。

        如果分块包含 parent_text（父子分块策略），优先使用父分块文本，
        以提供更完整的上下文信息。
        """
        context_parts = []

        for i, result in enumerate(results):
            source = result["metadata"].get("source", "未知")
            page = result["metadata"].get("page", "")
            score = result.get("score", 0)

            # 优先使用父分块文本以获得更完整的上下文
            text = result.get("parent_text") or result.get("text", "")

            # 构建带来源信息的引用头部
            header = f"[资料 {i + 1}] 来源: {source}"
            if page:
                header += f", 第 {page} 页"
            header += f" (相关度: {score:.2f})"

            context_parts.append(f"{header}\n{text}")

        return "\n\n---\n\n".join(context_parts)

    def _format_sources(self, results: list[dict[str, Any]]) -> list[dict]:
        """将检索结果格式化为引用来源列表，用于返回给前端展示。"""
        sources = []
        for result in results:
            meta = result.get("metadata", {})
            sources.append(
                {
                    "source": meta.get("source", "未知"),       # 来源文件名
                    "page": meta.get("page"),                   # 页码（如有）
                    "file_type": meta.get("file_type"),         # 文件类型
                    "score": round(result.get("score", 0), 4),  # 相似度得分
                    "snippet": result.get("text", "")[:200],    # 文本片段预览
                }
            )
        return sources

    def query(
        self,
        question: str,
        top_k: int | None = None,
        collections: list[str] | None = None,
        history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        非流式 RAG 查询：一次性返回完整回答。

        参数:
            question: 用户的问题。
            top_k: 检索的文档数量，默认使用配置值。
            collections: 要查询的知识库列表，为None则查询所有知识库。
            history: 对话历史（用于多轮对话）。
            system_prompt: 自定义系统提示词。

        返回:
            包含 'answer'（回答）、'sources'（引用来源）、'context'（上下文）的字典。
        """
        top_k = top_k or settings.top_k

        # 第一步：将用户问题向量化
        embedding_svc = get_embedding_service()
        query_embedding = embedding_svc.embed_text(question)

        # 第二步：向量检索相关文档分块（支持按知识库过滤）
        vectorstore = get_vector_store()
        results = vectorstore.search(query_embedding, top_k=top_k, collections=collections)

        # 未检索到相关内容时的兜底处理
        if not results:
            return {
                "answer": "抱歉，知识库中未找到与您问题相关的信息。请尝试换一种方式提问，或上传更多相关文档。",
                "sources": [],
                "context": "",
            }

        # 第三步：构建上下文
        context = self._build_context(results)

        # 第四步：LLM 生成回答
        llm = get_llm_service()
        answer = llm.chat(
            query=question,
            context=context,
            system_prompt=system_prompt,
            history=history,
        )

        sources = self._format_sources(results)

        return {
            "answer": answer,
            "sources": sources,
            "context": context,
        }

    def query_stream(
        self,
        question: str,
        top_k: int | None = None,
        collections: list[str] | None = None,
        history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """
        流式 RAG 查询：逐步产出回答。

        产出的事件序列：
        1. {"type": "sources", "data": [...]} — 引用来源列表（先于回答文本）
        2. {"type": "chunk", "data": "文本片段"} — LLM 回答的各个文本片段
        3. {"type": "done", "data": ""} — 流结束标记

        参数:
            question: 用户的问题。
            top_k: 检索的文档数量，默认使用配置值。
            collections: 要查询的知识库列表，为None则查询所有知识库。
            history: 对话历史（用于多轮对话）。
            system_prompt: 自定义系统提示词。
        """
        top_k = top_k or settings.top_k

        # 第一步：向量化
        embedding_svc = get_embedding_service()
        query_embedding = embedding_svc.embed_text(question)

        # 第二步：检索（支持按知识库过滤）
        vectorstore = get_vector_store()
        results = vectorstore.search(query_embedding, top_k=top_k, collections=collections)

        # 未检索到内容时的兜底
        if not results:
            yield {"type": "sources", "data": []}
            yield {
                "type": "chunk",
                "data": "抱歉，知识库中未找到与您问题相关的信息。请尝试换一种方式提问，或上传更多相关文档。",
            }
            yield {"type": "done", "data": ""}
            return

        # 第三步：先产出引用来源
        sources = self._format_sources(results)
        yield {"type": "sources", "data": sources}

        # 第四步：构建上下文并流式生成回答
        context = self._build_context(results)
        llm = get_llm_service()

        for text_chunk in llm.chat_stream(
            query=question,
            context=context,
            system_prompt=system_prompt,
            history=history,
        ):
            yield {"type": "chunk", "data": text_chunk}

        yield {"type": "done", "data": ""}


# ---- 全局单例 ----
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """获取或创建 RAG 服务的全局单例。"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
