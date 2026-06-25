# DeepSeek Quiz Generator

> AI-powered quiz generator — upload a document, get a structured quiz in seconds.

Built on **DeepSeek API**, this tool analyzes any text document and generates professionally structured quizzes with multiple question types, difficulty distribution, and detailed answer analysis.

![](https://img.shields.io/badge/Python-3.10%2B-blue) ![](https://img.shields.io/badge/FastAPI-0.115%2B-green) ![](https://img.shields.io/badge/DeepSeek-API-purple)

## Features

- **Multiple Question Types** — Single Choice, Multiple Choice, Fill-in-the-Blank, Short Answer
- **Smart Difficulty Distribution** — Easy / Medium / Hard / Mixed (auto-split 25/50/25%)
- **Rich Analysis** — Each question includes detailed reasoning, common mistakes, and knowledge tags
- **Dual Interface** — CLI for quick generation, Web UI for interactive use
- **Interactive Quiz Mode** — Take the quiz in-browser with real-time scoring and feedback
- **Dark Cyberpunk Theme** — Neon-accented dark mode UI
- **Bilingual Support** — UI in English; quiz language follows your document

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Copy `.env.example` to `.env` and add your DeepSeek API key:

```
DEEPSEEK_API_KEY=sk-your-key-here
```

Get a key at [platform.deepseek.com](https://platform.deepseek.com).

### 3. Run

**Web Mode** (recommended):
```bash
python run_web.py
```
Open `http://localhost:8000` in your browser.

**CLI Mode**:
```bash
python run_cli.py document.txt -n 10 -d mixed -t "单选题,填空题"
```

### 4. One-Click Launch (Windows)

Double-click `start.bat` — auto-creates virtual environment, installs dependencies, and launches.

## CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `-n, --count` | Number of questions (5-50) | 5 |
| `-d, --difficulty` | simple / medium / hard / mixed | mixed |
| `-t, --types` | Comma-separated: 单选题,多选题,填空题,简答题 | 单选题,填空题 |
| `-r, --require` | Custom requirements | — |
| `-o, --output` | Output JSON path | auto-named |

## Project Structure

```
deepseek-quiz-gen/
├── src/
│   ├── prompt.py          # System prompt template
│   ├── generator.py       # Core engine (API call + JSON parsing)
│   ├── cli.py             # Typer CLI entry
│   ├── web.py             # FastAPI web app
│   └── templates/
│       └── index.html     # Web UI (single-file app)
├── run_cli.py             # CLI launcher
├── run_web.py             # Web launcher
├── start.bat              # Windows one-click launcher
├── requirements.txt
└── .env.example
```

## Output Format

The generated quiz follows a strict JSON schema:

```json
{
  "quiz_metadata": {
    "title": "Quiz Title",
    "difficulty_distribution": "2简单_3中等_0困难",
    "question_count": 5,
    "estimated_solve_time_minutes": 25
  },
  "questions": [
    {
      "id": "q001",
      "type": "单选题",
      "difficulty": "中等",
      "stem": "Question text...",
      "options": { "A": "...", "B": "...", "C": "...", "D": "..." },
      "correct_answer": "B",
      "analysis": {
        "short": "Short answer (≤15 chars)",
        "detailed": "Full reasoning chain...",
        "common_mistakes": ["Mistake 1", "Mistake 2"]
      },
      "knowledge_tags": ["Category>Subcategory", "Key Concept"]
    }
  ]
}
```

## License

MIT
