<#
.SYNOPSIS
    AI Stock Trading 本地开发环境一键停止脚本

.DESCRIPTION
    停止以下服务进程：
    - 后端 (uvicorn)
    - 前端 (node/vite)
    - MCP数据服务 (akshare-one-mcp)

.NOTES
    使用方式: 右键运行或在 PowerShell 中执行 .\stop-dev.ps1
#>

# 设置编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 定义颜色输出函数
function Write-ColorText {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

Write-ColorText "`n======================================" "Yellow"
Write-ColorText "   AI Stock Trading - 停止开发服务" "Yellow"
Write-ColorText "======================================`n" "Yellow"

$stoppedCount = 0

# 停止占用 8000 端口的进程 (后端)
Write-ColorText "[后端] 检查端口 8000..." "Cyan"
$backend = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
           Select-Object -ExpandProperty OwningProcess -Unique
if ($backend) {
    foreach ($pid in $backend) {
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-ColorText "  停止进程: $($process.ProcessName) (PID: $pid)" "Gray"
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            $stoppedCount++
        }
    }
    Write-ColorText "  ✓ 后端服务已停止" "Green"
} else {
    Write-ColorText "  - 后端服务未运行" "DarkGray"
}

# 停止占用 5173 端口的进程 (前端)
Write-ColorText "[前端] 检查端口 5173..." "Cyan"
$frontend = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | 
            Select-Object -ExpandProperty OwningProcess -Unique
if ($frontend) {
    foreach ($pid in $frontend) {
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-ColorText "  停止进程: $($process.ProcessName) (PID: $pid)" "Gray"
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            $stoppedCount++
        }
    }
    Write-ColorText "  ✓ 前端服务已停止" "Green"
} else {
    Write-ColorText "  - 前端服务未运行" "DarkGray"
}

# 停止占用 8081 端口的进程 (MCP)
Write-ColorText "[MCP] 检查端口 8081..." "Cyan"
$mcp = Get-NetTCPConnection -LocalPort 8081 -ErrorAction SilentlyContinue | 
       Select-Object -ExpandProperty OwningProcess -Unique
if ($mcp) {
    foreach ($pid in $mcp) {
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-ColorText "  停止进程: $($process.ProcessName) (PID: $pid)" "Gray"
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            $stoppedCount++
        }
    }
    Write-ColorText "  ✓ MCP服务已停止" "Green"
} else {
    Write-ColorText "  - MCP服务未运行" "DarkGray"
}

Write-ColorText "`n======================================" "Yellow"
if ($stoppedCount -gt 0) {
    Write-ColorText "   已停止 $stoppedCount 个服务进程" "Green"
} else {
    Write-ColorText "   没有正在运行的开发服务" "DarkGray"
}
Write-ColorText "======================================`n" "Yellow"
