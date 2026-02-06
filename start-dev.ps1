<#
.SYNOPSIS
    AI Stock Trading - Dev Environment Startup Script

.DESCRIPTION
    Starts the following services:
    - Backend (FastAPI): http://localhost:8000
    - Frontend (Vite): http://localhost:5173

.NOTES
    Usage: Right-click to run or execute .\start-dev.ps1 in PowerShell
    Stop: Close the terminal window or press Ctrl+C
#>

# Set console encoding to UTF-8
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

# Define color output function
function Write-ColorText {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

# Define project root directory
$ProjectRoot = $PSScriptRoot

# Print startup info
Write-ColorText ""
Write-ColorText "======================================" "Cyan"
Write-ColorText "   AI Stock Trading - Dev Startup" "Cyan"
Write-ColorText "======================================" "Cyan"
Write-ColorText ""

# Check required tools
Write-ColorText "[Check] Verifying dependencies..." "Yellow"

# Check uv
$uvExists = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvExists) {
    Write-ColorText "[Error] uv not found, please install: https://docs.astral.sh/uv/" "Red"
    exit 1
}
Write-ColorText "  [OK] uv installed" "Green"

# Check Node.js
$nodeExists = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeExists) {
    Write-ColorText "[Error] Node.js not found, please install: https://nodejs.org/" "Red"
    exit 1
}
Write-ColorText "  [OK] Node.js installed ($(node --version))" "Green"

# Check npm
$npmExists = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmExists) {
    Write-ColorText "[Error] npm not found" "Red"
    exit 1
}
Write-ColorText "  [OK] npm installed ($(npm --version))" "Green"

Write-ColorText ""
Write-ColorText "[Starting] Launching all services..." "Yellow"
Write-ColorText ""

# Start backend service
Write-ColorText "[Backend] Starting FastAPI (port 8000)..." "Magenta"
$backendPath = Join-Path $ProjectRoot "backend"
Start-Process -FilePath "pwsh" -WorkingDirectory $backendPath -ArgumentList "-NoExit", "-Command", @'
chcp 65001 | Out-Null
$OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  [Backend] FastAPI Service' -ForegroundColor Cyan
Write-Host '  API Docs: http://localhost:8000/docs' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
uv sync
uv run uvicorn main:app --reload --port 8000
'@ -WindowStyle Normal

Start-Sleep -Seconds 1

# Start frontend service
Write-ColorText "[Frontend] Starting Vite dev server (port 5173)..." "Magenta"
$frontendPath = Join-Path $ProjectRoot "frontend"
Start-Process -FilePath "pwsh" -WorkingDirectory $frontendPath -ArgumentList "-NoExit", "-Command", @'
chcp 65001 | Out-Null
$OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host '========================================' -ForegroundColor Green
Write-Host '  [Frontend] Vite Dev Server' -ForegroundColor Green
Write-Host '  URL: http://localhost:5173' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green
Write-Host ''
npm run dev
'@ -WindowStyle Normal

# Print completion info
Write-ColorText ""
Write-ColorText "======================================" "Cyan"
Write-ColorText "   All services started!" "Green"
Write-ColorText "======================================" "Cyan"
Write-ColorText ""
Write-ColorText "  URLs:" "White"
Write-ColorText "  * Frontend: http://localhost:5173" "Green"
Write-ColorText "  * Backend:  http://localhost:8000" "Cyan"
Write-ColorText "  * API Docs: http://localhost:8000/docs" "Cyan"
Write-ColorText ""
Write-ColorText "  Data Source: akshare-one (Python library)" "Yellow"
Write-ColorText "  Note: Each service runs in a separate window" "DarkGray"
Write-ColorText "  Stop: Close the window or press Ctrl+C" "DarkGray"
Write-ColorText "======================================" "Cyan"
Write-ColorText ""

# Wait 3 seconds then open browser
Start-Sleep -Seconds 3
Write-ColorText "[Browser] Opening frontend app..." "Yellow"
Start-Process "http://localhost:5173"
