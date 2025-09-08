import React from 'react';
import ProductList from './components/ProductList';
import './App.css';

function App() {
  return (
    <div className="App">
      <header style={{ backgroundColor: '#282c34', padding: '20px', color: 'white' }}>
        <h1>商家管理后台</h1>
      </header>
      <main style={{ padding: '20px' }}>
        <ProductList />
      </main>
    </div>
  );
}

export default App;

export default App
