"""
A股MCP数据服务层
通过akshare-one-mcp获取真实A股市场数据
"""
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# MCP服务配置
MCP_SERVER_URL = "http://localhost:8081/mcp"
MCP_TIMEOUT = 30.0


class MCPClient:
    """MCP客户端，用于调用akshare-one-mcp服务"""
    
    def __init__(self, server_url: str = MCP_SERVER_URL):
        self.server_url = server_url
        self._request_id = 0
    
    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id
    
    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """调用MCP工具"""
        try:
            async with httpx.AsyncClient(timeout=MCP_TIMEOUT) as client:
                response = await client.post(
                    self.server_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments
                        },
                        "id": self._next_id()
                    }
                )
                result = response.json()
                
                if "error" in result:
                    logger.error(f"MCP error: {result['error']}")
                    return None
                    
                return result.get("result", {})
                
        except httpx.ConnectError:
            logger.warning("MCP服务未连接，将使用模拟数据")
            return None
        except Exception as e:
            logger.error(f"MCP调用失败: {e}")
            return None
    
    async def is_available(self) -> bool:
        """检查MCP服务是否可用"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self.server_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "id": 0
                    }
                )
                return response.status_code == 200
        except:
            return False


# 全局MCP客户端实例
mcp_client = MCPClient()


class StockDataService:
    """股票数据服务"""
    
    def __init__(self):
        self.mcp = mcp_client
    
    async def get_realtime_quote(self, symbol: str) -> Optional[dict]:
        """
        获取A股实时行情
        
        Args:
            symbol: 股票代码，如 '000001'（平安银行）
        """
        result = await self.mcp.call_tool("get_realtime_data", {
            "symbol": symbol,
            "source": "eastmoney_direct"
        })
        return result
    
    async def get_realtime_quotes_batch(self, symbols: List[str]) -> List[dict]:
        """批量获取实时行情"""
        tasks = [self.get_realtime_quote(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if r and not isinstance(r, Exception)]
    
    async def get_history(
        self, 
        symbol: str, 
        days: int = 30,
        interval: str = "day",
        with_indicators: bool = True
    ) -> Optional[dict]:
        """
        获取历史K线数据
        
        Args:
            symbol: 股票代码
            days: 获取天数
            interval: 时间间隔 (minute/hour/day/week/month)
            with_indicators: 是否包含技术指标
        """
        arguments = {
            "symbol": symbol,
            "interval": interval,
            "recent_n": days,
            "adjust": "qfq",  # 前复权
            "source": "eastmoney"
        }
        
        if with_indicators:
            arguments["indicators_list"] = ["MA", "RSI", "MACD", "BOLL", "KDJ"]
        
        return await self.mcp.call_tool("get_hist_data", arguments)
    
    async def get_news(self, symbol: str, count: int = 10) -> Optional[dict]:
        """获取股票相关新闻"""
        return await self.mcp.call_tool("get_news_data", {
            "symbol": symbol,
            "recent_n": count
        })
    
    async def get_financials(self, symbol: str) -> Optional[dict]:
        """获取财务指标"""
        return await self.mcp.call_tool("get_financial_metrics", {
            "symbol": symbol,
            "recent_n": 4  # 最近4个季度
        })
    
    async def get_balance_sheet(self, symbol: str) -> Optional[dict]:
        """获取资产负债表"""
        return await self.mcp.call_tool("get_balance_sheet", {
            "symbol": symbol,
            "recent_n": 4
        })
    
    async def get_income_statement(self, symbol: str) -> Optional[dict]:
        """获取利润表"""
        return await self.mcp.call_tool("get_income_statement", {
            "symbol": symbol,
            "recent_n": 4
        })


class AIStockAnalyzer:
    """AI选股分析器"""
    
    def __init__(self):
        self.data_service = StockDataService()
    
    async def calculate_technical_score(self, symbol: str) -> dict:
        """
        计算技术面评分
        
        返回：
            score: 0-100分
            signals: 信号列表
        """
        history = await self.data_service.get_history(symbol, days=60)
        
        if not history:
            return {"score": 50, "signals": [], "error": "数据获取失败"}
        
        signals = []
        score = 50  # 基础分
        
        # 这里需要解析MCP返回的数据结构
        # 根据技术指标计算评分
        # 示例逻辑（实际需根据返回数据调整）：
        
        try:
            data = history.get("content", [])
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1] if isinstance(data[-1], dict) else {}
                
                # RSI评分
                rsi = latest.get("RSI", 50)
                if rsi and rsi < 30:
                    score += 15
                    signals.append("RSI超卖，可能反弹")
                elif rsi and rsi > 70:
                    score -= 10
                    signals.append("RSI超买，注意风险")
                
                # MACD评分
                macd = latest.get("MACD", 0)
                macd_signal = latest.get("MACD_SIGNAL", 0)
                if macd and macd_signal and macd > macd_signal:
                    score += 10
                    signals.append("MACD金叉")
                elif macd and macd_signal and macd < macd_signal:
                    score -= 5
                    signals.append("MACD死叉")
                
                # 均线评分
                ma5 = latest.get("MA_5", 0)
                ma20 = latest.get("MA_20", 0)
                close = latest.get("close", 0)
                if close and ma5 and ma20:
                    if close > ma5 > ma20:
                        score += 10
                        signals.append("多头排列")
                    elif close < ma5 < ma20:
                        score -= 10
                        signals.append("空头排列")
        except Exception as e:
            logger.error(f"技术分析失败: {e}")
        
        return {
            "score": max(0, min(100, score)),
            "signals": signals
        }
    
    async def calculate_fundamental_score(self, symbol: str) -> dict:
        """
        计算基本面评分
        """
        financials = await self.data_service.get_financials(symbol)
        
        if not financials:
            return {"score": 50, "metrics": {}, "error": "数据获取失败"}
        
        score = 50
        metrics = {}
        
        try:
            data = financials.get("content", {})
            
            # ROE评分
            roe = data.get("roe", 0)
            if roe:
                metrics["ROE"] = f"{roe:.2f}%"
                if roe > 15:
                    score += 20
                elif roe > 10:
                    score += 10
                elif roe < 5:
                    score -= 10
            
            # 负债率评分
            debt_ratio = data.get("debt_ratio", 50)
            if debt_ratio:
                metrics["负债率"] = f"{debt_ratio:.2f}%"
                if debt_ratio < 40:
                    score += 15
                elif debt_ratio > 70:
                    score -= 15
            
            # 营收增长
            revenue_growth = data.get("revenue_growth", 0)
            if revenue_growth:
                metrics["营收增长"] = f"{revenue_growth:.2f}%"
                if revenue_growth > 20:
                    score += 15
                elif revenue_growth > 10:
                    score += 8
                elif revenue_growth < 0:
                    score -= 10
                    
        except Exception as e:
            logger.error(f"基本面分析失败: {e}")
        
        return {
            "score": max(0, min(100, score)),
            "metrics": metrics
        }
    
    async def get_recommendation(self, symbol: str) -> dict:
        """
        获取综合推荐
        """
        # 并行获取技术面和基本面评分
        tech_result, fund_result = await asyncio.gather(
            self.calculate_technical_score(symbol),
            self.calculate_fundamental_score(symbol)
        )
        
        tech_score = tech_result.get("score", 50)
        fund_score = fund_result.get("score", 50)
        
        # 综合评分 (技术面40% + 基本面60%)
        total_score = int(tech_score * 0.4 + fund_score * 0.6)
        
        # 推荐级别
        if total_score >= 75:
            recommendation = "买入"
        elif total_score >= 60:
            recommendation = "增持"
        elif total_score >= 40:
            recommendation = "持有"
        elif total_score >= 25:
            recommendation = "减持"
        else:
            recommendation = "卖出"
        
        return {
            "symbol": symbol,
            "total_score": total_score,
            "technical_score": tech_score,
            "fundamental_score": fund_score,
            "recommendation": recommendation,
            "signals": tech_result.get("signals", []),
            "metrics": fund_result.get("metrics", {})
        }


# 预设的A股热门股票列表
HOT_A_SHARES = [
    "600519",  # 贵州茅台
    "000858",  # 五粮液
    "601318",  # 中国平安
    "600036",  # 招商银行
    "000333",  # 美的集团
    "600900",  # 长江电力
    "601888",  # 中国中免
    "300750",  # 宁德时代
    "002594",  # 比亚迪
    "600276",  # 恒瑞医药
]


# 导出实例
stock_data_service = StockDataService()
ai_analyzer = AIStockAnalyzer()
