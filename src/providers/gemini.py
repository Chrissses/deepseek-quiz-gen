"""Google Gemini Provider —— 适配 Gemini generateContent API。"""

from typing import Any

from .base import BaseProvider, ProviderError


class GeminiProvider(BaseProvider):
    """Google Gemini API Provider。

    将 OpenAI 格式消息转为 Gemini 的 contents 格式，
    system prompt 通过 system_instruction 参数传递。
    """

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
        return self._client

    @staticmethod
    def _convert_messages(
        messages: list[dict[str, str]],
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """将 OpenAI 格式消息转为 Gemini contents 格式。

        Gemini contents 格式:
        [{"role": "user", "parts": [{"text": "..."}]},
         {"role": "model", "parts": [{"text": "..."}]}]

        Returns:
            (system_instruction, gemini_contents)
        """
        system_instruction: str | None = None
        gemini_contents: list[dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_instruction = content
            elif role == "user":
                gemini_contents.append({
                    "role": "user",
                    "parts": [{"text": content}],
                })
            elif role == "assistant":
                gemini_contents.append({
                    "role": "model",
                    "parts": [{"text": content}],
                })

        return system_instruction, gemini_contents

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        **kwargs: Any,
    ) -> str:
        """调用 Gemini API。

        Args:
            messages: OpenAI 格式消息列表（自动转换）
            model: 模型名称，如 gemini-2.0-flash
            temperature: 温度参数 (0-2)
            max_tokens: 最大输出 token 数
        """
        client = self._get_client()
        system_instruction, gemini_contents = self._convert_messages(messages)

        try:
            config: dict[str, Any] = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            if system_instruction:
                config["system_instruction"] = system_instruction

            response = client.models.generate_content(
                model=model,
                contents=gemini_contents,
                config=config,
            )

            if not response.text:
                raise ProviderError(
                    "Gemini 返回空内容",
                    provider="gemini",
                )

            return response.text

        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(
                f"Gemini API 调用失败: {e}",
                provider="gemini",
                original_error=e,
            ) from e
