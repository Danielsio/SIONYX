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
  Descriptions,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  EyeOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';
import {
  getAllPackages,
  createPackage,
  updatePackage,
  deletePackage,
  calculateFinalPrice,
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

  const user = useAuthStore(state => state.user);
  const {
    packages,
    setPackages,
    updatePackage: updateStorePackage,
    removePackage,
  } = useDataStore();

  useEffect(() => {
    loadPackages();
  }, []);

  const loadPackages = async () => {
    setLoading(true);

    // Get orgId from authenticated user
    const orgId = user?.orgId || localStorage.getItem('adminOrgId');

    if (!orgId) {
      message.error('מזהה ארגון לא נמצא. אנא התחבר שוב.');
      setLoading(false);
      return;
    }

    console.log('Loading packages for organization:', orgId);

    const result = await getAllPackages(orgId);

    if (result.success) {
      setPackages(result.packages);
      console.log(`Loaded ${result.packages.length} packages`);
    } else {
      message.error(result.error || 'נכשל בטעינת החבילות');
      console.error('Failed to load packages:', result.error);
    }

    setLoading(false);
  };

  const handleCreate = () => {
    setEditingPackage(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = record => {
    setEditingPackage(record);
    form.setFieldsValue({
      name: record.name,
      description: record.description,
      price: record.price,
      discountPercent: record.discountPercent || 0,
      minutes: record.minutes || 0,
      prints: record.prints || 0,
    });
    setModalVisible(true);
  };

  const handleView = record => {
    setViewingPackage(record);
    setViewModalVisible(true);
  };

  const handleDelete = async record => {
    // Get orgId
    const orgId = user?.orgId || localStorage.getItem('adminOrgId');

    if (!orgId) {
      message.error('מזהה ארגון לא נמצא. אנא התחבר שוב.');
      return;
    }

    console.log('Deleting package:', record.id, 'from org:', orgId);

    const result = await deletePackage(orgId, record.id);

    if (result.success) {
      message.success('החבילה נמחקה בהצלחה');
      removePackage(record.id);
    } else {
      message.error(result.error || 'נכשל במחיקת החבילה');
      console.error('Failed to delete package:', result.error);
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();

      // Get orgId
      const orgId = user?.orgId || localStorage.getItem('adminOrgId');

      if (!orgId) {
        message.error('מזהה ארגון לא נמצא. אנא התחבר שוב.');
        return;
      }

      if (editingPackage) {
        // Update existing package
        console.log('Updating package:', editingPackage.id, 'in org:', orgId);
        const result = await updatePackage(orgId, editingPackage.id, values);

        if (result.success) {
          message.success('החבילה עודכנה בהצלחה');
          updateStorePackage(editingPackage.id, values);
          setModalVisible(false);
        } else {
          message.error(result.error || 'נכשל בעדכון החבילה');
          console.error('Failed to update package:', result.error);
        }
      } else {
        // Create new package
        console.log('Creating new package in org:', orgId);
        const result = await createPackage(orgId, values);

        if (result.success) {
          message.success('החבילה נוצרה בהצלחה');
          // Reload to get the new package with ID
          await loadPackages();
          setModalVisible(false);
        } else {
          message.error(result.error || 'נכשל ביצירת החבילה');
          console.error('Failed to create package:', result.error);
        }
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const columns = [
    {
      title: 'שם החבילה',
      dataIndex: 'name',
      key: 'name',
      render: name => (
        <Space>
          <AppstoreOutlined style={{ color: '#1890ff' }} />
          <Text strong>{name}</Text>
        </Space>
      ),
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: 'מחיר',
      dataIndex: 'price',
      key: 'price',
      render: price => `₪${price?.toFixed(2) || '0.00'}`,
      sorter: (a, b) => a.price - b.price,
    },
    {
      title: 'הנחה',
      dataIndex: 'discountPercent',
      key: 'discountPercent',
      render: discount => (discount ? `${discount}%` : 'אין'),
      sorter: (a, b) => (a.discountPercent || 0) - (b.discountPercent || 0),
    },
    {
      title: 'מחיר סופי',
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
      title: 'זמן',
      dataIndex: 'minutes',
      key: 'minutes',
      render: minutes => {
        if (!minutes || minutes === 0) return '-';
        if (minutes < 60) return `${minutes}ד`;
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return mins > 0 ? `${hours}ש ${mins}ד` : `${hours}ש`;
      },
      sorter: (a, b) => (a.minutes || 0) - (b.minutes || 0),
    },
    {
      title: 'הדפסות',
      dataIndex: 'prints',
      key: 'prints',
      render: prints => prints || 0,
      sorter: (a, b) => (a.prints || 0) - (b.prints || 0),
    },
    {
      title: 'סטטוס',
      key: 'status',
      render: (_, record) => {
        const hasTime = record.minutes > 0;
        const hasPrints = record.prints > 0;
        return (
          <Space>
            {hasTime && <Tag color='blue'>זמן</Tag>}
            {hasPrints && <Tag color='green'>הדפסות</Tag>}
            {!hasTime && !hasPrints && <Tag>ריק</Tag>}
          </Space>
        );
      },
    },
    {
      title: 'פעולה',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type='link'
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
            size='small'
          >
            צפה
          </Button>
          <Button
            type='link'
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size='small'
          >
            ערוך
          </Button>
          <Popconfirm
            title='מחק חבילה'
            description='האם אתה בטוח שברצונך למחוק את החבילה הזו?'
            onConfirm={() => handleDelete(record)}
            okText='כן'
            cancelText='לא'
            okType='danger'
          >
            <Button type='link' danger icon={<DeleteOutlined />} size='small'>
              מחק
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ direction: 'rtl' }}>
      <Space direction='vertical' size='large' style={{ width: '100%' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ marginBottom: 8 }}>
              חבילות
            </Title>
            <Text type='secondary'>נהל חבילות זמינות לרכישה בארגון שלך</Text>
          </div>
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadPackages} loading={loading}>
              רענן
            </Button>
            <Button type='primary' icon={<PlusOutlined />} onClick={handleCreate}>
              הוסף חבילה
            </Button>
          </Space>
        </div>

        {/* Packages Table */}
        <Card>
          <Table
            columns={columns}
            dataSource={packages}
            rowKey='id'
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: total => `סך ${total} חבילות`,
            }}
          />
        </Card>
      </Space>

      {/* Create/Edit Modal */}
      <Modal
        title={editingPackage ? 'ערוך חבילה' : 'יצירת חבילה חדשה'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        width={600}
        okText={editingPackage ? 'עדכן' : 'צור'}
      >
        <Form form={form} layout='vertical' style={{ marginTop: 24 }}>
          <Form.Item
            name='name'
            label='שם החבילה'
            rules={[{ required: true, message: 'אנא הזן שם חבילה' }]}
          >
            <Input placeholder='למשל, חבילת בסיס, חבילה פרמיום' />
          </Form.Item>

          <Form.Item
            name='description'
            label='תיאור'
            rules={[{ required: true, message: 'אנא הזן תיאור' }]}
          >
            <TextArea rows={3} placeholder='תאר מה החבילה כוללת...' />
          </Form.Item>

          <Form.Item
            name='price'
            label='מחיר (₪)'
            rules={[
              { required: true, message: 'אנא הזן מחיר' },
              { type: 'number', min: 0, message: 'המחיר חייב להיות חיובי' },
            ]}
          >
            <InputNumber style={{ width: '100%' }} precision={2} placeholder='0.00' prefix='₪' />
          </Form.Item>

          <Form.Item
            name='discountPercent'
            label='הנחה (%)'
            rules={[
              { type: 'number', min: 0, max: 100, message: 'הנחה חייבת להיות בין 0-100' },
            ]}
          >
            <InputNumber style={{ width: '100%' }} placeholder='0' min={0} max={100} />
          </Form.Item>

          <Form.Item
            name='minutes'
            label='זמן (דקות)'
            rules={[{ type: 'number', min: 0, message: 'הזמן חייב להיות חיובי' }]}
          >
            <InputNumber style={{ width: '100%' }} placeholder='0' min={0} />
          </Form.Item>

          <Form.Item
            name='prints'
            label='מספר הדפסות'
            rules={[{ type: 'number', min: 0, message: 'הדפסות חייבות להיות חיוביות' }]}
          >
            <InputNumber style={{ width: '100%' }} placeholder='0' min={0} />
          </Form.Item>
        </Form>
      </Modal>

      {/* View Package Modal */}
      <Modal
        title='פרטי חבילה'
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        footer={[
          <Button key='close' onClick={() => setViewModalVisible(false)}>
            סגור
          </Button>,
          <Button
            key='edit'
            type='primary'
            icon={<EditOutlined />}
            onClick={() => {
              setViewModalVisible(false);
              handleEdit(viewingPackage);
            }}
          >
            ערוך
          </Button>,
        ]}
        width={600}
      >
        {viewingPackage && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label='שם החבילה'>
              <Text strong>{viewingPackage.name}</Text>
            </Descriptions.Item>
            <Descriptions.Item label='תיאור'>{viewingPackage.description}</Descriptions.Item>
            <Descriptions.Item label='מחיר מקורי'>
              ₪{viewingPackage.price?.toFixed(2) || '0.00'}
            </Descriptions.Item>
            <Descriptions.Item label='הנחה'>
              {viewingPackage.discountPercent ? `${viewingPackage.discountPercent}%` : 'אין'}
            </Descriptions.Item>
            <Descriptions.Item label='מחיר סופי'>
              <Text strong style={{ color: '#52c41a', fontSize: 18 }}>
                ₪
                {calculateFinalPrice(
                  viewingPackage.price,
                  viewingPackage.discountPercent
                ).finalPrice.toFixed(2)}
              </Text>
              {viewingPackage.discountPercent > 0 && (
                <Text type='secondary' style={{ marginLeft: 8 }}>
                  (חיסכון ₪
                  {calculateFinalPrice(
                    viewingPackage.price,
                    viewingPackage.discountPercent
                  ).savings.toFixed(2)}
                  )
                </Text>
              )}
            </Descriptions.Item>
            <Descriptions.Item label='זמן כלול'>
              {viewingPackage.minutes
                ? viewingPackage.minutes < 60
                  ? `${viewingPackage.minutes} דקות`
                  : `${Math.floor(viewingPackage.minutes / 60)} שעות ${viewingPackage.minutes % 60 > 0 ? `${viewingPackage.minutes % 60} דקות` : ''}`
                : 'אין'}
            </Descriptions.Item>
            <Descriptions.Item label='הדפסות כלולות'>
              {viewingPackage.prints || 0}
            </Descriptions.Item>
            <Descriptions.Item label='נוצר'>
              {viewingPackage.createdAt
                ? dayjs(viewingPackage.createdAt).format('MMMM D, YYYY HH:mm')
                : 'לא זמין'}
            </Descriptions.Item>
            <Descriptions.Item label='עודכן לאחרונה'>
              {viewingPackage.updatedAt
                ? dayjs(viewingPackage.updatedAt).format('MMMM D, YYYY HH:mm')
                : 'לא זמין'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default PackagesPage;
