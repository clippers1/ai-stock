/**
 * 自选股页面 - 显示用户收藏的股票
 */
import { useState, useEffect } from 'react';
import { getFavorites, removeFavorite } from '../services/favorites';
import { getStockQuote } from '../services/api';
import './Favorites.css';

// 图标组件
const StarIcon = ({ filled }) => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
);

const TrendUpIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
    </svg>
);

const TrendDownIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="22 17 13.5 8.5 8.5 13.5 2 7" />
    </svg>
);

const RefreshIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="23 4 23 10 17 10" />
        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    </svg>
);

export default function Favorites({ onSelectStock }) {
    const [favorites, setFavorites] = useState([]);
    const [stockData, setStockData] = useState({});
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    // 加载收藏列表
    useEffect(() => {
        loadFavorites();
        
        // 监听收藏变化
        const handleFavoritesChanged = () => loadFavorites();
        window.addEventListener('favoritesChanged', handleFavoritesChanged);
        
        return () => {
            window.removeEventListener('favoritesChanged', handleFavoritesChanged);
        };
    }, []);

    const loadFavorites = async () => {
        setLoading(true);
        try {
            const favs = getFavorites();
            setFavorites(favs);
            
            // 获取实时行情
            await fetchQuotes(favs);
        } catch (error) {
            console.error('加载收藏失败:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchQuotes = async (favs) => {
        const quotes = {};
        for (const fav of favs) {
            try {
                const quote = await getStockQuote(fav.symbol);
                if (quote) {
                    quotes[fav.symbol] = quote;
                }
            } catch (error) {
                console.error(`获取 ${fav.symbol} 行情失败:`, error);
            }
        }
        setStockData(quotes);
    };

    const handleRefresh = async () => {
        setRefreshing(true);
        await fetchQuotes(favorites);
        setRefreshing(false);
    };

    const handleRemove = (e, symbol) => {
        e.stopPropagation();
        if (confirm('确定要取消收藏吗？')) {
            removeFavorite(symbol);
            setFavorites(prev => prev.filter(f => f.symbol !== symbol));
        }
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
        <div className="page-container favorites-page">
            <header className="page-header">
                <div className="header-content">
                    <div className="header-left">
                        <h1 className="page-title">自选股</h1>
                        <span className="header-subtitle">{favorites.length} 只股票</span>
                    </div>
                    <button 
                        className={`icon-button ${refreshing ? 'spinning' : ''}`} 
                        onClick={handleRefresh}
                        disabled={refreshing}
                    >
                        <RefreshIcon />
                    </button>
                </div>
            </header>

            <main className="page-content">
                {favorites.length === 0 ? (
                    <div className="empty-state">
                        <StarIcon filled={false} />
                        <h3>暂无自选股</h3>
                        <p>在股票详情页点击收藏按钮添加</p>
                    </div>
                ) : (
                    <div className="favorites-list">
                        {favorites.map((fav) => {
                            const quote = stockData[fav.symbol] || {};
                            const change = quote.change_percent || 0;
                            const isUp = change >= 0;
                            
                            return (
                                <div
                                    key={fav.symbol}
                                    className="favorite-card"
                                    onClick={() => onSelectStock && onSelectStock(fav.symbol)}
                                >
                                    <div className="fav-info">
                                        <span className="fav-symbol">{fav.symbol}</span>
                                        <span className="fav-name">{fav.name}</span>
                                    </div>
                                    <div className="fav-price">
                                        <span className="price-value">
                                            ¥{(quote.price || 0).toFixed(2)}
                                        </span>
                                        <span className={`price-change ${isUp ? 'up' : 'down'}`}>
                                            {isUp ? <TrendUpIcon /> : <TrendDownIcon />}
                                            {isUp ? '+' : ''}{change.toFixed(2)}%
                                        </span>
                                    </div>
                                    <button 
                                        className="remove-btn"
                                        onClick={(e) => handleRemove(e, fav.symbol)}
                                    >
                                        <StarIcon filled={true} />
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>
        </div>
    );
}

