import { useEffect, useState } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Typography,
  Modal,
  Form,
  Input,
  InputNumber,
  message,
  Popconfirm,
  Tag,
  Descriptions
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  EyeOutlined,
  AppstoreOutlined
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';
import { 
  getAllPackages, 
  createPackage, 
  updatePackage, 
  deletePackage,
  calculateFinalPrice
} from '../services/packageService';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { TextArea } = Input;

const PackagesPage = () => {
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [editingPackage, setEditingPackage] = useState(null);
  const [viewingPackage, setViewingPackage] = useState(null);
  const [form] = Form.useForm();

  const user = useAuthStore((state) => state.user);
  const { packages, setPackages, updatePackage: updateStorePackage, removePackage } = useDataStore();

  useEffect(() => {
    loadPackages();
  }, []);

  const loadPackages = async () => {
    setLoading(true);
    
    // Get orgId from authenticated user
    const orgId = user?.orgId || localStorage.getItem('adminOrgId');

    if (!orgId) {
      message.error('Organization ID not found. Please log in again.');
      setLoading(false);
      return;
    }

    console.log('Loading packages for organization:', orgId);

    const result = await getAllPackages(orgId);

    if (result.success) {
      setPackages(result.packages);
      console.log(`Loaded ${result.packages.length} packages`);
    } else {
      message.error(result.error || 'Failed to load packages');
      console.error('Failed to load packages:', result.error);
    }

    setLoading(false);
  };

  const handleCreate = () => {
    setEditingPackage(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingPackage(record);
    form.setFieldsValue({
      name: record.name,
      description: record.description,
      price: record.price,
      discountPercent: record.discountPercent || 0,
      timeMinutes: record.timeMinutes || 0,
      prints: record.prints || 0,
    });
    setModalVisible(true);
  };

  const handleView = (record) => {
    setViewingPackage(record);
    setViewModalVisible(true);
  };

  const handleDelete = async (record) => {
    // Get orgId
    const orgId = user?.orgId || localStorage.getItem('adminOrgId');
    
    if (!orgId) {
      message.error('Organization ID not found. Please log in again.');
      return;
    }

    console.log('Deleting package:', record.id, 'from org:', orgId);
    
    const result = await deletePackage(orgId, record.id);

    if (result.success) {
      message.success('Package deleted successfully');
      removePackage(record.id);
    } else {
      message.error(result.error || 'Failed to delete package');
      console.error('Failed to delete package:', result.error);
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      // Get orgId
      const orgId = user?.orgId || localStorage.getItem('adminOrgId');

      if (!orgId) {
        message.error('Organization ID not found. Please log in again.');
        return;
      }

      if (editingPackage) {
        // Update existing package
        console.log('Updating package:', editingPackage.id, 'in org:', orgId);
        const result = await updatePackage(orgId, editingPackage.id, values);
        
        if (result.success) {
          message.success('Package updated successfully');
          updateStorePackage(editingPackage.id, values);
          setModalVisible(false);
        } else {
          message.error(result.error || 'Failed to update package');
          console.error('Failed to update package:', result.error);
        }
      } else {
        // Create new package
        console.log('Creating new package in org:', orgId);
        const result = await createPackage(orgId, values);
        
        if (result.success) {
          message.success('Package created successfully');
          // Reload to get the new package with ID
          await loadPackages();
          setModalVisible(false);
        } else {
          message.error(result.error || 'Failed to create package');
          console.error('Failed to create package:', result.error);
        }
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const columns = [
    {
      title: 'Package Name',
      dataIndex: 'name',
      key: 'name',
      render: (name) => (
        <Space>
          <AppstoreOutlined style={{ color: '#1890ff' }} />
          <Text strong>{name}</Text>
        </Space>
      ),
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      render: (price) => `₪${price?.toFixed(2) || '0.00'}`,
      sorter: (a, b) => a.price - b.price,
    },
    {
      title: 'Discount',
      dataIndex: 'discountPercent',
      key: 'discountPercent',
      render: (discount) => discount ? `${discount}%` : 'None',
      sorter: (a, b) => (a.discountPercent || 0) - (b.discountPercent || 0),
    },
    {
      title: 'Final Price',
      key: 'finalPrice',
      render: (_, record) => {
        const { finalPrice } = calculateFinalPrice(record.price, record.discountPercent);
        return (
          <Text strong style={{ color: '#52c41a' }}>
            ₪{finalPrice.toFixed(2)}
          </Text>
        );
      },
      sorter: (a, b) => {
        const priceA = calculateFinalPrice(a.price, a.discountPercent).finalPrice;
        const priceB = calculateFinalPrice(b.price, b.discountPercent).finalPrice;
        return priceA - priceB;
      },
    },
    {
      title: 'Time',
      dataIndex: 'timeMinutes',
      key: 'timeMinutes',
      render: (minutes) => {
        if (!minutes || minutes === 0) return '-';
        if (minutes < 60) return `${minutes}m`;
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
      },
      sorter: (a, b) => (a.timeMinutes || 0) - (b.timeMinutes || 0),
    },
    {
      title: 'Prints',
      dataIndex: 'prints',
      key: 'prints',
      render: (prints) => prints || 0,
      sorter: (a, b) => (a.prints || 0) - (b.prints || 0),
    },
    {
      title: 'Status',
      key: 'status',
      render: (_, record) => {
        const hasTime = record.timeMinutes > 0;
        const hasPrints = record.prints > 0;
        return (
          <Space>
            {hasTime && <Tag color="blue">Time</Tag>}
            {hasPrints && <Tag color="green">Prints</Tag>}
            {!hasTime && !hasPrints && <Tag>Empty</Tag>}
          </Space>
        );
      },
    },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
            size="small"
          >
            View
          </Button>
          <Button 
            type="link" 
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            Edit
          </Button>
          <Popconfirm
            title="Delete package"
            description="Are you sure you want to delete this package?"
            onConfirm={() => handleDelete(record)}
            okText="Yes"
            cancelText="No"
            okType="danger"
          >
            <Button 
              type="link" 
              danger
              icon={<DeleteOutlined />}
              size="small"
            >
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ marginBottom: 8 }}>
              Packages
            </Title>
            <Text type="secondary">
              Manage packages available for purchase in your organization
            </Text>
          </div>
          <Space>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={loadPackages}
              loading={loading}
            >
              Refresh
            </Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              Add Package
            </Button>
          </Space>
        </div>

        {/* Packages Table */}
        <Card>
          <Table
            columns={columns}
            dataSource={packages}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} packages`,
            }}
          />
        </Card>
      </Space>

      {/* Create/Edit Modal */}
      <Modal
        title={editingPackage ? 'Edit Package' : 'Create New Package'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        width={600}
        okText={editingPackage ? 'Update' : 'Create'}
      >
        <Form
          form={form}
          layout="vertical"
          style={{ marginTop: 24 }}
        >
          <Form.Item
            name="name"
            label="Package Name"
            rules={[{ required: true, message: 'Please enter package name' }]}
          >
            <Input placeholder="e.g., Basic Plan, Premium Package" />
          </Form.Item>

          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: 'Please enter description' }]}
          >
            <TextArea 
              rows={3} 
              placeholder="Describe what this package includes..."
            />
          </Form.Item>

          <Form.Item
            name="price"
            label="Price (₪)"
            rules={[
              { required: true, message: 'Please enter price' },
              { type: 'number', min: 0, message: 'Price must be positive' }
            ]}
          >
            <InputNumber 
              style={{ width: '100%' }}
              precision={2}
              placeholder="0.00"
              prefix="₪"
            />
          </Form.Item>

          <Form.Item
            name="discountPercent"
            label="Discount (%)"
            rules={[
              { type: 'number', min: 0, max: 100, message: 'Discount must be between 0-100' }
            ]}
          >
            <InputNumber 
              style={{ width: '100%' }}
              placeholder="0"
              min={0}
              max={100}
            />
          </Form.Item>

          <Form.Item
            name="timeMinutes"
            label="Time (minutes)"
            rules={[
              { type: 'number', min: 0, message: 'Time must be positive' }
            ]}
          >
            <InputNumber 
              style={{ width: '100%' }}
              placeholder="0"
              min={0}
            />
          </Form.Item>

          <Form.Item
            name="prints"
            label="Number of Prints"
            rules={[
              { type: 'number', min: 0, message: 'Prints must be positive' }
            ]}
          >
            <InputNumber 
              style={{ width: '100%' }}
              placeholder="0"
              min={0}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* View Package Modal */}
      <Modal
        title="Package Details"
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            Close
          </Button>,
          <Button 
            key="edit" 
            type="primary"
            icon={<EditOutlined />}
            onClick={() => {
              setViewModalVisible(false);
              handleEdit(viewingPackage);
            }}
          >
            Edit
          </Button>
        ]}
        width={600}
      >
        {viewingPackage && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="Package Name">
              <Text strong>{viewingPackage.name}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="Description">
              {viewingPackage.description}
            </Descriptions.Item>
            <Descriptions.Item label="Original Price">
              ₪{viewingPackage.price?.toFixed(2) || '0.00'}
            </Descriptions.Item>
            <Descriptions.Item label="Discount">
              {viewingPackage.discountPercent ? `${viewingPackage.discountPercent}%` : 'None'}
            </Descriptions.Item>
            <Descriptions.Item label="Final Price">
              <Text strong style={{ color: '#52c41a', fontSize: 18 }}>
                ₪{calculateFinalPrice(viewingPackage.price, viewingPackage.discountPercent).finalPrice.toFixed(2)}
              </Text>
              {viewingPackage.discountPercent > 0 && (
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  (Save ₪{calculateFinalPrice(viewingPackage.price, viewingPackage.discountPercent).savings.toFixed(2)})
                </Text>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="Time Included">
              {viewingPackage.timeMinutes ? (
                viewingPackage.timeMinutes < 60 
                  ? `${viewingPackage.timeMinutes} minutes`
                  : `${Math.floor(viewingPackage.timeMinutes / 60)} hours ${viewingPackage.timeMinutes % 60 > 0 ? `${viewingPackage.timeMinutes % 60} minutes` : ''}`
              ) : 'None'}
            </Descriptions.Item>
            <Descriptions.Item label="Prints Included">
              {viewingPackage.prints || 0}
            </Descriptions.Item>
            <Descriptions.Item label="Created">
              {viewingPackage.createdAt 
                ? dayjs(viewingPackage.createdAt).format('MMMM D, YYYY HH:mm')
                : 'N/A'
              }
            </Descriptions.Item>
            <Descriptions.Item label="Last Updated">
              {viewingPackage.updatedAt 
                ? dayjs(viewingPackage.updatedAt).format('MMMM D, YYYY HH:mm')
                : 'N/A'
              }
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default PackagesPage;

