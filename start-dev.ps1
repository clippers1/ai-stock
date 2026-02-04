<#
.SYNOPSIS
    AI Stock Trading 本地开发环境一键启动脚本

.DESCRIPTION
    启动以下服务：
    - 后端 (FastAPI): http://localhost:8000
    - 前端 (Vite): http://localhost:5173
    - MCP数据服务 (akshare-one-mcp): http://localhost:8081

.NOTES
    使用方式: 右键运行或在 PowerShell 中执行 .\start-dev.ps1
    停止服务: 关闭对应的终端窗口或按 Ctrl+C
#>

# 设置编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 定义颜色输出函数
function Write-ColorText {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

# 定义项目根目录
$ProjectRoot = $PSScriptRoot

# 打印启动信息
Write-ColorText "`n======================================" "Cyan"
Write-ColorText "   AI Stock Trading - 开发环境启动" "Cyan"
Write-ColorText "======================================`n" "Cyan"

# 检查必要的工具
Write-ColorText "[检查] 验证环境依赖..." "Yellow"

# 检查 uv
$uvExists = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvExists) {
    Write-ColorText "[错误] 未找到 uv，请先安装: https://docs.astral.sh/uv/" "Red"
    exit 1
}
Write-ColorText "  ✓ uv 已安装" "Green"

# 检查 Node.js
$nodeExists = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeExists) {
    Write-ColorText "[错误] 未找到 Node.js，请先安装: https://nodejs.org/" "Red"
    exit 1
}
Write-ColorText "  ✓ Node.js 已安装 ($(node --version))" "Green"

# 检查 npm
$npmExists = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmExists) {
    Write-ColorText "[错误] 未找到 npm" "Red"
    exit 1
}
Write-ColorText "  ✓ npm 已安装 ($(npm --version))" "Green"

Write-ColorText "`n[启动] 正在启动所有服务...`n" "Yellow"

# 启动后端服务
Write-ColorText "[后端] 启动 FastAPI 服务 (端口 8000)..." "Magenta"
$backendPath = Join-Path $ProjectRoot "backend"
Start-Process -FilePath "pwsh" -ArgumentList "-NoExit", "-Command", @"
Set-Location '$backendPath'
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  [后端] FastAPI 服务' -ForegroundColor Cyan
Write-Host '  API文档: http://localhost:8000/docs' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
uv sync
uv run uvicorn main:app --reload --port 8000
"@ -WindowStyle Normal

Start-Sleep -Seconds 1


# 启动前端服务
Write-ColorText "[前端] 启动 Vite 开发服务器 (端口 5173)..." "Magenta"
$frontendPath = Join-Path $ProjectRoot "frontend"
Start-Process -FilePath "pwsh" -ArgumentList "-NoExit", "-Command", @"
Set-Location '$frontendPath'
Write-Host '========================================' -ForegroundColor Green
Write-Host '  [前端] Vite 开发服务器' -ForegroundColor Green
Write-Host '  访问: http://localhost:5173' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green
Write-Host ''
npm run dev
"@ -WindowStyle Normal

# 打印完成信息
Write-ColorText "`n======================================" "Cyan"
Write-ColorText "   所有服务已启动!" "Green"
Write-ColorText "======================================" "Cyan"
Write-ColorText ""
Write-ColorText "  服务地址:" "White"
Write-ColorText "  • 前端应用: http://localhost:5173" "Green"
Write-ColorText "  • 后端API:  http://localhost:8000" "Cyan"
Write-ColorText "  • API文档:  http://localhost:8000/docs" "Cyan"
Write-ColorText ""
Write-ColorText "  数据源: akshare-one (内置Python库)" "Yellow"
Write-ColorText "  提示: 每个服务运行在独立窗口中" "DarkGray"
Write-ColorText "  停止: 关闭对应窗口或按 Ctrl+C" "DarkGray"
Write-ColorText "======================================`n" "Cyan"

# 等待 3 秒后自动打开浏览器
Start-Sleep -Seconds 3
Write-ColorText "[浏览器] 正在打开前端应用..." "Yellow"
Start-Process "http://localhost:5173"
