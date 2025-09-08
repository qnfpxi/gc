import React, { useEffect, useState } from 'react';
import { 
  Table, 
  Button, 
  Space, 
  Tag, 
  Popconfirm, 
  message, 
  Card, 
  Row, 
  Col, 
  Input, 
  Select,
  Typography,
  Spin,
  Empty
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  EyeOutlined,
  SearchOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import productAPI, { ProductListItem, ProductSearchResponse } from '../../services/productAPI';
import { Link } from 'react-router-dom';

const { Title } = Typography;
const { Search } = Input;
const { Option } = Select;

interface ProductListProps {
  onEdit: (productId: number) => void;
  onCreate: () => void;
}

const ProductList: React.FC<ProductListProps> = ({ onEdit, onCreate }) => {
  const [searchParams, setSearchParams] = useState({
    page: 1,
    per_page: 10,
    q: '',
    status: '',
    category_id: undefined as number | undefined
  });
  
  const queryClient = useQueryClient();

  // 获取商品列表
  const { data, isLoading, isError, error, refetch } = useQuery<ProductSearchResponse>({
    queryKey: ['products', searchParams],
    queryFn: () => productAPI.getProducts(searchParams),
    keepPreviousData: true
  });

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchParams(prev => ({
      ...prev,
      q: value,
      page: 1
    }));
  };

  // 处理状态筛选
  const handleStatusChange = (value: string) => {
    setSearchParams(prev => ({
      ...prev,
      status: value,
      page: 1
    }));
  };

  // 处理分页
  const handleTableChange = (pagination: any) => {
    setSearchParams(prev => ({
      ...prev,
      page: pagination.current,
      per_page: pagination.pageSize
    }));
  };

  // 删除商品
  const handleDelete = async (productId: number) => {
    try {
      await productAPI.deleteProduct(productId);
      message.success('商品删除成功');
      queryClient.invalidateQueries({ queryKey: ['products'] });
    } catch (error: any) {
      message.error('删除失败: ' + error.message);
    }
  };

  // 获取状态标签颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'inactive': return 'orange';
      case 'discontinued': return 'red';
      default: return 'default';
    }
  };

  // 获取库存状态标签颜色
  const getStockStatusColor = (stockStatus: string) => {
    switch (stockStatus) {
      case 'in_stock': return 'green';
      case 'low_stock': return 'orange';
      case 'out_of_stock': return 'red';
      default: return 'default';
    }
  };

  const columns = [
    {
      title: '商品名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <Typography.Text strong>{text}</Typography.Text>
      )
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number, record: ProductListItem) => (
        price ? `¥${price.toFixed(2)}` : '面议'
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {status === 'active' ? '上架' : status === 'inactive' ? '下架' : '已停产'}
        </Tag>
      )
    },
    {
      title: '库存状态',
      dataIndex: 'stock_status',
      key: 'stock_status',
      render: (stockStatus: string) => (
        <Tag color={getStockStatusColor(stockStatus)}>
          {stockStatus === 'in_stock' ? '有库存' : stockStatus === 'low_stock' ? '库存不足' : '缺货'}
        </Tag>
      )
    },
    {
      title: '浏览量',
      dataIndex: 'view_count',
      key: 'view_count',
      sorter: (a: ProductListItem, b: ProductListItem) => a.view_count - b.view_count
    },
    {
      title: '收藏数',
      dataIndex: 'favorite_count',
      key: 'favorite_count',
      sorter: (a: ProductListItem, b: ProductListItem) => a.favorite_count - b.favorite_count
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ProductListItem) => (
        <Space size="middle">
          <Button 
            type="link" 
            icon={<EyeOutlined />} 
            onClick={() => message.info('查看详情功能正在开发中')}
          >
            查看
          </Button>
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => onEdit(record.id)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个商品吗？"
            description="删除后无法恢复"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载中...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <Card>
        <Empty 
          description={
            <span>
              数据加载失败: {(error as Error).message}
            </span>
          }
        >
          <Button type="primary" onClick={() => refetch()}>
            重新加载
          </Button>
        </Empty>
      </Card>
    );
  }

  return (
    <Card>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Title level={4} style={{ margin: 0 }}>商品管理</Title>
        </Col>
        <Col>
          <Space>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={onCreate}
            >
              添加商品
            </Button>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => refetch()}
            >
              刷新
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 搜索和筛选区域 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Search
            placeholder="搜索商品名称或描述"
            allowClear
            enterButton={<SearchOutlined />}
            onSearch={handleSearch}
            defaultValue={searchParams.q}
          />
        </Col>
        <Col span={6}>
          <Select
            style={{ width: '100%' }}
            placeholder="状态筛选"
            allowClear
            onChange={handleStatusChange}
            defaultValue={searchParams.status}
          >
            <Option value="">全部状态</Option>
            <Option value="active">上架</Option>
            <Option value="inactive">下架</Option>
            <Option value="discontinued">已停产</Option>
          </Select>
        </Col>
      </Row>

      {/* 商品表格 */}
      <Table
        columns={columns}
        dataSource={data?.products || []}
        rowKey="id"
        pagination={{
          current: searchParams.page,
          pageSize: searchParams.per_page,
          total: data?.total || 0,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`
        }}
        onChange={handleTableChange}
        locale={{
          emptyText: (
            <Empty description="暂无商品数据">
              <Button type="primary" onClick={onCreate}>
                添加第一个商品
              </Button>
            </Empty>
          )
        }}
      />
    </Card>
  );
};

export default ProductList;