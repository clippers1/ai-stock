"""
AI Stock Trading Backend API
FastAPI服务，提供A股实时数据、AI分析和智能对话功能
集成akshare-one-mcp获取真实市场数据
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import random
import logging

from services.stock_data import (
    stock_data_service,
    ai_analyzer,
    mcp_client,
    HOT_A_SHARES
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Stock Trading API",
    description="AI炒股后端服务 - A股实时数据与智能分析",
    version="2.0.0"
)

# 配置CORS允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 数据模型 ====================

class Stock(BaseModel):
    """股票基本信息"""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    recommendation: str
    ai_score: int

class StockDetail(Stock):
    """股票详细信息"""
    open_price: float
    high: float
    low: float
    volume: int
    market_cap: str
    pe_ratio: float
    ai_analysis: str
    price_history: List[dict]
    technical_signals: List[str] = []
    fundamental_metrics: dict = {}

class ChatMessage(BaseModel):
    """聊天消息"""
    role: str
    content: str
    timestamp: str

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str
    suggestions: List[str]


# ==================== 模拟数据（MCP不可用时的后备） ====================

MOCK_STOCKS = {
    "600519": {"name": "贵州茅台", "price": 1680.50},
    "000858": {"name": "五粮液", "price": 158.20},
    "601318": {"name": "中国平安", "price": 42.35},
    "600036": {"name": "招商银行", "price": 35.80},
    "000333": {"name": "美的集团", "price": 58.90},
    "600900": {"name": "长江电力", "price": 28.15},
    "601888": {"name": "中国中免", "price": 85.60},
    "300750": {"name": "宁德时代", "price": 185.40},
    "002594": {"name": "比亚迪", "price": 245.80},
    "600276": {"name": "恒瑞医药", "price": 42.15},
}


async def get_stock_with_fallback(symbol: str) -> dict:
    """获取股票数据，MCP不可用时使用模拟数据"""
    # 尝试从MCP获取真实数据
    realtime = await stock_data_service.get_realtime_quote(symbol)
    
    if realtime and "content" in realtime:
        try:
            data = realtime["content"]
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                return {
                    "symbol": symbol,
                    "name": item.get("name", MOCK_STOCKS.get(symbol, {}).get("name", "未知")),
                    "price": float(item.get("close", item.get("price", 0))),
                    "change": float(item.get("change", 0)),
                    "change_percent": float(item.get("pct_chg", item.get("change_percent", 0))),
                    "volume": int(item.get("volume", 0)),
                    "high": float(item.get("high", 0)),
                    "low": float(item.get("low", 0)),
                    "open": float(item.get("open", 0)),
                }
        except Exception as e:
            logger.error(f"解析实时数据失败: {e}")
    
    # 使用模拟数据
    mock = MOCK_STOCKS.get(symbol, {"name": f"股票{symbol}", "price": 100.0})
    change = random.uniform(-3, 5)
    return {
        "symbol": symbol,
        "name": mock["name"],
        "price": mock["price"],
        "change": round(mock["price"] * change / 100, 2),
        "change_percent": round(change, 2),
        "volume": random.randint(10000000, 100000000),
        "high": round(mock["price"] * 1.02, 2),
        "low": round(mock["price"] * 0.98, 2),
        "open": round(mock["price"] * 0.995, 2),
    }


# ==================== API端点 ====================

@app.get("/")
async def root():
    """健康检查"""
    mcp_available = await mcp_client.is_available()
    return {
        "status": "ok",
        "message": "AI Stock Trading API is running",
        "mcp_connected": mcp_available,
        "version": "2.0.0"
    }


@app.get("/api/recommendations", response_model=List[Stock])
async def get_recommendations():
    """获取AI推荐股票列表"""
    stocks = []
    
    for symbol in HOT_A_SHARES[:8]:  # 取前8只热门股票
        # 获取基础数据
        data = await get_stock_with_fallback(symbol)
        
        # 获取AI推荐
        recommendation = await ai_analyzer.get_recommendation(symbol)
        
        stocks.append(Stock(
            symbol=symbol,
            name=data["name"],
            price=data["price"],
            change=data["change"],
            change_percent=data["change_percent"],
            recommendation=recommendation.get("recommendation", "持有"),
            ai_score=recommendation.get("total_score", 50)
        ))
    
    # 按AI评分排序
    stocks.sort(key=lambda x: x.ai_score, reverse=True)
    return stocks


@app.get("/api/stock/{symbol}", response_model=StockDetail)
async def get_stock_detail(symbol: str):
    """获取股票详细信息"""
    # 获取基础数据
    data = await get_stock_with_fallback(symbol)
    
    # 获取AI分析
    recommendation = await ai_analyzer.get_recommendation(symbol)
    
    # 获取历史数据
    history = await stock_data_service.get_history(symbol, days=30)
    
    # 解析历史数据
    price_history = []
    if history and "content" in history:
        try:
            raw_history = history["content"]
            if isinstance(raw_history, list):
                for item in raw_history[-30:]:
                    price_history.append({
                        "date": item.get("date", ""),
                        "open": float(item.get("open", 0)),
                        "high": float(item.get("high", 0)),
                        "low": float(item.get("low", 0)),
                        "close": float(item.get("close", 0)),
                        "volume": int(item.get("volume", 0))
                    })
        except Exception as e:
            logger.error(f"解析历史数据失败: {e}")
    
    # 如果没有真实历史数据，生成模拟数据
    if not price_history:
        base_price = data["price"] * 0.9
        for i in range(30):
            day_change = random.uniform(-0.03, 0.04)
            base_price = base_price * (1 + day_change)
            price_history.append({
                "date": f"2026-01-{str(i+1).zfill(2)}",
                "open": round(base_price * 0.99, 2),
                "high": round(base_price * 1.02, 2),
                "low": round(base_price * 0.98, 2),
                "close": round(base_price, 2),
                "volume": random.randint(10000000, 50000000)
            })
    
    # 生成AI分析文本
    score = recommendation.get("total_score", 50)
    rec = recommendation.get("recommendation", "持有")
    signals = recommendation.get("signals", [])
    
    analysis_parts = [
        f"{data['name']}当前价格¥{data['price']:.2f}，",
        f"{'上涨' if data['change'] > 0 else '下跌'}{abs(data['change_percent']):.2f}%。",
        f"AI综合评分{score}分，建议{rec}。"
    ]
    if signals:
        analysis_parts.append(f"技术信号：{', '.join(signals[:3])}。")
    
    return StockDetail(
        symbol=symbol,
        name=data["name"],
        price=data["price"],
        change=data["change"],
        change_percent=data["change_percent"],
        recommendation=rec,
        ai_score=score,
        open_price=data.get("open", data["price"] * 0.995),
        high=data.get("high", data["price"] * 1.02),
        low=data.get("low", data["price"] * 0.98),
        volume=data.get("volume", random.randint(20000000, 100000000)),
        market_cap=f"{random.randint(500, 3000)}亿",
        pe_ratio=round(random.uniform(15, 45), 2),
        ai_analysis="".join(analysis_parts),
        price_history=price_history,
        technical_signals=signals,
        fundamental_metrics=recommendation.get("metrics", {})
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """AI对话接口"""
    message = request.message.lower()
    
    # 检测是否询问具体股票
    stock_mentioned = None
    for symbol, info in MOCK_STOCKS.items():
        if symbol in message or info["name"] in message:
            stock_mentioned = symbol
            break
    
    # 如果提到了股票，获取分析
    if stock_mentioned:
        data = await get_stock_with_fallback(stock_mentioned)
        recommendation = await ai_analyzer.get_recommendation(stock_mentioned)
        
        reply = f"关于{data['name']}({stock_mentioned})的分析：\n\n"
        reply += f"📈 当前价格：¥{data['price']:.2f}\n"
        reply += f"📊 今日涨跌：{'↑' if data['change'] > 0 else '↓'}{abs(data['change_percent']):.2f}%\n"
        reply += f"🤖 AI评分：{recommendation.get('total_score', 50)}分\n"
        reply += f"💡 建议操作：{recommendation.get('recommendation', '持有')}\n"
        
        signals = recommendation.get("signals", [])
        if signals:
            reply += f"\n技术信号：{', '.join(signals)}"
        
        return ChatResponse(
            reply=reply,
            suggestions=[f"分析{list(MOCK_STOCKS.values())[0]['name']}", "今日推荐", "大盘走势"]
        )
    
    # 推荐类问题
    if "推荐" in message or "买什么" in message or "选股" in message:
        # 获取推荐列表
        top_stocks = []
        for symbol in HOT_A_SHARES[:3]:
            rec = await ai_analyzer.get_recommendation(symbol)
            data = await get_stock_with_fallback(symbol)
            top_stocks.append({
                "name": data["name"],
                "symbol": symbol,
                "score": rec.get("total_score", 50),
                "rec": rec.get("recommendation", "持有")
            })
        
        top_stocks.sort(key=lambda x: x["score"], reverse=True)
        
        reply = "根据AI分析，今日推荐关注：\n\n"
        for i, s in enumerate(top_stocks, 1):
            reply += f"{i}. {s['name']}({s['symbol']}) - AI评分{s['score']}分 - {s['rec']}\n"
        
        reply += "\n💡 以上推荐基于技术面和基本面综合分析，仅供参考。"
        
        return ChatResponse(
            reply=reply,
            suggestions=["分析贵州茅台", "分析宁德时代", "查看大盘"]
        )
    
    # 大盘类问题
    if "大盘" in message or "市场" in message or "指数" in message:
        reply = "今日A股市场概况：\n\n"
        reply += "📊 上证指数：整体呈现震荡走势\n"
        reply += "📈 热门板块：消费、新能源、科技\n"
        reply += "📉 调整板块：地产、金融\n\n"
        reply += "💡 建议关注业绩确定性强的白马股，注意控制仓位。"
        
        return ChatResponse(
            reply=reply,
            suggestions=["今日推荐", "分析贵州茅台", "分析比亚迪"]
        )
    
    # 默认回复
    return ChatResponse(
        reply="您好！我是AI投资助手。\n\n我可以帮您：\n• 分析个股（如：分析贵州茅台）\n• 推荐股票（如：今日推荐）\n• 解答投资问题\n\n请问有什么可以帮您的？",
        suggestions=["今日有什么推荐？", "分析贵州茅台", "大盘走势如何？"]
    )


@app.get("/api/sectors")
async def get_sectors():
    """获取热门板块"""
    return [
        {"name": "白酒", "change": 2.35, "hot": True},
        {"name": "新能源", "change": 1.82, "hot": True},
        {"name": "银行", "change": 0.56, "hot": False},
        {"name": "医药", "change": -0.82, "hot": False},
        {"name": "科技", "change": 1.92, "hot": True},
    ]


@app.get("/api/news/{symbol}")
async def get_stock_news(symbol: str):
    """获取股票新闻"""
    news = await stock_data_service.get_news(symbol)
    
    if news and "content" in news:
        return {"symbol": symbol, "news": news["content"]}
    
    # 模拟新闻
    return {
        "symbol": symbol,
        "news": [
            {"title": f"{MOCK_STOCKS.get(symbol, {}).get('name', symbol)}发布最新业绩报告", "time": "10:30"},
            {"title": "分析师上调目标价", "time": "09:15"},
            {"title": "机构持续增持", "time": "昨日"},
        ]
    }


@app.get("/api/health")
async def health_check():
    """详细健康检查"""
    mcp_available = await mcp_client.is_available()
    return {
        "api": "healthy",
        "mcp_connection": "connected" if mcp_available else "disconnected",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
