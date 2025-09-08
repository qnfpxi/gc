import React, { useEffect, useState } from 'react';
import { 
  Form, 
  Input, 
  InputNumber, 
  Select, 
  Switch, 
  Button, 
  Card, 
  Row, 
  Col, 
  Space, 
  message,
  Upload,
  Modal,
  Typography
} from 'antd';
import { 
  UploadOutlined, 
  SaveOutlined, 
  RollbackOutlined,
  PlusOutlined,
  MinusCircleOutlined
} from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import productAPI, { ProductInfo, ProductCreateRequest, ProductUpdateRequest } from '../../services/productAPI';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface ProductFormProps {
  productId?: number;
  onCancel: () => void;
  onSuccess: () => void;
}

const ProductForm: React.FC<ProductFormProps> = ({ productId, onCancel, onSuccess }) => {
  const [form] = Form.useForm();
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewImage, setPreviewImage] = useState('');
  const [fileList, setFileList] = useState<any[]>([]);
  const queryClient = useQueryClient();

  // 获取商品详情（编辑模式）
  useEffect(() => {
    if (productId) {
      productAPI.getProductById(productId).then(product => {
        form.setFieldsValue({
          name: product.name,
          description: product.description,
          price: product.price,
          price_unit: product.price_unit,
          is_price_negotiable: product.is_price_negotiable,
          currency: product.currency,
          category_id: product.category_id,
          tags: product.tags,
          status: product.status,
          sort_order: product.sort_order
        });
        
        // 设置图片列表
        if (product.image_urls && product.image_urls.length > 0) {
          const images = product.image_urls.map((url, index) => ({
            uid: `-${index}`,
            name: `image-${index}.jpg`,
            status: 'done',
            url: url
          }));
          setFileList(images);
        }
      }).catch(error => {
        message.error('加载商品信息失败: ' + error.message);
      });
    }
  }, [productId, form]);

  // 上传图片
  const handleUploadChange = ({ fileList: newFileList }: any) => {
    setFileList(newFileList);
  };

  // 预览图片
  const handlePreview = async (file: any) => {
    if (!file.url && !file.preview) {
      file.preview = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.readAsDataURL(file.originFileObj);
        reader.onload = () => resolve(reader.result);
      });
    }
    
    setPreviewImage(file.url || file.preview);
    setPreviewOpen(true);
  };

  // 创建或更新商品
  const mutation = useMutation({
    mutationFn: (values: any) => {
      // 准备图片URL列表
      const imageUrls = fileList
        .filter(file => file.status === 'done' && file.url)
        .map(file => file.url);
      
      // 准备请求数据
      const requestData: ProductCreateRequest | ProductUpdateRequest = {
        name: values.name,
        description: values.description,
        price: values.price,
        price_unit: values.price_unit || 'unit',
        is_price_negotiable: values.is_price_negotiable || false,
        currency: values.currency || 'CNY',
        category_id: values.category_id,
        image_urls: imageUrls,
        tags: values.tags || [],
        status: values.status || 'active',
        sort_order: values.sort_order || 0
      };
      
      if (productId) {
        // 更新模式
        return productAPI.updateProduct(productId, requestData);
      } else {
        // 创建模式
        return productAPI.createProduct(requestData as ProductCreateRequest);
      }
    },
    onSuccess: () => {
      message.success(productId ? '商品更新成功' : '商品创建成功');
      queryClient.invalidateQueries({ queryKey: ['products'] });
      onSuccess();
    },
    onError: (error: any) => {
      message.error((productId ? '更新' : '创建') + '商品失败: ' + error.message);
    }
  });

  // 提交表单
  const onFinish = (values: any) => {
    mutation.mutate(values);
  };

  // 商品分类选项
  const categoryOptions = [
    { value: 1, label: '餐饮美食' },
    { value: 2, label: '生活服务' },
    { value: 3, label: '教育培训' },
    { value: 4, label: '美容美发' },
    { value: 5, label: '休闲娱乐' },
    { value: 6, label: '购物零售' },
    { value: 7, label: '交通出行' },
    { value: 8, label: '医疗健康' }
  ];

  return (
    <Card>
      <Title level={4} style={{ marginBottom: 24 }}>
        {productId ? '编辑商品' : '添加商品'}
      </Title>
      
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          price_unit: 'unit',
          currency: 'CNY',
          is_price_negotiable: false,
          status: 'active',
          sort_order: 0
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="name"
              label="商品名称"
              rules={[{ required: true, message: '请输入商品名称' }]}
            >
              <Input placeholder="请输入商品名称" />
            </Form.Item>
          </Col>
          
          <Col span={12}>
            <Form.Item
              name="category_id"
              label="商品分类"
              rules={[{ required: true, message: '请选择商品分类' }]}
            >
              <Select placeholder="请选择商品分类">
                {categoryOptions.map(option => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>
        
        <Form.Item
          name="description"
          label="商品描述"
        >
          <TextArea 
            placeholder="请输入商品详细描述" 
            autoSize={{ minRows: 3, maxRows: 6 }} 
          />
        </Form.Item>
        
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="price"
              label="价格"
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="请输入价格"
                min={0}
                step={0.01}
                formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={value => value!.replace(/\¥\s?|(,*)/g, '') as any}
              />
            </Form.Item>
          </Col>
          
          <Col span={8}>
            <Form.Item
              name="is_price_negotiable"
              label="价格可议"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
          </Col>
          
          <Col span={8}>
            <Form.Item
              name="status"
              label="商品状态"
            >
              <Select>
                <Option value="active">上架</Option>
                <Option value="inactive">下架</Option>
                <Option value="discontinued">已停产</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
        
        <Form.Item
          name="tags"
          label="商品标签"
        >
          <Select
            mode="tags"
            placeholder="输入标签后按回车确认"
            tokenSeparators={[',']}
          />
        </Form.Item>
        
        <Form.Item
          label="商品图片"
          extra="支持JPG、PNG格式，建议尺寸800x600"
        >
          <Upload
            listType="picture-card"
            fileList={fileList}
            onChange={handleUploadChange}
            onPreview={handlePreview}
            beforeUpload={() => false} // 禁用自动上传
          >
            {fileList.length >= 8 ? null : (
              <div>
                <PlusOutlined />
                <div style={{ marginTop: 8 }}>上传图片</div>
              </div>
            )}
          </Upload>
          <Modal 
            open={previewOpen} 
            title="图片预览" 
            footer={null} 
            onCancel={() => setPreviewOpen(false)}
          >
            <img alt="预览图片" style={{ width: '100%' }} src={previewImage} />
          </Modal>
        </Form.Item>
        
        <Form.Item>
          <Space>
            <Button 
              type="primary" 
              htmlType="submit" 
              icon={<SaveOutlined />}
              loading={mutation.isPending}
            >
              保存商品
            </Button>
            <Button 
              icon={<RollbackOutlined />} 
              onClick={onCancel}
            >
              取消
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default ProductForm;