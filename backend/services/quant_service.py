"""
量化分析服务 - 使用 pandas-ta 计算技术指标
提供 RSI, MACD, 布林带, 均线等指标分析
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import concurrent.futures

logger = logging.getLogger(__name__)

# 线程池
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


def _run_sync(func, *args, **kwargs):
    """在线程池中运行同步函数"""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(_executor, lambda: func(*args, **kwargs))


class QuantService:
    """量化分析服务"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, float] = {}
        self._cache_ttl = 300  # 5分钟缓存
        self._ak = None
        self._ta = None
    
    def _get_libs(self):
        """延迟加载库"""
        if self._ak is None:
            try:
                import akshare as ak
                import pandas_ta as ta
                self._ak = ak
                self._ta = ta
                print("[Quant] ✅ 量化分析库加载成功")
            except ImportError as e:
                logger.error(f"量化库未安装: {e}")
                print(f"[Quant] ❌ 库未安装: {e}")
                return None, None
        return self._ak, self._ta
    
    def _is_cache_valid(self, key: str) -> bool:
        if key not in self._cache:
            return False
        cache_age = datetime.now().timestamp() - self._cache_time.get(key, 0)
        return cache_age < self._cache_ttl
    
    def _get_hist_data_sync(self, symbol: str, days: int = 60) -> Optional[Any]:
        """同步获取历史K线"""
        ak, _ = self._get_libs()
        if not ak:
            return None
        
        try:
            # 判断是沪市还是深市
            if symbol.startswith("6"):
                full_symbol = f"sh{symbol}"
            else:
                full_symbol = f"sz{symbol}"
            
            # 获取日K线
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=(datetime.now() - timedelta(days=days)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust="qfq"
            )
            return df
        except Exception as e:
            logger.error(f"获取K线失败 {symbol}: {e}")
            return None
    
    def _calculate_indicators_sync(self, df) -> Dict:
        """同步计算技术指标"""
        _, ta = self._get_libs()
        if df is None or df.empty or ta is None:
            return {}
        
        try:
            # 确保列名正确
            df = df.rename(columns={
                "日期": "date",
                "开盘": "open",
                "收盘": "close", 
                "最高": "high",
                "最低": "low",
                "成交量": "volume"
            })
            
            if len(df) < 20:
                return {"error": "数据不足"}
            
            close = df["close"]
            high = df["high"]
            low = df["low"]
            volume = df["volume"]
            
            result = {}
            
            # RSI (14)
            rsi = ta.rsi(close, length=14)
            if rsi is not None and len(rsi) > 0:
                result["rsi_14"] = round(rsi.iloc[-1], 2) if not rsi.iloc[-1] != rsi.iloc[-1] else 50
                # RSI信号
                if result["rsi_14"] < 30:
                    result["rsi_signal"] = "超卖"
                elif result["rsi_14"] > 70:
                    result["rsi_signal"] = "超买"
                else:
                    result["rsi_signal"] = "中性"
            
            # MACD
            macd = ta.macd(close, fast=12, slow=26, signal=9)
            if macd is not None and len(macd) > 1:
                macd_line = macd.iloc[-1, 0] if not macd.iloc[-1, 0] != macd.iloc[-1, 0] else 0
                signal_line = macd.iloc[-1, 2] if not macd.iloc[-1, 2] != macd.iloc[-1, 2] else 0
                prev_macd = macd.iloc[-2, 0] if not macd.iloc[-2, 0] != macd.iloc[-2, 0] else 0
                prev_signal = macd.iloc[-2, 2] if not macd.iloc[-2, 2] != macd.iloc[-2, 2] else 0
                
                result["macd"] = round(macd_line, 3)
                result["macd_signal_line"] = round(signal_line, 3)
                
                # MACD金叉/死叉
                if prev_macd < prev_signal and macd_line > signal_line:
                    result["macd_signal"] = "金叉"
                elif prev_macd > prev_signal and macd_line < signal_line:
                    result["macd_signal"] = "死叉"
                elif macd_line > signal_line:
                    result["macd_signal"] = "多头"
                else:
                    result["macd_signal"] = "空头"
            
            # 布林带
            bbands = ta.bbands(close, length=20, std=2)
            if bbands is not None and len(bbands) > 0:
                upper = bbands.iloc[-1, 0]
                mid = bbands.iloc[-1, 1]
                lower = bbands.iloc[-1, 2]
                current_price = close.iloc[-1]
                
                result["bb_upper"] = round(upper, 2)
                result["bb_mid"] = round(mid, 2)
                result["bb_lower"] = round(lower, 2)
                
                # 布林带位置
                if current_price > upper:
                    result["bb_position"] = "突破上轨"
                elif current_price < lower:
                    result["bb_position"] = "跌破下轨"
                elif current_price > mid:
                    result["bb_position"] = "上半区"
                else:
                    result["bb_position"] = "下半区"
            
            # 均线
            ma5 = ta.sma(close, length=5)
            ma10 = ta.sma(close, length=10)
            ma20 = ta.sma(close, length=20)
            
            if ma5 is not None and ma10 is not None and ma20 is not None:
                result["ma5"] = round(ma5.iloc[-1], 2)
                result["ma10"] = round(ma10.iloc[-1], 2)
                result["ma20"] = round(ma20.iloc[-1], 2)
                
                # 均线趋势
                if ma5.iloc[-1] > ma10.iloc[-1] > ma20.iloc[-1]:
                    result["ma_trend"] = "多头排列"
                elif ma5.iloc[-1] < ma10.iloc[-1] < ma20.iloc[-1]:
                    result["ma_trend"] = "空头排列"
                else:
                    result["ma_trend"] = "震荡整理"
            
            # 量比
            if len(volume) >= 5:
                avg_vol_5 = volume.iloc[-6:-1].mean()
                current_vol = volume.iloc[-1]
                if avg_vol_5 > 0:
                    result["volume_ratio"] = round(current_vol / avg_vol_5, 2)
                    if result["volume_ratio"] > 2:
                        result["volume_signal"] = "放量"
                    elif result["volume_ratio"] < 0.5:
                        result["volume_signal"] = "缩量"
                    else:
                        result["volume_signal"] = "正常"
            
            return result
            
        except Exception as e:
            logger.error(f"计算指标失败: {e}")
            return {"error": str(e)}
    
    async def analyze_stock(self, symbol: str) -> Dict:
        """分析单只股票的技术指标"""
        cache_key = f"quant_{symbol}"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        try:
            # 获取历史数据
            df = await _run_sync(self._get_hist_data_sync, symbol)
            if df is None:
                return {}
            
            # 计算指标
            result = await _run_sync(self._calculate_indicators_sync, df)
            
            if result and "error" not in result:
                self._cache[cache_key] = result
                self._cache_time[cache_key] = datetime.now().timestamp()
            
            return result
            
        except Exception as e:
            logger.error(f"分析股票失败 {symbol}: {e}")
            return {}
    
    async def batch_analyze(self, symbols: List[str], max_count: int = 10) -> Dict[str, Dict]:
        """批量分析多只股票（限制数量避免过慢）"""
        results = {}
        
        for symbol in symbols[:max_count]:
            try:
                result = await self.analyze_stock(symbol)
                if result:
                    results[symbol] = result
            except Exception:
                continue
        
        return results
    
    def get_signal_summary(self, indicators: Dict) -> str:
        """将技术指标汇总为信号描述"""
        if not indicators or "error" in indicators:
            return ""
        
        signals = []
        
        # RSI
        if "rsi_signal" in indicators:
            if indicators["rsi_signal"] in ["超买", "超卖"]:
                signals.append(f"RSI{indicators['rsi_signal']}")
        
        # MACD
        if "macd_signal" in indicators:
            if indicators["macd_signal"] in ["金叉", "死叉"]:
                signals.append(f"MACD{indicators['macd_signal']}")
        
        # 均线
        if "ma_trend" in indicators:
            if indicators["ma_trend"] != "震荡整理":
                signals.append(indicators["ma_trend"])
        
        # 布林带
        if "bb_position" in indicators:
            if "突破" in indicators["bb_position"] or "跌破" in indicators["bb_position"]:
                signals.append(indicators["bb_position"])
        
        # 量比
        if "volume_signal" in indicators:
            if indicators["volume_signal"] == "放量":
                signals.append("放量")
        
        return " | ".join(signals) if signals else ""


# 导出实例
quant_service = QuantService()
