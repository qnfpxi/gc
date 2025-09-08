import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Layout, 
  Card, 
  List, 
  Avatar, 
  Typography, 
  Input, 
  Button, 
  Space, 
  Divider,
  message,
  Spin,
  Row,
  Col,
  Tag
} from 'antd';
import { 
  SearchOutlined, 
  ShopOutlined, 
  StarOutlined,
  EyeOutlined,
  HeartOutlined,
  EnvironmentOutlined,
  FireOutlined
} from '@ant-design/icons';
import WebApp from '@twa-dev/sdk';
import apiService, { MerchantListItem, ProductListItem } from '../services/api';

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { Search } = Input;

const HomePage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');

  // 初始化 Telegram WebApp
  React.useEffect(() => {
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

  // 使用React Query获取推荐商家数据
  const { data: featuredMerchants, isLoading: merchantsLoading, error: merchantsError } = useQuery<MerchantListItem[], Error>(
    ['featuredMerchants'],
    () => apiService.getMerchants({ 
      limit: 3,
      is_featured: true
    }),
    {
      staleTime: 5 * 60 * 1000, // 5分钟
    }
  );

  // 使用React Query获取新品数据
  const { data: newProducts, isLoading: productsLoading, error: productsError } = useQuery<ProductListItem[], Error>(
    ['newProducts'],
    () => apiService.getProducts({ 
      sort_by: 'created_at',
      sort_order: 'desc',
      limit: 4
    }),
    {
      staleTime: 5 * 60 * 1000, // 5分钟
    }
  );

  // 处理错误
  React.useEffect(() => {
    if (merchantsError) {
      message.error('加载商家数据失败: ' + merchantsError.message);
    }
    if (productsError) {
      message.error('加载商品数据失败: ' + productsError.message);
    }
  }, [merchantsError, productsError]);

  const handleSearch = (value: string) => {
    if (value.trim()) {
      // 跳转到搜索结果页面
      window.location.hash = `#/search?q=${encodeURIComponent(value)}`;
    }
  };

  const handleMerchantClick = (merchantId: number) => {
    // 跳转到商家详情页面
    window.location.hash = `#/merchant/${merchantId}`;
  };

  const handleProductClick = (productId: number) => {
    // 跳转到商品详情页面
    window.location.hash = `#/product/${productId}`;
  };

  const loading = merchantsLoading || productsLoading;

  if (loading) {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <Content style={{ 
          padding: '20px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          flexDirection: 'column'
        }}>
          <Spin size="large" />
          <Title level={3} style={{ marginTop: '20px' }}>加载中...</Title>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Header style={{ 
        background: '#1890ff', 
        padding: '0 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Title level={4} style={{ color: 'white', margin: 0 }}>
          🔍 发现好物
        </Title>
      </Header>

      <Content style={{ padding: '16px' }}>
        {/* 搜索框 */}
        <Card style={{ marginBottom: '16px' }}>
          <Search
            placeholder="搜索商家或商品..."
            allowClear
            enterButton={<SearchOutlined />}
            size="large"
            onSearch={handleSearch}
            onChange={(e) => setSearchQuery(e.target.value)}
            value={searchQuery}
          />
        </Card>

        {/* 推荐商家 */}
        <Card 
          title={
            <Space>
              <FireOutlined style={{ color: '#ff4d4f' }} />
              <span>🔥 推荐商家</span>
            </Space>
          } 
          style={{ marginBottom: '16px' }}
        >
          <List
            grid={{ gutter: 16, column: 1 }}
            dataSource={featuredMerchants || []}
            renderItem={merchant => (
              <List.Item>
                <Card 
                  hoverable
                  onClick={() => handleMerchantClick(merchant.id)}
                  style={{ borderRadius: '8px' }}
                >
                  <Row align="middle">
                    <Col span={4}>
                      <Avatar 
                        size={48} 
                        src={merchant.logo_url} 
                        icon={<ShopOutlined />} 
                        style={{ 
                          backgroundColor: merchant.subscription_tier === 'enterprise' ? '#722ed1' : 
                                          merchant.subscription_tier === 'professional' ? '#1890ff' : '#52c41a'
                        }}
                      />
                    </Col>
                    <Col span={20}>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Row justify="space-between" align="middle">
                          <Col>
                            <Space>
                              <Text strong>{merchant.name}</Text>
                              {merchant.is_featured && (
                                <Tag color="red">推荐</Tag>
                              )}
                            </Space>
                          </Col>
                          <Col>
                            <Space size="small">
                              <StarOutlined style={{ color: '#faad14' }} />
                              <Text strong>{merchant.rating_avg}</Text>
                              <Text type="secondary">({merchant.rating_count})</Text>
                            </Space>
                          </Col>
                        </Row>
                        <Text type="secondary" ellipsis>{merchant.description}</Text>
                        <Row justify="space-between">
                          <Col>
                            <Space size="small">
                              <EnvironmentOutlined />
                              <Text type="secondary">{merchant.address}</Text>
                            </Space>
                          </Col>
                          <Col>
                            <Space size="small">
                              <EyeOutlined />
                              <Text type="secondary">{merchant.view_count}</Text>
                            </Space>
                          </Col>
                        </Row>
                      </Space>
                    </Col>
                  </Row>
                </Card>
              </List.Item>
            )}
          />
        </Card>

        {/* 新品推荐 */}
        <Card 
          title={
            <Space>
              <StarOutlined style={{ color: '#faad14' }} />
              <span>⭐ 新品推荐</span>
            </Space>
          }
        >
          <List
            grid={{ gutter: 16, column: 2, xs: 1, sm: 2 }}
            dataSource={newProducts || []}
            renderItem={product => (
              <List.Item>
                <Card 
                  hoverable
                  onClick={() => handleProductClick(product.id)}
                  cover={
                    <img 
                      alt={product.name} 
                      src={product.main_image_url || "https://via.placeholder.com/150x150/f0f2f5/000000?text=No+Image"} 
                      style={{ height: '120px', objectFit: 'cover' }}
                    />
                  }
                  style={{ borderRadius: '8px' }}
                >
                  <Card.Meta
                    title={
                      <Space>
                        <Text strong ellipsis>{product.name}</Text>
                        {product.is_new && (
                          <Tag color="orange">新品</Tag>
                        )}
                      </Space>
                    }
                    description={
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text type="secondary" ellipsis style={{ fontSize: '12px' }}>
                          {product.description}
                        </Text>
                        <Row justify="space-between" align="middle">
                          <Col>
                            <Text strong style={{ color: '#ff4d4f' }}>
                              {product.currency === 'CNY' ? '¥' : product.currency}{product.price?.toFixed(2)}
                            </Text>
                          </Col>
                          <Col>
                            <Space size="small">
                              <HeartOutlined />
                              <Text type="secondary">{product.favorite_count}</Text>
                            </Space>
                          </Col>
                        </Row>
                      </Space>
                    }
                  />
                </Card>
              </List.Item>
            )}
          />
        </Card>

        <Divider />
        
        {/* 页脚信息 */}
        <div style={{ textAlign: 'center', padding: '16px 0' }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            🚀 发现好物 · 连接你我
          </Text>
        </div>
      </Content>
    </Layout>
  );
};

export default HomePage;