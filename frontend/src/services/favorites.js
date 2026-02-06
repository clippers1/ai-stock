/**
 * 自选股收藏服务
 * 使用 localStorage 存储收藏的股票
 */

const STORAGE_KEY = 'ai_stock_favorites';

/**
 * 获取所有收藏的股票
 * @returns {Array} 收藏的股票列表
 */
export function getFavorites() {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error('读取收藏失败:', error);
    return [];
  }
}

/**
 * 添加股票到收藏
 * @param {Object} stock - 股票信息 { symbol, name }
 * @returns {boolean} 是否添加成功
 */
export function addFavorite(stock) {
  try {
    const favorites = getFavorites();
    
    // 检查是否已存在
    if (favorites.some(f => f.symbol === stock.symbol)) {
      return false;
    }
    
    favorites.push({
      symbol: stock.symbol,
      name: stock.name,
      addedAt: new Date().toISOString(),
    });
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites));
    
    // 触发自定义事件，通知其他组件
    window.dispatchEvent(new CustomEvent('favoritesChanged', { detail: favorites }));
    
    return true;
  } catch (error) {
    console.error('添加收藏失败:', error);
    return false;
  }
}

/**
 * 从收藏中移除股票
 * @param {string} symbol - 股票代码
 * @returns {boolean} 是否移除成功
 */
export function removeFavorite(symbol) {
  try {
    const favorites = getFavorites();
    const newFavorites = favorites.filter(f => f.symbol !== symbol);
    
    if (newFavorites.length === favorites.length) {
      return false; // 未找到
    }
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newFavorites));
    
    // 触发自定义事件
    window.dispatchEvent(new CustomEvent('favoritesChanged', { detail: newFavorites }));
    
    return true;
  } catch (error) {
    console.error('移除收藏失败:', error);
    return false;
  }
}

/**
 * 切换收藏状态
 * @param {Object} stock - 股票信息 { symbol, name }
 * @returns {boolean} 切换后的收藏状态（true=已收藏）
 */
export function toggleFavorite(stock) {
  if (isFavorite(stock.symbol)) {
    removeFavorite(stock.symbol);
    return false;
  } else {
    addFavorite(stock);
    return true;
  }
}

/**
 * 检查股票是否已收藏
 * @param {string} symbol - 股票代码
 * @returns {boolean} 是否已收藏
 */
export function isFavorite(symbol) {
  const favorites = getFavorites();
  return favorites.some(f => f.symbol === symbol);
}

/**
 * 清空所有收藏
 */
export function clearFavorites() {
  localStorage.removeItem(STORAGE_KEY);
  window.dispatchEvent(new CustomEvent('favoritesChanged', { detail: [] }));
}

/**
 * 获取收藏数量
 * @returns {number} 收藏数量
 */
export function getFavoritesCount() {
  return getFavorites().length;
}

