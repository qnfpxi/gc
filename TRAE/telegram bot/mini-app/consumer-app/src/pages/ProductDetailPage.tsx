import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Layout, 
  Card, 
  Image, 
  Typography, 
  Button, 
  Space, 
  Divider,
  message,
  Spin,
  Row,
  Col,
  Tag,
  Descriptions,
  Rate,
  Badge,
  Carousel,
  Modal
} from 'antd';
import { 
  ShoppingCartOutlined, 
  StarOutlined,
  EyeOutlined,
  HeartOutlined,
  ShareAltOutlined,
  LeftOutlined,
  CheckCircleOutlined,
  CrownOutlined,
  PhoneOutlined,
  MessageOutlined,
  EnvironmentOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import WebApp from '@twa-dev/sdk';
import apiService, { ProductDetail, MerchantDetail } from '../services/api';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

const ProductDetailPage: React.FC = () => {
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewImage, setPreviewImage] = useState('');
  const [productId, setProductId] = useState<number | null>(null);

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
    
    // 从URL获取商品ID
    const pathParts = window.location.hash.split('/');
    const id = pathParts[pathParts.length - 1];
    if (id) {
      const productId = parseInt(id, 10);
      setProductId(productId);
    }
  }, []);

  // 使用React Query获取商品详情
  const { data: product, isLoading: productLoading, error: productError } = useQuery<ProductDetail, Error>(
    ['product', productId],
    () => apiService.getProductById(productId!),
    {
      enabled: !!productId,
      staleTime: 5 * 60 * 1000, // 5分钟
    }
  );

  // 使用React Query获取商家信息
  const { data: merchant, isLoading: merchantLoading, error: merchantError } = useQuery<MerchantDetail, Error>(
    ['merchant', product?.merchant_id],
    () => apiService.getMerchantById(product!.merchant_id),
    {
      enabled: !!product?.merchant_id,
      staleTime: 5 * 60 * 1000, // 5分钟
    }
  );

  // 处理错误
  useEffect(() => {
    if (productError) {
      message.error('加载商品信息失败: ' + productError.message);
    }
    if (merchantError) {
      message.error('加载商家信息失败: ' + merchantError.message);
    }
  }, [productError, merchantError]);

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
      'https://your-domain.com/product/' + productId,
      '发现了一个很棒的商品：' + product?.name
    );
  };

  const handlePreview = (image: string) => {
    setPreviewImage(image);
    setPreviewVisible(true);
  };

  const handleFavorite = async () => {
    try {
      if (product) {
        await apiService.favoriteProduct(product.id);
        WebApp.showAlert('已收藏该商品');
        // 这里可以更新UI来反映收藏状态的变化
      }
    } catch (error: any) {
      WebApp.showAlert('收藏失败: ' + error.message);
    }
  };

  const loading = productLoading || merchantLoading;

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

  if (!product) {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <Content style={{ padding: '20px', textAlign: 'center' }}>
          <Title level={3}>❌ 未找到商品信息</Title>
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
          🛍️ 商品详情
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
        {/* 商品图片轮播 */}
        <Card style={{ marginBottom: '16px' }}>
          <Carousel autoplay>
            {product.image_urls.map((image, index) => (
              <div key={index} onClick={() => handlePreview(image)}>
                <Image
                  src={image}
                  alt={`${product.name} - 图片 ${index + 1}`}
                  style={{ width: '100%', height: '300px', objectFit: 'cover' }}
                  preview={false}
                />
              </div>
            ))}
          </Carousel>
        </Card>

        {/* 商品基本信息 */}
        <Card style={{ marginBottom: '16px' }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Row justify="space-between" align="top">
              <Col>
                <Title level={3} style={{ margin: 0 }}>
                  {product.name}
                </Title>
              </Col>
              <Col>
                <Button 
                  type="text" 
                  icon={<HeartOutlined />} 
                  onClick={handleFavorite}
                >
                  {product.favorite_count}
                </Button>
              </Col>
            </Row>
            
            <Text type="secondary">{product.description}</Text>
            
            <Row justify="space-between" align="middle">
              <Col>
                <Space>
                  <Text strong style={{ fontSize: '24px', color: '#ff4d4f' }}>
                    {product.currency === 'CNY' ? '¥' : product.currency}{product.price?.toFixed(2)}
                  </Text>
                  {product.is_price_negotiable && (
                    <Tag color="orange">面议</Tag>
                  )}
                  <Text type="secondary">/ {product.price_unit}</Text>
                </Space>
              </Col>
              <Col>
                <Space>
                  <EyeOutlined />
                  <Text type="secondary">{product.view_count}</Text>
                </Space>
              </Col>
            </Row>
            
            {/* 标签 */}
            <Space wrap>
              {product.tags.map((tag, index) => (
                <Tag color="blue" key={index}>{tag}</Tag>
              ))}
            </Space>
          </Space>
        </Card>

        {/* 商家信息 */}
        {merchant && (
          <Card 
            title={
              <Space>
                <ShopOutlined style={{ color: '#1890ff' }} />
                <span>🏪 商家信息</span>
              </Space>
            } 
            style={{ marginBottom: '16px' }}
          >
            <Row gutter={16}>
              <Col span={6}>
                <Avatar 
                  size={60} 
                  src={merchant.logo_url} 
                  icon={<ShopOutlined />} 
                  style={{ 
                    backgroundColor: merchant.subscription_tier === 'enterprise' ? '#722ed1' : 
                                    merchant.subscription_tier === 'professional' ? '#1890ff' : '#52c41a'
                  }}
                />
              </Col>
              <Col span={18}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Row justify="space-between" align="top">
                    <Col>
                      <Space>
                        <Title level={4} style={{ margin: 0 }}>
                          {merchant.name}
                        </Title>
                        {merchant.is_verified && (
                          <Badge count={<CheckCircleOutlined style={{ color: '#52c41a' }} />} />
                        )}
                        {merchant.subscription_tier === 'enterprise' && (
                          <CrownOutlined style={{ color: '#faad14', fontSize: '16px' }} />
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
                  
                  <Text type="secondary">
                    <EnvironmentOutlined /> {merchant.address}
                  </Text>
                </Space>
              </Col>
            </Row>
            
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
                  icon={<ShopOutlined />}
                  onClick={() => window.location.hash = `#/merchant/${merchant.id}`}
                >
                  进店看看
                </Button>
              </Col>
            </Row>
          </Card>
        )}

        {/* 商品统计信息 */}
        <Card 
          title={
            <Space>
              <BarChartOutlined style={{ color: '#722ed1' }} />
              <span>📊 商品数据</span>
            </Space>
          }
          style={{ marginBottom: '16px' }}
        >
          <Descriptions column={2} size="small">
            <Descriptions.Item label="浏览量">
              <Space>
                <EyeOutlined />
                <Text>{product.view_count}</Text>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="收藏数">
              <Space>
                <HeartOutlined />
                <Text>{product.favorite_count}</Text>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="销量">
              <Space>
                <ShoppingCartOutlined />
                <Text>{product.sales_count}</Text>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="上架时间">
              {new Date(product.created_at).toLocaleDateString()}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        <Divider />
        
        {/* 页脚信息 */}
        <div style={{ textAlign: 'center', padding: '16px 0' }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            🚀 发现好物 · 连接你我
          </Text>
        </div>
      </Content>

      {/* 图片预览模态框 */}
      <Modal
        visible={previewVisible}
        footer={null}
        onCancel={() => setPreviewVisible(false)}
        width="90%"
      >
        <img 
          alt="预览图片" 
          style={{ width: '100%' }} 
          src={previewImage} 
        />
      </Modal>
    </Layout>
  );
};

export default ProductDetailPage;