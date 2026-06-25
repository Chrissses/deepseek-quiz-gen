"""核心出题引擎 —— 调用 DeepSeek API，解析校验返回的 JSON。"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

from .prompt import build_messages

load_dotenv()

# ── 配置 ──────────────────────────────────────────────────────────────────

DEFAULT_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEFAULT_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
API_KEY = os.getenv("DEEPSEEK_API_KEY", "")


def _get_client():
    """延迟导入 openai，仅在需要时创建客户端。"""
    from openai import OpenAI

    return OpenAI(api_key=API_KEY, base_url=DEFAULT_BASE_URL)


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


# ── 主入口 ────────────────────────────────────────────────────────────────


def generate_quiz(
    document_text: str,
    question_count: int = 5,
    difficulty: str = "混合",
    question_types: list[str] | None = None,
    source_filename: str = "document.txt",
    custom_requirements: str = "",
    model: str | None = None,
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

    # 2. 检查 API Key
    if not API_KEY:
        return {
            "error": True,
            "message": "未配置 DEEPSEEK_API_KEY",
            "error_type": "config_error",
            "suggestion": "请在 .env 文件或环境变量中设置 DEEPSEEK_API_KEY。",
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

    client = _get_client()

    try:
        response = client.chat.completions.create(
            model=model or DEFAULT_MODEL,
            messages=messages,  # pyright: ignore[reportArgumentType]
            temperature=0.7,
            max_tokens=8192,
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content

        if not raw_content:
            return {
                "error": True,
                "message": "API 返回空内容",
                "error_type": "api_empty_response",
                "suggestion": "请重试或检查 API 配置。",
            }

        # Debug: 打印原始返回
        print(f"[DEBUG] Raw response ({len(raw_content)} chars):")
        print(raw_content[:500])
        print("---")

    except Exception as e:
        return {
            "error": True,
            "message": f"API 调用失败: {str(e)}",
            "error_type": "api_error",
            "suggestion": "请检查 API Key 与网络连接。",
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
