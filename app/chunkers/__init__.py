"""
Document chunkers package.

Provides a factory function to get the appropriate chunker by strategy name.
"""

from .base import BaseChunker, Chunk
from .fixed_size import FixedSizeChunker
from .recursive import RecursiveChunker
from .parent_child import ParentChildChunker

_STRATEGIES: dict[str, type[BaseChunker]] = {
    "fixed": FixedSizeChunker,
    "fixed_size": FixedSizeChunker,
    "recursive": RecursiveChunker,
    "parent_child": ParentChildChunker,
}


def get_chunker(strategy: str = "recursive", **kwargs) -> BaseChunker:
    """
    Get a chunker instance by strategy name.

    Args:
        strategy: Chunking strategy name. One of: 'fixed', 'recursive', 'parent_child'.
        **kwargs: Parameters forwarded to the chunker constructor
                  (e.g., chunk_size, chunk_overlap).

    Returns:
        An instance of the requested chunker.

    Raises:
        ValueError: If the strategy name is not recognized.
    """
    chunker_cls = _STRATEGIES.get(strategy.lower())
    if chunker_cls is None:
        available = ", ".join(sorted(set(_STRATEGIES.keys())))
        raise ValueError(
            f"Unknown chunking strategy: '{strategy}'. Available: {available}"
        )
    return chunker_cls(**kwargs)


def get_available_strategies() -> list[str]:
    """Return list of available strategy names."""
    return sorted(set(_STRATEGIES.keys()))


__all__ = [
    "BaseChunker",
    "Chunk",
    "FixedSizeChunker",
    "RecursiveChunker",
    "ParentChildChunker",
    "get_chunker",
    "get_available_strategies",
]
