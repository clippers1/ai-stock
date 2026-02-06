/**
 * API服务 - 与后端通信
 */

const API_BASE = 'http://localhost:8000/api';

/**
 * 获取AI推荐股票列表（按分类）
 * @param {string} category - 推荐分类: shortterm, trend, value
 */
export async function getRecommendationsByCategory(category = 'shortterm') {
  try {
    const response = await fetch(`${API_BASE}/recommendations?category=${category}`);
    if (!response.ok) throw new Error('获取推荐失败');
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    // 返回模拟数据作为后备
    return getMockRecommendationsByCategory(category);
  }
}

/**
 * 获取AI推荐股票列表（旧接口，兼容）
 */
export async function getRecommendations() {
  return getRecommendationsByCategory('shortterm');
}

/**
 * 获取股票详情
 */
export async function getStockDetail(symbol) {
  try {
    const response = await fetch(`${API_BASE}/stock/${symbol}`);
    if (!response.ok) throw new Error('获取股票详情失败');
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    return getMockStockDetail(symbol);
  }
}

/**
 * 发送聊天消息
 */
export async function sendChatMessage(message, history = []) {
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history })
    });
    if (!response.ok) throw new Error('发送消息失败');
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    return getMockChatResponse(message);
  }
}

/**
 * 获取热门板块
 */
export async function getSectors() {
  try {
    const response = await fetch(`${API_BASE}/sectors`);
    if (!response.ok) throw new Error('获取板块失败');
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    return getMockSectors();
  }
}

/**
 * 获取股票实时行情（用于自选股）
 * @param {string} symbol - 股票代码
 */
export async function getStockQuote(symbol) {
  try {
    const response = await fetch(`${API_BASE}/stock/${symbol}`);
    if (!response.ok) throw new Error('获取行情失败');
    const data = await response.json();
    return {
      price: data.price || 0,
      change: data.change || 0,
      change_percent: data.change_percent || 0,
    };
  } catch (error) {
    console.error('API Error:', error);
    // 返回模拟数据
    return {
      price: 100 + Math.random() * 50,
      change: (Math.random() - 0.5) * 10,
      change_percent: (Math.random() - 0.5) * 5,
    };
  }
}


// ==================== 模拟数据（后备） ====================

/**
 * 按分类获取模拟推荐数据
 */
function getMockRecommendationsByCategory(category) {
  const categoryData = {
    // 短线强势：涨停池+技术突破
    shortterm: [
      { symbol: "000001", name: "平安银行", price: 12.85, change: 1.17, change_percent: 10.02, recommendation: "强势", ai_score: 95, signal: "涨停" },
      { symbol: "600519", name: "贵州茅台", price: 1725.00, change: 86.25, change_percent: 5.26, recommendation: "突破", ai_score: 92, signal: "放量突破" },
      { symbol: "002475", name: "立讯精密", price: 32.45, change: 2.95, change_percent: 10.00, recommendation: "强势", ai_score: 90, signal: "涨停" },
      { symbol: "300059", name: "东方财富", price: 18.92, change: 1.72, change_percent: 10.00, recommendation: "强势", ai_score: 88, signal: "涨停" },
      { symbol: "002415", name: "海康威视", price: 35.80, change: 2.65, change_percent: 8.00, recommendation: "突破", ai_score: 86, signal: "新高突破" },
    ],
    // 趋势动量：均线多头+放量
    trend: [
      { symbol: "300750", name: "宁德时代", price: 195.60, change: 8.80, change_percent: 4.71, recommendation: "买入", ai_score: 91, signal: "均线多头" },
      { symbol: "002594", name: "比亚迪", price: 268.50, change: 12.80, change_percent: 5.01, recommendation: "买入", ai_score: 89, signal: "放量上攻" },
      { symbol: "600036", name: "招商银行", price: 38.25, change: 1.45, change_percent: 3.94, recommendation: "买入", ai_score: 85, signal: "趋势延续" },
      { symbol: "000858", name: "五粮液", price: 165.30, change: 5.80, change_percent: 3.64, recommendation: "买入", ai_score: 83, signal: "MACD金叉" },
      { symbol: "601318", name: "中国平安", price: 45.60, change: 1.35, change_percent: 3.05, recommendation: "关注", ai_score: 78, signal: "量价齐升" },
      { symbol: "000333", name: "美的集团", price: 62.40, change: 1.80, change_percent: 2.97, recommendation: "关注", ai_score: 75, signal: "站稳60日线" },
    ],
    // 价值低估：超跌反弹机会
    value: [
      { symbol: "601166", name: "兴业银行", price: 16.25, change: 0.48, change_percent: 3.04, recommendation: "超跌", ai_score: 82, signal: "PE仅4.2倍" },
      { symbol: "600276", name: "恒瑞医药", price: 38.90, change: 1.12, change_percent: 2.96, recommendation: "超跌", ai_score: 80, signal: "跌幅超40%" },
      { symbol: "002304", name: "洋河股份", price: 102.50, change: 2.85, change_percent: 2.86, recommendation: "超跌", ai_score: 79, signal: "估值底部" },
      { symbol: "600887", name: "伊利股份", price: 28.65, change: 0.72, change_percent: 2.58, recommendation: "超跌", ai_score: 77, signal: "高股息" },
      { symbol: "000651", name: "格力电器", price: 38.20, change: 0.85, change_percent: 2.28, recommendation: "超跌", ai_score: 75, signal: "破净反弹" },
    ]
  };

  return categoryData[category] || categoryData.shortterm;
}

/**
 * 获取模拟推荐数据（兼容旧接口）
 */
function getMockRecommendations() {
  return getMockRecommendationsByCategory('shortterm');
}

function getMockStockDetail(symbol) {
  const stocks = getMockRecommendations();
  const stock = stocks.find(s => s.symbol === symbol) || stocks[0];

  // 生成模拟价格历史
  const priceHistory = [];
  let basePrice = stock.price * 0.9;
  for (let i = 0; i < 30; i++) {
    const change = (Math.random() - 0.45) * 0.04;
    basePrice = basePrice * (1 + change);
    priceHistory.push({
      date: `2026-01-${String(i + 1).padStart(2, '0')}`,
      open: +(basePrice * 0.99).toFixed(2),
      high: +(basePrice * 1.02).toFixed(2),
      low: +(basePrice * 0.98).toFixed(2),
      close: +basePrice.toFixed(2),
      volume: Math.floor(Math.random() * 40000000) + 10000000
    });
  }

  return {
    ...stock,
    open_price: +(stock.price * 0.99).toFixed(2),
    high: +(stock.price * 1.02).toFixed(2),
    low: +(stock.price * 0.97).toFixed(2),
    volume: Math.floor(Math.random() * 80000000) + 20000000,
    market_cap: `${Math.floor(Math.random() * 2500) + 500}B`,
    pe_ratio: +(Math.random() * 30 + 15).toFixed(2),
    ai_analysis: `${stock.name}当前表现${stock.change > 0 ? '强劲' : '平稳'}，AI评分${stock.ai_score}分，建议${stock.recommendation}。技术指标显示${stock.change > 0 ? '上涨' : '盘整'}趋势，MACD呈现金叉形态，RSI处于适中区域。`,
    price_history: priceHistory
  };
}

function getMockChatResponse(message) {
  const msg = message.toLowerCase();

  if (msg.includes('推荐') || msg.includes('买')) {
    return {
      reply: '根据AI分析，今日推荐关注：\n\n1. 贵州茅台(600519) - AI评分92分 - 买入\n2. 宁德时代(300750) - AI评分88分 - 买入\n3. 比亚迪(002594) - AI评分85分 - 买入\n\n💡 以上推荐基于技术面和基本面综合分析，仅供参考。',
      suggestions: ['分析贵州茅台', '大盘走势', '投资风险提示']
    };
  }

  if (msg.includes('大盘') || msg.includes('市场')) {
    return {
      reply: '今日A股市场概况：\n\n📊 上证指数：整体呈现震荡走势\n📈 热门板块：白酒、新能源、科技\n📉 调整板块：地产、金融\n\n💡 建议关注业绩确定性强的白马股，注意控制仓位。',
      suggestions: ['今日推荐', '分析贵州茅台', '分析比亚迪']
    };
  }

  return {
    reply: '您好！我是AI投资助手。\n\n我可以帮您：\n• 分析个股（如：分析贵州茅台）\n• 推荐股票（如：今日推荐）\n• 解答投资问题\n\n请问有什么可以帮您的？',
    suggestions: ['今日有什么推荐？', '分析贵州茅台', '大盘走势如何？']
  };
}

function getMockSectors() {
  return [
    { name: "白酒", change: 2.35, hot: true },
    { name: "新能源", change: 1.82, hot: true },
    { name: "银行", change: 0.56, hot: false },
    { name: "医药", change: -0.82, hot: false },
    { name: "科技", change: 1.92, hot: true },
  ];
}


// ==================== AI回测相关 ====================

/**
 * 获取回测记录列表
 * @param {string} timeFilter - 时间筛选: 7d, 30d, 90d, all
 * @param {string|null} status - 状态筛选: active, closed, 或 null(全部)
 */
export async function getBacktestRecords(timeFilter = '30d', status = null) {
  try {
    let url = `${API_BASE}/backtest/records?period=${timeFilter}`;
    if (status) {
      url += `&status=${status}`;
    }
    const response = await fetch(url);
    if (!response.ok) throw new Error('获取回测记录失败');
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    return getMockBacktestRecords(timeFilter);
  }
}

/**
 * 平仓操作
 * @param {number} recordId - 记录ID
 * @param {number|null} closePrice - 平仓价格（可选）
 */
export async function closePosition(recordId, closePrice = null) {
  try {
    const options = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    };
    if (closePrice !== null) {
      options.body = JSON.stringify({ close_price: closePrice });
    }
    const response = await fetch(`${API_BASE}/backtest/close/${recordId}`, options);
    if (!response.ok) throw new Error('平仓操作失败');
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    return { success: false, message: error.message };
  }
}

/**
 * 获取回测统计摘要
 * @param {string} timeFilter - 时间筛选: 7d, 30d, 90d, all
 */
export async function getBacktestSummary(timeFilter = '30d') {
  try {
    const response = await fetch(`${API_BASE}/backtest/summary?period=${timeFilter}`);
    if (!response.ok) throw new Error('获取回测摘要失败');
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    return getMockBacktestSummary(timeFilter);
  }
}

/**
 * 获取收益曲线数据
 * @param {string} timeFilter - 时间筛选: 7d, 30d, 90d, all
 */
export async function getPerformanceCurve(timeFilter = '30d') {
  try {
    const response = await fetch(`${API_BASE}/backtest/performance?period=${timeFilter}`);
    if (!response.ok) throw new Error('获取收益曲线失败');
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    // 返回空数据
    return {
      dates: [],
      daily_returns: [],
      cumulative_returns: [],
      daily_count: [],
      period: timeFilter
    };
  }
}

/**
 * 模拟回测记录数据
 */
function getMockBacktestRecords(timeFilter) {
  const allRecords = [
    {
      id: 1,
      symbol: "000001",
      name: "平安银行",
      recommendation: "买入",
      recommendDate: "2026-01-15",
      entryPrice: 18.50,
      currentPrice: 21.20,
      profitPercent: 14.6,
      trendData: "0,25 20,22 40,18 60,15 80,12 100,8"
    },
    {
      id: 2,
      symbol: "600519",
      name: "贵州茅台",
      recommendation: "买入",
      recommendDate: "2026-01-14",
      entryPrice: 2150.00,
      currentPrice: 2038.00,
      profitPercent: -5.2,
      trendData: "0,5 20,8 40,12 60,18 80,22 100,25"
    },
    {
      id: 3,
      symbol: "002594",
      name: "比亚迪",
      recommendation: "买入",
      recommendDate: "2026-01-12",
      entryPrice: 280.10,
      currentPrice: 315.60,
      profitPercent: 12.7,
      trendData: "0,28 20,25 40,20 60,18 80,12 100,8"
    },
    {
      id: 4,
      symbol: "688981",
      name: "中芯国际",
      recommendation: "持有",
      recommendDate: "2026-01-10",
      entryPrice: 52.80,
      currentPrice: 51.85,
      profitPercent: -1.8,
      trendData: "0,15 20,12 40,16 60,18 80,17 100,16"
    },
    {
      id: 5,
      symbol: "300750",
      name: "宁德时代",
      recommendation: "买入",
      recommendDate: "2026-01-08",
      entryPrice: 172.30,
      currentPrice: 185.10,
      profitPercent: 7.4,
      trendData: "0,22 20,20 40,18 60,15 80,12 100,10"
    },
    {
      id: 6,
      symbol: "601318",
      name: "中国平安",
      recommendation: "买入",
      recommendDate: "2026-01-05",
      entryPrice: 40.25,
      currentPrice: 42.80,
      profitPercent: 6.3,
      trendData: "0,24 20,22 40,19 60,17 80,15 100,12"
    },
    {
      id: 7,
      symbol: "000858",
      name: "五粮液",
      recommendation: "买入",
      recommendDate: "2025-12-28",
      entryPrice: 152.60,
      currentPrice: 158.90,
      profitPercent: 4.1,
      trendData: "0,20 20,18 40,16 60,15 80,14 100,13"
    },
    {
      id: 8,
      symbol: "600036",
      name: "招商银行",
      recommendation: "持有",
      recommendDate: "2025-12-20",
      entryPrice: 36.80,
      currentPrice: 35.60,
      profitPercent: -3.3,
      trendData: "0,10 20,12 40,14 60,16 80,17 100,18"
    },
  ];

  // 根据时间筛选返回不同数量的记录
  const counts = { '7d': 3, '30d': 5, '90d': 7, 'all': 8 };
  return allRecords.slice(0, counts[timeFilter] || 5);
}

/**
 * 模拟回测统计摘要
 */
function getMockBacktestSummary(timeFilter) {
  const summaries = {
    '7d': { totalReturn: 8.2, winRate: 67, totalCount: 6 },
    '30d': { totalReturn: 23.5, winRate: 68, totalCount: 47 },
    '90d': { totalReturn: 42.8, winRate: 71, totalCount: 126 },
    'all': { totalReturn: 68.5, winRate: 65, totalCount: 312 }
  };
  return summaries[timeFilter] || summaries['30d'];
}

