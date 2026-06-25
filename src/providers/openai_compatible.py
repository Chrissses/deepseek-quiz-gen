"""OpenAI 兼容协议 Provider —— 覆盖 DeepSeek / OpenAI / 通义千问 / 智谱 / Kimi / 豆包 等。"""

from typing import Any

from .base import BaseProvider, ProviderError


class OpenAICompatibleProvider(BaseProvider):
    """基于 OpenAI Python SDK 的通用 Provider。

    任何兼容 OpenAI chat/completions 协议的 API 均可使用：
    - DeepSeek (api.deepseek.com)
    - OpenAI (api.openai.com)
    - 通义千问 (dashscope.aliyuncs.com)
    - 智谱 (open.bigmodel.cn)
    - Moonshot/Kimi (api.moonshot.cn)
    - 豆包 (ark.cn-beijing.volces.com)
    - 本地 Ollama / vLLM
    """

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self._api_key = api_key
        self._base_url = base_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        return self._client

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        response_format: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> str:
        """调用 OpenAI-compatible API。

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数 (0-2)
            max_tokens: 最大输出 token 数
            response_format: 响应格式，如 {"type": "json_object"}
        """
        client = self._get_client()

        try:
            params: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format is not None:
                params["response_format"] = response_format

            response = client.chat.completions.create(**params)
            content = response.choices[0].message.content

            if not content:
                raise ProviderError(
                    "API 返回空内容",
                    provider="openai_compatible",
                )

            return content

        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(
                f"API 调用失败: {e}",
                provider="openai_compatible",
                original_error=e,
            ) from e
