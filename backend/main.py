"""
AI Stock Trading Backend API
FastAPI服务，提供A股实时数据、AI分析和智能对话功能
使用akshare-one库获取真实市场数据
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import random
import logging

# 导入服务
from services.akshare_service import akshare_service
from services.ai_analyzer import openai_analyzer
from services.backtest_service import backtest_service
from services.scheduler_service import scheduler_service

# 导入数据库
from database import init_db

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化数据库
init_db()

app = FastAPI(
    title="AI Stock Trading API",
    description="AI炒股后端服务 - A股实时数据与智能分析",
    version="2.0.0",
)

# 配置CORS允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 应用生命周期事件 ====================


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("🚀 应用启动中...")

    # 启动定时任务
    try:
        scheduler_service.start()
        logger.info("✅ 定时任务调度器已启动")
    except Exception as e:
        logger.error(f"❌ 定时任务启动失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("🛑 应用关闭中...")

    # 停止定时任务
    try:
        scheduler_service.stop()
        logger.info("✅ 定时任务调度器已停止")
    except Exception as e:
        logger.error(f"❌ 定时任务停止失败: {e}")


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


# ==================== 模拟数据（后备数据） ====================

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
    """获取股票数据，优先使用akshare_service"""
    # 尝试从akshare获取真实数据
    try:
        quote = await akshare_service.get_stock_quote(symbol)
        if quote and quote.get("price", 0) > 0:
            return {
                "symbol": symbol,
                "name": quote.get(
                    "name", MOCK_STOCKS.get(symbol, {}).get("name", "未知")
                ),
                "price": float(quote.get("price", 0)),
                "change": float(quote.get("change", 0)),
                "change_percent": float(quote.get("change_percent", 0)),
                "volume": int(quote.get("volume", 0)),
                "high": float(quote.get("high", 0)),
                "low": float(quote.get("low", 0)),
                "open": float(quote.get("open", 0)),
            }
    except Exception as e:
        logger.error(f"获取股票数据失败: {e}")

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
    akshare_available = await akshare_service.is_available()
    return {
        "status": "ok",
        "message": "AI Stock Trading API is running",
        "data_source": "akshare",
        "data_available": akshare_available,
        "version": "2.1.0",
    }


@app.get("/api/recommendations")
async def get_recommendations(category: str = "shortterm"):
    """
    获取AI推荐股票列表

    Args:
        category: 推荐分类
            - shortterm: 短线强势（涨停池+技术突破）
            - trend: 趋势动量（均线多头+放量）
            - value: 价值低估（超跌反弹机会）
    """
    # 使用OpenAI分析器获取智能推荐
    stocks = await openai_analyzer.analyze_stocks(category)

    # 转换为响应格式
    result = []
    for stock in stocks:
        result.append(
            {
                "symbol": stock.get("symbol", ""),
                "name": stock.get("name", ""),
                "price": stock.get("price", 0),
                "change": stock.get("change", 0),
                "change_percent": stock.get("change_percent", 0),
                "recommendation": stock.get("recommendation", "持有"),
                "ai_score": stock.get("ai_score", 50),
                "signal": stock.get("signal", ""),
                "reason": stock.get("reason", ""),
            }
        )

    # 将推荐记录保存到数据库（用于回测）
    if result:
        try:
            saved_count = backtest_service.batch_create_recommendations(
                result, category
            )
            logger.info(f"保存推荐记录: {saved_count} 条 (类别: {category})")
        except Exception as e:
            logger.error(f"保存推荐记录失败: {e}")

    return result


@app.get("/api/stock/{symbol}", response_model=StockDetail)
async def get_stock_detail(symbol: str, days: int = 30):
    """获取股票详细信息"""
    # 获取基础数据
    data = await get_stock_with_fallback(symbol)

    # 获取真实历史K线数据
    price_history = await akshare_service.get_stock_history(symbol, days)

    # 如果获取失败，使用模拟数据作为降级方案
    if not price_history:
        logger.warning(f"无法获取 {symbol} 历史K线，使用模拟数据")
        price_history = []
        base_price = data["price"] * 0.9
        from datetime import timedelta
        for i in range(days):
            day_change = random.uniform(-0.03, 0.04)
            base_price = base_price * (1 + day_change)
            date = (datetime.now() - timedelta(days=days - i - 1)).strftime("%Y-%m-%d")
            price_history.append(
                {
                    "date": date,
                    "open": round(base_price * 0.99, 2),
                    "high": round(base_price * 1.02, 2),
                    "low": round(base_price * 0.98, 2),
                    "close": round(base_price, 2),
                    "volume": random.randint(10000000, 50000000),
                }
            )

    # 简单评分逻辑
    change_percent = data.get("change_percent", 0)
    score = 50 + int(change_percent * 5)  # 基础评分
    score = max(20, min(95, score))  # 限制在20-95之间

    if score >= 70:
        rec = "买入"
    elif score >= 55:
        rec = "增持"
    elif score >= 45:
        rec = "持有"
    else:
        rec = "观望"

    signals = []
    if change_percent > 3:
        signals.append("强势上涨")
    elif change_percent > 0:
        signals.append("温和上涨")
    elif change_percent < -3:
        signals.append("大幅下跌")

    # 生成AI分析文本
    analysis_parts = [
        f"{data['name']}当前价格¥{data['price']:.2f}，",
        f"{'上涨' if data['change'] > 0 else '下跌'}{abs(data['change_percent']):.2f}%。",
        f"AI综合评分{score}分，建议{rec}。",
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
        fundamental_metrics={},
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """AI对话接口 - 使用真实OpenAI API"""
    import os
    import httpx

    # 获取API配置
    api_key = os.getenv("OPENAI_API_KEY", "")
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4")

    message = request.message

    # 没有API Key时返回模拟响应
    if not api_key or api_key == "your-api-key-here":
        logger.warning("未配置OpenAI API密钥")
        return ChatResponse(
            reply=f"根据AI分析，今日推荐关注：\n1. 贵州茅台(600519) - AI评分50分 - 持有\n2. 五粮液(000858) - AI评分50分 - 持有\n3. 中国平安(601318) - AI评分50分 - 持有\n\n💡 以上推荐基于技术面和基本面综合分析，仅供参考。",
            suggestions=["分析贵州茅台", "分析宁德时代", "查看大盘"],
        )

    # 获取实时股票数据作为上下文
    stock_context = ""
    try:
        quotes = await akshare_service.get_realtime_quotes()
        if quotes:
            top_5 = sorted(
                quotes[:20], key=lambda x: x.get("change_percent", 0), reverse=True
            )[:5]
            stock_context = "今日A股涨幅前5:\n"
            for s in top_5:
                stock_context += f"- {s['name']}({s['symbol']}): {s['price']:.2f}元, 涨跌{s['change_percent']:.2f}%\n"
    except Exception as e:
        logger.error(f"获取股票数据失败: {e}")

    # 构建系统提示词
    system_prompt = """你是一位专业的A股投资顾问AI助手。你的职责是：
1. 回答用户关于股票投资的问题
2. 分析具体股票的投资价值
3. 提供投资建议和风险提示

请用简洁专业的语言回答，适当使用emoji增强可读性。
每次回复都要包含风险提示。
"""

    if stock_context:
        system_prompt += f"\n\n当前市场数据：\n{stock_context}"

    # 构建对话历史
    messages = [{"role": "system", "content": system_prompt}]

    # 添加历史消息
    if request.history:
        for h in request.history[-6:]:  # 只保留最近6条
            messages.append({"role": h.role, "content": h.content})

    # 添加当前消息
    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 1000,
                    "temperature": 0.7,
                },
            )

            if response.status_code == 200:
                data = response.json()
                reply = data["choices"][0]["message"]["content"]
                logger.info(f"OpenAI响应成功: {len(reply)}字符")

                # 动态生成建议
                suggestions = ["今日有什么推荐？", "分析贵州茅台", "查看大盘"]
                if "茅台" in message or "白酒" in message:
                    suggestions = ["分析五粮液", "白酒板块走势", "今日推荐"]
                elif "新能源" in message or "宁德" in message or "比亚迪" in message:
                    suggestions = ["分析宁德时代", "分析比亚迪", "新能源板块"]

                return ChatResponse(reply=reply, suggestions=suggestions)
            else:
                logger.error(
                    f"OpenAI API错误: {response.status_code} - {response.text}"
                )

    except Exception as e:
        logger.error(f"调用OpenAI失败: {e}")

    # 降级到简单回复
    return ChatResponse(
        reply="抱歉，AI服务暂时不可用。请稍后再试。\n\n💡 您可以尝试：查看今日推荐、分析具体股票等。",
        suggestions=["今日有什么推荐？", "分析贵州茅台", "查看大盘"],
    )


@app.get("/api/sectors")
async def get_sectors():
    """获取热门板块 - 动态数据"""
    sectors = await akshare_service.get_hot_sectors(limit=10)

    if sectors:
        return sectors

    # 降级到静态数据
    return [
        {"name": "新能源车", "change": 2.35, "hot": True},
        {"name": "半导体", "change": 1.82, "hot": True},
        {"name": "AI人工智能", "change": 1.56, "hot": True},
        {"name": "银行", "change": 0.56, "hot": False},
        {"name": "医药", "change": -0.82, "hot": False},
    ]


@app.get("/api/news/{symbol}")
async def get_stock_news(symbol: str):
    """获取股票新闻"""
    # 返回模拟新闻（可后续接入真实新闻API）
    stock_name = MOCK_STOCKS.get(symbol, {}).get("name", symbol)
    return {
        "symbol": symbol,
        "news": [
            {"title": f"{stock_name}发布最新业绩报告", "time": "10:30"},
            {"title": "分析师上调目标价", "time": "09:15"},
            {"title": "机构持续增持", "time": "昨日"},
        ],
    }


@app.get("/api/health")
async def health_check():
    """详细健康检查"""
    akshare_available = await akshare_service.is_available()
    return {
        "api": "healthy",
        "data_source": "akshare-one",
        "data_available": akshare_available,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/backtest/summary")
async def get_backtest_summary(period: str = "30d"):
    """
    获取回测汇总统计

    Args:
        period: 统计周期 (7d/30d/90d/all)
    """
    return backtest_service.get_summary(period)


@app.get("/api/backtest/performance")
async def get_backtest_performance(period: str = "30d"):
    """
    获取收益曲线数据

    Args:
        period: 统计周期 (7d/30d/90d/all)

    Returns:
        {
            dates: ["2025-01-01", ...],
            daily_returns: [0.5, -0.2, ...],
            cumulative_returns: [0.5, 0.3, ...],
            daily_count: [3, 2, ...],
            period: str
        }
    """
    return backtest_service.get_performance_curve(period)


@app.get("/api/backtest/records")
async def get_backtest_records(
    period: str = "30d",
    status: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    获取回测记录列表

    Args:
        period: 统计周期 (7d/30d/90d/all)
        status: 状态筛选 (active/closed)
        category: 类别筛选 (shortterm/trend/value)
        page: 页码
        page_size: 每页数量
    """
    return backtest_service.get_records(
        period=period, status=status, category=category, page=page, page_size=page_size
    )


@app.post("/api/backtest/close/{record_id}")
async def close_position(record_id: int, close_price: Optional[float] = None):
    """
    手动平仓

    Args:
        record_id: 推荐记录ID
        close_price: 平仓价格（可选，不提供则使用当前价格）
    """
    try:
        # 如果没有提供平仓价格，获取当前价格
        if close_price is None:
            db = backtest_service._get_db()
            try:
                from database.models import RecommendationRecord
                record = db.query(RecommendationRecord).filter(
                    RecommendationRecord.id == record_id
                ).first()

                if not record:
                    raise HTTPException(status_code=404, detail="记录不存在")

                close_price = record.current_price or record.entry_price
            finally:
                db.close()

        success = backtest_service.close_position(
            record_id=record_id,
            close_price=close_price,
            close_reason="manual"
        )

        if success:
            return {"success": True, "message": "平仓成功"}
        else:
            raise HTTPException(status_code=400, detail="平仓失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"平仓API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 止盈止损配置 API ====================

@app.get("/api/backtest/stop-config")
async def get_stop_config():
    """获取当前止盈止损配置"""
    return scheduler_service.get_stop_config()


@app.post("/api/backtest/stop-config")
async def set_stop_config(
    stop_profit: Optional[float] = None,
    stop_loss: Optional[float] = None,
    max_days: Optional[int] = None,
    enabled: Optional[bool] = None,
):
    """
    设置止盈止损配置

    Args:
        stop_profit: 止盈阈值(%)，如 15.0
        stop_loss: 止损阈值(%)，如 -8.0（负数）
        max_days: 最大持有天数
        enabled: 是否启用自动平仓
    """
    scheduler_service.set_stop_config(
        stop_profit=stop_profit,
        stop_loss=stop_loss,
        max_days=max_days,
        enabled=enabled,
    )
    return {
        "success": True,
        "config": scheduler_service.get_stop_config()
    }


@app.post("/api/backtest/check-auto-close")
async def trigger_auto_close():
    """手动触发一次自动止盈止损检查"""
    closed = await scheduler_service.check_auto_close()
    return {
        "success": True,
        "closed_count": len(closed),
        "closed_records": closed
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
