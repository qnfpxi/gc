import React, { useState, useEffect } from 'react';
import {
  Form,
  Input,
  Button,
  Card,
  Select,
  message,
  Space,
  Typography,
  Divider,
  Row,
  Col
} from 'antd';
import {
  SaveOutlined,
  EditOutlined,
  UndoOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { merchantAPI, MerchantInfo, MerchantUpdateRequest } from '../services/merchantAPI';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface EditMerchantProps {
  merchantInfo: MerchantInfo;
  onUpdateSuccess: (updatedInfo: MerchantInfo) => void;
  onCancel: () => void;
}

const EditMerchant: React.FC<EditMerchantProps> = ({
  merchantInfo,
  onUpdateSuccess,
  onCancel
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // 地区选项（实际项目中应该从API获取）
  const regionOptions = [
    { value: 1, label: '北京市' },
    { value: 7, label: '上海市' },
    { value: 12, label: '广州市' },
    { value: 4, label: '深圳市' },
  ];

  // 联系方式类型选项
  const contactTypes = [
    { value: 'phone', label: '📱 手机号码' },
    { value: 'telegram', label: '💬 Telegram' },
    { value: 'wechat', label: '💚 微信' },
  ];

  useEffect(() => {
    // 初始化表单数据
    form.setFieldsValue({
      name: merchantInfo.name,
      description: merchantInfo.description || '',
      region_id: merchantInfo.region_id,
      address: merchantInfo.address || '',
      contact_phone: merchantInfo.contact_phone || '',
      contact_telegram: merchantInfo.contact_telegram || '',
      contact_wechat: merchantInfo.contact_wechat || '',
    });
  }, [merchantInfo, form]);

  // 监听表单变化
  const handleValuesChange = () => {
    setHasChanges(true);
  };

  // 提交更新
  const handleSubmit = async (values: any) => {
    setLoading(true);
    
    try {
      // 构建更新请求数据
      const updateData: MerchantUpdateRequest = {
        name: values.name.trim(),
        description: values.description?.trim() || undefined,
        region_id: values.region_id,
        address: values.address?.trim() || undefined,
        contact_phone: values.contact_phone?.trim() || undefined,
        contact_telegram: values.contact_telegram?.trim() || undefined,
        contact_wechat: values.contact_wechat?.trim() || undefined,
      };

      // 调用API更新
      const updatedMerchant = await merchantAPI.updateMerchant(
        merchantInfo.merchant_id,
        updateData
      );

      message.success('商家信息更新成功！');
      setHasChanges(false);
      onUpdateSuccess(updatedMerchant);

    } catch (error: any) {
      console.error('更新失败:', error);
      message.error(error.message || '更新失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 重置表单
  const handleReset = () => {
    form.resetFields();
    setHasChanges(false);
  };

  // 获取联系方式显示文本
  const getContactDisplay = () => {
    const { contact_phone, contact_telegram, contact_wechat } = merchantInfo;
    
    if (contact_phone) {
      return `📱 ${contact_phone}`;
    } else if (contact_telegram) {
      return `💬 ${contact_telegram}`;
    } else if (contact_wechat) {
      return `💚 ${contact_wechat}`;
    } else {
      return '🔒 TG匿名聊天';
    }
  };

  return (
    <Card
      title={
        <Space>
          <EditOutlined />
          <span>编辑商家信息</span>
        </Space>
      }
      extra={
        <Button 
          type="text" 
          onClick={onCancel}
          disabled={loading}
        >
          返回
        </Button>
      }
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        onValuesChange={handleValuesChange}
        size="large"
      >
        {/* 基础信息 */}
        <Title level={4}>📝 基础信息</Title>
        
        <Form.Item
          name="name"
          label="店铺名称"
          rules={[
            { required: true, message: '请输入店铺名称' },
            { min: 2, message: '店铺名称至少2个字符' },
            { max: 50, message: '店铺名称不超过50个字符' }
          ]}
        >
          <Input 
            placeholder="请输入店铺名称"
            showCount
            maxLength={50}
          />
        </Form.Item>

        <Form.Item
          name="description"
          label="店铺描述"
          rules={[
            { max: 500, message: '描述不超过500个字符' }
          ]}
        >
          <TextArea
            rows={3}
            placeholder="请简单介绍您的店铺特色、主营业务等"
            showCount
            maxLength={500}
          />
        </Form.Item>

        <Divider />

        {/* 位置信息 */}
        <Title level={4}>📍 位置信息</Title>
        
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="region_id"
              label="所在地区"
              rules={[{ required: true, message: '请选择所在地区' }]}
            >
              <Select placeholder="请选择地区">
                {regionOptions.map(region => (
                  <Option key={region.value} value={region.value}>
                    {region.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="address"
              label="详细地址"
              rules={[
                { max: 200, message: '地址不超过200个字符' }
              ]}
            >
              <Input 
                placeholder="街道、门牌号等"
                showCount
                maxLength={200}
              />
            </Form.Item>
          </Col>
        </Row>

        <Divider />

        {/* 联系方式 */}
        <Title level={4}>📱 联系方式</Title>
        <Text type="secondary" style={{ marginBottom: '16px', display: 'block' }}>
          当前联系方式：{getContactDisplay()}
        </Text>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="contact_phone"
              label="手机号码"
              rules={[
                { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码' }
              ]}
            >
              <Input placeholder="13800138000" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="contact_telegram"
              label="Telegram"
              rules={[
                { pattern: /^@[a-zA-Z0-9_]{5,32}$/, message: '请输入正确的Telegram用户名' }
              ]}
            >
              <Input placeholder="@username" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="contact_wechat"
              label="微信号"
              rules={[
                { min: 6, message: '微信号至少6个字符' },
                { max: 20, message: '微信号不超过20个字符' }
              ]}
            >
              <Input placeholder="wechat_id" />
            </Form.Item>
          </Col>
        </Row>

        <Text type="secondary" style={{ fontSize: '12px' }}>
          💡 提示：至少填写一种联系方式。如果都不填写，将使用TG匿名聊天功能。
        </Text>

        <Divider />

        {/* 操作按钮 */}
        <Form.Item style={{ marginTop: '32px', marginBottom: 0 }}>
          <Space size="large">
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<SaveOutlined />}
              size="large"
              disabled={!hasChanges}
            >
              {loading ? '保存中...' : '保存修改'}
            </Button>
            
            <Button
              onClick={handleReset}
              icon={<UndoOutlined />}
              disabled={loading || !hasChanges}
            >
              重置
            </Button>
            
            <Button
              onClick={onCancel}
              disabled={loading}
            >
              取消
            </Button>
          </Space>
        </Form.Item>

        {hasChanges && (
          <div style={{ 
            marginTop: '16px', 
            padding: '8px 12px', 
            background: '#fff7e6', 
            border: '1px solid #ffd591',
            borderRadius: '6px'
          }}>
            <Text type="warning">
              <CheckCircleOutlined /> 您有未保存的修改
            </Text>
          </div>
        )}
      </Form>
    </Card>
  );
};

export default EditMerchant;