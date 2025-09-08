import React from 'react';

const SimpleTest: React.FC = () => {
  // 检查 Telegram WebApp 环境
  const isInTelegram = !!(window as any).Telegram?.WebApp;
  
  if (isInTelegram) {
    const tg = (window as any).Telegram.WebApp;
    tg.ready();
    tg.expand();
  }

  return (
    <div style={{ 
      padding: '20px', 
      textAlign: 'center',
      minHeight: '100vh',
      background: '#f0f2f5',
      fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif'
    }}>
      <h1 style={{ color: '#1890ff' }}>🚀 Mini App 测试</h1>
      
      <div style={{ 
        background: 'white', 
        padding: '20px', 
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        margin: '20px 0'
      }}>
        <h2>📱 访问状态</h2>
        <p style={{ 
          color: isInTelegram ? '#52c41a' : '#faad14',
          fontSize: '18px',
          fontWeight: 'bold'
        }}>
          {isInTelegram ? '✅ Telegram WebApp 环境' : '⚠️ 浏览器环境'}
        </p>
        
        <div style={{ marginTop: '20px' }}>
          <p><strong>时间:</strong> {new Date().toLocaleString()}</p>
          <p><strong>URL:</strong> {window.location.href}</p>
          <p><strong>用户代理:</strong> {navigator.userAgent.slice(0, 50)}...</p>
        </div>
      </div>

      <div style={{ 
        background: 'white', 
        padding: '20px', 
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h2>🎯 功能测试</h2>
        <button 
          style={{
            background: '#1890ff',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '8px',
            fontSize: '16px',
            cursor: 'pointer',
            margin: '10px'
          }}
          onClick={() => {
            if (isInTelegram) {
              (window as any).Telegram.WebApp.showAlert('✅ Mini App 功能正常工作！');
            } else {
              alert('✅ 测试成功！Mini App 可以正常运行！');
            }
          }}
        >
          测试功能
        </button>

        {isInTelegram && (
          <button 
            style={{
              background: '#ff4d4f',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '8px',
              fontSize: '16px',
              cursor: 'pointer',
              margin: '10px'
            }}
            onClick={() => {
              (window as any).Telegram.WebApp.close();
            }}
          >
            关闭应用
          </button>
        )}
      </div>
      
      <p style={{ marginTop: '20px', color: '#666' }}>
        🔧 如果你看到这个页面，说明 Mini App 已经成功运行！
      </p>
    </div>
  );
};

export default SimpleTest;