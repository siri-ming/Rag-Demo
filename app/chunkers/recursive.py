"""Recursive character text chunker."""

from app.parsers.base import Document

from .base import BaseChunker, Chunk


class RecursiveChunker(BaseChunker):
    """
    Recursively splits text using a hierarchy of separators.

    Separator priority (from coarsest to finest):
    1. Double newlines (paragraph breaks)
    2. Single newlines
    3. Chinese period / full stop (。)
    4. English period (.)
    5. Commas (,，)
    6. Spaces

    This strategy preserves natural text boundaries as much as possible.
    """

    # Ordered from coarsest to finest
    DEFAULT_SEPARATORS = ["\n\n", "\n", "。", ".", "，", ",", " "]

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: list[str] | None = None,
    ):
        super().__init__(chunk_size, chunk_overlap)
        self.separators = separators or self.DEFAULT_SEPARATORS

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using the separator hierarchy."""
        if not text.strip():
            return []

        # If text is already small enough, return as-is
        if len(text) <= self.chunk_size:
            return [text]

        if not separators:
            # No more separators to try; force split by chunk_size
            return self._force_split(text)

        separator = separators[0]
        remaining_separators = separators[1:]

        parts = text.split(separator) if separator else list(text)

        chunks = []
        current_chunk = ""

        for part in parts:
            # Re-add the separator (except for the first part)
            candidate = (
                part
                if not current_chunk
                else current_chunk + separator + part
            )

            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                # Flush current chunk
                if current_chunk.strip():
                    chunks.append(current_chunk)

                # If the part itself is too large, recurse with finer separator
                if len(part) > self.chunk_size:
                    sub_chunks = self._split_text(part, remaining_separators)
                    chunks.extend(sub_chunks[:-1] if len(sub_chunks) > 1 else sub_chunks)
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
                else:
                    current_chunk = part

        if current_chunk.strip():
            chunks.append(current_chunk)

        # Apply overlap: prepend tail of previous chunk to next chunk
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped = [chunks[0]]
            for i in range(1, len(chunks)):
                prev_tail = chunks[i - 1][-self.chunk_overlap :]
                overlapped.append(prev_tail + chunks[i])
            chunks = overlapped

        return chunks

    def _force_split(self, text: str) -> list[str]:
        """Force split text by character count when no separator works."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        return chunks

    def chunk(self, documents: list[Document]) -> list[Chunk]:
        chunks = []
        chunk_idx = 0

        for doc in documents:
            text_chunks = self._split_text(doc.text, list(self.separators))
            for text_chunk in text_chunks:
                chunks.append(
                    Chunk(
                        text=text_chunk,
                        metadata=self._build_metadata(doc, chunk_idx),
                    )
                )
                chunk_idx += 1

        return chunks
