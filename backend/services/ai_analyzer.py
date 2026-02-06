"""
AI股票分析服务
使用OpenAI兼容API进行真正的股票AI分析
支持三种分析策略：短线强势、趋势动量、价值低估
集成MCP获取真实A股数据
"""
import httpx
import asyncio
import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# 导入数据服务
from .akshare_service import akshare_service
from .quant_service import quant_service

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

# OpenAI API配置
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
OPENAI_TIMEOUT = 60.0


# ==================== Agent角色预设 ====================

AGENT_PROMPTS = {
    # 短线强势分析师 - 专注涨停池+技术突破
    "shortterm": """你是一位专业的A股短线交易分析师，专注于捕捉短线强势股。

你的分析策略：
1. **涨停池分析**：关注涨停股、连板股、首板股
2. **技术突破**：识别突破关键阻力位、放量突破、形态突破
3. **资金流向**：关注主力资金净流入、游资动向
4. **市场情绪**：结合市场热点、题材概念

分析要求：
- 每只股票给出AI评分(0-100)
- 给出明确的操作建议：强势/突破/观望
- 标注关键信号：如"涨停"、"放量突破"、"新高突破"等
- 返回JSON格式数据

输出格式要求（严格JSON）：
{
    "stocks": [
        {
            "symbol": "股票代码",
            "name": "股票名称",
            "price": 当前价格,
            "change": 涨跌额,
            "change_percent": 涨跌幅,
            "recommendation": "强势/突破/观望",
            "ai_score": AI评分,
            "signal": "信号说明",
            "reason": "推荐理由"
        }
    ],
    "market_view": "市场观点简述"
}""",

    # 趋势动量分析师 - 专注均线多头+放量
    "trend": """你是一位专业的A股趋势交易分析师，专注于捕捉趋势动量股。

你的分析策略：
1. **均线系统**：识别多头排列(5日>10日>20日>60日)
2. **量价配合**：放量上涨、量价齐升
3. **趋势延续**：MACD金叉、KDJ向上、RSI强势区
4. **支撑位确认**：站稳关键均线、回踩确认

分析要求：
- 每只股票给出AI评分(0-100)
- 给出明确的操作建议：买入/关注/持有
- 标注关键信号：如"均线多头"、"放量上攻"、"MACD金叉"等
- 返回JSON格式数据

输出格式要求（严格JSON）：
{
    "stocks": [
        {
            "symbol": "股票代码",
            "name": "股票名称",
            "price": 当前价格,
            "change": 涨跌额,
            "change_percent": 涨跌幅,
            "recommendation": "买入/关注/持有",
            "ai_score": AI评分,
            "signal": "信号说明",
            "reason": "推荐理由"
        }
    ],
    "market_view": "市场观点简述"
}""",

    # 价值低估分析师 - 专注超跌反弹机会
    "value": """你是一位专业的A股价值投资分析师，专注于发掘价值低估和超跌反弹机会。

你的分析策略：
1. **估值分析**：PE/PB处于历史低位、低于行业平均
2. **超跌判断**：跌幅超过30%以上、RSI进入超卖区
3. **基本面支撑**：业绩稳定、高股息、现金流健康
4. **反弹信号**：底部放量、止跌企稳、技术性反弹

分析要求：
- 每只股票给出AI评分(0-100)
- 给出明确的操作建议：超跌/低估/观望
- 标注关键信号：如"PE低估"、"高股息"、"超跌反弹"等
- 返回JSON格式数据

输出格式要求（严格JSON）：
{
    "stocks": [
        {
            "symbol": "股票代码",
            "name": "股票名称",
            "price": 当前价格,
            "change": 涨跌额,
            "change_percent": 涨跌幅,
            "recommendation": "超跌/低估/观望",
            "ai_score": AI评分,
            "signal": "信号说明",
            "reason": "推荐理由"
        }
    ],
    "market_view": "市场观点简述"
}"""
}


# 股票池配置 - 默认候选股票（MCP不可用时使用）
DEFAULT_STOCK_POOLS = {
    "shortterm": [
        {"symbol": "000001", "name": "平安银行"},
        {"symbol": "600519", "name": "贵州茅台"},
        {"symbol": "002475", "name": "立讯精密"},
        {"symbol": "300059", "name": "东方财富"},
        {"symbol": "002415", "name": "海康威视"},
        {"symbol": "600036", "name": "招商银行"},
        {"symbol": "300750", "name": "宁德时代"},
        {"symbol": "000858", "name": "五粮液"},
        {"symbol": "601318", "name": "中国平安"},
        {"symbol": "000333", "name": "美的集团"},
    ],
    "trend": [
        {"symbol": "300750", "name": "宁德时代"},
        {"symbol": "002594", "name": "比亚迪"},
        {"symbol": "600036", "name": "招商银行"},
        {"symbol": "000858", "name": "五粮液"},
        {"symbol": "601318", "name": "中国平安"},
        {"symbol": "000333", "name": "美的集团"},
        {"symbol": "600519", "name": "贵州茅台"},
        {"symbol": "600900", "name": "长江电力"},
        {"symbol": "601888", "name": "中国中免"},
        {"symbol": "600276", "name": "恒瑞医药"},
    ],
    "value": [
        {"symbol": "601166", "name": "兴业银行"},
        {"symbol": "600276", "name": "恒瑞医药"},
        {"symbol": "002304", "name": "洋河股份"},
        {"symbol": "600887", "name": "伊利股份"},
        {"symbol": "000651", "name": "格力电器"},
        {"symbol": "601318", "name": "中国平安"},
        {"symbol": "600036", "name": "招商银行"},
        {"symbol": "601398", "name": "工商银行"},
        {"symbol": "601288", "name": "农业银行"},
        {"symbol": "600030", "name": "中信证券"},
    ]
}


class OpenAIStockAnalyzer:
    """使用OpenAI API进行股票分析"""
    
    def __init__(self):
        self.api_base = OPENAI_API_BASE
        self.api_key = OPENAI_API_KEY
        self.model = OPENAI_MODEL
        self.data_service = akshare_service
        # 缓存分析结果
        self._cache: Dict[str, Dict] = {}
        self._cache_ttl = 1800  # 30分钟缓存
    
    def _is_cache_valid(self, category: str) -> bool:
        """检查缓存是否有效"""
        if category not in self._cache:
            return False
        cache_time = self._cache[category].get("timestamp", 0)
        return (datetime.now().timestamp() - cache_time) < self._cache_ttl
    
    async def _get_stock_pool(self, category: str) -> List[Dict]:
        """
        获取股票池数据
        
        优先使用akshare获取实时数据，失败时使用默认股票池
        """
        # 尝试使用akshare获取实时数据
        try:
            stock_pool = await self.data_service.get_stock_pool_by_category(category, limit=15)
            if stock_pool and len(stock_pool) > 0:
                print(f"[AI分析] ✅ 今akshare获取到{len(stock_pool)}只股票")
                return stock_pool
        except Exception as e:
            print(f"[AI分析] ⚠️ akshare获取失败: {e}")
        
        # 失败时使用默认股票池
        print(f"[AI分析] ⚠️ 使用默认股票池")
        return DEFAULT_STOCK_POOLS.get(category, DEFAULT_STOCK_POOLS["shortterm"])
    
    async def analyze_stocks(
        self, 
        category: str = "shortterm",
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        使用AI分析股票
        
        Args:
            category: 分析类别 (shortterm/trend/value)
            force_refresh: 是否强制刷新
            
        Returns:
            分析结果列表
        """
        # 检查缓存
        if not force_refresh and self._is_cache_valid(category):
            logger.info(f"返回缓存的{category}分析结果")
            return self._cache[category]["data"]
        
        # 没有API密钥时返回模拟数据
        if not self.api_key or self.api_key == "your-api-key-here":
            logger.warning("未配置OpenAI API密钥，返回模拟数据")
            print("[AI分析] ⚠️ 未配置API密钥，返回Mock数据")
            return self._get_mock_analysis(category)
        
        try:
            # 获取真实股票数据
            stock_pool = await self._get_stock_pool(category)
            
            # 构建提示词
            system_prompt = AGENT_PROMPTS.get(category, AGENT_PROMPTS["shortterm"])
            
            # 尝试获取技术指标（前5只股票）
            tech_indicators = {}
            try:
                symbols = [s["symbol"] for s in stock_pool[:5] if "symbol" in s]
                if symbols:
                    print(f"[AI分析] 📊 获取技术指标: {symbols}")
                    tech_indicators = await quant_service.batch_analyze(symbols, max_count=5)
            except Exception as e:
                print(f"[AI分析] ⚠️ 技术指标获取失败: {e}")
            
            # 构建user_prompt
            stock_data_str = json.dumps(stock_pool, ensure_ascii=False, indent=2)
            tech_data_str = ""
            if tech_indicators:
                tech_data_str = f"""\n
技术指标分析（部分股票）:
{json.dumps(tech_indicators, ensure_ascii=False, indent=2)}

指标说明:
- RSI < 30: 超卖, RSI > 70: 超买
- MACD金叉: 看多信号, MACD死叉: 看空信号
- 均线多头排列: 强势上涨趋势
- 放量: 成交量超过5日均量2倍以上
"""
            
            user_prompt = f"""请分析以下A股股票，给出{self._get_category_name(category)}推荐：

股票池：
{stock_data_str}
{tech_data_str}
当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

请基于你的专业分析，从中选出5-6只符合策略的股票进行推荐。
注意：价格和涨跌幅可以根据市场情况合理估计，重点是分析逻辑和推荐理由。

请严格按照JSON格式返回结果。"""

            # 调用API
            print(f"[AI分析] 🚀 正在调用AI API: {self.api_base}")
            print(f"[AI分析] 📊 模型: {self.model}, 分类: {category}")
            result = await self._call_api(system_prompt, user_prompt)
            
            if result:
                print(f"[AI分析] ✅ AI返回成功，长度: {len(result)} 字符")
                print(f"[AI分析] 📝 AI原始返回内容:\n{result[:500]}..." if len(result) > 500 else f"[AI分析] 📝 AI原始返回内容:\n{result}")
                # 解析结果
                stocks = self._parse_response(result, category)
                
                # 更新缓存
                self._cache[category] = {
                    "data": stocks,
                    "timestamp": datetime.now().timestamp()
                }
                
                return stocks
            
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            print(f"[AI分析] ❌ AI分析异常: {e}")
        
        # 失败时返回模拟数据
        print(f"[AI分析] ⚠️ API调用失败或超时，返回Mock数据")
        return self._get_mock_analysis(category)
    
    def _get_category_name(self, category: str) -> str:
        """获取分类名称"""
        names = {
            "shortterm": "短线强势",
            "trend": "趋势动量", 
            "value": "价值低估"
        }
        return names.get(category, "综合")
    
    async def _call_api(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """调用OpenAI兼容API"""
        try:
            async with httpx.AsyncClient(timeout=OPENAI_TIMEOUT) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    print(f"[AI API] ✅ 请求成功")
                    return content
                else:
                    logger.error(f"API调用失败: {response.status_code} - {response.text}")
                    print(f"[AI API] ❌ 请求失败: {response.status_code}")
                    print(f"[AI API] 错误详情: {response.text[:200]}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("API请求超时")
            print(f"[AI API] ⏰ 请求超时 (>{OPENAI_TIMEOUT}秒)")
            return None
        except Exception as e:
            logger.error(f"API请求异常: {e}")
            print(f"[AI API] ❌ 请求异常: {e}")
            return None
    
    def _parse_response(self, content: str, category: str) -> List[Dict]:
        """解析AI返回的JSON响应"""
        try:
            # 尝试提取JSON部分
            content = content.strip()
            
            # 处理可能的markdown代码块
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            data = json.loads(content)
            stocks = data.get("stocks", [])
            
            # 验证和规范化数据
            result = []
            for stock in stocks:
                result.append({
                    "symbol": stock.get("symbol", ""),
                    "name": stock.get("name", ""),
                    "price": float(stock.get("price", 0)),
                    "change": float(stock.get("change", 0)),
                    "change_percent": float(stock.get("change_percent", 0)),
                    "recommendation": stock.get("recommendation", "持有"),
                    "ai_score": int(stock.get("ai_score", 50)),
                    "signal": stock.get("signal", ""),
                    "reason": stock.get("reason", "")
                })
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 内容: {content[:200]}")
            return self._get_mock_analysis(category)
    
    def _get_mock_analysis(self, category: str) -> List[Dict]:
        """返回模拟分析数据"""
        mock_data = {
            "shortterm": [
                {"symbol": "000001", "name": "平安银行", "price": 12.85, "change": 1.17, "change_percent": 10.02, "recommendation": "强势", "ai_score": 95, "signal": "涨停"},
                {"symbol": "600519", "name": "贵州茅台", "price": 1725.00, "change": 86.25, "change_percent": 5.26, "recommendation": "突破", "ai_score": 92, "signal": "放量突破"},
                {"symbol": "002475", "name": "立讯精密", "price": 32.45, "change": 2.95, "change_percent": 10.00, "recommendation": "强势", "ai_score": 90, "signal": "涨停"},
                {"symbol": "300059", "name": "东方财富", "price": 18.92, "change": 1.72, "change_percent": 10.00, "recommendation": "强势", "ai_score": 88, "signal": "涨停"},
                {"symbol": "002415", "name": "海康威视", "price": 35.80, "change": 2.65, "change_percent": 8.00, "recommendation": "突破", "ai_score": 86, "signal": "新高突破"},
            ],
            "trend": [
                {"symbol": "300750", "name": "宁德时代", "price": 195.60, "change": 8.80, "change_percent": 4.71, "recommendation": "买入", "ai_score": 91, "signal": "均线多头"},
                {"symbol": "002594", "name": "比亚迪", "price": 268.50, "change": 12.80, "change_percent": 5.01, "recommendation": "买入", "ai_score": 89, "signal": "放量上攻"},
                {"symbol": "600036", "name": "招商银行", "price": 38.25, "change": 1.45, "change_percent": 3.94, "recommendation": "买入", "ai_score": 85, "signal": "趋势延续"},
                {"symbol": "000858", "name": "五粮液", "price": 165.30, "change": 5.80, "change_percent": 3.64, "recommendation": "买入", "ai_score": 83, "signal": "MACD金叉"},
                {"symbol": "601318", "name": "中国平安", "price": 45.60, "change": 1.35, "change_percent": 3.05, "recommendation": "关注", "ai_score": 78, "signal": "量价齐升"},
            ],
            "value": [
                {"symbol": "601166", "name": "兴业银行", "price": 16.25, "change": 0.48, "change_percent": 3.04, "recommendation": "超跌", "ai_score": 82, "signal": "PE仅4.2倍"},
                {"symbol": "600276", "name": "恒瑞医药", "price": 38.90, "change": 1.12, "change_percent": 2.96, "recommendation": "超跌", "ai_score": 80, "signal": "跌幅超40%"},
                {"symbol": "002304", "name": "洋河股份", "price": 102.50, "change": 2.85, "change_percent": 2.86, "recommendation": "超跌", "ai_score": 79, "signal": "估值底部"},
                {"symbol": "600887", "name": "伊利股份", "price": 28.65, "change": 0.72, "change_percent": 2.58, "recommendation": "超跌", "ai_score": 77, "signal": "高股息"},
                {"symbol": "000651", "name": "格力电器", "price": 38.20, "change": 0.85, "change_percent": 2.28, "recommendation": "超跌", "ai_score": 75, "signal": "破净反弹"},
            ]
        }
        return mock_data.get(category, mock_data["shortterm"])
    
    def clear_cache(self, category: Optional[str] = None):
        """清除缓存"""
        if category:
            self._cache.pop(category, None)
        else:
            self._cache.clear()


# 导出实例
openai_analyzer = OpenAIStockAnalyzer()
