"""Fixed-size text chunker with overlap support."""

from app.parsers.base import Document

from .base import BaseChunker, Chunk


class FixedSizeChunker(BaseChunker):
    """
    Splits text into chunks of a fixed character size with optional overlap.

    This is the simplest chunking strategy, useful for uniform-length text.
    """

    def _split_text(self, text: str) -> list[str]:
        """Split text into fixed-size chunks with overlap."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end - self.chunk_overlap
            # Prevent infinite loop when overlap >= chunk_size
            if start >= len(text):
                break

        return chunks

    def chunk(self, documents: list[Document]) -> list[Chunk]:
        chunks = []
        chunk_idx = 0

        for doc in documents:
            text_chunks = self._split_text(doc.text)
            for text_chunk in text_chunks:
                chunks.append(
                    Chunk(
                        text=text_chunk,
                        metadata=self._build_metadata(doc, chunk_idx),
                    )
                )
                chunk_idx += 1

        return chunks
