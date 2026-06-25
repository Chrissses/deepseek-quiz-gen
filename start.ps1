# DeepSeek Quiz Generator - Launcher
$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "DeepSeek Quiz Generator"
Set-Location $PSScriptRoot

# ── 检测 Python ──────────────────────────────────
$pyCmd = $null
@("python", "python3", "py") | ForEach-Object {
    if (-not $pyCmd) {
        $result = & $_ --version 2>$null
        if ($LASTEXITCODE -eq 0) { $pyCmd = $_ }
    }
}

if (-not $pyCmd) {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ERROR: Python not found" -ForegroundColor Red
    Write-Host "  Install Python 3.10+ from python.org" -ForegroundColor Yellow
    Write-Host "  Check 'Add Python to PATH' during install" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# ── 创建虚拟环境（首次运行）─────────────────────
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[Setup] Creating virtual environment..." -ForegroundColor Cyan
    & $pyCmd -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create venv" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
    Write-Host ""
}

$venvPy = ".venv\Scripts\python.exe"
$venvPip = ".venv\Scripts\pip.exe"

# ── 安装依赖 ──────────────────────────────────
Write-Host "[Setup] Installing dependencies (first run, ~30s)..." -ForegroundColor Cyan
& $venvPip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    # 可能 venv 损坏，重建
    Write-Host "[Setup] Venv may be corrupted, recreating..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
    & $pyCmd -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create venv" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[Setup] Retrying install..." -ForegroundColor Cyan
    & $venvPip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install. Please check:" -ForegroundColor Red
        Write-Host "  1. Network connection" -ForegroundColor Yellow
        Write-Host "  2. Run manually: .venv\Scripts\pip.exe install -r requirements.txt" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Host "[OK] Dependencies ready" -ForegroundColor Green
Write-Host ""

# ── 配置 .env（首次运行）────────────────────────
if (-not (Test-Path ".env")) {
    Write-Host "[Setup] Creating .env from template..." -ForegroundColor Cyan
    Copy-Item ".env.example" ".env" -Force

    $apiKey = Read-Host "Enter DeepSeek API Key (or press Enter to skip)"
    if ($apiKey) {
        (Get-Content ".env") -replace "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", $apiKey | Set-Content ".env"
    }
    Write-Host "[OK] .env file ready" -ForegroundColor Green
    Write-Host ""
}

# ── 主菜单循环 ──────────────────────────────────
while ($true) {
    Clear-Host
    Write-Host ""
    Write-Host "+---------------------------------------------+"
    Write-Host "|     AI Quiz Generator v1.1 (Multi-Provider)  |"
    Write-Host "+---------------------------------------------+"
    Write-Host "|  1. CLI  - Command line mode                 |"
    Write-Host "|  2. Web  - Browser mode                      |"
    Write-Host "|  3. Edit .env config                         |"
    Write-Host "|  0. Exit                                     |"
    Write-Host "+---------------------------------------------+"
    Write-Host ""

    $mode = Read-Host "Select [1/2/3/0]"

    switch ($mode) {
        "0" { Write-Host "Bye!"; break }
        "3" { notepad .env; continue }

        "1" {
            Clear-Host
            Write-Host ""
            Write-Host "-----------------------------------------------"
            Write-Host "  CLI Mode - Generate quiz from document"
            Write-Host "  (You can drag a .txt file into this window)"
            Write-Host "-----------------------------------------------"
            Write-Host ""

            $docPath = Read-Host "Document path"
            if (-not $docPath) {
                Write-Host "No file path entered" -ForegroundColor Yellow
                Read-Host "Press Enter to continue"
                continue
            }
            $docPath = $docPath.Trim('"').Trim("'")

            if (-not (Test-Path $docPath)) {
                Write-Host "File not found: $docPath" -ForegroundColor Red
                Read-Host "Press Enter to continue"
                continue
            }

            $count = Read-Host "Question count [default 5]"
            if (-not $count) { $count = 5 }

            $diff = Read-Host "Difficulty: simple/medium/hard/mixed [default mixed]"
            if (-not $diff) { $diff = "mixed" }

            $types = Read-Host "Types, comma separated [default single_choice,fill_blank]"
            if (-not $types) { $types = "single_choice,fill_blank" }

            $reqs = Read-Host "Custom requirements [optional]"

            Write-Host ""
            Write-Host "Generating, please wait..." -ForegroundColor Cyan
            Write-Host ""

            & $venvPy run_cli.py $docPath -n $count -d $diff -t $types -r $reqs

            Write-Host ""
            Write-Host "-----------------------------------------------"
            Read-Host "Press Enter to return to menu"
        }

        "2" {
            Clear-Host
            Write-Host ""
            Write-Host "-----------------------------------------------"
            Write-Host "  Web Mode"
            Write-Host "  Open http://localhost:8000 in your browser"
            Write-Host "  Press Ctrl+C to stop the server"
            Write-Host "-----------------------------------------------"
            Write-Host ""

            Start-Process "http://localhost:8000"
            & $venvPy run_web.py
        }

        default {
            Write-Host "Invalid option" -ForegroundColor Yellow
            Start-Sleep 1
        }
    }

    if ($mode -eq "0") { break }
}
