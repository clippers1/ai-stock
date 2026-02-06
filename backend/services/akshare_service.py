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
        self._ak = None  # akshare库用于涨停池
        
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
    
    def _get_akshare(self):
        """延迟加载akshare"""
        if self._ak is None:
            try:
                import akshare as ak
                self._ak = ak
                print("[AKShare] ✅ akshare 库加载成功")
            except ImportError:
                print("[AKShare] ❌ akshare 库未安装")
                return None
        return self._ak
    
    async def get_zhangting_pool(self) -> List[Dict]:
        """获取今日涨停池"""
        cache_key = "zhangting_pool"
        if self._is_cache_valid(cache_key):
            print("[AKShare] 返回缓存的涨停池")
            return self._cache[cache_key]
        
        ak = self._get_akshare()
        if not ak:
            return []
        
        try:
            today = datetime.now().strftime("%Y%m%d")
            print(f"[AKShare] 🚀 获取 {today} 涨停池数据...")
            
            df = await _run_sync(ak.stock_zt_pool_em, today)
            
            if df is None or df.empty:
                print("[AKShare] ⚠️ 涨停池无数据（可能非交易时间）")
                return []
            
            result = []
            for _, row in df.iterrows():
                try:
                    result.append({
                        "symbol": str(row.get("代码", "")),
                        "name": str(row.get("名称", "")),
                        "price": float(row.get("最新价", 0) or 0),
                        "change": 0,
                        "change_percent": float(row.get("涨跌幅", 0) or 0),
                        "volume": float(row.get("成交额", 0) or 0),
                        "turnover": float(row.get("成交额", 0) or 0),
                        "high": float(row.get("最新价", 0) or 0),
                        "low": 0,
                        "open": 0,
                        "prev_close": 0,
                        "amplitude": 0,
                        "turnover_rate": float(row.get("换手率", 0) or 0),
                        "pe_ratio": 0,
                        "pb_ratio": 0,
                        "first_zt_time": str(row.get("首次封板时间", "")),
                        "zt_count": str(row.get("涨停统计", "")),
                        "lianban": int(row.get("连板数", 1) or 1),
                        "industry": str(row.get("所属行业", "")),
                    })
                except Exception:
                    continue
            
            # 按连板数排序
            result.sort(key=lambda x: x.get("lianban", 0), reverse=True)
            
            self._cache[cache_key] = result
            self._cache_time[cache_key] = datetime.now().timestamp()
            
            print(f"[AKShare] ✅ 获取 {len(result)} 只涨停股")
            return result
            
        except Exception as e:
            logger.error(f"获取涨停池失败: {e}")
            print(f"[AKShare] ❌ 获取涨停池失败: {e}")
            return []
    
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
                # 短线强势：优先从涨停池获取
                zhangting = await self.get_zhangting_pool()
                if zhangting:
                    print(f"[AKShare-One] 短线强势: 使用涨停池 {len(zhangting)} 只股票")
                    return zhangting[:limit]
                
                # 涨停池无数据则从行情筛选
                filtered = [q for q in quotes if q["change_percent"] > 5 and q["price"] > 0]
                filtered.sort(key=lambda x: x["change_percent"], reverse=True)
                print(f"[AKShare-One] 短线强势: 筛选出 {len(filtered)} 只涨幅>5%的股票")
                
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
    
    async def get_hot_sectors(self, limit: int = 10) -> List[Dict]:
        """获取热门行业板块涨跌数据"""
        cache_key = "hot_sectors"
        if self._is_cache_valid(cache_key):
            print("[AKShare] 返回缓存的板块数据")
            return self._cache[cache_key]
        
        import httpx
        
        # 新浪行业板块数据 - 按涨跌幅排序
        url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCount"
        
        # 预定义的热门行业板块节点
        sector_nodes = [
            ("new_dlqc", "新能源车"),
            ("new_bdtjs", "半导体"),
            ("zhineng_ai", "AI人工智能"),
            ("new_gfts", "光伏"),
            ("new_jqr", "机器人"),
            ("new_yy", "医药"),
            ("new_yh", "银行"),
            ("new_bx", "保险"),
            ("new_fdc", "房地产"),
            ("new_jc", "建材"),
            ("new_jj", "家电"),
            ("new_sp", "食品饮料"),
            ("new_jx", "机械"),
            ("new_hg", "化工"),
        ]
        
        try:
            print("[AKShare] 🚀 获取热门板块数据...")
            results = []
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                for node, name in sector_nodes[:limit + 4]:
                    try:
                        # 获取板块内股票数据来计算整体涨跌
                        data_url = f"http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=5&sort=changepercent&asc=0&node={node}"
                        resp = await client.get(
                            data_url,
                            headers={"Referer": "http://vip.stock.finance.sina.com.cn/"}
                        )
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            if data and len(data) > 0:
                                # 计算板块平均涨跌幅
                                changes = [float(s.get("changepercent", 0) or 0) for s in data[:5]]
                                avg_change = sum(changes) / len(changes) if changes else 0
                                
                                results.append({
                                    "name": name,
                                    "node": node,
                                    "change": round(avg_change, 2),
                                    "hot": avg_change > 2,  # 涨幅>2%标记为热门
                                    "top_stocks": [
                                        {"name": s.get("name", ""), "change": float(s.get("changepercent", 0) or 0)}
                                        for s in data[:3]
                                    ]
                                })
                    except Exception as e:
                        logger.debug(f"获取板块{name}失败: {e}")
                        continue
            
            # 按涨跌幅排序
            results.sort(key=lambda x: x["change"], reverse=True)
            
            # 缓存结果
            self._cache[cache_key] = results[:limit]
            self._cache_time[cache_key] = datetime.now().timestamp()
            
            print(f"[AKShare] ✅ 获取 {len(results)} 个板块数据")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"获取板块数据失败: {e}")
            print(f"[AKShare] ❌ 获取板块失败: {e}")
            return []
    
    async def is_available(self) -> bool:
        """检查服务是否可用"""
        return True  # 新浪API通常可用

    async def get_stock_history(self, symbol: str, days: int = 30) -> List[Dict]:
        """
        获取股票历史K线数据

        Args:
            symbol: 股票代码（如 600519）
            days: 获取天数，默认30天

        Returns:
            K线数据列表，每条包含 date, open, high, low, close, volume
        """
        cache_key = f"history_{symbol}_{days}"
        if self._is_cache_valid(cache_key):
            print(f"[AKShare] 返回缓存的K线数据: {symbol}")
            return self._cache[cache_key]

        ak = self._get_akshare()
        if not ak:
            print(f"[AKShare] ❌ akshare未加载，无法获取K线")
            return []

        try:
            from datetime import timedelta

            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 10)  # 多取几天以防节假日

            print(f"[AKShare] 🚀 获取 {symbol} 历史K线 ({days}天)...")

            # 使用 akshare 获取历史数据
            df = await _run_sync(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq"  # 前复权
            )

            if df is None or df.empty:
                print(f"[AKShare] ⚠️ {symbol} K线数据为空")
                return []

            # 转换为列表格式
            result = []
            for _, row in df.iterrows():
                result.append({
                    "date": str(row.get("日期", "")),
                    "open": float(row.get("开盘", 0)),
                    "high": float(row.get("最高", 0)),
                    "low": float(row.get("最低", 0)),
                    "close": float(row.get("收盘", 0)),
                    "volume": int(row.get("成交量", 0)),
                })

            # 只取最近 days 天
            result = result[-days:] if len(result) > days else result

            if result:
                # 更新缓存（K线数据缓存5分钟）
                self._cache[cache_key] = result
                self._cache_time[cache_key] = datetime.now().timestamp()
                print(f"[AKShare] ✅ 获取 {symbol} K线成功: {len(result)} 条")

            return result

        except Exception as e:
            logger.error(f"获取K线失败 {symbol}: {e}")
            print(f"[AKShare] ❌ 获取K线失败 {symbol}: {e}")
            return []


# 导出实例
akshare_service = AKShareOneService()
