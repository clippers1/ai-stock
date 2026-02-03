/**
 * AI推荐页面 - 首页展示推荐股票列表
 */
import { useState, useEffect } from 'react';
import { getRecommendations, getSectors } from '../services/api';
import './Recommendations.css';

// Lucide 图标组件
const BellIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
    </svg>
);

const TrendingUpIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
        <polyline points="16 7 22 7 22 13" />
    </svg>
);

const TrendingDownIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 17 13.5 8.5 8.5 13.5 2 7" />
        <polyline points="16 17 22 17 22 11" />
    </svg>
);

const SparklesIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
    </svg>
);

export default function Recommendations({ onSelectStock }) {
    const [stocks, setStocks] = useState([]);
    const [sectors, setSectors] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            setLoading(true);
            const [stocksData, sectorsData] = await Promise.all([
                getRecommendations(),
                getSectors()
            ]);
            setStocks(stocksData);
            setSectors(sectorsData);
            setLoading(false);
        }
        fetchData();
    }, []);

    const getRecommendationLabel = (rec) => {
        const labels = {
            '买入': { text: 'AI 买入', className: 'label-buy' },
            '持有': { text: '持有', className: 'label-hold' },
            '卖出': { text: '卖出', className: 'label-sell' }
        };
        return labels[rec] || { text: rec, className: 'label-hold' };
    };

    if (loading) {
        return (
            <div className="page-container">
                <div className="loading">
                    <div className="loading-spinner"></div>
                    <span>加载中...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="page-container recommendations-page">
            {/* 顶部栏 */}
            <header className="page-header">
                <div className="header-content">
                    <h1 className="app-title">AI Stock</h1>
                    <button className="icon-button" aria-label="通知">
                        <BellIcon />
                        <span className="notification-dot"></span>
                    </button>
                </div>
            </header>

            {/* 主内容 */}
            <main className="page-content">
                {/* 今日推荐 */}
                <section className="section">
                    <div className="section-header">
                        <h2 className="section-title">
                            <SparklesIcon /> 今日AI推荐
                        </h2>
                        <span className="section-badge">{stocks.length}只</span>
                    </div>

                    <div className="stock-list">
                        {stocks.map((stock) => {
                            const isPositive = stock.change >= 0;
                            const label = getRecommendationLabel(stock.recommendation);

                            return (
                                <button
                                    key={stock.symbol}
                                    className="stock-card"
                                    onClick={() => onSelectStock(stock.symbol)}
                                >
                                    <div className="stock-main">
                                        <div className="stock-info">
                                            <span className="stock-symbol">{stock.symbol}</span>
                                            <span className="stock-name">{stock.name}</span>
                                        </div>
                                        <div className="stock-price">
                                            <span className="price">¥{stock.price.toFixed(2)}</span>
                                            <span className={`change ${isPositive ? 'positive' : 'negative'}`}>
                                                {isPositive ? <TrendingUpIcon /> : <TrendingDownIcon />}
                                                {isPositive ? '+' : ''}{stock.change_percent.toFixed(2)}%
                                            </span>
                                        </div>
                                    </div>
                                    <div className="stock-meta">
                                        <span className={`recommendation-label ${label.className}`}>
                                            {label.text}
                                        </span>
                                        <span className="ai-score">
                                            AI评分 <strong>{stock.ai_score}</strong>
                                        </span>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                </section>

                {/* 热门板块 */}
                <section className="section">
                    <h2 className="section-title">热门板块</h2>
                    <div className="sectors-grid">
                        {sectors.map((sector) => (
                            <button key={sector.name} className="sector-chip">
                                <span className="sector-name">{sector.name}</span>
                                <span className={`sector-change ${sector.change >= 0 ? 'positive' : 'negative'}`}>
                                    {sector.change >= 0 ? '+' : ''}{sector.change}%
                                </span>
                                {sector.hot && <span className="hot-badge">热</span>}
                            </button>
                        ))}
                    </div>
                </section>
            </main>
        </div>
    );
}
