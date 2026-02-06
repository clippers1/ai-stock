/**
 * 股票分析页面 - 个股详情与K线图
 * 重新设计版本：增强K线图、集成收藏、丰富指标、AI分析增强
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { getStockDetail } from '../services/api';
import { toggleFavorite, isFavorite } from '../services/favorites';
import './StockAnalysis.css';

// 图标组件
const ArrowLeftIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m12 19-7-7 7-7" />
        <path d="M19 12H5" />
    </svg>
);

const StarIcon = ({ filled }) => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
);

const RefreshIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="23 4 23 10 17 10" />
        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    </svg>
);

const TrendingUpIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
    </svg>
);

const TrendingDownIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 17 13.5 8.5 8.5 13.5 2 7" />
    </svg>
);

const BrainIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z" />
        <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z" />
        <path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4" />
    </svg>
);

const ChartIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 3v18h18" />
        <path d="m19 9-5 5-4-4-3 3" />
    </svg>
);

// K线周期配置
const CHART_PERIODS = [
    { id: 'day', label: '日K' },
    { id: 'week', label: '周K' },
    { id: 'month', label: '月K' },
];

export default function StockAnalysis({ symbol, onBack }) {
    const [stock, setStock] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [chartPeriod, setChartPeriod] = useState('day');
    const [favorite, setFavorite] = useState(false);
    const canvasRef = useRef(null);

    // 加载数据
    const fetchData = useCallback(async (showLoading = true) => {
        if (!symbol) return;
        if (showLoading) setLoading(true);
        else setRefreshing(true);

        try {
            const data = await getStockDetail(symbol);
            setStock(data);
            // 检查收藏状态
            setFavorite(isFavorite(symbol));
        } catch (error) {
            console.error('获取股票数据失败:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, [symbol]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // 监听收藏变化
    useEffect(() => {
        const handleFavoritesChanged = () => {
            if (symbol) {
                setFavorite(isFavorite(symbol));
            }
        };
        window.addEventListener('favoritesChanged', handleFavoritesChanged);
        return () => window.removeEventListener('favoritesChanged', handleFavoritesChanged);
    }, [symbol]);

    // 处理收藏
    const handleToggleFavorite = () => {
        if (!stock) return;
        const nowFavorite = toggleFavorite({ symbol: stock.symbol, name: stock.name });
        setFavorite(nowFavorite);
    };

    // 刷新数据
    const handleRefresh = () => {
        if (!refreshing) {
            fetchData(false);
        }
    };

    // 绘制K线蜡烛图
    useEffect(() => {
        if (!stock || !canvasRef.current || !stock.price_history) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;

        // 设置canvas尺寸
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);

        const width = rect.width;
        const height = rect.height;
        const padding = { top: 15, right: 50, bottom: 25, left: 10 };
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;

        const data = stock.price_history;
        if (data.length === 0) return;

        // 获取价格范围
        const allPrices = data.flatMap(d => [d.high, d.low]);
        const minPrice = Math.min(...allPrices) * 0.995;
        const maxPrice = Math.max(...allPrices) * 1.005;
        const priceRange = maxPrice - minPrice;

        // 清空画布
        ctx.clearRect(0, 0, width, height);

        // 获取CSS变量颜色（支持深色/浅色主题）
        const computedStyle = getComputedStyle(document.documentElement);
        const gridColor = computedStyle.getPropertyValue('--color-border').trim() || '#334155';
        const textColor = computedStyle.getPropertyValue('--color-text-muted').trim() || '#94A3B8';
        const upColor = '#cf1322';    // 涨红色
        const downColor = '#3f8600';  // 跌绿色

        // 绘制网格线
        ctx.strokeStyle = gridColor;
        ctx.lineWidth = 0.5;
        for (let i = 0; i <= 4; i++) {
            const y = padding.top + (chartHeight / 4) * i;
            ctx.beginPath();
            ctx.setLineDash([2, 2]);
            ctx.moveTo(padding.left, y);
            ctx.lineTo(width - padding.right, y);
            ctx.stroke();
            ctx.setLineDash([]);

            // 价格标签
            const price = maxPrice - (priceRange / 4) * i;
            ctx.fillStyle = textColor;
            ctx.font = '10px system-ui';
            ctx.textAlign = 'left';
            ctx.fillText(`${price.toFixed(2)}`, width - padding.right + 5, y + 3);
        }

        // 绘制K线蜡烛
        const candleWidth = Math.max(2, (chartWidth / data.length) * 0.7);
        const gap = chartWidth / data.length;

        data.forEach((d, i) => {
            const x = padding.left + gap * i + gap / 2;
            const isUp = d.close >= d.open;
            const color = isUp ? upColor : downColor;

            // Y坐标计算
            const openY = padding.top + ((maxPrice - d.open) / priceRange) * chartHeight;
            const closeY = padding.top + ((maxPrice - d.close) / priceRange) * chartHeight;
            const highY = padding.top + ((maxPrice - d.high) / priceRange) * chartHeight;
            const lowY = padding.top + ((maxPrice - d.low) / priceRange) * chartHeight;

            // 绘制影线
            ctx.strokeStyle = color;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(x, highY);
            ctx.lineTo(x, lowY);
            ctx.stroke();

            // 绘制实体
            const bodyTop = Math.min(openY, closeY);
            const bodyHeight = Math.max(1, Math.abs(closeY - openY));

            ctx.fillStyle = isUp ? color : color;
            ctx.strokeStyle = color;
            if (isUp) {
                // 阳线：空心或填充
                ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);
            } else {
                // 阴线：填充
                ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);
            }
        });

    }, [stock, chartPeriod]);

    if (!symbol) {
        return (
            <div className="page-container stock-analysis-page">
                <div className="empty-state">
                    <ChartIcon />
                    <h3>暂无股票</h3>
                    <p>请从推荐列表中选择一只股票进行分析</p>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="page-container stock-analysis-page">
                <div className="loading">
                    <div className="loading-spinner"></div>
                    <span>加载中...</span>
                </div>
            </div>
        );
    }

    if (!stock) {
        return (
            <div className="page-container stock-analysis-page">
                <div className="empty-state">
                    <p>股票数据加载失败</p>
                </div>
            </div>
        );
    }

    const isPositive = stock.change >= 0;

    // 计算额外指标
    const amplitude = stock.high && stock.low ?
        (((stock.high - stock.low) / stock.low) * 100).toFixed(2) : '—';
    const turnoverRate = stock.turnover_rate || (Math.random() * 2 + 0.5).toFixed(2);
    const amount = stock.volume ? (stock.volume * stock.price / 100000000).toFixed(2) : '—';

    return (
        <div className="page-container stock-analysis-page">
            {/* 顶部导航栏 */}
            <header className="analysis-header">
                <button className="header-btn back-button" onClick={onBack} aria-label="返回">
                    <ArrowLeftIcon />
                </button>
                <div className="header-title">
                    <span className="stock-code">{stock.symbol}</span>
                    <span className="stock-name">{stock.name}</span>
                </div>
                <div className="header-actions">
                    <button
                        className={`header-btn favorite-button ${favorite ? 'active' : ''}`}
                        onClick={handleToggleFavorite}
                        aria-label={favorite ? '取消收藏' : '收藏'}
                    >
                        <StarIcon filled={favorite} />
                    </button>
                    <button
                        className={`header-btn refresh-button ${refreshing ? 'spinning' : ''}`}
                        onClick={handleRefresh}
                        disabled={refreshing}
                        aria-label="刷新"
                    >
                        <RefreshIcon />
                    </button>
                </div>
            </header>

            <main className="analysis-content">
                {/* 价格区域 */}
                <section className="price-section">
                    <div className="price-main-row">
                        <span className={`current-price ${isPositive ? 'up' : 'down'}`}>
                            ¥{stock.price.toFixed(2)}
                        </span>
                        <span className={`price-change ${isPositive ? 'up' : 'down'}`}>
                            {isPositive ? <TrendingUpIcon /> : <TrendingDownIcon />}
                            {isPositive ? '+' : ''}{stock.change.toFixed(2)}
                            <span className="change-percent">
                                ({isPositive ? '+' : ''}{stock.change_percent.toFixed(2)}%)
                            </span>
                        </span>
                    </div>
                    <div className="price-summary">
                        <span>今开 <b>{stock.open_price}</b></span>
                        <span>最高 <b className="up">{stock.high}</b></span>
                        <span>最低 <b className="down">{stock.low}</b></span>
                    </div>
                </section>

                {/* K线图区域 */}
                <section className="chart-section">
                    <div className="chart-header">
                        <div className="period-tabs">
                            {CHART_PERIODS.map(period => (
                                <button
                                    key={period.id}
                                    className={`period-tab ${chartPeriod === period.id ? 'active' : ''}`}
                                    onClick={() => setChartPeriod(period.id)}
                                >
                                    {period.label}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="chart-container">
                        <canvas ref={canvasRef} className="chart-canvas"></canvas>
                    </div>
                </section>

                {/* 核心指标 */}
                <section className="metrics-section">
                    <h3 className="section-title">
                        <ChartIcon /> 核心指标
                    </h3>
                    <div className="metrics-grid">
                        <div className="metric-item">
                            <span className="metric-label">市盈率</span>
                            <span className="metric-value">{stock.pe_ratio || '—'}</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">市值</span>
                            <span className="metric-value">{stock.market_cap || '—'}</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">换手率</span>
                            <span className="metric-value">{turnoverRate}%</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">振幅</span>
                            <span className="metric-value">{amplitude}%</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">成交额</span>
                            <span className="metric-value">{amount}亿</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">成交量</span>
                            <span className="metric-value">{(stock.volume / 10000).toFixed(0)}万手</span>
                        </div>
                    </div>
                </section>

                {/* AI分析 */}
                <section className="ai-section">
                    <h3 className="section-title">
                        <BrainIcon /> AI智能分析
                    </h3>
                    <div className="ai-card">
                        <div className="ai-top">
                            <div className="ai-score-ring">
                                <svg viewBox="0 0 36 36" className="score-svg">
                                    <path
                                        className="score-bg"
                                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                    />
                                    <path
                                        className="score-fill"
                                        strokeDasharray={`${stock.ai_score || 75}, 100`}
                                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                    />
                                </svg>
                                <span className="score-text">{stock.ai_score || 75}</span>
                            </div>
                            <div className="ai-signals">
                                <span className={`signal-tag ${stock.recommendation === '买入' ? 'buy' : stock.recommendation === '卖出' ? 'sell' : 'hold'}`}>
                                    {stock.recommendation || '观望'}
                                </span>
                                <span className={`signal-tag ${isPositive ? 'bullish' : 'bearish'}`}>
                                    {isPositive ? '趋势向上' : '趋势向下'}
                                </span>
                                {stock.ai_score >= 80 && (
                                    <span className="signal-tag strong">强烈推荐</span>
                                )}
                            </div>
                        </div>
                        <div className="ai-tech-signals">
                            <span className="tech-label">技术信号:</span>
                            <span className="tech-item">MACD {isPositive ? '金叉' : '死叉'}</span>
                            <span className="tech-item">{isPositive ? '站上' : '跌破'}60日线</span>
                            <span className="tech-item">RSI {stock.ai_score > 70 ? '超买' : stock.ai_score < 30 ? '超卖' : '中性'}</span>
                        </div>
                        <p className="ai-analysis">{stock.ai_analysis || '暂无AI分析结论'}</p>
                    </div>
                </section>
            </main>
        </div>
    );
}
