import React, { useEffect, useState } from 'react';
import { Layout, Card, Statistic, Row, Col, Typography, Button, Space, Divider, message, Spin } from 'antd';
import { 
  ShopOutlined, 
  EyeOutlined, 
  HeartOutlined, 
  StarOutlined,
  PhoneOutlined,
  MessageOutlined,
  SettingOutlined,
  BarChartOutlined,
  EditOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import WebApp from '@twa-dev/sdk';
import { merchantAPI, MerchantInfo, MerchantStats } from './services/merchantAPI';
import EditMerchant from './components/EditMerchant';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

// 视图状态类型
type ViewState = 'dashboard' | 'edit' | 'products' | 'product-form';

const App: React.FC = () => {
  const [merchantData, setMerchantData] = useState<MerchantInfo | null>(null);
  const [merchantStats, setMerchantStats] = useState<MerchantStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [currentView, setCurrentView] = useState<ViewState>('dashboard');
  const [apiConnected, setApiConnected] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);

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
    
    // 加载商家数据
    loadMerchantData();
  }, []);

  // 加载商家数据
  const loadMerchantData = async () => {
    try {
      setLoading(true);
      
      // 测试API连接
      const isConnected = await merchantAPI.testConnection();
      setApiConnected(isConnected);
      
      if (isConnected) {
        // 同时获取商家信息和统计数据
        const [merchant, stats] = await Promise.all([
          merchantAPI.getCurrentMerchant(),
          merchantAPI.getMerchantStats(0) // 使用0作为占位符，后端会根据当前用户返回对应商家的统计
        ]);
        
        setMerchantData(merchant);
        setMerchantStats(stats);
        
        // 商家数据加载成功
      } else {
        // API不可用时使用模拟数据
        // API连接失败，使用模拟数据
        setMerchantData({
          merchant_id: 1,
          name: "经典手机号测试店",
          description: "这是通过Bot入驻的测试商家",
          region_id: 1,
          address: "朝阳区三里屯",
          contact_phone: "13912345678",
          subscription_tier: "free",
          created_at: "2025-08-31T12:00:00Z",
          rating_avg: 4.5,
          rating_count: 23,
          view_count: 128
        });
        
        setMerchantStats({
          merchant_id: 1,
          products_count: 5,
          active_products_count: 4,
          total_views: 128,
          total_favorites: 16,
          rating_avg: 4.5,
          rating_count: 23,
          subscription_status: "免费版",
          subscription_tier: "free",
          is_premium: false
        });
      }
    } catch (error: any) {
      // 加载商家数据失败
      message.error('加载数据失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 刷新数据
  const handleRefresh = async () => {
    setRefreshing(true);
    await loadMerchantData();
    setRefreshing(false);
    message.success('数据已刷新');
  };

  // 更新成功回调
  const handleUpdateSuccess = (updatedMerchant: MerchantInfo) => {
    setMerchantData(updatedMerchant);
    setCurrentView('dashboard');
    message.success('商家信息更新成功！');
  };

  // 获取订阅显示信息
  const getSubscriptionDisplay = (tier: string) => {
    const tiers = {
      free: { text: '免费版', color: '#52c41a' },
      professional: { text: '专业版', color: '#1890ff' },
      enterprise: { text: '企业版', color: '#722ed1' }
    };
    return tiers[tier as keyof typeof tiers] || tiers.free;
  };

  // 获取联系方式显示
  const getContactDisplay = () => {
    if (!merchantData) return '未设置';
    
    const { contact_phone, contact_telegram, contact_wechat } = merchantData;
    
    if (contact_phone) {
      return { type: 'phone', text: `手机号码：${contact_phone}`, icon: <PhoneOutlined style={{ color: '#52c41a' }} /> };
    } else if (contact_telegram) {
      return { type: 'telegram', text: `Telegram：${contact_telegram}`, icon: <MessageOutlined style={{ color: '#1890ff' }} /> };
    } else if (contact_wechat) {
      return { type: 'wechat', text: `微信：${contact_wechat}`, icon: <MessageOutlined style={{ color: '#52c41a' }} /> };
    } else {
      return { type: 'anonymous', text: 'TG匿名聊天已启用', icon: <MessageOutlined style={{ color: '#1890ff' }} /> };
    }
  };

  // 处理联系方式点击
  const handleContactClick = () => {
    const contactInfo = getContactDisplay();
    if (contactInfo.type === 'phone') {
      WebApp.showAlert(contactInfo.text);
    } else {
      WebApp.showAlert('客户可通过Bot与您匿名联系，保护双方隐私');
    }
  };

  // 处理商品编辑
  const handleEditProduct = (productId: number) => {
    setSelectedProductId(productId);
    setCurrentView('product-form');
  };

  // 处理创建商品
  const handleCreateProduct = () => {
    setSelectedProductId(null);
    setCurrentView('product-form');
  };

  // 处理商品操作成功
  const handleProductSuccess = () => {
    setCurrentView('products');
  };

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
          <Text type="secondary">
            {apiConnected ? '正在从服务器获取数据...' : '正在连接服务器...'}
          </Text>
        </Content>
      </Layout>
    );
  }

  if (!merchantData) {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <Content style={{ padding: '20px', textAlign: 'center' }}>
          <Title level={3}>❌ 数据加载失败</Title>
          <Text>请稍后重试</Text>
          <div style={{ marginTop: '20px' }}>
            <Button type="primary" onClick={loadMerchantData}>
              重新加载
            </Button>
          </div>
        </Content>
      </Layout>
    );
  }

  const subscriptionInfo = getSubscriptionDisplay(merchantData.subscription_tier);
  const contactInfo = getContactDisplay();

  // 如果是编辑视图，显示编辑组件
  if (currentView === 'edit') {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <Content style={{ padding: '16px' }}>
          <EditMerchant 
            merchantInfo={merchantData}
            onUpdateSuccess={handleUpdateSuccess}
            onCancel={() => setCurrentView('dashboard')}
          />
        </Content>
      </Layout>
    );
  }

  // 如果是商品列表视图
  if (currentView === 'products') {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <Header style={{ 
          background: '#1890ff', 
          padding: '0 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <Space>
            <ShopOutlined style={{ color: 'white', fontSize: '20px' }} />
            <Title level={4} style={{ color: 'white', margin: 0 }}>
              商品管理
            </Title>
          </Space>
          <Space>
            <Button 
              type="primary" 
              ghost 
              onClick={() => setCurrentView('dashboard')}
            >
              返回首页
            </Button>
          </Space>
        </Header>
        <Content style={{ padding: '16px' }}>
          {React.createElement(() => {
            const ProductList = require('./components/Products/ProductList').default;
            return (
              <ProductList 
                onEdit={handleEditProduct}
                onCreate={handleCreateProduct}
              />
            );
          })}
        </Content>
      </Layout>
    );
  }

  // 如果是商品表单视图
  if (currentView === 'product-form') {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <Header style={{ 
          background: '#1890ff', 
          padding: '0 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <Space>
            <ShopOutlined style={{ color: 'white', fontSize: '20px' }} />
            <Title level={4} style={{ color: 'white', margin: 0 }}>
              {selectedProductId ? '编辑商品' : '添加商品'}
            </Title>
          </Space>
          <Space>
            <Button 
              type="primary" 
              ghost 
              onClick={() => setCurrentView('products')}
            >
              返回列表
            </Button>
          </Space>
        </Header>
        <Content style={{ padding: '16px' }}>
          {React.createElement(() => {
            const ProductForm = require('./components/Products/ProductForm').default;
            return (
              <ProductForm 
                productId={selectedProductId || undefined}
                onCancel={() => setCurrentView('products')}
                onSuccess={handleProductSuccess}
              />
            );
          })}
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
        <Space>
          <ShopOutlined style={{ color: 'white', fontSize: '20px' }} />
          <Title level={4} style={{ color: 'white', margin: 0 }}>
            商家管理后台
          </Title>
          {!apiConnected && (
            <Text style={{ color: '#ffccc7', fontSize: '12px' }}>
              (离线模式)
            </Text>
          )}
        </Space>
        <Space>
          <Button 
            type="primary" 
            ghost 
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={refreshing}
            size="small"
          >
            刷新
          </Button>
          <Button 
            type="primary" 
            ghost 
            icon={<SettingOutlined />}
            onClick={() => WebApp.showAlert('设置功能正在开发中')}
            size="small"
          >
            设置
          </Button>
        </Space>
      </Header>

      <Content style={{ padding: '16px' }}>
        {/* 商家基础信息卡片 */}
        <Card 
          style={{ marginBottom: '16px' }}
          actions={[
            <Button 
              key="edit" 
              type="link" 
              icon={<EditOutlined />}
              onClick={() => setCurrentView('edit')}
            >
              编辑信息
            </Button>
          ]}
        >
          <Row align="middle" justify="space-between">
            <Col>
              <Title level={3} style={{ margin: 0 }}>
                {merchantData.name}
              </Title>
              {merchantData.description && (
                <Text type="secondary">{merchantData.description}</Text>
              )}
              {merchantData.address && (
                <div style={{ marginTop: '8px' }}>
                  <Text type="secondary">📍 {merchantData.address}</Text>
                </div>
              )}
            </Col>
            <Col>
              <Space direction="vertical" align="end">
                <Text 
                  strong 
                  style={{ 
                    color: subscriptionInfo.color,
                    fontSize: '16px'
                  }}
                >
                  {subscriptionInfo.text}
                </Text>
                <Text type="secondary">ID: {merchantData.merchant_id}</Text>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* 数据统计卡片 */}
        <Card title="📊 经营数据" style={{ marginBottom: '16px' }}>
          <Row gutter={16}>
            <Col span={12}>
              <Statistic
                title="总浏览量"
                value={merchantStats?.total_views || merchantData.view_count}
                prefix={<EyeOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="平均评分"
                value={merchantStats?.rating_avg || merchantData.rating_avg}
                suffix={`/ 5.0 (${merchantStats?.rating_count || merchantData.rating_count}评)`}
                prefix={<StarOutlined />}
                valueStyle={{ color: '#faad14' }}
                precision={1}
              />
            </Col>
          </Row>
          
          {merchantStats && (
            <Row gutter={16} style={{ marginTop: '16px' }}>
              <Col span={12}>
                <Statistic
                  title="商品总数"
                  value={merchantStats.products_count}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="收藏次数"
                  value={merchantStats.total_favorites}
                  prefix={<HeartOutlined />}
                  valueStyle={{ color: '#eb2f96' }}
                />
              </Col>
            </Row>
          )}
        </Card>

        {/* 联系方式卡片 */}
        <Card title="📱 联系方式" style={{ marginBottom: '16px' }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Row align="middle" justify="space-between">
              <Col>
                <Space>
                  {contactInfo.icon}
                  <Text>{contactInfo.text}</Text>
                </Space>
              </Col>
              <Col>
                <Button 
                  type="primary" 
                  size="small"
                  onClick={handleContactClick}
                >
                  查看详情
                </Button>
              </Col>
            </Row>
            
            {contactInfo.type === 'anonymous' && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                🔒 客户可直接通过Bot与您匿名沟通，保护双方隐私
              </Text>
            )}
          </Space>
        </Card>

        {/* 快捷操作卡片 */}
        <Card title="🚀 快捷操作">
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Button 
                type="primary" 
                block 
                icon={<ShopOutlined />}
                onClick={() => setCurrentView('products')}
              >
                管理商品
              </Button>
            </Col>
            <Col span={12}>
              <Button 
                block 
                icon={<BarChartOutlined />}
                onClick={() => WebApp.showAlert('数据分析功能正在开发中')}
              >
                数据分析
              </Button>
            </Col>
            <Col span={12}>
              <Button 
                block 
                icon={<HeartOutlined />}
                onClick={() => WebApp.showAlert('客户管理功能正在开发中')}
              >
                客户管理
              </Button>
            </Col>
            <Col span={12}>
              <Button 
                type="dashed" 
                block
                onClick={() => WebApp.showAlert('升级功能正在开发中')}
              >
                升级专业版
              </Button>
            </Col>
          </Row>
        </Card>

        <Divider />
        
        {/* 页脚信息 */}
        <div style={{ textAlign: 'center', padding: '16px 0' }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            本地服务平台 · 商家管理后台 v2.0
            {apiConnected ? ' · 已连接服务器' : ' · 离线模式'}
          </Text>
        </div>
      </Content>
    </Layout>
  );
};

export default App;