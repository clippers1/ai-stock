"""
A股数据服务 - 使用 akshare-one 和新浪财经获取实时数据
优先获取沪深300成分股，覆盖市场主流股票
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import concurrent.futures

logger = logging.getLogger(__name__)

# 线程池用于运行同步函数
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def _run_sync(func, *args, **kwargs):
    """在线程池中运行同步函数"""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(_executor, lambda: func(*args, **kwargs))


class AKShareOneService:
    """使用 akshare-one 和新浪财经获取A股数据的服务"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, float] = {}
        self._cache_ttl = 60  # 60秒缓存
        self._akshare_one = None
        
    def _get_akshare_one(self):
        """延迟加载 akshare-one"""
        if self._akshare_one is None:
            try:
                from akshare_one import get_realtime_data, get_hist_data
                self._akshare_one = {
                    "get_realtime_data": get_realtime_data,
                    "get_hist_data": get_hist_data
                }
                print("[AKShare-One] ✅ akshare-one 库加载成功")
            except ImportError as e:
                logger.error(f"akshare-one 未安装: {e}")
                print("[AKShare-One] ❌ akshare-one 库未安装")
                return None
        return self._akshare_one
    
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self._cache:
            return False
        cache_age = datetime.now().timestamp() - self._cache_time.get(key, 0)
        return cache_age < self._cache_ttl
    
    async def _get_hs300_from_sina(self) -> List[Dict]:
        """从新浪财经获取沪深300成分股实时数据"""
        import httpx
        
        result = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 分页获取沪深300全部成分股（每页60条，共5页）
                for page in range(1, 6):
                    url = f"http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={page}&num=60&sort=symbol&asc=1&node=hs300"
                    
                    response = await client.get(
                        url,
                        headers={
                            "Referer": "http://vip.stock.finance.sina.com.cn/",
                            "User-Agent": "Mozilla/5.0"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        for item in data:
                            try:
                                result.append({
                                    "symbol": item.get("code", ""),
                                    "name": item.get("name", ""),
                                    "price": float(item.get("trade", 0) or 0),
                                    "change": float(item.get("pricechange", 0) or 0),
                                    "change_percent": float(item.get("changepercent", 0) or 0),
                                    "volume": float(item.get("volume", 0) or 0),
                                    "turnover": float(item.get("amount", 0) or 0),
                                    "high": float(item.get("high", 0) or 0),
                                    "low": float(item.get("low", 0) or 0),
                                    "open": float(item.get("open", 0) or 0),
                                    "prev_close": float(item.get("settlement", 0) or 0),
                                    "amplitude": 0,
                                    "turnover_rate": float(item.get("turnoverratio", 0) or 0),
                                    "pe_ratio": float(item.get("per", 0) or 0),
                                    "pb_ratio": float(item.get("pb", 0) or 0),
                                })
                            except Exception:
                                continue
                                
        except Exception as e:
            print(f"[AKShare-One] ❌ 获取沪深300失败: {e}")
        
        return result
    
    async def _get_hot_sectors_from_sina(self) -> List[Dict]:
        """从新浪财经获取热门板块股票"""
        import httpx
        
        result = []
        # 热门板块节点
        hot_nodes = [
            "zhineng_ai",      # AI人工智能
            "new_dlqc",        # 新能源车  
            "new_bdtjs",       # 半导体
            "new_gfts",        # 光伏
            "new_jqr",         # 机器人
        ]
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for node in hot_nodes:
                    url = f"http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=30&sort=changepercent&asc=0&node={node}"
                    
                    try:
                        response = await client.get(
                            url,
                            headers={
                                "Referer": "http://vip.stock.finance.sina.com.cn/",
                                "User-Agent": "Mozilla/5.0"
                            }
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            for item in data:
                                try:
                                    result.append({
                                        "symbol": item.get("code", ""),
                                        "name": item.get("name", ""),
                                        "price": float(item.get("trade", 0) or 0),
                                        "change": float(item.get("pricechange", 0) or 0),
                                        "change_percent": float(item.get("changepercent", 0) or 0),
                                        "volume": float(item.get("volume", 0) or 0),
                                        "turnover": float(item.get("amount", 0) or 0),
                                        "high": float(item.get("high", 0) or 0),
                                        "low": float(item.get("low", 0) or 0),
                                        "open": float(item.get("open", 0) or 0),
                                        "prev_close": float(item.get("settlement", 0) or 0),
                                        "amplitude": 0,
                                        "turnover_rate": float(item.get("turnoverratio", 0) or 0),
                                        "pe_ratio": float(item.get("per", 0) or 0),
                                        "pb_ratio": float(item.get("pb", 0) or 0),
                                    })
                                except Exception:
                                    continue
                    except Exception:
                        continue
                        
        except Exception as e:
            print(f"[AKShare-One] ❌ 获取热门板块失败: {e}")
        
        return result
    
    async def get_realtime_quotes(self) -> Optional[List[Dict]]:
        """
        获取A股实时行情
        优先使用新浪财经获取沪深300 + 热门板块股票
        """
        cache_key = "realtime_all"
        if self._is_cache_valid(cache_key):
            print("[AKShare-One] 返回缓存的实时行情")
            return self._cache[cache_key]
        
        try:
            print("[AKShare-One] 🚀 获取沪深300 + 热门板块数据...")
            
            # 并行获取沪深300和热门板块
            hs300_data, hot_data = await asyncio.gather(
                self._get_hs300_from_sina(),
                self._get_hot_sectors_from_sina()
            )
            
            # 合并并去重
            seen_symbols = set()
            result = []
            
            for item in hs300_data + hot_data:
                symbol = item["symbol"]
                if symbol and symbol not in seen_symbols and item["price"] > 0:
                    seen_symbols.add(symbol)
                    result.append(item)
            
            if result:
                # 更新缓存
                self._cache[cache_key] = result
                self._cache_time[cache_key] = datetime.now().timestamp()
                
                print(f"[AKShare-One] ✅ 成功获取 {len(result)} 只股票 (沪深300: {len(hs300_data)}, 热门板块: {len(hot_data)})")
                return result
            else:
                print("[AKShare-One] ⚠️ 未获取到数据")
                return None
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            print(f"[AKShare-One] ❌ 获取实时行情失败: {e}")
            return None
    
    async def get_stock_pool_by_category(self, category: str, limit: int = 15) -> List[Dict]:
        """
        根据分类获取股票池
        
        Args:
            category: shortterm(短线强势) / trend(趋势动量) / value(价值低估)
            limit: 返回数量
        """
        quotes = await self.get_realtime_quotes()
        if not quotes:
            return []
        
        try:
            if category == "shortterm":
                # 短线强势：按涨跌幅降序
                filtered = [q for q in quotes if q["change_percent"] > 2 and q["price"] > 0]
                filtered.sort(key=lambda x: x["change_percent"], reverse=True)
                print(f"[AKShare-One] 短线强势: 筛选出 {len(filtered)} 只涨幅>2%的股票")
                
            elif category == "trend":
                # 趋势动量：成交活跃+涨幅适中
                filtered = [q for q in quotes if 0.5 < q["change_percent"] < 7 and q["turnover"] > 100000000 and q["price"] > 0]
                filtered.sort(key=lambda x: x["turnover"], reverse=True)
                print(f"[AKShare-One] 趋势动量: 筛选出 {len(filtered)} 只成交活跃股票")
                
            elif category == "value":
                # 价值低估：低PE + 低PB
                filtered = [q for q in quotes if 0 < q["pe_ratio"] < 15 and 0 < q["pb_ratio"] < 2 and q["change_percent"] > 0 and q["price"] > 0]
                filtered.sort(key=lambda x: x["pe_ratio"])
                print(f"[AKShare-One] 价值低估: 筛选出 {len(filtered)} 只低估值股票")
                
            else:
                filtered = [q for q in quotes if q["price"] > 0][:limit]
            
            return filtered[:limit]
            
        except Exception as e:
            logger.error(f"筛选股票池失败: {e}")
            print(f"[AKShare-One] ❌ 筛选失败: {e}")
            return []
    
    async def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """获取单只股票的实时行情"""
        quotes = await self.get_realtime_quotes()
        if not quotes:
            return None
            
        for q in quotes:
            if q["symbol"] == symbol:
                return q
        return None
    
    async def is_available(self) -> bool:
        """检查服务是否可用"""
        return True  # 新浪API通常可用


# 导出实例
akshare_service = AKShareOneService()
