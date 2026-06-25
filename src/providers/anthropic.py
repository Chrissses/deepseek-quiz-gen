"""Anthropic Claude Provider —— 适配 Anthropic Messages API。"""

from typing import Any

from .base import BaseProvider, ProviderError


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API Provider。

    由于 Anthropic API 的 system prompt 是顶层参数（非 messages 元素），
    需将 OpenAI 格式的 system 消息提取为独立参数，其余消息按 roles 映射。
    """

    def __init__(self, api_key: str, base_url: str | None = None):
        self._api_key = api_key
        self._base_url = base_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            from anthropic import Anthropic

            kwargs: dict[str, Any] = {"api_key": self._api_key}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = Anthropic(**kwargs)
        return self._client

    @staticmethod
    def _convert_messages(
        messages: list[dict[str, str]],
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """将 OpenAI 格式消息转为 Anthropic 格式。

        Returns:
            (system_prompt, anthropic_messages)
        """
        system_prompt: str | None = None
        anthropic_msgs: list[dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                # Anthropic 的 system prompt 是顶层参数
                system_prompt = content
            elif role == "user":
                anthropic_msgs.append({"role": "user", "content": content})
            elif role == "assistant":
                anthropic_msgs.append({"role": "assistant", "content": content})
            # 忽略其他角色

        return system_prompt, anthropic_msgs

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        **kwargs: Any,
    ) -> str:
        """调用 Anthropic Messages API。

        Args:
            messages: OpenAI 格式消息列表（自动转换）
            model: 模型名称，如 claude-3-5-sonnet-20240620
            temperature: 温度参数 (0-1)
            max_tokens: 最大输出 token 数
        """
        client = self._get_client()
        system_prompt, anthropic_msgs = self._convert_messages(messages)

        try:
            params: dict[str, Any] = {
                "model": model,
                "messages": anthropic_msgs,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if system_prompt:
                params["system"] = system_prompt

            response = client.messages.create(**params)

            # Anthropic 返回 content 为列表 [{"type": "text", "text": "..."}]
            for block in response.content:
                if block.type == "text":
                    return block.text

            raise ProviderError(
                "Claude 返回了非文本内容",
                provider="anthropic",
            )

        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(
                f"Anthropic API 调用失败: {e}",
                provider="anthropic",
                original_error=e,
            ) from e
