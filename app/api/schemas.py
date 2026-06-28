"""Pydantic schemas for API request/response models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def convert_db_value(value):
    """
    将数据库返回值转换为JSON可序列化的类型。
    
    处理:
    - UUID -> str
    - datetime -> ISO格式字符串
    """
    if isinstance(value, UUID):
        return str(value)
    elif isinstance(value, datetime):
        return value.isoformat()
    return value


# ---- Document Schemas ----

class UploadResponse(BaseModel):
    """Response for document upload."""
    doc_id: str
    collection: str = "default"  # 知识库名称
    file_name: str
    file_type: str
    file_size: int
    total_segments: int
    total_chunks: int
    total_characters: int
    chunk_strategy: str
    chunk_size: int
    chunk_overlap: int
    sliding_window: int = 0  # 滑动窗口大小
    uploaded_at: str


class DocumentListItem(BaseModel):
    """Document list entry."""
    doc_id: str
    collection: str = "default"
    file_name: str
    file_type: str
    file_size: int
    total_chunks: int
    total_characters: int
    chunk_strategy: str
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    uploaded_at: str


class DocumentListResponse(BaseModel):
    """Response for listing documents."""
    documents: list[DocumentListItem]
    total: int


class DeleteResponse(BaseModel):
    """Response for document deletion."""
    success: bool
    doc_id: str
    message: str


class ClearAllResponse(BaseModel):
    """清空知识库的响应模型。"""
    success: bool
    message: str
    deleted_documents: int  # 删除的文档数
    deleted_chunks: int     # 删除的分块数


class StatsResponse(BaseModel):
    """System statistics response."""
    total_documents: int
    supported_extensions: list[str]
    available_strategies: list[str]
    collection: dict


# ---- Chat Schemas ----

class ChatRequest(BaseModel):
    """Chat query request."""
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    top_k: int = Field(default=5, ge=1, le=20, description="检索文档数量")
    collections: list[str] | None = Field(
        default=None, description="要查询的知识库列表，为空则查询所有知识库"
    )
    history: list[dict[str, str]] | None = Field(
        default=None, description="对话历史"
    )
    stream: bool = Field(default=False, description="是否流式返回")


class CollectionInfo(BaseModel):
    """知识库信息。"""
    name: str
    document_count: int
    chunk_count: int


class CollectionListResponse(BaseModel):
    """知识库列表响应。"""
    collections: list[CollectionInfo]
    total: int


class SourceReference(BaseModel):
    """Source reference from retrieval."""
    source: str
    page: int | None = None
    file_type: str | None = None
    score: float
    snippet: str


class ChatResponse(BaseModel):
    """Non-streaming chat response."""
    answer: str
    sources: list[SourceReference]


class StreamEvent(BaseModel):
    """SSE stream event."""
    type: str  # "sources" | "chunk" | "done" | "error"
    data: str | list | dict


class ChunkInfo(BaseModel):
    """Document chunk information for preview."""
    chunk_id: str
    text: str
    chunk_index: int
    metadata: dict
    parent_text: str | None = None  # 父分块文本（父子分块策略）
    parent_id: str | None = None  # 父分块ID


class ChunkListResponse(BaseModel):
    """Response for listing document chunks."""
    doc_id: str
    chunks: list[ChunkInfo]
    total: int
