/**
 * AI回测页面 - 复盘AI预测后的股票表现
 */
import { useState, useEffect } from 'react';
import { getBacktestRecords, getBacktestSummary } from '../services/api';
import './AIBacktest.css';

// 图标组件
const FilterIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </svg>
);

const TrendUpIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
        <polyline points="16 7 22 7 22 13" />
    </svg>
);

const TrendDownIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 17 13.5 8.5 8.5 13.5 2 7" />
        <polyline points="16 17 22 17 22 11" />
    </svg>
);

const HistoryIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
        <path d="M3 3v5h5" />
        <path d="M12 7v5l4 2" />
    </svg>
);

// 时间筛选选项
const TIME_FILTERS = [
    { id: '7d', label: '近7日' },
    { id: '30d', label: '近30日' },
    { id: '90d', label: '近3月' },
    { id: 'all', label: '全部' },
];

export default function AIBacktest({ onSelectStock }) {
    const [records, setRecords] = useState([]);
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(true);
    const [timeFilter, setTimeFilter] = useState('30d');

    useEffect(() => {
        async function fetchData() {
            setLoading(true);
            try {
                const [recordsData, summaryData] = await Promise.all([
                    getBacktestRecords(timeFilter),
                    getBacktestSummary(timeFilter)
                ]);
                // 处理records数据（可能是嵌套格式）
                const recordsList = recordsData?.records || recordsData || [];
                setRecords(recordsList);
                setSummary(summaryData);
            } catch (error) {
                console.error('获取回测数据失败:', error);
                setRecords([]);
                setSummary(null);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, [timeFilter]);

    // 格式化日期
    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    };

    // 获取推荐类型样式
    const getRecommendationStyle = (type) => {
        const styles = {
            '买入': 'label-buy',
            '持有': 'label-hold',
            '卖出': 'label-sell'
        };
        return styles[type] || 'label-hold';
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
        <div className="page-container backtest-page">
            {/* 顶部栏 */}
            <header className="page-header">
                <div className="header-content">
                    <div className="header-left">
                        <h1 className="page-title">AI回测</h1>
                        <span className="header-subtitle">AI智能回测结果，仅供参考</span>
                    </div>
                    <button className="icon-button" aria-label="筛选">
                        <FilterIcon />
                    </button>
                </div>
            </header>

            {/* 主内容 */}
            <main className="page-content">
                {/* 统计摘要卡片 */}
                {summary && (
                    <section className="summary-section">
                        <div className="summary-cards">
                            <div className="summary-card summary-profit">
                                <span className="summary-value positive">
                                    {(summary.total_return ?? 0) >= 0 ? '+' : ''}{(summary.total_return ?? 0).toFixed(1)}%
                                </span>
                                <span className="summary-label">
                                    <TrendUpIcon /> 总收益率
                                </span>
                            </div>
                            <div className="summary-card summary-winrate">
                                <span className="summary-value">{summary.win_rate ?? 0}%</span>
                                <span className="summary-label">胜率</span>
                            </div>
                            <div className="summary-card summary-count">
                                <span className="summary-value">{summary.total_recommendations ?? 0}</span>
                                <span className="summary-label">推荐次数</span>
                            </div>
                        </div>
                    </section>
                )}

                {/* 时间筛选 */}
                <section className="filter-section">
                    <div className="time-filters">
                        {TIME_FILTERS.map((filter) => (
                            <button
                                key={filter.id}
                                className={`filter-tab ${timeFilter === filter.id ? 'active' : ''}`}
                                onClick={() => setTimeFilter(filter.id)}
                            >
                                {filter.label}
                            </button>
                        ))}
                    </div>
                </section>

                {/* 回测记录列表 */}
                <section className="records-section">
                    <div className="records-list">
                        {records.length === 0 ? (
                            <div className="empty-state">
                                <HistoryIcon />
                                <span>暂无回测记录</span>
                            </div>
                        ) : (
                            records.map((record) => {
                                const profitPercent = record.profit_percent ?? 0;
                                const isProfit = profitPercent >= 0;
                                const entryPrice = record.entry_price ?? 0;
                                const currentPrice = record.current_price ?? 0;
                                return (
                                    <button
                                        key={record.id}
                                        className="record-card"
                                        onClick={() => onSelectStock && onSelectStock(record.symbol)}
                                    >
                                        {/* 股票信息行 */}
                                        <div className="record-header">
                                            <div className="record-stock">
                                                <span className="stock-symbol">{record.symbol}</span>
                                                <span className="stock-name">{record.name}</span>
                                            </div>
                                            <span className={`profit-badge ${isProfit ? 'positive' : 'negative'}`}>
                                                {isProfit ? <TrendUpIcon /> : <TrendDownIcon />}
                                                {isProfit ? '+' : ''}{profitPercent.toFixed(1)}%
                                            </span>
                                        </div>

                                        {/* 推荐标签和日期 */}
                                        <div className="record-meta">
                                            <span className={`recommendation-label ${getRecommendationStyle(record.recommendation_label)}`}>
                                                AI{record.recommendation_label}
                                            </span>
                                            <span className="record-date">
                                                推荐日期: {record.recommendation_date}
                                            </span>
                                        </div>

                                        {/* 价格信息 */}
                                        <div className="record-prices">
                                            <div className="price-item">
                                                <span className="price-label">买入价</span>
                                                <span className="price-value">¥{entryPrice.toFixed(2)}</span>
                                            </div>
                                            <div className="price-arrow">→</div>
                                            <div className="price-item">
                                                <span className="price-label">现价</span>
                                                <span className={`price-value ${isProfit ? 'positive' : 'negative'}`}>
                                                    ¥{currentPrice.toFixed(2)}
                                                </span>
                                            </div>
                                        </div>

                                        {/* 迷你趋势图 */}
                                        <div className="mini-chart">
                                            <svg viewBox="0 0 100 30" className={isProfit ? 'chart-up' : 'chart-down'}>
                                                <polyline
                                                    fill="none"
                                                    strokeWidth="2"
                                                    points={record.trendData || (isProfit ? "0,25 20,20 40,22 60,15 80,10 100,5" : "0,5 20,10 40,8 60,15 80,20 100,25")}
                                                />
                                            </svg>
                                        </div>
                                    </button>
                                );
                            })
                        )}
                    </div>
                </section>
            </main>
        </div>
    );
}
