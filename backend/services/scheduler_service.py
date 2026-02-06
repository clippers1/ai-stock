"""
定时任务服务
使用 APScheduler 定期更新活跃持仓的股票价格
支持自动止盈止损
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from services.akshare_service import akshare_service
from services.backtest_service import backtest_service

logger = logging.getLogger(__name__)


# 止盈止损配置
STOP_PROFIT_PERCENT = 15.0   # 止盈阈值：盈利超过15%自动平仓
STOP_LOSS_PERCENT = -8.0     # 止损阈值：亏损超过8%自动平仓
MAX_HOLDING_DAYS = 30        # 最大持有天数：超过30天自动平仓


class SchedulerService:
    """定时任务服务"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

        # 止盈止损配置（可通过方法动态调整）
        self.stop_profit_percent = STOP_PROFIT_PERCENT
        self.stop_loss_percent = STOP_LOSS_PERCENT
        self.max_holding_days = MAX_HOLDING_DAYS
        self.auto_close_enabled = True  # 是否启用自动平仓

    def set_stop_config(
        self,
        stop_profit: float = None,
        stop_loss: float = None,
        max_days: int = None,
        enabled: bool = None
    ):
        """动态设置止盈止损配置"""
        if stop_profit is not None:
            self.stop_profit_percent = stop_profit
        if stop_loss is not None:
            self.stop_loss_percent = stop_loss
        if max_days is not None:
            self.max_holding_days = max_days
        if enabled is not None:
            self.auto_close_enabled = enabled

        logger.info(
            f"[止盈止损] 配置更新: 止盈={self.stop_profit_percent}%, "
            f"止损={self.stop_loss_percent}%, 最大持有={self.max_holding_days}天, "
            f"启用={self.auto_close_enabled}"
        )

    def get_stop_config(self) -> Dict:
        """获取当前止盈止损配置"""
        return {
            "stop_profit_percent": self.stop_profit_percent,
            "stop_loss_percent": self.stop_loss_percent,
            "max_holding_days": self.max_holding_days,
            "auto_close_enabled": self.auto_close_enabled,
        }

    async def check_auto_close(self) -> List[Dict]:
        """
        检查并执行自动止盈止损

        Returns:
            被自动平仓的记录列表
        """
        if not self.auto_close_enabled:
            return []

        closed_records = []

        try:
            logger.info("[止盈止损] 开始检查自动平仓条件...")

            # 获取所有活跃记录
            result = backtest_service.get_records(period="all", status="active", page_size=1000)
            records = result.get("records", [])

            if not records:
                logger.info("[止盈止损] 没有活跃持仓")
                return []

            for record in records:
                record_id = record.get("id")
                symbol = record.get("symbol")
                profit_percent = record.get("profit_percent", 0)
                holding_days = record.get("holding_days", 0)
                current_price = record.get("current_price", 0)

                close_reason = None

                # 检查止盈
                if profit_percent >= self.stop_profit_percent:
                    close_reason = "profit"
                    logger.info(
                        f"[止盈止损] 🎉 {symbol} 触发止盈: {profit_percent:.1f}% >= {self.stop_profit_percent}%"
                    )

                # 检查止损
                elif profit_percent <= self.stop_loss_percent:
                    close_reason = "loss"
                    logger.info(
                        f"[止盈止损] ⚠️ {symbol} 触发止损: {profit_percent:.1f}% <= {self.stop_loss_percent}%"
                    )

                # 检查最大持有天数
                elif holding_days >= self.max_holding_days:
                    close_reason = "expired"
                    logger.info(
                        f"[止盈止损] ⏰ {symbol} 持有超时: {holding_days}天 >= {self.max_holding_days}天"
                    )

                # 执行平仓
                if close_reason:
                    success = backtest_service.close_position(
                        record_id=record_id,
                        close_price=current_price,
                        close_reason=close_reason
                    )

                    if success:
                        closed_records.append({
                            "id": record_id,
                            "symbol": symbol,
                            "profit_percent": profit_percent,
                            "reason": close_reason,
                        })
                        logger.info(f"[止盈止损] ✅ {symbol} 自动平仓成功")
                    else:
                        logger.error(f"[止盈止损] ❌ {symbol} 自动平仓失败")

            if closed_records:
                logger.info(f"[止盈止损] 本次自动平仓 {len(closed_records)} 条记录")

            return closed_records

        except Exception as e:
            logger.error(f"[止盈止损] 检查失败: {e}")
            return []

    async def update_stock_prices(self):
        """
        更新所有活跃持仓的股票价格
        从 akshare 获取最新价格并更新数据库
        """
        try:
            logger.info("[定时任务] 开始更新股票价格...")

            # 获取所有活跃持仓的股票代码
            active_symbols = backtest_service.get_active_symbols()

            if not active_symbols:
                logger.info("[定时任务] 没有活跃持仓，跳过更新")
                return

            logger.info(f"[定时任务] 需要更新 {len(active_symbols)} 只股票")

            # 批量获取股票价格
            price_data: Dict[str, float] = {}

            for symbol in active_symbols:
                try:
                    quote = await akshare_service.get_stock_quote(symbol)
                    if quote and quote.get("price", 0) > 0:
                        price_data[symbol] = float(quote["price"])
                        logger.debug(f"[定时任务] {symbol}: {quote['price']}")
                except Exception as e:
                    logger.error(f"[定时任务] 获取 {symbol} 价格失败: {e}")
                    continue

            # 更新数据库
            if price_data:
                updated_count = backtest_service.update_prices(price_data)
                logger.info(
                    f"[定时任务] ✅ 价格更新完成: {updated_count}/{len(active_symbols)} 条记录"
                )

                # 价格更新后检查自动止盈止损
                await self.check_auto_close()
            else:
                logger.warning("[定时任务] ⚠️ 未获取到任何价格数据")

        except Exception as e:
            logger.error(f"[定时任务] 更新价格失败: {e}")

    def start(self):
        """启动定时任务"""
        if self._is_running:
            logger.warning("[定时任务] 调度器已在运行")
            return

        try:
            # 添加定时任务：每天交易时间段更新价格
            # 工作日 9:30-15:00，每30分钟更新一次
            self.scheduler.add_job(
                self.update_stock_prices,
                CronTrigger(
                    day_of_week="mon-fri",  # 周一到周五
                    hour="9-11,13-14",      # 9-11点和13-14点
                    minute="*/30",          # 每30分钟
                ),
                id="update_prices_trading_hours",
                name="交易时段更新股票价格",
                replace_existing=True,
            )

            # 添加收盘后更新任务：每天15:30执行一次
            self.scheduler.add_job(
                self.update_stock_prices,
                CronTrigger(
                    day_of_week="mon-fri",
                    hour=15,
                    minute=30,
                ),
                id="update_prices_after_close",
                name="收盘后更新股票价格",
                replace_existing=True,
            )

            self.scheduler.start()
            self._is_running = True
            logger.info("[定时任务] ✅ 调度器启动成功")
            logger.info("[定时任务] 📅 交易时段: 周一至周五 9:30-15:00，每30分钟更新")
            logger.info("[定时任务] 📅 收盘更新: 周一至周五 15:30")

        except Exception as e:
            logger.error(f"[定时任务] 启动失败: {e}")

    def stop(self):
        """停止定时任务"""
        if not self._is_running:
            return

        try:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("[定时任务] 调度器已停止")
        except Exception as e:
            logger.error(f"[定时任务] 停止失败: {e}")

    def get_jobs(self):
        """获取所有定时任务"""
        return self.scheduler.get_jobs()


# 全局单例
scheduler_service = SchedulerService()
