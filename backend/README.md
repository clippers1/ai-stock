# AI Stock Trading Backend

AI炒股后端API服务

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行服务

```bash
uvicorn main:app --reload --port 8000
```

## API端点

- `GET /api/recommendations` - 获取AI推荐股票列表
- `GET /api/stock/{symbol}` - 获取股票详情和分析
- `POST /api/chat` - AI对话接口
