/**
 * AI Stock Trading - 主应用入口
 */
import { useState } from 'react';
import Recommendations from './pages/Recommendations';
import StockAnalysis from './pages/StockAnalysis';
import AIChat from './pages/AIChat';
import BottomNav from './components/BottomNav';
import './App.css';

export default function App() {
  const [currentPage, setCurrentPage] = useState('recommendations');
  const [selectedStock, setSelectedStock] = useState(null);

  // 处理股票选择，跳转到分析页
  const handleSelectStock = (symbol) => {
    setSelectedStock(symbol);
    setCurrentPage('analysis');
  };

  // 从分析页返回
  const handleBackFromAnalysis = () => {
    setCurrentPage('recommendations');
  };

  // 渲染当前页面
  const renderPage = () => {
    switch (currentPage) {
      case 'recommendations':
        return <Recommendations onSelectStock={handleSelectStock} />;
      case 'analysis':
        return <StockAnalysis symbol={selectedStock} onBack={handleBackFromAnalysis} />;
      case 'chat':
        return <AIChat />;
      default:
        return <Recommendations onSelectStock={handleSelectStock} />;
    }
  };

  return (
    <div className="app">
      {renderPage()}
      <BottomNav currentPage={currentPage} onNavigate={setCurrentPage} />
    </div>
  );
}
