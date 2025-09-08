import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Layout, 
  Card, 
  List, 
  Avatar, 
  Typography, 
  Button, 
  Space, 
  Divider,
  message,
  Spin,
  Row,
  Col, 
  Tag,
  Image,
  Descriptions,
  Rate,
  Badge
} from 'antd';
import { 
  ShopOutlined, 
  StarOutlined,
  EyeOutlined,
  HeartOutlined,
  EnvironmentOutlined,
  PhoneOutlined,
  MessageOutlined,
  ShareAltOutlined,
  LeftOutlined,
  CheckCircleOutlined,
  CrownOutlined,
  ShoppingCartOutlined
} from '@ant-design/icons';
import WebApp from '@twa-dev/sdk';
import apiService, { MerchantDetail, ProductListItem } from '../services/api';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

const MerchantDetailPage: React.FC = () => {
  const [merchantId, setMerchantId] = useState<number | null>(null);

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
    
    // 从URL获取商家ID
    const pathParts = window.location.hash.split('/');
    const id = pathParts[pathParts.length - 1];
    if (id) {
      const merchantId = parseInt(id, 10);
      setMerchantId(merchantId);
    }
  }, []);

  // 使用React Query获取商家详情
  const { data: merchant, isLoading: merchantLoading, error: merchantError } = useQuery<MerchantDetail, Error>(
    ['merchant', merchantId],
    () => apiService.getMerchantById(merchantId!),
    {
      enabled: !!merchantId,
      staleTime: 5 * 60 * 1000, // 5分钟
    }
  );

  // 使用React Query获取商家商品列表
  const { data: products, isLoading: productsLoading, error: productsError } = useQuery<ProductListItem[], Error>(
    ['merchantProducts', merchantId],
    () => apiService.getProducts({ 
      merchant_id: merchantId!,
      limit: 10
    }),
    {
      enabled: !!merchantId,
      staleTime: 5 * 60 * 1000, // 5分钟
    }
  );

  // 处理错误
  useEffect(() => {
    if (merchantError) {
      message.error('加载商家信息失败: ' + merchantError.message);
    }
    if (productsError) {
      message.error('加载商品信息失败: ' + productsError.message);
    }
  }, [merchantError, productsError]);

  const handleProductClick = (productId: number) => {
    // 跳转到商品详情页面
    window.location.hash = `#/product/${productId}`;
  };

  const handleBack = () => {
    // 返回上一页
    window.history.back();
  };

  const handleContact = () => {
    if (merchant?.contact_telegram) {
      // 打开Telegram聊天
      WebApp.openTelegramLink(`https://t.me/${merchant.contact_telegram.replace('@', '')}`);
    } else {
      WebApp.showAlert('商家暂未提供联系方式');
    }
  };

  const handleShare = () => {
    // 分享功能
    WebApp.shareToStory(
      'https://your-domain.com/merchant/' + merchantId,
      '发现了一家很棒的商家：' + merchant?.name
    );
  };

  const loading = merchantLoading || productsLoading;

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

  if (!merchant) {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <Content style={{ padding: '20px', textAlign: 'center' }}>
          <Title level={3}>❌ 未找到商家信息</Title>
          <Text>请稍后重试</Text>
          <div style={{ marginTop: '20px' }}>
            <Button type="primary" onClick={handleBack}>
              返回上一页
            </Button>
          </div>
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
          <LeftOutlined /> 返回
        </Button>
        <Title level={4} style={{ color: 'white', margin: 0 }}>
          🏪 商家详情
        </Title>
        <Space>
          <Button 
            type="link" 
            onClick={handleShare}
            style={{ color: 'white' }}
          >
            <ShareAltOutlined />
          </Button>
        </Space>
      </Header>

      <Content style={{ padding: '16px' }}>
        {/* 商家基本信息 */}
        <Card style={{ marginBottom: '16px' }}>
          <Row gutter={16}>
            <Col span={8}>
              <Avatar 
                size={80} 
                src={merchant.logo_url} 
                icon={<ShopOutlined />} 
                style={{ 
                  backgroundColor: merchant.subscription_tier === 'enterprise' ? '#722ed1' : 
                                  merchant.subscription_tier === 'professional' ? '#1890ff' : '#52c41a'
                }}
              />
            </Col>
            <Col span={16}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Row justify="space-between" align="top">
                  <Col>
                    <Space>
                      <Title level={3} style={{ margin: 0 }}>
                        {merchant.name}
                      </Title>
                      {merchant.is_verified && (
                        <Badge count={<CheckCircleOutlined style={{ color: '#52c41a' }} />} />
                      )}
                      {merchant.subscription_tier === 'enterprise' && (
                        <CrownOutlined style={{ color: '#faad14', fontSize: '20px' }} />
                      )}
                    </Space>
                  </Col>
                </Row>
                
                <Rate 
                  disabled 
                  value={merchant.rating_avg} 
                  allowHalf 
                  style={{ fontSize: '14px' }}
                />
                <Text type="secondary">
                  {merchant.rating_avg} 分 ({merchant.rating_count} 条评价)
                </Text>
                
                <Text type="secondary">{merchant.description}</Text>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* 商家详细信息 */}
        <Card 
          title={
            <Space>
              <ShopOutlined style={{ color: '#1890ff' }} />
              <span>🏢 商家信息</span>
            </Space>
          } 
          style={{ marginBottom: '16px' }}
        >
          <Descriptions column={1} size="small">
            <Descriptions.Item label="地址">
              <Space>
                <EnvironmentOutlined />
                <Text>{merchant.address}</Text>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="联系方式">
              <Space>
                {merchant.contact_phone && (
                  <>
                    <PhoneOutlined />
                    <Text>{merchant.contact_phone}</Text>
                  </>
                )}
                {merchant.contact_telegram && (
                  <>
                    <MessageOutlined />
                    <Text>{merchant.contact_telegram}</Text>
                  </>
                )}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="入驻时间">
              {new Date(merchant.created_at).toLocaleDateString()}
            </Descriptions.Item>
            <Descriptions.Item label="浏览量">
              <Space>
                <EyeOutlined />
                <Text>{merchant.view_count}</Text>
              </Space>
            </Descriptions.Item>
          </Descriptions>
          
          <Divider style={{ margin: '12px 0' }} />
          
          <Row gutter={16}>
            <Col span={12}>
              <Button 
                type="primary" 
                block 
                icon={<MessageOutlined />}
                onClick={handleContact}
              >
                联系商家
              </Button>
            </Col>
            <Col span={12}>
              <Button 
                block 
                icon={<HeartOutlined />}
                onClick={() => WebApp.showAlert('已收藏该商家')}
              >
                收藏商家
              </Button>
            </Col>
          </Row>
        </Card>

        {/* 商品列表 */}
        <Card 
          title={
            <Space>
              <ShoppingCartOutlined style={{ color: '#52c41a' }} />
              <span>🛍️ 商品 ({products?.length || 0})</span>
            </Space>
          }
        >
          {products && products.length > 0 ? (
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
          ) : (
            <Empty 
              description="该商家暂无商品" 
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
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

export default MerchantDetailPage;