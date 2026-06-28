"""
百炼（阿里云 DashScope）LLM 大语言模型服务封装模块。

通过 DashScope 的 OpenAI 兼容接口调用通义千问系列模型（如 qwen-plus），
提供对话生成能力，支持基于检索上下文的问答。
支持流式（SSE）和非流式两种响应模式。
"""

import logging
from collections.abc import Generator

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# RAG 场景默认系统提示词
# {context} 占位符会在运行时被检索到的文档内容替换
DEFAULT_SYSTEM_PROMPT = """你是一个专业的知识库问答助手。请根据提供的参考资料回答用户的问题。

回答规则：
1. 仅基于提供的参考资料进行回答，不要编造信息。
2. 如果参考资料中没有相关信息，请明确告知用户。
3. 回答时尽量引用具体的来源信息。
4. 保持回答准确、简洁、有条理。

以下是相关的参考资料：
{context}"""


class LLMService:
    """
    百炼 Chat Completion API（通义千问系列）服务封装。

    通过 OpenAI SDK 调用 DashScope 兼容接口，支持：
    - 非流式完整响应 (chat)
    - 流式逐块响应 (chat_stream)
    - 自定义系统提示词和对话历史
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        self.api_key = api_key or settings.dashscope_api_key
        self.model = model or settings.dashscope_llm_model
        self.base_url = base_url or settings.dashscope_base_url
        self.temperature = temperature or settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens
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

    def _build_messages(
        self,
        query: str,
        context: str,
        system_prompt: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        """
        构建发送给 API 的消息列表。

        消息结构：
        1. system 消息：包含系统提示词和检索到的上下文
        2. history 消息（可选）：之前的对话记录
        3. user 消息：用户当前的问题
        """
        prompt_template = system_prompt or DEFAULT_SYSTEM_PROMPT
        messages = [
            {"role": "system", "content": prompt_template.format(context=context)},
        ]

        # 追加对话历史（如有）
        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": query})
        return messages

    def chat(
        self,
        query: str,
        context: str,
        system_prompt: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """
        非流式对话：一次性返回完整回答。

        参数:
            query: 用户的问题。
            context: 从向量库检索到的文档上下文。
            system_prompt: 可选的自定义系统提示词（覆盖默认值）。
            history: 可选的对话历史，用于多轮对话。

        返回:
            模型生成的完整回答文本。
        """
        messages = self._build_messages(query, context, system_prompt, history)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        return response.choices[0].message.content or ""

    def chat_stream(
        self,
        query: str,
        context: str,
        system_prompt: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> Generator[str, None, None]:
        """
        流式对话：逐步生成回答文本块。

        适用于 SSE（Server-Sent Events）场景，
        用户可以在模型生成过程中实时看到回答。

        参数:
            query: 用户的问题。
            context: 从向量库检索到的文档上下文。
            system_prompt: 可选的自定义系统提示词。
            history: 可选的对话历史。

        生成:
            逐步产出回答文本的各个片段（字符串）。
        """
        messages = self._build_messages(query, context, system_prompt, history)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,  # 启用流式输出
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# ---- 全局单例 ----
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """获取或创建 LLM 服务的全局单例。"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
