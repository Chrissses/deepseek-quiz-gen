"""Provider 配置加载器 —— 从 providers.json 读取多厂商配置，支持环境变量插值。"""

import json
import os
import re
from pathlib import Path
from typing import Any


# providers.json 位置：项目根目录
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "providers.json"


def _interpolate_env(value: str) -> str:
    """替换字符串中的 ${VAR_NAME} 为环境变量值。"""
    def _replace(match: re.Match[str]) -> str:
        var_name = match.group(1)
        return os.getenv(var_name, "")

    return re.sub(r"\$\{(\w+)\}", _replace, value)


def _interpolate_dict(data: dict[str, Any]) -> dict[str, Any]:
    """递归替换字典中所有字符串的 ${VAR_NAME}。"""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = _interpolate_env(value)
        elif isinstance(value, dict):
            result[key] = _interpolate_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _interpolate_env(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def load_providers(config_path: Path | None = None) -> list[dict[str, Any]]:
    """加载所有已配置的 Provider。

    Args:
        config_path: 自定义配置文件路径，默认使用项目根目录的 providers.json

    Returns:
        Provider 配置字典列表，每个字典包含:
        - id: 唯一标识
        - name: 显示名称
        - type: openai_compatible / anthropic / gemini
        - api_key: 已插值的 API Key
        - base_url: (可选) API 端点
        - model: 默认模型
        - default: (可选) 是否为默认 Provider
    """
    path = config_path or _CONFIG_PATH

    if not path.exists():
        # 降级：无配置文件时，从环境变量构建单个 DeepSeek provider
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if api_key:
            return [
                {
                    "id": "deepseek",
                    "name": "DeepSeek",
                    "type": "openai_compatible",
                    "api_key": api_key,
                    "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                    "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                    "default": True,
                }
            ]
        return []

    raw = json.loads(path.read_text(encoding="utf-8"))
    providers = raw.get("providers", [])

    return [_interpolate_dict(p) for p in providers]


def get_default_provider(providers: list[dict[str, Any]]) -> dict[str, Any] | None:
    """获取默认 Provider 配置。

    优先选择 default=true 的，否则返回第一个有 API Key 的。
    """
    # 1. 优先 default=true
    for p in providers:
        if p.get("default") and p.get("api_key"):
            return p

    # 2. 第一个有 API Key 的
    for p in providers:
        if p.get("api_key"):
            return p

    return None


def get_provider_by_id(
    providers: list[dict[str, Any]], provider_id: str
) -> dict[str, Any] | None:
    """按 ID 查找 Provider。"""
    for p in providers:
        if p.get("id") == provider_id:
            return p
    return None
