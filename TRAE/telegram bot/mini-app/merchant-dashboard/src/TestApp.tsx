import React, { useEffect, useState } from 'react';
import { Layout, Card, Statistic, Row, Col, Typography, Button, Space, Alert } from 'antd';
import { 
  ShopOutlined, 
  EyeOutlined, 
  StarOutlined,
  PhoneOutlined,
  MessageOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

const TestApp: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [testPassed, setTestPassed] = useState(false);

  useEffect(() => {
    // 测试Telegram WebApp环境
    console.log('Testing Telegram WebApp environment...');
    
    // 检查Telegram WebApp对象
    const isInTelegram = !!(window as any).Telegram?.WebApp;
    console.log('Is in Telegram:', isInTelegram);
    
    if (isInTelegram) {
      const tg = (window as any).Telegram.WebApp;
      tg.ready();
      tg.expand();
      console.log('Telegram WebApp initialized');
      setTestPassed(true);
    } else {
      console.log('Not in Telegram environment - showing demo mode');
      setTestPassed(false);
    }
    
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <Content style={{ padding: '20px', textAlign: 'center' }}>
          <Title level={3}>🚀 Mini App 加载中...</Title>
          <Text>正在初始化 Telegram WebApp...</Text>
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
        <Space>
          <ShopOutlined style={{ color: 'white', fontSize: '20px' }} />
          <Title level={4} style={{ color: 'white', margin: 0 }}>
            商家管理后台测试版
          </Title>
        </Space>
      </Header>

      <Content style={{ padding: '16px' }}>
        {/* 测试状态提示 */}
        <Alert
          message={testPassed ? "✅ Telegram WebApp 环境检测成功" : "⚠️ 非 Telegram 环境 - 演示模式"}
          type={testPassed ? "success" : "warning"}
          showIcon
          style={{ marginBottom: '16px' }}
        />

        {/* Mini App 功能演示 */}
        <Card style={{ marginBottom: '16px' }}>
          <Row align="middle" justify="space-between">
            <Col>
              <Title level={3} style={{ margin: 0 }}>
                🏪 测试商家店铺
              </Title>
              <Text type="secondary">这是一个Mini App测试界面</Text>
            </Col>
            <Col>
              <Space direction="vertical" align="end">
                <Text strong style={{ color: '#52c41a', fontSize: '16px' }}>
                  免费版
                </Text>
                <Text type="secondary">ID: 001</Text>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* 数据统计 */}
        <Card title="📊 店铺数据" style={{ marginBottom: '16px' }}>
          <Row gutter={16}>
            <Col span={12}>
              <Statistic
                title="总浏览量"
                value={128}
                prefix={<EyeOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="平均评分"
                value={4.5}
                suffix="/ 5.0 (23评)"
                prefix={<StarOutlined />}
                valueStyle={{ color: '#faad14' }}
                precision={1}
              />
            </Col>
          </Row>
        </Card>

        {/* 联系方式 */}
        <Card title="📱 联系方式" style={{ marginBottom: '16px' }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Row align="middle" justify="space-between">
              <Col>
                <Space>
                  <MessageOutlined style={{ color: '#1890ff' }} />
                  <Text>TG匿名聊天已启用</Text>
                </Space>
              </Col>
              <Col>
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
              </Col>
            </Row>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              🔒 客户可直接通过Bot与您匿名沟通，保护双方隐私
            </Text>
          </Space>
        </Card>

        {/* 功能测试 */}
        <Card title="🧪 功能测试">
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Button 
                type="primary" 
                block 
                icon={<ShopOutlined />}
                onClick={() => {
                  if (testPassed) {
                    (window as any).Telegram.WebApp.showAlert('✅ Mini App 功能正常！');
                  } else {
                    alert('✅ 演示模式 - 功能正常！');
                  }
                }}
              >
                测试功能
              </Button>
            </Col>
            <Col span={12}>
              <Button 
                block 
                onClick={() => {
                  if (testPassed) {
                    (window as any).Telegram.WebApp.showConfirm('确认关闭 Mini App？', (result: boolean) => {
                      if (result) {
                        (window as any).Telegram.WebApp.close();
                      }
                    });
                  } else {
                    alert('演示模式 - 关闭功能');
                  }
                }}
              >
                关闭应用
              </Button>
            </Col>
          </Row>

          <div style={{ marginTop: '16px', padding: '12px', background: '#f6f6f6', borderRadius: '8px' }}>
            <Text strong>🔍 诊断信息：</Text>
            <br />
            <Text code>环境: {testPassed ? 'Telegram WebApp' : '浏览器'}</Text>
            <br />
            <Text code>时间: {new Date().toLocaleString()}</Text>
            <br />
            <Text code>状态: {testPassed ? '✅ 正常' : '⚠️ 演示模式'}</Text>
          </div>
        </Card>
      </Content>
    </Layout>
  );
};

export default TestApp;