"""
数据库模型定义
使用 SQLAlchemy ORM
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 数据库配置
DATABASE_URL = "sqlite:///./data/ai_stock.db"

# 创建引擎
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},  # SQLite 需要这个参数
    echo=False  # 设为True可以看到SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


class RecommendationRecord(Base):
    """
    AI推荐记录表
    记录每次AI发出的推荐，用于回测分析
    """
    __tablename__ = "recommendation_records"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 股票信息
    symbol = Column(String(10), nullable=False, index=True)  # 股票代码
    name = Column(String(50), nullable=False)                 # 股票名称
    
    # 推荐信息
    category = Column(String(20), nullable=False, index=True)  # 推荐类别: shortterm/trend/value
    recommendation = Column(String(20), nullable=False)        # 推荐操作: 买入/增持/持有/突破/超跌等
    ai_score = Column(Integer, default=50)                     # AI评分 0-100
    signal = Column(String(100))                               # 信号说明
    reason = Column(Text)                                      # 推荐理由
    
    # 入场信息
    entry_price = Column(Float, nullable=False)               # 推荐时价格
    entry_date = Column(DateTime, nullable=False, default=datetime.now)  # 推荐日期
    
    # 当前状态（定时更新）
    current_price = Column(Float)                             # 最新价格
    price_updated_at = Column(DateTime)                       # 价格更新时间
    
    # 持仓状态
    status = Column(String(20), default="active", index=True)  # active/closed
    
    # 平仓信息（如果已平仓）
    close_price = Column(Float)                               # 平仓价格
    close_date = Column(DateTime)                             # 平仓日期
    close_reason = Column(String(50))                         # 平仓原因: profit/loss/manual/expired
    
    # 计算字段（存储以便快速查询）
    profit_percent = Column(Float, default=0)                 # 盈亏百分比
    holding_days = Column(Integer, default=0)                 # 持有天数
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Recommendation {self.symbol} {self.name} {self.category} {self.status}>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "category": self.category,
            "recommendation": self.recommendation,
            "recommendation_label": self.recommendation,  # 兼容前端
            "recommendation_type": self.category,         # 兼容前端
            "ai_score": self.ai_score,
            "signal": self.signal,
            "reason": self.reason,
            "entry_price": self.entry_price,
            "entry_date": self.entry_date.strftime("%Y-%m-%d") if self.entry_date else None,
            "recommendation_date": self.entry_date.strftime("%Y-%m-%d") if self.entry_date else None,
            "current_price": self.current_price or self.entry_price,
            "price_updated_at": self.price_updated_at.isoformat() if self.price_updated_at else None,
            "status": self.status,
            "close_price": self.close_price,
            "close_date": self.close_date.strftime("%Y-%m-%d") if self.close_date else None,
            "close_reason": self.close_reason,
            "profit_percent": self.profit_percent or 0,
            "holding_days": self.holding_days or 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def calculate_profit(self):
        """计算盈亏百分比"""
        if self.entry_price and self.entry_price > 0:
            price = self.close_price if self.status == "closed" else self.current_price
            if price:
                self.profit_percent = round((price - self.entry_price) / self.entry_price * 100, 2)
        return self.profit_percent
    
    def calculate_holding_days(self):
        """计算持有天数"""
        if self.entry_date:
            end_date = self.close_date if self.status == "closed" else datetime.now()
            self.holding_days = (end_date - self.entry_date).days
        return self.holding_days


def init_db():
    """初始化数据库，创建所有表"""
    import os
    # 确保 data 目录存在
    os.makedirs("data", exist_ok=True)
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("[Database] ✅ 数据库初始化完成")


def get_db():
    """获取数据库会话（用于依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
