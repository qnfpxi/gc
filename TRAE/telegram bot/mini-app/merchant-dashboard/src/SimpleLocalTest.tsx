import React from 'react';

const SimpleLocalTest: React.FC = () => {
  return (
    <div style={{ 
      padding: '20px', 
      background: '#f0f2f5', 
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1>🧪 Mini App 本地测试</h1>
      
      <div style={{ 
        background: 'white', 
        padding: '20px', 
        borderRadius: '8px',
        marginBottom: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h2>✅ 测试环境状态</h2>
        <p><strong>时间:</strong> {new Date().toLocaleString()}</p>
        <p><strong>页面:</strong> 本地测试界面</p>
        <p><strong>状态:</strong> 正常运行</p>
      </div>

      <div style={{ 
        background: 'white', 
        padding: '20px', 
        borderRadius: '8px',
        marginBottom: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h2>📋 模拟商家数据</h2>
        <p><strong>店铺名称:</strong> 测试咖啡店（三里屯总店）</p>
        <p><strong>描述:</strong> 精品咖啡，手工制作，欢迎品尝。</p>
        <p><strong>地区:</strong> 上海市</p>
        <p><strong>地址:</strong> 朝阳区三里屯路19号</p>
        <p><strong>联系方式:</strong> 13800138000</p>
        <p><strong>订阅等级:</strong> 免费版</p>
      </div>

      <div style={{ 
        background: 'white', 
        padding: '20px', 
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h2>🎯 测试验证项目</h2>
        <div style={{ marginBottom: '10px' }}>
          ✅ <strong>页面加载:</strong> 成功
        </div>
        <div style={{ marginBottom: '10px' }}>
          ✅ <strong>数据渲染:</strong> 成功
        </div>
        <div style={{ marginBottom: '10px' }}>
          🔄 <strong>API集成:</strong> 待测试
        </div>
        <div style={{ marginBottom: '10px' }}>
          🔄 <strong>编辑功能:</strong> 待测试
        </div>
        
        <button 
          style={{
            background: '#1890ff',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '6px',
            cursor: 'pointer',
            marginTop: '20px'
          }}
          onClick={() => {
            alert('✅ 按钮点击测试成功！\n\n接下来可以测试完整的编辑功能。');
          }}
        >
          测试按钮功能
        </button>
      </div>
    </div>
  );
};

export default SimpleLocalTest;