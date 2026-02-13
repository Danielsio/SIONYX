import { useEffect, useState } from 'react';
import {
  Card,
  Button,
  Space,
  Typography,
  Modal,
  Form,
  Input,
  InputNumber,
  App,
  Tag,
  Descriptions,
  Row,
  Col,
  Dropdown,
  Empty,
  Spin,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  AppstoreOutlined,
  ClockCircleOutlined,
  PrinterOutlined,
  MoreOutlined,
  GiftOutlined,
  CalendarOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';
import { useOrgId } from '../hooks/useOrgId';
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
  const isAdmin = user?.isAdmin;
  const { message } = App.useApp();
  const {
    packages,
    setPackages,
    updatePackage: updateStorePackage,
    removePackage,
  } = useDataStore();
  const orgId = useOrgId();

  useEffect(() => {
    loadPackages();
  }, [orgId]);

  const loadPackages = async () => {
    setLoading(true);

    if (!orgId) {
      message.error('מזהה ארגון לא נמצא. אנא התחבר שוב.');
      setLoading(false);
      return;
    }

    const result = await getAllPackages(orgId);
    if (result.success) {
      setPackages(result.packages);
    } else {
      message.error(result.error || 'נכשל בטעינת החבילות');
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
      validityDays: record.validityDays || 0,
    });
    setModalVisible(true);
  };

  const handleView = record => {
    setViewingPackage(record);
    setViewModalVisible(true);
  };

  const handleDelete = async record => {
    if (!orgId) {
      message.error('מזהה ארגון לא נמצא.');
      return;
    }

    const result = await deletePackage(orgId, record.id);
    if (result.success) {
      message.success('החבילה נמחקה בהצלחה');
      removePackage(record.id);
    } else {
      message.error(result.error || 'נכשל במחיקת החבילה');
    }
  };

  const normalizePackageValues = values => ({
    ...values,
    discountPercent: values.discountPercent ?? 0,
    minutes: values.minutes ?? 0,
    prints: values.prints ?? 0,
    validityDays: values.validityDays ?? 0,
  });

  const handleModalOk = async () => {
    try {
      const values = normalizePackageValues(await form.validateFields());

      if (!orgId) {
        message.error('מזהה ארגון לא נמצא.');
        return;
      }

      if (editingPackage) {
        const result = await updatePackage(orgId, editingPackage.id, values);
        if (result.success) {
          message.success('החבילה עודכנה בהצלחה');
          updateStorePackage(editingPackage.id, values);
          setModalVisible(false);
        } else {
          message.error(result.error || 'נכשל בעדכון החבילה');
        }
      } else {
        const result = await createPackage(orgId, values);
        if (result.success) {
          message.success('החבילה נוצרה בהצלחה');
          await loadPackages();
          setModalVisible(false);
        } else {
          message.error(result.error || 'נכשל ביצירת החבילה');
        }
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const formatTime = minutes => {
    if (!minutes || minutes === 0) return null;
    if (minutes < 60) return `${minutes} דקות`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours} שעות ${mins} דקות` : `${hours} שעות`;
  };

  // Package Card Component
  const PackageCard = ({ pkg }) => {
    const { finalPrice, savings } = calculateFinalPrice(pkg.price, pkg.discountPercent);
    const hasDiscount = pkg.discountPercent > 0;
    const timeDisplay = formatTime(pkg.minutes);

    const menuItems = [
      { key: 'edit', icon: <EditOutlined />, label: 'ערוך', onClick: () => handleEdit(pkg) },
      { type: 'divider' },
      ...(isAdmin
        ? [
            {
              key: 'delete',
              icon: <DeleteOutlined />,
              label: 'מחק',
              danger: true,
              onClick: () => {
                Modal.confirm({
                  title: 'מחק חבילה',
                  content: `האם אתה בטוח שברצונך למחוק את "${pkg.name}"?`,
                  okText: 'מחק',
                  cancelText: 'ביטול',
                  okType: 'danger',
                  onOk: () => handleDelete(pkg),
                });
              },
            },
          ]
        : []),
    ];

    return (
      <Card
        hoverable
        onClick={() => handleView(pkg)}
        style={{
          borderRadius: 16,
          overflow: 'hidden',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}
        styles={{
          body: {
            padding: 0,
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
          },
        }}
      >
        {/* Header with gradient */}
        <div
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            padding: '20px 16px',
            color: '#fff',
            position: 'relative',
          }}
        >
          {hasDiscount && (
            <Tag
              color='#ff4d4f'
              style={{
                position: 'absolute',
                top: 12,
                left: 12,
                fontWeight: 'bold',
                borderRadius: 8,
              }}
            >
              {pkg.discountPercent}% הנחה
            </Tag>
          )}
          <div onClick={e => e.stopPropagation()} style={{ position: 'absolute', top: 8, right: 8 }}>
            <Dropdown menu={{ items: menuItems }} trigger={['click']}>
              <Button
                type='text'
                icon={<MoreOutlined />}
                style={{ color: '#fff' }}
                size='small'
              />
            </Dropdown>
          </div>
          <div style={{ textAlign: 'center', paddingTop: 8 }}>
            <GiftOutlined style={{ fontSize: 28, marginBottom: 8 }} />
            <Title level={4} style={{ color: '#fff', margin: 0 }}>
              {pkg.name}
            </Title>
          </div>
        </div>

        {/* Body */}
        <div style={{ padding: 16, flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Description */}
          <Text
            type='secondary'
            style={{
              display: 'block',
              marginBottom: 16,
              minHeight: 40,
              fontSize: 13,
            }}
            ellipsis={{ rows: 2 }}
          >
            {pkg.description || 'אין תיאור'}
          </Text>

          {/* Features */}
          <div style={{ marginBottom: 16, flex: 1 }}>
            {timeDisplay && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 12px',
                  background: '#f0f5ff',
                  borderRadius: 8,
                  marginBottom: 8,
                }}
              >
                <ClockCircleOutlined style={{ color: '#1890ff' }} />
                <Text style={{ color: '#1890ff' }}>{timeDisplay}</Text>
              </div>
            )}
            {pkg.prints > 0 && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 12px',
                  background: '#f6ffed',
                  borderRadius: 8,
                  marginBottom: pkg.validityDays > 0 ? 8 : 0,
                }}
              >
                <PrinterOutlined style={{ color: '#52c41a' }} />
                <Text style={{ color: '#52c41a' }}>₪{pkg.prints} תקציב הדפסות</Text>
              </div>
            )}
            {pkg.validityDays > 0 && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 12px',
                  background: '#fff7e6',
                  borderRadius: 8,
                }}
              >
                <CalendarOutlined style={{ color: '#fa8c16' }} />
                <Text style={{ color: '#fa8c16' }}>תקף ל-{pkg.validityDays} ימים</Text>
              </div>
            )}
          </div>

          {/* Price */}
          <div style={{ textAlign: 'center', borderTop: '1px solid #f0f0f0', paddingTop: 16 }}>
            {hasDiscount && (
              <Text delete type='secondary' style={{ fontSize: 14, display: 'block' }}>
                ₪{pkg.price?.toFixed(2)}
              </Text>
            )}
            <Title level={2} style={{ margin: 0, color: '#52c41a' }}>
              ₪{finalPrice.toFixed(2)}
            </Title>
            {hasDiscount && (
              <Text type='success' style={{ fontSize: 12 }}>
                חיסכון ₪{savings.toFixed(2)}
              </Text>
            )}
          </div>
        </div>
      </Card>
    );
  };

  return (
    <div style={{ direction: 'rtl' }}>
      {/* Header */}
      <div
        className='page-header'
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 12,
          marginBottom: 24,
        }}
      >
        <div>
          <Title level={2} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 12 }}>
            <AppstoreOutlined />
            חבילות
          </Title>
          <Text type='secondary'>נהל חבילות זמינות לרכישה בארגון שלך</Text>
        </div>
        <Space wrap>
          <Button icon={<ReloadOutlined />} onClick={loadPackages} loading={loading}>
            רענן
          </Button>
          <Button type='primary' icon={<PlusOutlined />} onClick={handleCreate}>
            הוסף חבילה
          </Button>
        </Space>
      </div>

      {/* Packages Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size='large' />
          <div style={{ marginTop: 16 }}>
            <Text type='secondary'>טוען חבילות...</Text>
          </div>
        </div>
      ) : packages.length === 0 ? (
        <Card>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description='אין חבילות'
          >
            <Button type='primary' icon={<PlusOutlined />} onClick={handleCreate}>
              צור חבילה ראשונה
            </Button>
          </Empty>
        </Card>
      ) : (
        <Row gutter={[16, 16]}>
          {packages.map(pkg => (
            <Col key={pkg.id} xs={24} sm={12} lg={8} xl={6}>
              <PackageCard pkg={pkg} />
            </Col>
          ))}
        </Row>
      )}

      {/* Create/Edit Modal */}
      <Modal
        title={editingPackage ? 'ערוך חבילה' : 'יצירת חבילה חדשה'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        width={Math.min(600, window.innerWidth - 32)}
        okText={editingPackage ? 'עדכן' : 'צור'}
        cancelText='ביטול'
      >
        <Form
          form={form}
          layout='vertical'
          style={{ marginTop: 24 }}
          initialValues={{
            discountPercent: 0,
            minutes: 0,
            prints: 0,
            validityDays: 0,
          }}
        >
          <Form.Item
            name='name'
            label='שם החבילה'
            rules={[{ required: true, message: 'אנא הזן שם חבילה' }]}
          >
            <Input placeholder='למשל, חבילת בסיס' />
          </Form.Item>

          <Form.Item
            name='description'
            label='תיאור'
            rules={[{ required: true, message: 'אנא הזן תיאור' }]}
          >
            <TextArea rows={3} placeholder='תאר מה החבילה כוללת...' />
          </Form.Item>

          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                name='price'
                label='מחיר (₪)'
                rules={[
                  { required: true, message: 'אנא הזן מחיר' },
                  { type: 'number', min: 0, message: 'המחיר חייב להיות חיובי' },
                ]}
              >
                <InputNumber style={{ width: '100%' }} precision={2} placeholder='0.00' />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name='discountPercent'
                label='הנחה (%)'
                rules={[
                  { type: 'number', min: 0, max: 100, message: 'הנחה חייבת להיות בין 0-100' },
                ]}
              >
                <InputNumber style={{ width: '100%' }} placeholder='0' min={0} max={100} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                name='minutes'
                label='זמן (דקות)'
                rules={[{ type: 'number', min: 0, message: 'הזמן חייב להיות חיובי' }]}
              >
                <InputNumber style={{ width: '100%' }} placeholder='0' min={0} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name='prints'
                label='תקציב הדפסות (₪)'
                rules={[{ type: 'number', min: 0, message: 'חייב להיות חיובי' }]}
              >
                <InputNumber style={{ width: '100%' }} placeholder='0' min={0} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name='validityDays'
            label='תוקף (ימים)'
            tooltip='מספר ימים שהחבילה תקפה אחרי הרכישה. השאר 0 ללא תוקף.'
            rules={[{ type: 'number', min: 0, message: 'חייב להיות חיובי' }]}
          >
            <InputNumber 
              style={{ width: '100%' }} 
              placeholder='0 = ללא הגבלה' 
              min={0}
              addonAfter='ימים'
            />
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
          ...(isAdmin
            ? [
                <Button
                  key='delete'
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => {
                    if (!viewingPackage) return;
                    Modal.confirm({
                      title: 'מחק חבילה',
                      content: `האם אתה בטוח שברצונך למחוק את "${viewingPackage.name}"?`,
                      okText: 'מחק',
                      cancelText: 'ביטול',
                      okType: 'danger',
                      onOk: async () => {
                        await handleDelete(viewingPackage);
                        setViewModalVisible(false);
                      },
                    });
                  }}
                >
                  מחק
                </Button>,
              ]
            : []),
        ]}
        width={Math.min(600, window.innerWidth - 32)}
      >
        {viewingPackage && (
          <Descriptions column={1} bordered size='small'>
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
                ₪{calculateFinalPrice(viewingPackage.price, viewingPackage.discountPercent).finalPrice.toFixed(2)}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label='זמן כלול'>
              {formatTime(viewingPackage.minutes) || 'אין'}
            </Descriptions.Item>
            <Descriptions.Item label='תקציב הדפסות'>
              {viewingPackage.prints ? `₪${viewingPackage.prints}` : 'אין'}
            </Descriptions.Item>
            <Descriptions.Item label='תוקף'>
              {viewingPackage.validityDays > 0 
                ? `${viewingPackage.validityDays} ימים` 
                : 'ללא הגבלה'}
            </Descriptions.Item>
            <Descriptions.Item label='נוצר'>
              {viewingPackage.createdAt ? dayjs(viewingPackage.createdAt).format('DD/MM/YYYY HH:mm') : 'לא זמין'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default PackagesPage;
