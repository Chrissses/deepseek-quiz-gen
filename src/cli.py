"""CLI 命令行入口 —— 用 Typer 实现，支持文档路径和参数传入。"""

import json
from pathlib import Path
from typing import Optional

import typer

from .generator import VALID_DIFFICULTIES, VALID_QUESTION_TYPES, generate_quiz

app = typer.Typer(
    name="deepseek-quiz",
    help="基于 DeepSeek AI 的智能出题工具 —— 根据文档自动生成结构化试卷 JSON。",
    add_completion=False,
)


@app.command()
def generate(
    document: Path = typer.Argument(
        ..., exists=True, readable=True, help="输入文档路径（.txt / .md 等纯文本格式）"
    ),
    count: int = typer.Option(5, "--count", "-n", min=5, max=50, help="题目数量 (5-50)"),
    difficulty: str = typer.Option(
        "混合",
        "--difficulty",
        "-d",
        help="难度：简单 / 中等 / 困难 / 混合",
    ),
    types: str = typer.Option(
        "单选题,填空题",
        "--types",
        "-t",
        help="题型，逗号分隔：单选题,填空题,多选题,简答题",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出 JSON 文件路径（不指定则自动命名）",
    ),
    requirements: str = typer.Option(
        "",
        "--require",
        "-r",
        help="定制需求，如 '不出多选题' 或 '侧重第三章'",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="覆盖默认模型名称",
    ),
    pretty: bool = typer.Option(
        True,
        "--pretty/--compact",
        help="是否格式化输出 JSON",
    ),
):
    """根据文档内容生成试卷 JSON。"""
    # 解析题型
    question_types = [t.strip() for t in types.split(",") if t.strip()]

    # 读取文档
    try:
        doc_text = document.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        doc_text = document.read_text(encoding="gbk")

    source_name = document.name

    # 生成
    typer.echo(f"📄 文档: {source_name} ({len(doc_text)} 字符)")
    typer.echo(f"📝 题目数: {count}  | 难度: {difficulty}  | 题型: {', '.join(question_types)}")
    typer.echo("⏳ 正在调用 DeepSeek API 生成试卷...")

    result = generate_quiz(
        document_text=doc_text,
        question_count=count,
        difficulty=difficulty,
        question_types=question_types,
        source_filename=source_name,
        custom_requirements=requirements,
        model=model,
    )

    # 输出
    if result.get("error"):
        typer.secho(f"\n❌ 生成失败: {result.get('message')}", fg="red")
        typer.secho(f"   错误类型: {result.get('error_type')}", fg="yellow")
        if suggestion := result.get("suggestion"):
            typer.secho(f"   建议: {suggestion}", fg="yellow")
        raise typer.Exit(1)

    # 确定输出路径
    if output is None:
        stem = document.stem or "quiz"
        output = Path(f"{stem}_quiz.json")

    indent = 2 if pretty else None
    output.write_text(json.dumps(result, ensure_ascii=False, indent=indent), encoding="utf-8")

    typer.secho(f"\n✅ 试卷已生成: {output.absolute()}", fg="green")

    # 打印摘要
    meta = result.get("quiz_metadata", {})
    questions = result.get("questions", [])
    typer.echo(f"   标题: {meta.get('title', 'N/A')}")
    typer.echo(f"   题目数: {len(questions)}")
    typer.echo(f"   难度分布: {meta.get('difficulty_distribution', 'N/A')}")
    typer.echo(f"   预计用时: {meta.get('estimated_solve_time_minutes', 'N/A')} 分钟")


@app.command()
def version():
    """显示版本信息。"""
    from . import __version__

    typer.echo(f"DeepSeek Quiz Generator v{__version__}")


def main():
    app()


if __name__ == "__main__":
    main()
