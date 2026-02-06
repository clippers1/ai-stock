/**
 * AI回测页面 - 复盘AI预测后的股票表现
 */
import { useState, useEffect } from 'react';
import { getBacktestRecords, getBacktestSummary, closePosition, getPerformanceCurve } from '../services/api';
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

const CloseIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
);

// 时间筛选选项
const TIME_FILTERS = [
    { id: '7d', label: '近7日' },
    { id: '30d', label: '近30日' },
    { id: '90d', label: '近3月' },
    { id: 'all', label: '全部' },
];

// 状态筛选选项
const STATUS_FILTERS = [
    { id: 'all', label: '全部' },
    { id: 'active', label: '持仓中' },
    { id: 'closed', label: '已平仓' },
];

export default function AIBacktest({ onSelectStock }) {
    const [records, setRecords] = useState([]);
    const [summary, setSummary] = useState(null);
    const [performanceData, setPerformanceData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [timeFilter, setTimeFilter] = useState('30d');
    const [statusFilter, setStatusFilter] = useState('all');
    const [closingId, setClosingId] = useState(null);
    const [showChart, setShowChart] = useState(true);

    // 获取数据
    const fetchData = async () => {
        setLoading(true);
        try {
            const status = statusFilter === 'all' ? null : statusFilter;
            const [recordsData, summaryData, perfData] = await Promise.all([
                getBacktestRecords(timeFilter, status),
                getBacktestSummary(timeFilter),
                getPerformanceCurve(timeFilter)
            ]);
            // 处理records数据（可能是嵌套格式）
            const recordsList = recordsData?.records || recordsData || [];
            setRecords(recordsList);
            setSummary(summaryData);
            setPerformanceData(perfData);
        } catch (error) {
            console.error('获取回测数据失败:', error);
            setRecords([]);
            setSummary(null);
            setPerformanceData(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [timeFilter, statusFilter]);

    // 处理平仓操作
    const handleClose = async (e, recordId) => {
        e.stopPropagation(); // 阻止冒泡，避免触发卡片点击

        if (!confirm('确定要平仓这条记录吗？')) return;

        setClosingId(recordId);
        try {
            const result = await closePosition(recordId);
            if (result.success) {
                // 刷新数据
                await fetchData();
            } else {
                alert('平仓失败：' + (result.message || '未知错误'));
            }
        } catch (error) {
            console.error('平仓失败:', error);
            alert('平仓失败，请稍后重试');
        } finally {
            setClosingId(null);
        }
    };

    // 获取推荐类型样式
    const getRecommendationStyle = (type) => {
        const styles = {
            '买入': 'label-buy',
            '增持': 'label-buy',
            '突破': 'label-buy',
            '持有': 'label-hold',
            '卖出': 'label-sell',
            '观望': 'label-sell'
        };
        return styles[type] || 'label-hold';
    };

    // 获取类别标签
    const getCategoryLabel = (category) => {
        const labels = {
            'shortterm': '短线',
            'trend': '趋势',
            'value': '价值'
        };
        return labels[category] || category;
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
                                <span className={`summary-value ${(summary.total_return ?? 0) >= 0 ? 'positive' : 'negative'}`}>
                                    {(summary.total_return ?? 0) >= 0 ? '+' : ''}{(summary.total_return ?? 0).toFixed(1)}%
                                </span>
                                <span className="summary-label">
                                    <TrendUpIcon /> 总收益率
                                </span>
                            </div>
                            <div className="summary-card summary-winrate">
                                <span className="summary-value">{(summary.win_rate ?? 0).toFixed(1)}%</span>
                                <span className="summary-label">胜率</span>
                            </div>
                            <div className="summary-card summary-count">
                                <span className="summary-value">{summary.total_recommendations ?? 0}</span>
                                <span className="summary-label">推荐次数</span>
                            </div>
                        </div>
                        {/* 额外统计信息 */}
                        <div className="summary-extra">
                            <span className="extra-item">
                                持仓: <strong>{summary.active_count ?? 0}</strong>
                            </span>
                            <span className="extra-item">
                                已平仓: <strong>{summary.closed_count ?? 0}</strong>
                            </span>
                            <span className="extra-item">
                                平均持有: <strong>{(summary.avg_holding_days ?? 0).toFixed(1)}天</strong>
                            </span>
                        </div>
                    </section>
                )}

                {/* 收益曲线图 */}
                {performanceData && performanceData.dates && performanceData.dates.length > 0 && (
                    <section className="chart-section">
                        <div className="chart-header">
                            <h3 className="chart-title">📊 收益曲线</h3>
                            <button
                                className="chart-toggle"
                                onClick={() => setShowChart(!showChart)}
                            >
                                {showChart ? '收起' : '展开'}
                            </button>
                        </div>
                        {showChart && (
                            <div className="performance-chart">
                                <svg viewBox={`0 0 ${Math.max(300, performanceData.dates.length * 15)} 120`} className="chart-svg">
                                    {/* 零线 */}
                                    <line
                                        x1="0"
                                        y1="60"
                                        x2={Math.max(300, performanceData.dates.length * 15)}
                                        y2="60"
                                        stroke="var(--color-border)"
                                        strokeDasharray="4,4"
                                    />
                                    {/* 累计收益曲线 */}
                                    {(() => {
                                        const data = performanceData.cumulative_returns;
                                        if (!data || data.length === 0) return null;

                                        const maxVal = Math.max(...data.map(Math.abs), 10);
                                        const scale = 50 / maxVal;
                                        const width = Math.max(300, data.length * 15);
                                        const xStep = width / (data.length - 1 || 1);

                                        const points = data.map((val, i) =>
                                            `${i * xStep},${60 - val * scale}`
                                        ).join(' ');

                                        const isPositive = data[data.length - 1] >= 0;

                                        return (
                                            <>
                                                {/* 填充区域 */}
                                                <polygon
                                                    points={`0,60 ${points} ${(data.length - 1) * xStep},60`}
                                                    fill={isPositive ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)'}
                                                />
                                                {/* 曲线 */}
                                                <polyline
                                                    fill="none"
                                                    stroke={isPositive ? 'var(--color-success)' : 'var(--color-danger)'}
                                                    strokeWidth="2"
                                                    points={points}
                                                />
                                                {/* 数据点 */}
                                                {data.map((val, i) => (
                                                    <circle
                                                        key={i}
                                                        cx={i * xStep}
                                                        cy={60 - val * scale}
                                                        r="3"
                                                        fill={val >= 0 ? 'var(--color-success)' : 'var(--color-danger)'}
                                                    />
                                                ))}
                                            </>
                                        );
                                    })()}
                                </svg>
                                {/* 图表标签 */}
                                <div className="chart-labels">
                                    <span className="chart-label-start">
                                        {performanceData.dates[0]?.slice(5)}
                                    </span>
                                    <span className={`chart-label-value ${(performanceData.cumulative_returns?.[performanceData.cumulative_returns.length - 1] ?? 0) >= 0 ? 'positive' : 'negative'}`}>
                                        累计: {(performanceData.cumulative_returns?.[performanceData.cumulative_returns.length - 1] ?? 0) >= 0 ? '+' : ''}
                                        {(performanceData.cumulative_returns?.[performanceData.cumulative_returns.length - 1] ?? 0).toFixed(1)}%
                                    </span>
                                    <span className="chart-label-end">
                                        {performanceData.dates[performanceData.dates.length - 1]?.slice(5)}
                                    </span>
                                </div>
                            </div>
                        )}
                    </section>
                )}

                {/* 筛选区域 */}
                <section className="filter-section">
                    <div className="filter-row">
                        {/* 时间筛选 */}
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
                    </div>
                    {/* 状态筛选 */}
                    <div className="status-filters">
                        {STATUS_FILTERS.map((filter) => (
                            <button
                                key={filter.id}
                                className={`status-tab ${statusFilter === filter.id ? 'active' : ''}`}
                                onClick={() => setStatusFilter(filter.id)}
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
                                const currentPrice = record.current_price ?? record.close_price ?? 0;
                                const isActive = record.status === 'active';
                                const isClosing = closingId === record.id;
                                return (
                                    <div
                                        key={record.id}
                                        className={`record-card ${!isActive ? 'closed' : ''}`}
                                    >
                                        {/* 股票信息行 */}
                                        <div className="record-header" onClick={() => onSelectStock && onSelectStock(record.symbol)}>
                                            <div className="record-stock">
                                                <span className="stock-symbol">{record.symbol}</span>
                                                <span className="stock-name">{record.name}</span>
                                                {!isActive && <span className="status-badge closed">已平仓</span>}
                                            </div>
                                            <span className={`profit-badge ${isProfit ? 'positive' : 'negative'}`}>
                                                {isProfit ? <TrendUpIcon /> : <TrendDownIcon />}
                                                {isProfit ? '+' : ''}{profitPercent.toFixed(1)}%
                                            </span>
                                        </div>

                                        {/* 推荐标签和日期 */}
                                        <div className="record-meta">
                                            <div className="meta-left">
                                                <span className={`recommendation-label ${getRecommendationStyle(record.recommendation || record.recommendation_label)}`}>
                                                    AI{record.recommendation || record.recommendation_label}
                                                </span>
                                                {record.category && (
                                                    <span className="category-label">{getCategoryLabel(record.category)}</span>
                                                )}
                                            </div>
                                            <span className="record-date">
                                                {isActive ? '推荐' : '平仓'}: {isActive ? record.recommendation_date || record.entry_date?.split('T')[0] : record.close_date?.split('T')[0]}
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
                                                <span className="price-label">{isActive ? '现价' : '平仓价'}</span>
                                                <span className={`price-value ${isProfit ? 'positive' : 'negative'}`}>
                                                    ¥{currentPrice.toFixed(2)}
                                                </span>
                                            </div>
                                            {record.holding_days !== undefined && (
                                                <div className="holding-days">
                                                    持有{record.holding_days}天
                                                </div>
                                            )}
                                        </div>

                                        {/* 操作区域 */}
                                        <div className="record-actions">
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
                                            {/* 平仓按钮 - 仅活跃记录显示 */}
                                            {isActive && (
                                                <button
                                                    className="close-btn"
                                                    onClick={(e) => handleClose(e, record.id)}
                                                    disabled={isClosing}
                                                >
                                                    {isClosing ? '处理中...' : '平仓'}
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </section>
            </main>
        </div>
    );
}
