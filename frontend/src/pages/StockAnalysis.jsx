/**
 * 股票分析页面 - 个股详情与K线图
 */
import { useState, useEffect, useRef } from 'react';
import { getStockDetail } from '../services/api';
import './StockAnalysis.css';

// 图标组件
const ArrowLeftIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m12 19-7-7 7-7" />
        <path d="M19 12H5" />
    </svg>
);

const StarIcon = ({ filled }) => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
);

const TrendingUpIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
        <polyline points="16 7 22 7 22 13" />
    </svg>
);

const TrendingDownIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 17 13.5 8.5 8.5 13.5 2 7" />
        <polyline points="16 17 22 17 22 11" />
    </svg>
);

const BrainIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z" />
        <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z" />
        <path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4" />
        <path d="M17.599 6.5a3 3 0 0 0 .399-1.375" />
        <path d="M6.003 5.125A3 3 0 0 0 6.401 6.5" />
        <path d="M3.477 10.896a4 4 0 0 1 .585-.396" />
        <path d="M19.938 10.5a4 4 0 0 1 .585.396" />
        <path d="M6 18a4 4 0 0 1-1.967-.516" />
        <path d="M19.967 17.484A4 4 0 0 1 18 18" />
    </svg>
);

const timeRanges = ['1D', '1W', '1M', '3M', '1Y'];

export default function StockAnalysis({ symbol, onBack }) {
    const [stock, setStock] = useState(null);
    const [loading, setLoading] = useState(true);
    const [timeRange, setTimeRange] = useState('1M');
    const [favorite, setFavorite] = useState(false);
    const canvasRef = useRef(null);

    useEffect(() => {
        async function fetchData() {
            if (!symbol) return;
            setLoading(true);
            const data = await getStockDetail(symbol);
            setStock(data);
            setLoading(false);
        }
        fetchData();
    }, [symbol]);

    // 绘制简易K线图
    useEffect(() => {
        if (!stock || !canvasRef.current) return;

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
        const padding = { top: 20, right: 10, bottom: 30, left: 10 };
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;

        // 获取价格范围
        const prices = stock.price_history.map(d => d.close);
        const minPrice = Math.min(...prices) * 0.98;
        const maxPrice = Math.max(...prices) * 1.02;

        // 清空画布
        ctx.clearRect(0, 0, width, height);

        // 绘制网格线
        ctx.strokeStyle = '#334155';
        ctx.lineWidth = 0.5;
        for (let i = 0; i <= 4; i++) {
            const y = padding.top + (chartHeight / 4) * i;
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(width - padding.right, y);
            ctx.stroke();
        }

        // 绘制价格线
        ctx.beginPath();
        ctx.strokeStyle = stock.change >= 0 ? '#10B981' : '#EF4444';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        prices.forEach((price, i) => {
            const x = padding.left + (chartWidth / (prices.length - 1)) * i;
            const y = padding.top + chartHeight - ((price - minPrice) / (maxPrice - minPrice)) * chartHeight;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();

        // 绘制渐变填充
        const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
        gradient.addColorStop(0, stock.change >= 0 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)');
        gradient.addColorStop(1, 'rgba(15, 23, 42, 0)');

        ctx.lineTo(width - padding.right, height - padding.bottom);
        ctx.lineTo(padding.left, height - padding.bottom);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();

        // 绘制当前价格点
        const lastX = width - padding.right;
        const lastY = padding.top + chartHeight - ((prices[prices.length - 1] - minPrice) / (maxPrice - minPrice)) * chartHeight;

        ctx.beginPath();
        ctx.arc(lastX, lastY, 5, 0, Math.PI * 2);
        ctx.fillStyle = stock.change >= 0 ? '#10B981' : '#EF4444';
        ctx.fill();

        // 价格标签
        ctx.fillStyle = '#94A3B8';
        ctx.font = '11px IBM Plex Sans';
        ctx.textAlign = 'left';
        ctx.fillText(`¥${maxPrice.toFixed(0)}`, padding.left, padding.top - 5);
        ctx.fillText(`¥${minPrice.toFixed(0)}`, padding.left, height - padding.bottom + 15);

    }, [stock, timeRange]);

    if (!symbol) {
        return (
            <div className="page-container stock-analysis-page">
                <div className="empty-state">
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

    const isPositive = stock.change >= 0;

    return (
        <div className="page-container stock-analysis-page">
            {/* 顶部栏 */}
            <header className="analysis-header">
                <button className="back-button" onClick={onBack} aria-label="返回">
                    <ArrowLeftIcon />
                </button>
                <h1 className="stock-title">{stock.symbol}</h1>
                <button
                    className={`favorite-button ${favorite ? 'active' : ''}`}
                    onClick={() => setFavorite(!favorite)}
                    aria-label={favorite ? '取消收藏' : '收藏'}
                >
                    <StarIcon filled={favorite} />
                </button>
            </header>

            <main className="analysis-content">
                {/* 价格区域 */}
                <section className="price-section">
                    <div className="price-info">
                        <span className="company-name">{stock.name}</span>
                        <div className="price-main">
                            <span className="current-price">¥{stock.price.toFixed(2)}</span>
                            <span className={`price-change ${isPositive ? 'positive' : 'negative'}`}>
                                {isPositive ? <TrendingUpIcon /> : <TrendingDownIcon />}
                                {isPositive ? '+' : ''}{stock.change.toFixed(2)} ({isPositive ? '+' : ''}{stock.change_percent.toFixed(2)}%)
                            </span>
                        </div>
                    </div>
                </section>

                {/* K线图 */}
                <section className="chart-section">
                    <canvas ref={canvasRef} className="chart-canvas"></canvas>
                    <div className="time-range-buttons">
                        {timeRanges.map(range => (
                            <button
                                key={range}
                                className={`time-button ${timeRange === range ? 'active' : ''}`}
                                onClick={() => setTimeRange(range)}
                            >
                                {range}
                            </button>
                        ))}
                    </div>
                </section>

                {/* 关键指标 */}
                <section className="metrics-section">
                    <div className="metrics-grid">
                        <div className="metric-item">
                            <span className="metric-label">开盘价</span>
                            <span className="metric-value">¥{stock.open_price}</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">最高</span>
                            <span className="metric-value positive">¥{stock.high}</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">最低</span>
                            <span className="metric-value negative">¥{stock.low}</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">成交量</span>
                            <span className="metric-value">{(stock.volume / 1000000).toFixed(1)}M</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">市值</span>
                            <span className="metric-value">{stock.market_cap}</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">市盈率</span>
                            <span className="metric-value">{stock.pe_ratio}</span>
                        </div>
                    </div>
                </section>

                {/* AI分析 */}
                <section className="ai-section">
                    <div className="ai-header">
                        <BrainIcon />
                        <h2>AI分析观点</h2>
                        <span className={`ai-badge ${stock.recommendation === '买入' ? 'buy' : stock.recommendation === '卖出' ? 'sell' : 'hold'}`}>
                            {stock.recommendation}
                        </span>
                    </div>
                    <div className="ai-card">
                        <div className="ai-score-ring">
                            <svg viewBox="0 0 36 36" className="score-svg">
                                <path
                                    className="score-bg"
                                    d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                                />
                                <path
                                    className="score-fill"
                                    strokeDasharray={`${stock.ai_score}, 100`}
                                    d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                                />
                            </svg>
                            <span className="score-text">{stock.ai_score}</span>
                        </div>
                        <p className="ai-analysis">{stock.ai_analysis}</p>
                    </div>
                </section>
            </main>
        </div>
    );
}
