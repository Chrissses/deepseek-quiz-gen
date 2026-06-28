"""核心出题引擎 —— 调用 AI Provider API，解析校验返回的 JSON。"""

import json
import re
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

from .prompt import build_messages
from .providers import create_provider
from .provider_config import get_default_provider, get_provider_by_id, load_providers

load_dotenv()

# ── JSON 提取 ─────────────────────────────────────────────────────────────

def _extract_json(text: str) -> str:
    """从 LLM 响应中提取纯 JSON 字符串（去除 markdown 代码块包裹）。"""
    text = text.strip()

    # 匹配 ```json ... ``` 或 ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        candidate = match.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass

    # 尝试匹配最外层 { ... } — 支持嵌套大括号
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start != -1:
                candidate = text[start : i + 1]
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    start = -1

    # 最后兜底：直接返回原文
    return text


# ── 输入校验 ──────────────────────────────────────────────────────────────

VALID_DIFFICULTIES = {"简单", "中等", "困难", "混合"}
VALID_QUESTION_TYPES = {"单选题", "填空题", "多选题", "简答题"}

# ── 中英文映射 ──────────────────────────────────

DIFFICULTY_MAP = {
    "simple": "简单", "easy": "简单",
    "medium": "中等", "normal": "中等",
    "hard": "困难", "difficult": "困难",
    "mixed": "混合", "mix": "混合",
}

TYPE_MAP = {
    "single_choice": "单选题", "single": "单选题", "choice": "单选题",
    "fill_blank": "填空题", "fill": "填空题", "blank": "填空题",
    "multi_choice": "多选题", "multiple": "多选题",
    "short_answer": "简答题", "short": "简答题", "essay": "简答题",
}


def _normalize_difficulty(value: str) -> str:
    """将英文难度值转为中文。"""
    return DIFFICULTY_MAP.get(value.lower(), value)


def _normalize_types(types: list[str]) -> list[str]:
    """将英文题型转为中文。"""
    return [TYPE_MAP.get(t.lower(), t) for t in types]


def validate_inputs(
    document_text: str,
    question_count: int,
    difficulty: str,
    question_types: list[str],
) -> dict[str, Any] | None:
    """前置校验。返回 None 表示通过，否则返回错误 dict。"""
    difficulty = _normalize_difficulty(difficulty)
    question_types = _normalize_types(question_types)

    if difficulty not in VALID_DIFFICULTIES:
        return {
            "error": True,
            "message": f"不支持的难度参数: '{difficulty}'",
            "error_type": "unsupported_difficulty",
            "suggestion": "难度仅支持：简单/中等/困难/混合。",
        }

    if question_count < 5 or question_count > 50:
        return {
            "error": True,
            "message": f"题目数量 {question_count} 不在有效范围 (5-50)",
            "error_type": "invalid_count",
            "suggestion": "请将题目数量设定在 5 到 50 之间。",
        }

    invalid_types = [t for t in question_types if t not in VALID_QUESTION_TYPES]
    if invalid_types:
        return {
            "error": True,
            "message": f"不支持的题型: {', '.join(invalid_types)}",
            "error_type": "invalid_question_types",
            "suggestion": "仅支持：单选题/填空题/多选题/简答题。",
        }

    # 粗略估算 token 数（中文 ~2-3 字符/token，英文 ~4 字符/token）
    estimated_tokens = len(document_text) // 2
    if estimated_tokens < 100:
        return {
            "error": True,
            "message": "文档内容过短（估算 < 100 tokens）",
            "error_type": "content_too_short",
            "suggestion": "请补充更完整的文档内容。",
        }
    if estimated_tokens > 950_000:
        return {
            "error": True,
            "message": "文档内容过大（估算 > 950K tokens）",
            "error_type": "content_too_large",
            "suggestion": "请减少文档内容或分批上传。",
        }

    return None


# ── Provider 解析 ──────────────────────────────────────────────────────────


def _resolve_provider_config(
    provider_id: str | None,
) -> dict[str, Any] | None:
    """解析 Provider 配置。

    Args:
        provider_id: 指定的 provider ID，为 None 时使用默认

    Returns:
        Provider 配置字典，包含 type / api_key / base_url / model 等

    Raises:
        ValueError: 未找到 provider 或未配置 API Key
    """
    all_providers = load_providers()

    if not all_providers:
        raise ValueError(
            "未找到任何 AI Provider 配置。请创建 providers.json 并在 .env 中设置对应的 API Key。"
        )

    if provider_id:
        config = get_provider_by_id(all_providers, provider_id)
        if config is None:
            available = ", ".join(p["id"] for p in all_providers)
            raise ValueError(
                f"未找到 provider '{provider_id}'。可用: {available}"
            )
    else:
        config = get_default_provider(all_providers)
        if config is None:
            available = ", ".join(p["id"] for p in all_providers)
            raise ValueError(
                f"没有可用的默认 Provider。请在 providers.json 中设置 default: true，或在 .env 中配置 API Key。可用: {available}"
            )

    if not config.get("api_key"):
        raise ValueError(
            f"Provider '{config['id']}' 未配置 API Key。请在 .env 中设置 {config.get('id', '').upper()}_API_KEY。"
        )

    return config


# ── 主入口 ────────────────────────────────────────────────────────────────


def generate_quiz(
    document_text: str,
    question_count: int = 5,
    difficulty: str = "混合",
    question_types: list[str] | None = None,
    source_filename: str = "document.txt",
    custom_requirements: str = "",
    model: str | None = None,
    provider_id: str | None = None,
    api_key: str = "",
    base_url: str = "",
) -> dict[str, Any]:
    """生成试卷的主入口。

    Args:
        document_text: 文档原文
        question_count: 题目数量 (5-50)
        difficulty: 简单/中等/困难/混合
        question_types: 题型列表，默认 ["单选题", "填空题"]
        source_filename: 源文件名
        custom_requirements: 定制需求
        model: 覆盖默认模型
        provider_id: 指定 AI provider ID，为 None 使用默认
        api_key: 直接传入 API Key（跳过配置文件）
        base_url: 直接传入 Base URL（配合 api_key 使用）

    Returns:
        正常试卷 dict 或错误 dict
    """
    if question_types is None:
        question_types = ["单选题", "填空题"]

    # 0. 规范化中英文
    difficulty = _normalize_difficulty(difficulty)
    question_types = _normalize_types(question_types)

    # 1. 前置校验
    error = validate_inputs(document_text, question_count, difficulty, question_types)
    if error:
        return error

    # 2. 解析 Provider（优先使用直接传入的 api_key）
    if api_key:
        # 如果同时选了 provider，继承其 base_url / model
        _base_url = base_url
        _model = model
        if provider_id and (not base_url or not model):
            for p in load_providers():
                if p["id"] == provider_id:
                    if not _base_url:
                        _base_url = p.get("base_url", "")
                    if not _model:
                        _model = p.get("model", "")
                    break
        provider_config = {
            "id": "custom",
            "name": "Custom",
            "type": "openai_compatible",
            "api_key": api_key,
            "base_url": _base_url or "https://api.openai.com/v1",
            "model": _model or "gpt-4o",
        }
    else:
        try:
            provider_config = _resolve_provider_config(provider_id)
        except ValueError as e:
            return {
                "error": True,
                "message": str(e),
                "error_type": "config_error",
                "suggestion": "请在 .env 中设置 API Key，或直接在界面中输入。",
            }

    # 3. 构建消息并调用 API
    messages = build_messages(
        document_text=document_text,
        question_count=question_count,
        difficulty=difficulty,
        question_types=question_types,
        source_filename=source_filename,
        custom_requirements=custom_requirements,
    )

    provider = create_provider(provider_config)
    effective_model = model or provider_config.get("model", "")

    try:
        raw_content = provider.generate(
            messages=messages,
            model=effective_model,
            temperature=0.7,
            max_tokens=8192,
            response_format={"type": "json_object"},
        )

        # Debug: 打印原始返回
        print(f"[DEBUG] Raw response ({len(raw_content)} chars):")
        print(raw_content[:500])
        print("---")

    except Exception as e:
        err_msg = str(e)
        hint = "请检查 API Key 是否正确，以及 Base URL 是否匹配所选厂商。"
        if "401" in err_msg or "invalid_api_key" in err_msg:
            hint = "API Key 无效或已过期。请确认：1) Key 正确 2) 所选厂商与 Key 匹配（如 OpenAI key 应选 OpenAI 厂商）"
        return {
            "error": True,
            "message": f"AI 调用失败 [{provider_config['id']}]: {e}",
            "error_type": "api_error",
            "suggestion": hint,
        }

    # 4. 解析 JSON
    json_str = _extract_json(raw_content)

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError:
        return {
            "error": True,
            "message": "LLM 返回内容无法解析为 JSON",
            "error_type": "parse_error",
            "suggestion": "请重试或调整文档内容。",
            "raw_response": raw_content[:300],
            "extracted_attempt": json_str[:300],
        }

    # 5. 如果是 LLM 返回的错误
    if result.get("error"):
        return result

    # 6. 附加时间戳
    if "quiz_metadata" in result and "created_at" not in result["quiz_metadata"]:
        result["quiz_metadata"]["created_at"] = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    return result


def list_available_providers() -> list[dict[str, Any]]:
    """列出所有可用的 Provider（供 CLI / Web 展示）。"""
    return load_providers()
