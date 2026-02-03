/**
 * API服务 - 与后端通信
 */

const API_BASE = 'http://localhost:8000/api';

/**
 * 获取AI推荐股票列表
 */
export async function getRecommendations() {
  try {
    const response = await fetch(`${API_BASE}/recommendations`);
    if (!response.ok) throw new Error('获取推荐失败');
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    // 返回模拟数据作为后备
    return getMockRecommendations();
  }
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


// ==================== 模拟数据（后备） ====================

function getMockRecommendations() {
  return [
    { symbol: "600519", name: "贵州茅台", price: 1680.50, change: 25.30, change_percent: 1.53, recommendation: "买入", ai_score: 92 },
    { symbol: "300750", name: "宁德时代", price: 185.40, change: 8.25, change_percent: 4.66, recommendation: "买入", ai_score: 88 },
    { symbol: "002594", name: "比亚迪", price: 245.80, change: 12.45, change_percent: 5.33, recommendation: "买入", ai_score: 85 },
    { symbol: "000858", name: "五粮液", price: 158.20, change: 3.18, change_percent: 2.05, recommendation: "增持", ai_score: 78 },
    { symbol: "601318", name: "中国平安", price: 42.35, change: 0.85, change_percent: 2.05, recommendation: "持有", ai_score: 72 },
    { symbol: "600036", name: "招商银行", price: 35.80, change: -0.45, change_percent: -1.24, recommendation: "持有", ai_score: 68 },
    { symbol: "000333", name: "美的集团", price: 58.90, change: 1.20, change_percent: 2.08, recommendation: "持有", ai_score: 65 },
    { symbol: "600276", name: "恒瑞医药", price: 42.15, change: -1.35, change_percent: -3.10, recommendation: "观望", ai_score: 55 },
  ];
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
