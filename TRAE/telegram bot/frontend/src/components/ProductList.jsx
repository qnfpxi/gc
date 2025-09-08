import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ProductList = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        // 在开发环境中，API运行在8000端口
        // 在生产环境中，API与前端在同一域名下
        const apiUrl = process.env.NODE_ENV === 'development' 
          ? 'http://localhost:8000/api/v1/products/' 
          : '/api/v1/products/';
        
        const response = await axios.get(apiUrl);
        setProducts(response.data.products || response.data);
        setLoading(false);
      } catch (err) {
        setError('获取商品列表失败: ' + err.message);
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved':
        return 'green';
      case 'pending_moderation':
        return 'orange';
      case 'rejected':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'approved':
        return '已批准';
      case 'pending_moderation':
        return '审核中';
      case 'rejected':
        return '已拒绝';
      default:
        return status;
    }
  };

  if (loading) {
    return <div>加载中...</div>;
  }

  if (error) {
    return <div style={{ color: 'red' }}>{error}</div>;
  }

  return (
    <div>
      <h2>商品列表</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>商品名称</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>价格</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>审核状态</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>拒绝原因</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={product.id}>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{product.name}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>¥{product.price}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                <span style={{
                  color: 'white',
                  backgroundColor: getStatusColor(product.moderation_status),
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontWeight: 'bold'
                }}>
                  {getStatusText(product.moderation_status)}
                </span>
              </td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                {product.rejection_reason || '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ProductList;