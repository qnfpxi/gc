import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import WebApp from '@twa-dev/sdk';
import HomePage from './pages/HomePage';
import SearchResultsPage from './pages/SearchResultsPage';
import MerchantDetailPage from './pages/MerchantDetailPage';
import ProductDetailPage from './pages/ProductDetailPage';
import queryClient from './services/queryClient';

const App: React.FC = () => {
  useEffect(() => {
    // 初始化 Telegram WebApp
    WebApp.ready();
    WebApp.expand();
    
    // 设置主题颜色
    if (WebApp.setHeaderColor) {
      WebApp.setHeaderColor('#1890ff');
    }
    if (WebApp.setBackgroundColor) {
      WebApp.setBackgroundColor('#f0f2f5');
    }
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchResultsPage />} />
          <Route path="/merchant/:id" element={<MerchantDetailPage />} />
          <Route path="/product/:id" element={<ProductDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
};

export default App;