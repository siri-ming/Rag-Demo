"""
文档分块器基类和数据模型。

定义了所有分块策略的统一接口。分块是将长文档拆分为
适合向量嵌入和检索的小文本片段的关键步骤。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.parsers.base import Document


@dataclass
class Chunk:
    """
    文本分块数据对象。

    属性:
        text: 分块的文本内容。
        metadata: 从父文档继承的元数据（来源、页码等）。
        parent_text: 父分块文本（仅父子分块策略使用，检索时提供更完整的上下文）。
        chunk_id: 分块唯一标识（父子分块策略下生成）。
        parent_id: 所属父分块的标识。
    """

    text: str
    metadata: dict = field(default_factory=dict)
    parent_text: str | None = None
    chunk_id: str | None = None
    parent_id: str | None = None

    @property
    def char_count(self) -> int:
        """返回分块的字符数。"""
        return len(self.text)


class BaseChunker(ABC):
    """
    所有分块策略的抽象基类。

    子类必须实现 chunk() 方法。
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        参数:
            chunk_size: 每个分块的目标字符数。
            chunk_overlap: 相邻分块之间的重叠字符数，保证上下文连续性。
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    def chunk(self, documents: list[Document]) -> list[Chunk]:
        """
        将文档列表拆分为分块列表。

        参数:
            documents: 待分块的 Document 对象列表。

        返回:
            Chunk 对象列表。
        """

    def _build_metadata(self, doc: Document, chunk_index: int) -> dict:
        """从父文档构建分块元数据，附加分块索引和策略名称。"""
        meta = {**doc.metadata}
        meta["chunk_index"] = chunk_index
        meta["chunk_strategy"] = self.__class__.__name__
        return meta
