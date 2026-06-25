"""AI Provider 抽象基类 —— 所有厂商适配器必须实现此接口。"""

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """AI 服务提供商的统一抽象。

    所有厂商适配器（OpenAI-compatible / Anthropic / Gemini）均继承此类，
    对外暴露唯一的 generate() 方法，屏蔽底层 API 差异。
    """

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        **kwargs: Any,
    ) -> str:
        """调用 AI API 生成文本。

        Args:
            messages: 标准 OpenAI 格式的消息列表
                      [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            model: 模型名称
            **kwargs: 厂商特定参数

        Returns:
            模型返回的纯文本内容

        Raises:
            ProviderError: 调用失败时抛出
        """
        ...


class ProviderError(Exception):
    """Provider 调用异常。"""

    def __init__(self, message: str, provider: str = "", original_error: Exception | None = None):
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error
