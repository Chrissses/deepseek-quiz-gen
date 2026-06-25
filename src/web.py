"""FastAPI Web 应用 —— 浏览器界面，上传文档 + 配置参数 + 选择 AI 厂商 + 生成试卷。"""

import json
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from starlette.requests import Request

from .generator import generate_quiz, list_available_providers

app = FastAPI(title="DeepSeek Quiz Generator", version="1.1.0")

# ── 静态文件 & 模板 ───────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
jinja_env = Environment(loader=FileSystemLoader(str(BASE_DIR / "templates")))
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ── 页面 ──────────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    template = jinja_env.get_template("index.html")
    return HTMLResponse(template.render(request=request))


# ── API ───────────────────────────────────────────────────────────────────


@app.get("/api/providers")
async def api_list_providers():
    """列出所有已配置的 AI Provider。"""
    providers = list_available_providers()
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "type": p["type"],
            "model": p.get("model", ""),
            "default": p.get("default", False),
            "has_key": bool(p.get("api_key")),
        }
        for p in providers
    ]


@app.post("/api/generate")
async def api_generate(
    file: UploadFile = File(...),
    count: int = Form(5, ge=5, le=50),
    difficulty: str = Form("混合"),
    types: str = Form("单选题,填空题"),
    custom_requirements: str = Form(""),
    model: Optional[str] = Form(None),
    provider_id: Optional[str] = Form(None),
):
    """生成试卷 API。"""
    # 读取上传文件
    try:
        raw = await file.read()
        try:
            doc_text = raw.decode("utf-8")
        except UnicodeDecodeError:
            doc_text = raw.decode("gbk")
    except Exception as e:
        return JSONResponse(
            {"error": True, "message": f"文件读取失败: {e}", "error_type": "file_error"},
            status_code=400,
        )

    question_types = [t.strip() for t in types.split(",") if t.strip()]

    result = generate_quiz(
        document_text=doc_text,
        question_count=count,
        difficulty=difficulty,
        question_types=question_types,
        source_filename=file.filename or "document.txt",
        custom_requirements=custom_requirements,
        model=model,
        provider_id=provider_id,
    )

    if result.get("error"):
        return JSONResponse(result, status_code=400)

    return result


@app.post("/api/generate/download")
async def api_generate_download(
    file: UploadFile = File(...),
    count: int = Form(5, ge=5, le=50),
    difficulty: str = Form("混合"),
    types: str = Form("单选题,填空题"),
    custom_requirements: str = Form(""),
    model: Optional[str] = Form(None),
    provider_id: Optional[str] = Form(None),
):
    """生成试卷并直接下载 JSON 文件。"""
    raw = await file.read()
    try:
        doc_text = raw.decode("utf-8")
    except UnicodeDecodeError:
        doc_text = raw.decode("gbk")

    question_types = [t.strip() for t in types.split(",") if t.strip()]

    result = generate_quiz(
        document_text=doc_text,
        question_count=count,
        difficulty=difficulty,
        question_types=question_types,
        source_filename=file.filename or "document.txt",
        custom_requirements=custom_requirements,
        model=model,
        provider_id=provider_id,
    )

    if result.get("error"):
        return JSONResponse(result, status_code=400)

    # 写入临时文件供下载
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(result, tmp, ensure_ascii=False, indent=2)
    tmp.close()

    stem = Path(file.filename or "quiz").stem
    download_name = f"{stem}_quiz.json"

    return FileResponse(
        tmp.name,
        media_type="application/json",
        filename=download_name,
    )
