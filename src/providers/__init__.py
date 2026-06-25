"""AI Provider 层 —— 统一的多厂商适配。

使用方式:
    from src.providers import create_provider
    provider = create_provider(provider_config)
    text = provider.generate(messages, model="deepseek-chat")
"""

from .base import BaseProvider, ProviderError
from .anthropic import AnthropicProvider
from .gemini import GeminiProvider
from .openai_compatible import OpenAICompatibleProvider

__all__ = [
    "BaseProvider",
    "ProviderError",
    "AnthropicProvider",
    "GeminiProvider",
    "OpenAICompatibleProvider",
    "create_provider",
]


def create_provider(config: dict) -> BaseProvider:
    """根据配置字典创建对应的 Provider 实例。

    Args:
        config: Provider 配置字典，需包含:
            - type: "openai_compatible" | "anthropic" | "gemini"
            - api_key: API 密钥
            - base_url: (可选) API 端点

    Returns:
        对应的 Provider 实例

    Raises:
        ValueError: 不支持的 provider type
    """
    provider_type = config.get("type", "openai_compatible")
    api_key = config.get("api_key", "")

    if provider_type == "openai_compatible":
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=config.get("base_url", "https://api.openai.com/v1"),
        )
    elif provider_type == "anthropic":
        return AnthropicProvider(
            api_key=api_key,
            base_url=config.get("base_url"),
        )
    elif provider_type == "gemini":
        return GeminiProvider(api_key=api_key)
    else:
        raise ValueError(f"不支持的 provider type: '{provider_type}'")
