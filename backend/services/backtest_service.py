"""
回测服务层
提供推荐记录的CRUD操作和统计分析
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
import logging

from database.models import RecommendationRecord, SessionLocal

logger = logging.getLogger(__name__)


class BacktestService:
    """回测服务"""

    def __init__(self):
        pass

    def _get_db(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()

    # ==================== 创建记录 ====================

    def create_recommendation(
        self,
        symbol: str,
        name: str,
        category: str,
        recommendation: str,
        entry_price: float,
        ai_score: int = 50,
        signal: str = "",
        reason: str = "",
    ) -> Optional[RecommendationRecord]:
        """
        创建推荐记录

        Args:
            symbol: 股票代码
            name: 股票名称
            category: 推荐类别 (shortterm/trend/value)
            recommendation: 推荐操作 (买入/增持/突破等)
            entry_price: 入场价格
            ai_score: AI评分
            signal: 信号说明
            reason: 推荐理由

        Returns:
            创建的记录对象
        """
        db = self._get_db()
        try:
            # 检查今天是否已经推荐过同一只股票（同类别）
            today = datetime.now().date()
            existing = (
                db.query(RecommendationRecord)
                .filter(
                    and_(
                        RecommendationRecord.symbol == symbol,
                        RecommendationRecord.category == category,
                        func.date(RecommendationRecord.entry_date) == today,
                    )
                )
                .first()
            )

            if existing:
                logger.info(f"今日已存在相同推荐: {symbol} {category}")
                return existing

            # 创建新记录
            record = RecommendationRecord(
                symbol=symbol,
                name=name,
                category=category,
                recommendation=recommendation,
                ai_score=ai_score,
                signal=signal,
                reason=reason,
                entry_price=entry_price,
                entry_date=datetime.now(),
                current_price=entry_price,
                price_updated_at=datetime.now(),
                status="active",
                profit_percent=0,
                holding_days=0,
            )

            db.add(record)
            db.commit()
            db.refresh(record)

            logger.info(f"创建推荐记录: {symbol} {name} {category} @ {entry_price}")
            return record

        except Exception as e:
            logger.error(f"创建推荐记录失败: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def batch_create_recommendations(
        self, stocks: List[Dict[str, Any]], category: str
    ) -> int:
        """
        批量创建推荐记录

        Args:
            stocks: 股票列表，每个包含 symbol, name, price, recommendation, ai_score, signal, reason
            category: 推荐类别

        Returns:
            成功创建的记录数
        """
        count = 0
        for stock in stocks:
            result = self.create_recommendation(
                symbol=stock.get("symbol", ""),
                name=stock.get("name", ""),
                category=category,
                recommendation=stock.get("recommendation", "持有"),
                entry_price=stock.get("price", 0),
                ai_score=stock.get("ai_score", 50),
                signal=stock.get("signal", ""),
                reason=stock.get("reason", ""),
            )
            if result:
                count += 1

        logger.info(f"批量创建推荐记录: {count}/{len(stocks)} 条成功")
        return count

    # ==================== 查询记录 ====================

    def get_records(
        self,
        period: str = "30d",
        status: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        获取回测记录列表

        Args:
            period: 时间周期 (7d/30d/90d/all)
            status: 状态筛选 (active/closed)
            category: 类别筛选
            page: 页码
            page_size: 每页数量

        Returns:
            {records: [...], total: int, page: int, page_size: int}
        """
        db = self._get_db()
        try:
            query = db.query(RecommendationRecord)

            # 时间筛选
            if period != "all":
                days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
                start_date = datetime.now() - timedelta(days=days)
                query = query.filter(RecommendationRecord.entry_date >= start_date)

            # 状态筛选
            if status:
                query = query.filter(RecommendationRecord.status == status)

            # 类别筛选
            if category:
                query = query.filter(RecommendationRecord.category == category)

            # 总数
            total = query.count()

            # 分页 & 排序（最新的在前）
            records = (
                query.order_by(desc(RecommendationRecord.entry_date))
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )

            return {
                "records": [r.to_dict() for r in records],
                "total": total,
                "page": page,
                "page_size": page_size,
            }

        except Exception as e:
            logger.error(f"查询回测记录失败: {e}")
            return {"records": [], "total": 0, "page": page, "page_size": page_size}
        finally:
            db.close()

    def get_summary(self, period: str = "30d") -> Dict[str, Any]:
        """
        获取回测统计摘要

        Args:
            period: 时间周期 (7d/30d/90d/all)

        Returns:
            {total_return: float, win_rate: float, total_recommendations: int, ...}
        """
        db = self._get_db()
        try:
            query = db.query(RecommendationRecord)

            # 时间筛选
            if period != "all":
                days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
                start_date = datetime.now() - timedelta(days=days)
                query = query.filter(RecommendationRecord.entry_date >= start_date)

            records = query.all()

            if not records:
                return {
                    "total_return": 0,
                    "win_rate": 0,
                    "total_recommendations": 0,
                    "active_count": 0,
                    "closed_count": 0,
                    "avg_holding_days": 0,
                    "best_profit": 0,
                    "worst_loss": 0,
                    "period": period,
                }

            # 计算统计数据
            total_count = len(records)
            active_count = sum(1 for r in records if r.status == "active")
            closed_count = total_count - active_count

            # 盈亏统计
            profits = [r.profit_percent or 0 for r in records]
            win_count = sum(1 for p in profits if p > 0)

            total_return = sum(profits)
            avg_return = total_return / total_count if total_count > 0 else 0
            win_rate = (win_count / total_count * 100) if total_count > 0 else 0

            # 持有天数
            holding_days = [r.holding_days or 0 for r in records]
            avg_holding_days = (
                sum(holding_days) / len(holding_days) if holding_days else 0
            )

            return {
                "total_return": round(avg_return * total_count, 2),  # 总收益率（累加）
                "avg_return": round(avg_return, 2),  # 平均收益率
                "win_rate": round(win_rate, 1),
                "total_recommendations": total_count,
                "active_count": active_count,
                "closed_count": closed_count,
                "avg_holding_days": round(avg_holding_days, 1),
                "best_profit": round(max(profits), 2) if profits else 0,
                "worst_loss": round(min(profits), 2) if profits else 0,
                "period": period,
            }

        except Exception as e:
            logger.error(f"获取回测统计失败: {e}")
            return {
                "total_return": 0,
                "win_rate": 0,
                "total_recommendations": 0,
                "period": period,
            }
        finally:
            db.close()

    # ==================== 更新记录 ====================

    def update_prices(self, price_data: Dict[str, float]) -> int:
        """
        批量更新股票价格

        Args:
            price_data: {symbol: price, ...}

        Returns:
            更新的记录数
        """
        db = self._get_db()
        try:
            # 获取所有活跃记录
            active_records = (
                db.query(RecommendationRecord)
                .filter(RecommendationRecord.status == "active")
                .all()
            )

            updated = 0
            now = datetime.now()

            for record in active_records:
                if record.symbol in price_data:
                    new_price = price_data[record.symbol]
                    record.current_price = new_price
                    record.price_updated_at = now
                    record.calculate_profit()
                    record.calculate_holding_days()
                    updated += 1

            db.commit()
            logger.info(f"更新价格: {updated}/{len(active_records)} 条记录")
            return updated

        except Exception as e:
            logger.error(f"更新价格失败: {e}")
            db.rollback()
            return 0
        finally:
            db.close()

    def close_position(
        self, record_id: int, close_price: float, close_reason: str = "manual"
    ) -> bool:
        """
        平仓（关闭持仓）

        Args:
            record_id: 记录ID
            close_price: 平仓价格
            close_reason: 平仓原因 (manual/profit/loss/expired)

        Returns:
            是否成功
        """
        db = self._get_db()
        try:
            record = (
                db.query(RecommendationRecord)
                .filter(RecommendationRecord.id == record_id)
                .first()
            )

            if not record:
                logger.warning(f"记录不存在: {record_id}")
                return False

            if record.status == "closed":
                logger.warning(f"记录已平仓: {record_id}")
                return False

            record.status = "closed"
            record.close_price = close_price
            record.close_date = datetime.now()
            record.close_reason = close_reason
            record.current_price = close_price
            record.calculate_profit()
            record.calculate_holding_days()

            db.commit()
            logger.info(
                f"平仓成功: {record.symbol} @ {close_price}, 盈亏: {record.profit_percent}%"
            )
            return True

        except Exception as e:
            logger.error(f"平仓失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    # ==================== 获取活跃股票列表 ====================

    def get_active_symbols(self) -> List[str]:
        """获取所有活跃持仓的股票代码"""
        db = self._get_db()
        try:
            records = (
                db.query(RecommendationRecord.symbol)
                .filter(RecommendationRecord.status == "active")
                .distinct()
                .all()
            )

            return [r[0] for r in records]

        except Exception as e:
            logger.error(f"获取活跃股票列表失败: {e}")
            return []
        finally:
            db.close()

    def get_performance_curve(self, period: str = "30d") -> Dict[str, Any]:
        """
        获取收益曲线数据（按日期汇总）

        Args:
            period: 时间周期 (7d/30d/90d/all)

        Returns:
            {
                dates: ["2025-01-01", ...],
                daily_returns: [0.5, -0.2, ...],
                cumulative_returns: [0.5, 0.3, ...],
                daily_count: [3, 2, ...],
                period: str
            }
        """
        db = self._get_db()
        try:
            # 时间范围
            if period == "all":
                days = 365
            else:
                days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)

            start_date = datetime.now() - timedelta(days=days)

            # 获取时间范围内的所有记录
            records = (
                db.query(RecommendationRecord)
                .filter(RecommendationRecord.entry_date >= start_date)
                .order_by(RecommendationRecord.entry_date)
                .all()
            )

            if not records:
                return {
                    "dates": [],
                    "daily_returns": [],
                    "cumulative_returns": [],
                    "daily_count": [],
                    "period": period,
                }

            # 按日期分组计算
            from collections import defaultdict
            daily_data = defaultdict(lambda: {"returns": [], "count": 0})

            for record in records:
                date_str = record.entry_date.strftime("%Y-%m-%d")
                profit = record.profit_percent or 0
                daily_data[date_str]["returns"].append(profit)
                daily_data[date_str]["count"] += 1

            # 排序并计算
            sorted_dates = sorted(daily_data.keys())
            dates = []
            daily_returns = []
            cumulative_returns = []
            daily_count = []
            cumulative = 0

            for date_str in sorted_dates:
                data = daily_data[date_str]
                # 当日平均收益
                avg_return = sum(data["returns"]) / len(data["returns"]) if data["returns"] else 0
                cumulative += avg_return

                dates.append(date_str)
                daily_returns.append(round(avg_return, 2))
                cumulative_returns.append(round(cumulative, 2))
                daily_count.append(data["count"])

            return {
                "dates": dates,
                "daily_returns": daily_returns,
                "cumulative_returns": cumulative_returns,
                "daily_count": daily_count,
                "period": period,
            }

        except Exception as e:
            logger.error(f"获取收益曲线失败: {e}")
            return {
                "dates": [],
                "daily_returns": [],
                "cumulative_returns": [],
                "daily_count": [],
                "period": period,
            }
        finally:
            db.close()


# 全局单例
backtest_service = BacktestService()
