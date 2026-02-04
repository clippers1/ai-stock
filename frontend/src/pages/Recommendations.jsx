/**
 * AI推荐页面 - 首页展示分类推荐股票列表
 * 支持3种推荐策略：短线强势、趋势动量、价值低估
 * 使用localStorage缓存推荐结果，减少API调用开销
 * 优化：stale-while-revalidate模式 + 骨架屏加载
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { getRecommendationsByCategory, getSectors } from '../services/api';
import ThemeToggle from '../components/ThemeToggle';
import './Recommendations.css';

// 推荐分类配置
const CATEGORIES = [
    {
        id: 'shortterm',
        name: '短线强势',
        description: '涨停池+技术突破',
        icon: '⚡'
    },
    {
        id: 'trend',
        name: '趋势动量',
        description: '均线多头+放量',
        icon: '📈'
    },
    {
        id: 'value',
        name: '价值低估',
        description: '超跌反弹机会',
        icon: '💎'
    }
];

// 缓存配置
const CACHE_KEY = 'ai_recommendations_cache';
const CACHE_EXPIRY_MS = 30 * 60 * 1000; // 30分钟缓存过期

// 缓存工具函数
const CacheUtils = {
    get(category) {
        try {
            const cached = localStorage.getItem(CACHE_KEY);
            if (!cached) return null;
            const data = JSON.parse(cached);
            const categoryCache = data[category];
            if (!categoryCache) return null;
            if (Date.now() - categoryCache.timestamp > CACHE_EXPIRY_MS) {
                return null;
            }
            return categoryCache.data;
        } catch {
            return null;
        }
    },
    set(category, data) {
        try {
            const cached = localStorage.getItem(CACHE_KEY);
            const allData = cached ? JSON.parse(cached) : {};
            allData[category] = { data, timestamp: Date.now() };
            localStorage.setItem(CACHE_KEY, JSON.stringify(allData));
        } catch (e) {
            console.warn('缓存写入失败:', e);
        }
    },
    clear(category) {
        try {
            const cached = localStorage.getItem(CACHE_KEY);
            if (cached) {
                const allData = JSON.parse(cached);
                delete allData[category];
                localStorage.setItem(CACHE_KEY, JSON.stringify(allData));
            }
        } catch { /* ignore */ }
    }
};

// 图标组件
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

const RefreshIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
        <path d="M21 3v5h-5" />
        <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
        <path d="M8 16H3v5" />
    </svg>
);

const SparklesIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
    </svg>
);

// 骨架屏组件
const SkeletonCard = () => (
    <div className="stock-card skeleton">
        <div className="skeleton-line title"></div>
        <div className="skeleton-line subtitle"></div>
        <div className="skeleton-line short"></div>
    </div>
);

export default function Recommendations({ onSelectStock }) {
    const [activeCategory, setActiveCategory] = useState('shortterm');
    // 初始化时立即从缓存加载，避免空白页面
    const [stocks, setStocks] = useState(() => CacheUtils.get('shortterm') || []);
    const [sectors, setSectors] = useState([]);
    const [initialLoading, setInitialLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [cacheInfo, setCacheInfo] = useState(null);

    // 使用ref防止StrictMode下重复请求
    const initRef = useRef(false);
    const fetchingRef = useRef(new Set());

    // 获取推荐数据（stale-while-revalidate模式）
    const fetchRecommendations = useCallback(async (category, forceRefresh = false) => {
        // 防止重复请求
        if (fetchingRef.current.has(category) && !forceRefresh) {
            return;
        }
        fetchingRef.current.add(category);

        // 先尝试从缓存获取并立即显示
        if (!forceRefresh) {
            const cached = CacheUtils.get(category);
            if (cached && cached.length > 0) {
                setStocks(cached);
                setCacheInfo({ fromCache: true, category });
                // 后台静默刷新
                getRecommendationsByCategory(category)
                    .then(data => {
                        if (data && data.length > 0) {
                            setStocks(data);
                            CacheUtils.set(category, data);
                            setCacheInfo({ fromCache: false, silentRefresh: true });
                        }
                    })
                    .catch(console.error)
                    .finally(() => fetchingRef.current.delete(category));
                return;
            }
        }

        // 无缓存或强制刷新，显示加载状态
        setRefreshing(true);
        try {
            const data = await getRecommendationsByCategory(category);
            if (data && data.length > 0) {
                setStocks(data);
                CacheUtils.set(category, data);
                setCacheInfo({ fromCache: false });
            }
        } catch (error) {
            console.error('获取推荐失败:', error);
        } finally {
            setRefreshing(false);
            fetchingRef.current.delete(category);
        }
    }, []);

    // 初始加载（仅执行一次）
    useEffect(() => {
        if (initRef.current) return;
        initRef.current = true;

        async function init() {
            // 并行加载
            const [sectorsData] = await Promise.all([
                getSectors(),
                fetchRecommendations(activeCategory)
            ]);
            setSectors(sectorsData);
            setInitialLoading(false);
        }
        init();
    }, [activeCategory, fetchRecommendations]);

    // 切换分类时加载数据
    useEffect(() => {
        if (initialLoading) return;

        // 先同步加载缓存
        const cached = CacheUtils.get(activeCategory);
        if (cached && cached.length > 0) {
            setStocks(cached);
            setCacheInfo({ fromCache: true });
        } else {
            setStocks([]);
        }

        // 然后后台刷新
        fetchRecommendations(activeCategory);
    }, [activeCategory, fetchRecommendations, initialLoading]);

    // 强制刷新
    const handleRefresh = () => {
        CacheUtils.clear(activeCategory);
        fetchingRef.current.delete(activeCategory);
        fetchRecommendations(activeCategory, true);
    };

    const getRecommendationLabel = (rec) => {
        const labels = {
            '买入': { text: 'AI 买入', className: 'label-buy' },
            '强势': { text: '强势', className: 'label-buy' },
            '突破': { text: '突破', className: 'label-buy' },
            '持有': { text: '持有', className: 'label-hold' },
            '关注': { text: '关注', className: 'label-hold' },
            '卖出': { text: '卖出', className: 'label-sell' },
            '超跌': { text: '超跌', className: 'label-value' }
        };
        return labels[rec] || { text: rec, className: 'label-hold' };
    };

    const currentCategory = CATEGORIES.find(c => c.id === activeCategory);
    const showSkeleton = initialLoading && stocks.length === 0;

    return (
        <div className="page-container recommendations-page">
            {/* 顶部栏 */}
            <header className="page-header">
                <div className="header-content">
                    <h1 className="app-title">AI Stock</h1>
                    <div className="header-actions">
                        <ThemeToggle />
                        <button className="icon-button" aria-label="通知">
                            <BellIcon />
                            <span className="notification-dot"></span>
                        </button>
                    </div>
                </div>
            </header>

            {/* 主内容 */}
            <main className="page-content">
                {/* 分类切换标签 */}
                <section className="category-tabs">
                    {CATEGORIES.map((cat) => (
                        <button
                            key={cat.id}
                            className={`category-tab ${activeCategory === cat.id ? 'active' : ''}`}
                            onClick={() => setActiveCategory(cat.id)}
                        >
                            <span className="category-icon">{cat.icon}</span>
                            <span className="category-name">{cat.name}</span>
                        </button>
                    ))}
                </section>

                {/* 当前分类说明 */}
                <div className="category-description">
                    <span className="desc-text">
                        <SparklesIcon /> {currentCategory?.description}
                    </span>
                    <button
                        className={`refresh-btn ${refreshing ? 'spinning' : ''}`}
                        onClick={handleRefresh}
                        disabled={refreshing}
                        title="刷新推荐"
                    >
                        <RefreshIcon />
                    </button>
                </div>

                {/* 缓存状态提示 */}
                {cacheInfo?.fromCache && (
                    <div className="cache-hint">
                        来自缓存 · 点击刷新获取最新
                    </div>
                )}

                {/* 推荐列表 */}
                <section className="section">
                    <div className="section-header">
                        <h2 className="section-title">
                            {currentCategory?.icon} {currentCategory?.name}推荐
                        </h2>
                        <span className="section-badge">{stocks.length}只</span>
                    </div>

                    <div className="stock-list">
                        {showSkeleton ? (
                            // 骨架屏
                            [1, 2, 3, 4, 5].map(i => <SkeletonCard key={i} />)
                        ) : refreshing && stocks.length === 0 ? (
                            <div className="loading-inline">
                                <div className="loading-spinner small"></div>
                                <span>AI分析中...</span>
                            </div>
                        ) : stocks.length === 0 ? (
                            <div className="empty-state">
                                暂无{currentCategory?.name}推荐
                            </div>
                        ) : (
                            stocks.map((stock) => {
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
                                            <div className="stock-meta-row">
                                                <span className={`recommendation-label ${label.className}`}>
                                                    {label.text}
                                                </span>
                                                <span className="ai-score">
                                                    AI评分 <strong>{stock.ai_score}</strong>
                                                </span>
                                            </div>
                                            {stock.signal && (
                                                <div className="stock-signals">
                                                    {stock.signal.split(/[|｜]/).slice(0, 4).map((s, i) => (
                                                        <span key={i} className="stock-signal">{s.trim()}</span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </button>
                                );
                            })
                        )}
                    </div>

                    {/* 后台刷新指示器 */}
                    {refreshing && stocks.length > 0 && (
                        <div className="refresh-indicator">
                            <div className="loading-spinner tiny"></div>
                            <span>更新中...</span>
                        </div>
                    )}
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
