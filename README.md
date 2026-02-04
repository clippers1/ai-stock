# AI Stock Trading 📈🤖

一个面向移动端的AI智能炒股网页应用，支持A股实时数据获取和AI选股推荐。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![React](https://img.shields.io/badge/react-19-blue.svg)

## ✨ 功能特性

- 📊 **AI推荐** - 基于技术面+基本面综合评分的智能选股
- 📈 **股票分析** - K线图、技术指标、AI分析观点
- 💬 **AI对话** - 智能问答，支持个股分析查询
- 🔄 **实时数据** - 通过akshare-one-mcp获取A股实时行情

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React + Vite + CSS |
| 后端 | FastAPI + Python |
| 数据 | akshare-one-mcp (A股MCP服务) |

## 📦 项目结构

```
ai-stock/
├── frontend/          # React前端应用
│   ├── src/
│   │   ├── components/    # 通用组件
│   │   ├── pages/         # 页面组件
│   │   └── services/      # API服务层
│   └── index.html
├── backend/           # Python后端服务
│   ├── main.py            # API入口
│   ├── services/          # 业务服务
│   │   └── stock_data.py  # MCP数据服务
│   └── pyproject.toml
└── README.md
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- uv (Python包管理器)

### 安装步骤

**1. 克隆项目**
```bash
git clone https://github.com/your-username/ai-stock.git
cd ai-stock
```

**2. 一键启动（推荐）**
```powershell
# Windows PowerShell
.\start-dev.ps1

# 一键停止所有服务
.\stop-dev.ps1
```

> 💡 脚本会自动启动后端、前端和MCP服务，并在3秒后自动打开浏览器

**3. 手动启动（可选）**

<details>
<summary>点击展开手动启动步骤</summary>

**启动后端**
```bash
cd backend
uv sync
uv run uvicorn main:app --reload --port 8000
```

**启动前端**
```bash
cd frontend
npm install
npm run dev
```

**(可选) 启动MCP数据服务**
```bash
uvx akshare-one-mcp --streamable-http --port 8081
```

</details>

访问 http://localhost:5173 即可使用。

## 📱 界面预览

| AI推荐 | 股票分析 | AI对话 |
|--------|----------|--------|
| 智能选股推荐 | K线图+指标 | 智能问答 |

## 🔧 配置说明

### 后端API端口
默认运行在 `http://localhost:8000`

### MCP数据服务
默认连接 `http://localhost:8081/mcp`

> 💡 即使不启动MCP服务，应用也能正常运行（使用内置模拟数据）

## 📝 API文档

启动后端后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

## ⚠️ 免责声明

本项目仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。
