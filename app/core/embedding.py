"""
百炼（阿里云 DashScope）Embedding 服务封装模块。

通过 DashScope 的 OpenAI 兼容接口调用文本嵌入模型（如 text-embedding-v3），
将文本转换为高维浮点向量用于相似度检索。
支持单条和批量嵌入，内置重试机制以应对网络波动。
"""

import logging
import time

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    百炼文本嵌入服务。

    通过 OpenAI SDK 调用 DashScope 兼容接口，提供：
    - 单条文本嵌入 (embed_text)
    - 批量文本嵌入 (embed_batch)，自动分批处理
    - 失败自动重试（指数退避）
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        max_retries: int = 3,     # 最大重试次数
        retry_delay: float = 1.0, # 初始重试间隔（秒）
    ):
        self.api_key = api_key or settings.dashscope_api_key
        self.model = model or settings.dashscope_embedding_model
        self.base_url = base_url or settings.dashscope_base_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        """懒加载 OpenAI 客户端（指向 DashScope 兼容接口），首次调用时才初始化。"""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "DASHSCOPE_API_KEY 未配置。请在 .env 文件或环境变量中设置。"
                )
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    def embed_text(self, text: str) -> list[float]:
        """
        将单条文本转换为向量。

        参数:
            text: 待嵌入的文本字符串。

        返回:
            浮点数列表，表示文本的向量表示（维度由模型决定，text-embedding-v3 默认 1024 维）。
        """
        embeddings = self.embed_batch([text])
        return embeddings[0]

    def embed_batch(self, texts: list[str], batch_size: int = 16) -> list[list[float]]:
        """
        批量将文本转换为向量。

        如果文本数量超过单次 API 调用限制，会自动分批处理。

        参数:
            texts: 待嵌入的文本列表。
            batch_size: 每次 API 调用最多处理的文本数，默认 16。

        返回:
            向量列表，与输入文本一一对应。
        """
        if not texts:
            return []

        all_embeddings: list[list[float]] = []

        # 按 batch_size 分批调用 API
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self._embed_with_retry(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def _embed_with_retry(self, texts: list[str]) -> list[list[float]]:
        """
        带重试机制的 Embedding API 调用。

        采用指数退避策略：每次失败后等待时间翻倍，
        直到达到最大重试次数后抛出 RuntimeError。
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                )
                # 按 index 排序确保返回顺序与输入一致
                sorted_data = sorted(response.data, key=lambda x: x.index)
                return [item.embedding for item in sorted_data]

            except Exception as e:
                last_error = e
                logger.warning(
                    "Embedding API 调用失败 (第 %d/%d 次尝试): %s",
                    attempt + 1,
                    self.max_retries,
                    str(e),
                )
                if attempt < self.max_retries - 1:
                    # 指数退避：等待时间随重试次数递增
                    time.sleep(self.retry_delay * (attempt + 1))

        raise RuntimeError(
            f"Embedding API 在 {self.max_retries} 次尝试后仍然失败: {last_error}"
        )


# ---- 全局单例 ----
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """获取或创建 Embedding 服务的全局单例。"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
