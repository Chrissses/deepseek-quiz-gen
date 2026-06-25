# DeepSeek Quiz Generator

> AI-powered quiz generator — upload a document, get a structured quiz in seconds.

Built on a **multi-provider AI architecture**, this tool analyzes any text document and generates professionally structured quizzes with multiple question types, difficulty distribution, and detailed answer analysis. Supports DeepSeek, OpenAI, Claude, Gemini, Qwen, Zhipu, Moonshot, and any OpenAI-compatible API.

![](https://img.shields.io/badge/Python-3.10%2B-blue) ![](https://img.shields.io/badge/FastAPI-0.115%2B-green) ![](https://img.shields.io/badge/Multi--Provider-purple)

## Features

- **Multiple Question Types** — Single Choice, Multiple Choice, Fill-in-the-Blank, Short Answer
- **Smart Difficulty Distribution** — Easy / Medium / Hard / Mixed (auto-split 25/50/25%)
- **Rich Analysis** — Each question includes detailed reasoning, common mistakes, and knowledge tags
- **Dual Interface** — CLI for quick generation, Web UI for interactive use
- **Interactive Quiz Mode** — Take the quiz in-browser with real-time scoring and feedback
- **Dark Cyberpunk Theme** — Neon-accented dark mode UI
- **Bilingual Support** — UI in English; quiz language follows your document
- **🆕 Multi-Provider Support** — Switch between DeepSeek / OpenAI / Claude / Gemini / Qwen / Zhipu / Moonshot

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy `.env.example` to `.env` and add your API keys:

```env
# Required: at least one provider
DEEPSEEK_API_KEY=sk-your-key-here

# Optional: add more providers
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GEMINI_API_KEY=your-key-here
QWEN_API_KEY=sk-your-key-here
```

> 💡 Edit `providers.json` to customize which providers appear in the UI. Providers without API keys are automatically disabled.

### 3. Run

**Web Mode** (recommended):
```bash
python run_web.py
```
Open `http://localhost:8000` in your browser — select your AI provider from the dropdown.

**CLI Mode**:
```bash
# Use default provider
python run_cli.py document.txt -n 10 -d mixed -t "单选题,填空题"

# Use a specific provider
python run_cli.py document.txt -n 10 -p openai -m gpt-4o

# List all configured providers
python run_cli.py providers
```

### 4. One-Click Launch (Windows)

Double-click `start.bat` — auto-creates virtual environment, installs dependencies, and launches.

## CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `-n, --count` | Number of questions (5-50) | 5 |
| `-d, --difficulty` | simple / medium / hard / mixed | mixed |
| `-t, --types` | Comma-separated: 单选题,多选题,填空题,简答题 | 单选题,填空题 |
| `-p, --provider` | Provider ID (deepseek/openai/claude/gemini/...) | default in providers.json |
| `-m, --model` | Override default model | provider default |
| `-r, --require` | Custom requirements | — |
| `-o, --output` | Output JSON path | auto-named |

## Provider Configuration

Configure providers in `providers.json`. Each provider entry:

```json
{
  "id": "deepseek",
  "name": "DeepSeek",
  "type": "openai_compatible",
  "api_key": "${DEEPSEEK_API_KEY}",
  "base_url": "https://api.deepseek.com",
  "model": "deepseek-chat",
  "default": true
}
```

**Supported provider types:**

| Type | Description | Examples |
|------|-------------|----------|
| `openai_compatible` | OpenAI-compatible API | DeepSeek, OpenAI, Qwen, Zhipu, Moonshot, Ollama, vLLM |
| `anthropic` | Anthropic Messages API | Claude 3.5 Sonnet, Claude 3 Opus |
| `gemini` | Google Generative AI | Gemini 2.0 Flash, Gemini 1.5 Pro |

API keys use `${ENV_VAR}` syntax — values are read from `.env` at runtime.

## Project Structure

```
deepseek-quiz-gen/
├── src/
│   ├── providers/             # AI provider abstraction layer
│   │   ├── base.py            # Abstract base class
│   │   ├── openai_compatible.py  # OpenAI-compatible provider
│   │   ├── anthropic.py       # Anthropic Claude provider
│   │   ├── gemini.py          # Google Gemini provider
│   │   └── __init__.py        # Factory & exports
│   ├── provider_config.py     # Multi-provider config loader
│   ├── prompt.py              # System prompt template
│   ├── generator.py           # Core engine (provider dispatch + JSON parsing)
│   ├── cli.py                 # Typer CLI entry
│   ├── web.py                 # FastAPI web app
│   └── templates/
│       └── index.html         # Web UI (single-file app)
├── providers.json             # Provider definitions
├── run_cli.py                 # CLI launcher
├── run_web.py                 # Web launcher
├── start.bat                  # Windows one-click launcher
├── requirements.txt
└── .env.example
```

## Output Format

The generated quiz follows a strict JSON schema:

```json
{
  "quiz_metadata": {
    "title": "Quiz Title",
    "difficulty_distribution": "2easy_3medium_0hard",
    "question_count": 5,
    "estimated_solve_time_minutes": 25
  },
  "questions": [
    {
      "id": "q001",
      "type": "single_choice",
      "difficulty": "medium",
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
