import React, { useState, useEffect } from 'react';
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
  Tag,
  Empty,
  Tabs
} from 'antd';
import { 
  SearchOutlined, 
  ShopOutlined, 
  StarOutlined,
  EyeOutlined,
  HeartOutlined,
  EnvironmentOutlined,
  FireOutlined,
  ShoppingCartOutlined,
  FilterOutlined
} from '@ant-design/icons';
import WebApp from '@twa-dev/sdk';
import apiService, { MerchantListItem, ProductListItem, UnifiedSearchResult } from '../services/api';

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { Search } = Input;
const { TabPane } = Tabs;

const SearchResultsPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('all');

  // 初始化 Telegram WebApp
  useEffect(() => {
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

  // 从URL获取搜索关键词
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.hash.split('?')[1]);
    const query = urlParams.get('q') || '';
    setSearchQuery(query);
  }, []);

  // 使用React Query进行搜索
  const { data: searchResults, isLoading, error, refetch } = useQuery<UnifiedSearchResult, Error>(
    ['search', searchQuery],
    () => apiService.searchAll(searchQuery, 20),
    {
      enabled: !!searchQuery,
      staleTime: 5 * 60 * 1000, // 5分钟
    }
  );

  // 处理错误
  useEffect(() => {
    if (error) {
      message.error('搜索失败: ' + error.message);
    }
  }, [error]);

  const handleSearch = (value: string) => {
    if (value.trim()) {
      setSearchQuery(value);
      // 触发重新搜索
      refetch();
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

  const handleBack = () => {
    // 返回上一页或首页
    window.history.back();
  };

  const merchants = searchResults?.merchants || [];
  const products = searchResults?.products || [];
  const totalMerchants = searchResults?.total_merchants || 0;
  const totalProducts = searchResults?.total_products || 0;

  if (isLoading) {
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
          <Title level={3} style={{ marginTop: '20px' }}>搜索中...</Title>
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
        justifyContent: 'space-between'
      }}>
        <Button 
          type="link" 
          onClick={handleBack}
          style={{ color: 'white' }}
        >
          ← 返回
        </Button>
        <Title level={4} style={{ color: 'white', margin: 0 }}>
          🔍 搜索结果
        </Title>
        <div style={{ width: '40px' }}></div> {/* 占位符，保持标题居中 */}
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

        {/* 搜索结果统计 */}
        <Card style={{ marginBottom: '16px' }}>
          <Space>
            <Text>找到 </Text>
            <Text strong>{totalMerchants}</Text>
            <Text> 个商家，</Text>
            <Text strong>{totalProducts}</Text>
            <Text> 个商品</Text>
          </Space>
        </Card>

        {/* 结果分类标签 */}
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          style={{ marginBottom: '16px' }}
        >
          <TabPane tab={`全部 (${totalMerchants + totalProducts})`} key="all" />
          <TabPane tab={`商家 (${totalMerchants})`} key="merchants" />
          <TabPane tab={`商品 (${totalProducts})`} key="products" />
        </Tabs>

        {/* 商家结果 */}
        {(activeTab === 'all' || activeTab === 'merchants') && merchants.length > 0 && (
          <Card 
            title={
              <Space>
                <ShopOutlined style={{ color: '#1890ff' }} />
                <span>🏪 商家</span>
              </Space>
            } 
            style={{ marginBottom: '16px' }}
          >
            <List
              grid={{ gutter: 16, column: 1 }}
              dataSource={merchants}
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
        )}

        {/* 商品结果 */}
        {(activeTab === 'all' || activeTab === 'products') && products.length > 0 && (
          <Card 
            title={
              <Space>
                <ShoppingCartOutlined style={{ color: '#52c41a' }} />
                <span>🛍️ 商品</span>
              </Space>
            }
          >
            <List
              grid={{ gutter: 16, column: 2, xs: 1, sm: 2 }}
              dataSource={products}
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
        )}

        {/* 空结果提示 */}
        {merchants.length === 0 && products.length === 0 && !isLoading && (
          <Card>
            <Empty 
              description="未找到相关结果" 
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Button type="primary" onClick={() => handleBack()}>
                返回上一页
              </Button>
            </Empty>
          </Card>
        )}

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

export default SearchResultsPage;