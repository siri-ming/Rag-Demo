"""
父子分块策略（Parent-Child Chunking）。

一种两级分块方案，旨在兼顾检索精度和上下文完整性：

1. 第一级（父分块）：将文档拆分为较大的文本块（如 2000 字符），作为上下文窗口
2. 第二级（子分块）：将每个父分块进一步拆分为小块（如 500 字符），作为检索单元

检索时使用子分块进行精确匹配，但将对应的父分块文本提供给 LLM，
从而获得更丰富的上下文信息，提升回答质量。
"""

import uuid

from app.parsers.base import Document

from .base import BaseChunker, Chunk
from .recursive import RecursiveChunker


class ParentChildChunker(BaseChunker):
    """
    父子两级分块器。

    使用 RecursiveChunker 分别处理两个层级：
    - parent_splitter：按较大的 chunk_size 生成父分块
    - child_splitter：按较小的 chunk_size 生成子分块
    """

    def __init__(
        self,
        chunk_size: int = 500,          # 子分块大小（检索单元）
        chunk_overlap: int = 50,         # 子分块重叠
        parent_chunk_size: int = 2000,   # 父分块大小（上下文窗口）
        parent_overlap: int = 200,       # 父分块重叠
    ):
        super().__init__(chunk_size, chunk_overlap)
        self.parent_chunk_size = parent_chunk_size
        self.parent_overlap = parent_overlap

        # 父级和子级均使用递归字符分块器
        self._parent_splitter = RecursiveChunker(
            chunk_size=parent_chunk_size,
            chunk_overlap=parent_overlap,
        )
        self._child_splitter = RecursiveChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def chunk(self, documents: list[Document]) -> list[Chunk]:
        """
        执行两级分块。

        流程:
        1. 将每个文档拆分为父分块
        2. 将每个父分块进一步拆分为子分块
        3. 每个子分块携带其对应父分块的完整文本

        返回:
            子分块列表，每项的 parent_text 字段包含所属父分块的文本。
        """
        chunks = []

        for doc in documents:
            # 第一级：生成父分块
            parent_doc = Document(text=doc.text, metadata=doc.metadata)
            parent_chunks = self._parent_splitter.chunk([parent_doc])

            for parent_idx, parent_chunk in enumerate(parent_chunks):
                parent_id = str(uuid.uuid4())

                # 第二级：将父分块拆分为子分块
                child_doc = Document(
                    text=parent_chunk.text,
                    metadata={**doc.metadata, "parent_id": parent_id},
                )
                child_chunks = self._child_splitter.chunk([child_doc])

                for child_idx, child_chunk in enumerate(child_chunks):
                    chunk_id = str(uuid.uuid4())
                    meta = self._build_metadata(doc, len(chunks))
                    meta["parent_chunk_index"] = parent_idx   # 父分块序号
                    meta["child_chunk_index"] = child_idx     # 子分块序号

                    chunks.append(
                        Chunk(
                            text=child_chunk.text,            # 子分块文本（用于检索匹配）
                            metadata=meta,
                            parent_text=parent_chunk.text,    # 父分块文本（用于提供上下文）
                            chunk_id=chunk_id,
                            parent_id=parent_id,
                        )
                    )

        return chunks
