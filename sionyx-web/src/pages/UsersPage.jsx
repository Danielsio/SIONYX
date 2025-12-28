import { useEffect, useState } from 'react';
import {
  Card,
  Tag,
  Space,
  Button,
  Input,
  Typography,
  Drawer,
  Descriptions,
  Badge,
  App,
  Spin,
  Modal,
  Form,
  InputNumber,
  Dropdown,
  Row,
  Col,
  Empty,
  Avatar,
  Table,
} from 'antd';
import { getStatusLabel as getPurchaseStatusLabel, getStatusColor as getPurchaseStatusColor } from '../constants/purchaseStatus';
import { getUserStatus, getStatusLabel as getUserStatusLabel, getStatusColor as getUserStatusColor } from '../constants/userStatus';
import {
  SearchOutlined,
  UserOutlined,
  ClockCircleOutlined,
  PrinterOutlined,
  EyeOutlined,
  ReloadOutlined,
  EditOutlined,
  CrownOutlined,
  MoreOutlined,
  MinusCircleOutlined,
  MessageOutlined,
  SendOutlined,
  PhoneOutlined,
  MailOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';
import {
  getAllUsers,
  getUserPurchaseHistory,
  adjustUserBalance,
  grantAdminPermission,
  revokeAdminPermission,
  kickUser,
} from '../services/userService';
import { getMessagesForUser, sendMessage } from '../services/chatService';
import { formatTimeHebrewCompact } from '../utils/timeFormatter';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Search } = Input;

const UsersPage = () => {
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [userPurchases, setUserPurchases] = useState([]);
  const [loadingPurchases, setLoadingPurchases] = useState(false);
  const [adjustBalanceVisible, setAdjustBalanceVisible] = useState(false);
  const [adjustingUser, setAdjustingUser] = useState(null);
  const [adjusting, setAdjusting] = useState(false);
  const [kicking, setKicking] = useState(false);
  const [form] = Form.useForm();

  // Chat related state
  const [userMessages, setUserMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sendMessageVisible, setSendMessageVisible] = useState(false);
  const [messageForm] = Form.useForm();
  const [sending, setSending] = useState(false);

  const user = useAuthStore(state => state.user);
  const { users, setUsers } = useDataStore();
  const { message } = App.useApp();

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);

    // Get orgId from authenticated user
    const orgId = user?.orgId || localStorage.getItem('adminOrgId');

    if (!orgId) {
      message.error('מזהה ארגון לא נמצא. אנא התחבר שוב.');
      setLoading(false);
      return;
    }

    console.log('Loading users for organization:', orgId);

    const result = await getAllUsers(orgId);

    if (result.success) {
      setUsers(result.users);
      console.log(`Loaded ${result.users.length} users`);
    } else {
      message.error(result.error || 'Failed to load users');
      console.error('Failed to load users:', result.error);
    }

    setLoading(false);
  };

  const handleViewUser = async record => {
    setSelectedUser(record);
    setDrawerVisible(true);
    setLoadingPurchases(true);
    setLoadingMessages(true);

    // Get orgId
    const orgId = user?.orgId || localStorage.getItem('adminOrgId');

    // Load user's purchase history
    const purchaseResult = await getUserPurchaseHistory(orgId, record.uid);
    if (purchaseResult.success) {
      setUserPurchases(purchaseResult.purchases);
      console.log(`Loaded ${purchaseResult.purchases.length} purchases for user ${record.uid}`);
    } else {
      console.error('Failed to load user purchases:', purchaseResult.error);
    }
    setLoadingPurchases(false);

    // Load user's messages
    const messageResult = await getMessagesForUser(orgId, record.uid);
    if (messageResult.success) {
      setUserMessages(messageResult.messages);
      console.log(`Loaded ${messageResult.messages.length} messages for user ${record.uid}`);
    } else {
      console.error('Failed to load user messages:', messageResult.error);
    }
    setLoadingMessages(false);
  };

  const handleAdjustBalance = record => {
    setAdjustingUser(record);
    // Set current values as form initial values
    form.setFieldsValue({
      minutes: Math.floor((record.remainingTime || 0) / 60), // Convert seconds to minutes
      prints: record.remainingPrints || 0,
    });
    setAdjustBalanceVisible(true);
  };

  const handleBalanceSubmit = async () => {
    try {
      const values = await form.validateFields();
      setAdjusting(true);

      const orgId = user?.orgId || localStorage.getItem('adminOrgId');

      // Calculate the difference between new values and current values
      const currentTimeMinutes = Math.floor((adjustingUser.remainingTime || 0) / 60);
      const currentPrints = adjustingUser.remainingPrints || 0;

      const adjustments = {
        timeSeconds: (values.minutes - currentTimeMinutes) * 60, // Difference in seconds
        prints: values.prints - currentPrints, // Difference in prints
      };

      const result = await adjustUserBalance(orgId, adjustingUser.uid, adjustments);

      if (result.success) {
        message.success('User balance updated successfully');
        setAdjustBalanceVisible(false);
        form.resetFields();

        // Reload users to reflect changes
        await loadUsers();

        // Update selected user if viewing details
        if (selectedUser?.uid === adjustingUser.uid) {
          setSelectedUser({
            ...selectedUser,
            remainingTime: result.newBalance.remainingTime,
            remainingPrints: result.newBalance.remainingPrints,
          });
        }
      } else {
        message.error(result.error || 'Failed to update balance');
      }
    } catch (error) {
      console.error('Validation failed:', error);
    } finally {
      setAdjusting(false);
    }
  };

  const handleGrantAdmin = record => {
    Modal.confirm({
      title: 'Grant Admin Permission',
      content: `Are you sure you want to grant admin permission to ${record.firstName} ${record.lastName}?`,
      icon: <CrownOutlined style={{ color: '#faad14' }} />,
      okText: 'Grant',
      okType: 'primary',
      cancelText: 'Cancel',
      onOk: async () => {
        const orgId = user?.orgId || localStorage.getItem('adminOrgId');
        const result = await grantAdminPermission(orgId, record.uid);

        if (result.success) {
          message.success('Admin permission granted successfully');
          await loadUsers();

          // Update selected user if viewing details
          if (selectedUser?.uid === record.uid) {
            setSelectedUser({
              ...selectedUser,
              isAdmin: true,
            });
          }
        } else {
          message.error(result.error || 'Failed to grant admin permission');
        }
      },
    });
  };

  const handleRevokeAdmin = record => {
    Modal.confirm({
      title: 'Revoke Admin Permission',
      content: `Are you sure you want to revoke admin permission from ${record.firstName} ${record.lastName}?`,
      icon: <MinusCircleOutlined style={{ color: '#ff4d4f' }} />,
      okText: 'Revoke',
      okType: 'danger',
      cancelText: 'Cancel',
      onOk: async () => {
        const orgId = user?.orgId || localStorage.getItem('adminOrgId');
        const result = await revokeAdminPermission(orgId, record.uid);

        if (result.success) {
          message.success('Admin permission revoked successfully');
          await loadUsers();

          // Update selected user if viewing details
          if (selectedUser?.uid === record.uid) {
            setSelectedUser({
              ...selectedUser,
              isAdmin: false,
            });
          }
        } else {
          message.error(result.error || 'Failed to revoke admin permission');
        }
      },
    });
  };

  const handleKickUser = record => {
    Modal.confirm({
      title: 'Kick User',
      content: `Are you sure you want to kick ${record.firstName} ${record.lastName}? This will force them to log out immediately.`,
      icon: <MinusCircleOutlined style={{ color: '#ff4d4f' }} />,
      okText: 'Kick User',
      okType: 'danger',
      cancelText: 'Cancel',
      onOk: async () => {
        setKicking(true);
        try {
          const orgId = user?.orgId || localStorage.getItem('adminOrgId');
          const result = await kickUser(orgId, record.uid);

          if (result.success) {
            message.success(result.message);
            await loadUsers();
          } else {
            message.error(result.error || 'Failed to kick user');
          }
        } catch (error) {
          console.error('Error kicking user:', error);
          message.error('An error occurred while kicking user');
        } finally {
          setKicking(false);
        }
      },
    });
  };

  const formatTime = seconds => {
    return formatTimeHebrewCompact(seconds);
  };

  const handleSendMessageToUser = record => {
    setSelectedUser(record);
    setSendMessageVisible(true);
  };

  const handleSendMessage = async values => {
    try {
      const { message: messageText } = values;
      setSending(true);

      const orgId = user?.orgId || localStorage.getItem('adminOrgId');

      const result = await sendMessage(orgId, selectedUser.uid, messageText, user.uid);

      if (result.success) {
        message.success('הודעה נשלחה בהצלחה');
        setSendMessageVisible(false);
        messageForm.resetFields();

        // Reload messages if viewing user details
        if (drawerVisible) {
          const messageResult = await getMessagesForUser(orgId, selectedUser.uid);
          if (messageResult.success) {
            setUserMessages(messageResult.messages);
          }
        }
      } else {
        message.error(result.error || 'נכשל בשליחת ההודעה');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      message.error('שגיאה בשליחת ההודעה');
    } finally {
      setSending(false);
    }
  };

  // Color palette for user cards - vibrant and pleasant
  const cardGradients = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', // Purple-Indigo
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', // Pink-Rose
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', // Blue-Cyan
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', // Green-Teal
    'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', // Pink-Yellow
    'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)', // Mint-Pink (light)
    'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)', // Coral-Pink
    'linear-gradient(135deg, #5ee7df 0%, #b490ca 100%)', // Teal-Purple
    'linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)', // Lavender-Cream
    'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)', // Sky-Blue
  ];

  // Get consistent color for a user based on their ID
  const getUserGradient = (userId) => {
    if (!userId) return cardGradients[0];
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      hash = userId.charCodeAt(i) + ((hash << 5) - hash);
    }
    return cardGradients[Math.abs(hash) % cardGradients.length];
  };

  // User Card Component
  const UserCard = ({ userRecord }) => {
    const status = getUserStatus(userRecord);
    const statusColor = getUserStatusColor(status);
    const statusLabel = getUserStatusLabel(status);
    const userName = `${userRecord.firstName || ''} ${userRecord.lastName || ''}`.trim() || 'לא זמין';
    const userGradient = getUserGradient(userRecord.uid);

    const menuItems = [
      {
        key: 'view',
        icon: <EyeOutlined />,
        label: 'צפה בפרטים',
        onClick: () => handleViewUser(userRecord),
      },
      {
        key: 'message',
        icon: <MessageOutlined />,
        label: 'שלח הודעה',
        onClick: () => handleSendMessageToUser(userRecord),
      },
      {
        key: 'adjust',
        icon: <EditOutlined />,
        label: 'התאם יתרה',
        onClick: () => handleAdjustBalance(userRecord),
      },
      {
        type: 'divider',
      },
      userRecord.forceLogout !== true
        ? {
            key: 'kick',
            icon: <MinusCircleOutlined />,
            label: 'נתק משתמש',
            danger: true,
            onClick: () => handleKickUser(userRecord),
            disabled: kicking,
          }
        : {
            key: 'kicked',
            icon: <MinusCircleOutlined />,
            label: 'הותקן',
            disabled: true,
          },
      userRecord.isAdmin
        ? {
            key: 'revoke',
            icon: <MinusCircleOutlined />,
            label: 'הסר הרשאות מנהל',
            danger: true,
            onClick: () => handleRevokeAdmin(userRecord),
          }
        : {
            key: 'grant',
            icon: <CrownOutlined />,
            label: 'הענק הרשאות מנהל',
            onClick: () => handleGrantAdmin(userRecord),
          },
    ];

    return (
      <Card
        hoverable
        onClick={() => handleViewUser(userRecord)}
        style={{
          borderRadius: 20,
          overflow: 'hidden',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          border: 'none',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
          transition: 'all 0.3s ease',
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
        {/* Header with vibrant gradient */}
        <div
          style={{
            background: userGradient,
            padding: '16px',
            color: '#fff',
            position: 'relative',
          }}
        >
          {/* Status indicator dot */}
          <div
            style={{
              position: 'absolute',
              top: 12,
              right: 12,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: status === 'active' ? '#52c41a' : status === 'connected' ? '#1890ff' : '#d9d9d9',
                boxShadow: status === 'active' ? '0 0 8px #52c41a' : status === 'connected' ? '0 0 8px #1890ff' : 'none',
              }}
            />
          </div>

          {/* Admin Badge */}
          {userRecord.isAdmin && (
            <Tag
              color='gold'
              icon={<CrownOutlined />}
              style={{
                position: 'absolute',
                top: 10,
                left: 10,
                fontWeight: 'bold',
                borderRadius: 8,
                fontSize: 11,
              }}
            >
              מנהל
            </Tag>
          )}
          
          {/* Actions dropdown */}
          <div onClick={e => e.stopPropagation()} style={{ position: 'absolute', bottom: 8, right: 8 }}>
            <Dropdown menu={{ items: menuItems }} trigger={['click']}>
              <Button
                type='text'
                icon={<MoreOutlined />}
                style={{ color: '#fff', background: 'rgba(255,255,255,0.2)', borderRadius: 8 }}
                size='small'
              />
            </Dropdown>
          </div>

          {/* User Avatar and Name */}
          <div style={{ textAlign: 'center', paddingTop: 4 }}>
            <Avatar
              size={64}
              icon={<UserOutlined />}
              style={{ 
                backgroundColor: 'rgba(255,255,255,0.25)',
                marginBottom: 10,
                border: '3px solid rgba(255,255,255,0.3)',
              }}
            />
            <Title level={5} style={{ color: '#fff', margin: 0, marginBottom: 6, textShadow: '0 1px 2px rgba(0,0,0,0.2)' }}>
              {userName}
            </Title>
            <Tag 
              color={status === 'active' ? 'green' : status === 'connected' ? 'blue' : 'default'} 
              style={{ borderRadius: 12, fontWeight: 500 }}
            >
              {statusLabel}
            </Tag>
          </div>
        </div>

        {/* Body */}
        <div style={{ padding: 16, flex: 1, display: 'flex', flexDirection: 'column', background: '#fafafa' }}>
          {/* Contact Info */}
          <div style={{ marginBottom: 12, background: '#fff', padding: 10, borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            {userRecord.phoneNumber && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <PhoneOutlined style={{ color: '#667eea' }} />
                <Text style={{ direction: 'ltr', display: 'inline-block', color: '#333' }}>
                  {userRecord.phoneNumber}
                </Text>
              </div>
            )}
            {userRecord.email && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <MailOutlined style={{ color: '#667eea' }} />
                <Text 
                  style={{ fontSize: 12, color: '#666' }}
                  ellipsis={{ tooltip: userRecord.email }}
                >
                  {userRecord.email}
                </Text>
              </div>
            )}
            {!userRecord.phoneNumber && !userRecord.email && (
              <Text type='secondary' style={{ fontSize: 12 }}>אין פרטי קשר</Text>
            )}
          </div>

          {/* Balance Info */}
          <div style={{ flex: 1 }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '12px 14px',
                background: 'linear-gradient(135deg, #e6f7ff 0%, #f0f5ff 100%)',
                borderRadius: 10,
                marginBottom: 8,
                border: '1px solid #d6e4ff',
              }}
            >
              <ClockCircleOutlined style={{ color: '#1890ff', fontSize: 20 }} />
              <div>
                <Text style={{ color: '#1890ff', fontWeight: 700, fontSize: 18 }}>
                  {formatTime(userRecord.remainingTime || 0)}
                </Text>
                <Text type='secondary' style={{ display: 'block', fontSize: 11 }}>
                  זמן נותר
                </Text>
              </div>
            </div>
            
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '12px 14px',
                background: 'linear-gradient(135deg, #f6ffed 0%, #d9f7be 100%)',
                borderRadius: 10,
                border: '1px solid #b7eb8f',
              }}
            >
              <PrinterOutlined style={{ color: '#52c41a', fontSize: 20 }} />
              <div>
                <Text style={{ color: '#52c41a', fontWeight: 700, fontSize: 18 }}>
                  ₪{userRecord.remainingPrints || 0}
                </Text>
                <Text type='secondary' style={{ display: 'block', fontSize: 11 }}>
                  תקציב הדפסות
                </Text>
              </div>
            </div>
          </div>

          {/* Footer info */}
          <div style={{ paddingTop: 12, marginTop: 12, textAlign: 'center' }}>
            <Text type='secondary' style={{ fontSize: 11 }}>
              🗓️ הצטרף: {userRecord.createdAt ? dayjs(userRecord.createdAt).format('DD/MM/YYYY') : 'לא זמין'}
            </Text>
          </div>
        </div>
      </Card>
    );
  };

  const purchaseColumns = [
    {
      title: 'תאריך',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: date => (date ? dayjs(date).format('MMM D, YYYY HH:mm') : 'לא זמין'),
    },
    {
      title: 'חבילה',
      dataIndex: 'packageName',
      key: 'packageName',
    },
    {
      title: 'סכום',
      dataIndex: 'amount',
      key: 'amount',
      render: price => {
        const numPrice = parseFloat(price) || 0;
        return `₪${numPrice.toFixed(2)}`;
      },
    },
    {
      title: 'סטטוס',
      dataIndex: 'status',
      key: 'status',
      render: status => {
        return <Tag color={getPurchaseStatusColor(status)}>{getPurchaseStatusLabel(status)}</Tag>;
      },
    },
  ];

  const messageColumns = [
    {
      title: 'הודעה',
      dataIndex: 'message',
      key: 'message',
      render: text => (
        <Text style={{ maxWidth: 200 }} ellipsis={{ tooltip: text }}>
          {text}
        </Text>
      ),
    },
    {
      title: 'סטטוס',
      dataIndex: 'read',
      key: 'status',
      render: (read, record) => (
        <Space>
          {read ? (
            <Tag color='green' icon={<ClockCircleOutlined />}>
              נקרא
            </Tag>
          ) : (
            <Tag color='orange' icon={<ClockCircleOutlined />}>
              לא נקרא
            </Tag>
          )}
          {read && record.readAt && (
            <Text type='secondary' style={{ fontSize: '12px' }}>
              {dayjs(record.readAt).format('HH:mm')}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: 'נשלח',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: timestamp => (
        <Space direction='vertical' size={0}>
          <Text>{dayjs(timestamp).format('DD/MM/YYYY')}</Text>
          <Text type='secondary' style={{ fontSize: '12px' }}>
            {dayjs(timestamp).format('HH:mm:ss')}
          </Text>
        </Space>
      ),
    },
  ];

  // Filter users based on search
  const filteredUsers = users.filter(u => {
    if (!searchText) return true;
    const search = searchText.toLowerCase();
    return (
      (u.firstName?.toLowerCase() || '').includes(search) ||
      (u.lastName?.toLowerCase() || '').includes(search) ||
      (u.phoneNumber?.toLowerCase() || '').includes(search) ||
      (u.email?.toLowerCase() || '').includes(search)
    );
  });

  return (
    <div style={{ direction: 'rtl' }}>
      <Space direction='vertical' size='large' style={{ width: '100%' }}>
        {/* Header */}
        <div 
          className='page-header'
          style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 12,
          }}
        >
          <div>
            <Title level={2} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 12 }}>
              <UserOutlined />
              משתמשים
              <Badge 
                count={users.length} 
                style={{ backgroundColor: '#1890ff' }}
                overflowCount={999}
              />
            </Title>
            <Text type='secondary'>נהל וצפה בכל המשתמשים בארגון שלך</Text>
          </div>
          <Button icon={<ReloadOutlined />} onClick={loadUsers} loading={loading}>
            רענן
          </Button>
        </div>

        {/* Search */}
        <Card>
          <Search
            placeholder='חפש לפי שם, טלפון או אימייל'
            allowClear
            size='large'
            prefix={<SearchOutlined />}
            onChange={e => setSearchText(e.target.value)}
            style={{ width: '100%', maxWidth: 500 }}
          />
        </Card>

        {/* Users Grid */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: 60 }}>
            <Spin size='large' />
            <div style={{ marginTop: 16 }}>
              <Text type='secondary'>טוען משתמשים...</Text>
            </div>
          </div>
        ) : filteredUsers.length === 0 ? (
          <Card>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={searchText ? 'לא נמצאו משתמשים תואמים' : 'אין משתמשים'}
            />
          </Card>
        ) : (
          <Row gutter={[16, 16]}>
            {filteredUsers.map(userRecord => (
              <Col key={userRecord.uid} xs={24} sm={12} lg={8} xl={6}>
                <UserCard userRecord={userRecord} />
              </Col>
            ))}
          </Row>
        )}
      </Space>

      {/* Adjust Balance Modal */}
      <Modal
        title={
          <Space>
            <EditOutlined />
            <span>התאם יתרה</span>
          </Space>
        }
        open={adjustBalanceVisible}
        onOk={handleBalanceSubmit}
        onCancel={() => {
          setAdjustBalanceVisible(false);
          form.resetFields();
        }}
        confirmLoading={adjusting}
        okText='עדכן'
        cancelText='ביטול'
        width={500}
      >
        {adjustingUser && (
          <Space direction='vertical' size='large' style={{ width: '100%' }}>
            <div>
              <Text strong>משתמש: </Text>
              <Text>{`${adjustingUser.firstName} ${adjustingUser.lastName}`}</Text>
            </div>

            <Form form={form} layout='vertical'>
              <Form.Item
                name='minutes'
                label='יתרת זמן (דקות)'
                tooltip='ערוך את סך הדקות שהמשתמש צריך לקבל'
                rules={[
                  { required: true, message: 'אנא הכנס זמן' },
                  { type: 'number', min: 0, message: 'הזמן לא יכול להיות שלילי' },
                ]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder='למשל, 120 (שעתיים)'
                  prefix={<ClockCircleOutlined />}
                  min={0}
                />
              </Form.Item>

              <Form.Item
                name='prints'
                label='יתרת הדפסות (₪)'
                tooltip='ערוך את סך תקציב ההדפסות בשקלים שהמשתמש צריך לקבל'
                rules={[
                  { required: true, message: 'אנא הכנס הדפסות' },
                  { type: 'number', min: 0, message: 'הדפסות לא יכולות להיות שליליות' },
                ]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder='למשל, 50'
                  prefix={<PrinterOutlined />}
                  min={0}
                />
              </Form.Item>
            </Form>

            <div
              style={{
                padding: '8px',
                backgroundColor: '#e6f7ff',
                borderRadius: '4px',
                border: '1px solid #91d5ff',
              }}
            >
              <Text type='secondary' style={{ fontSize: '12px' }}>
                💡 טיפ: הערכים הנוכחיים מוצגים. ערוך אותם כדי לקבוע את היתרה החדשה. תוכל להגדיל,
                להקטין או לקבוע כל ערך.
              </Text>
            </div>
          </Space>
        )}
      </Modal>

      {/* User Detail Drawer */}
      <Drawer
        title='פרטי משתמש'
        placement='right'
        width={Math.min(600, window.innerWidth - 40)}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedUser && (
          <Space direction='vertical' size='large' style={{ width: '100%' }}>
            <Card>
              <Descriptions column={1} bordered>
                <Descriptions.Item label='שם'>
                  {`${selectedUser.firstName || ''} ${selectedUser.lastName || ''}`.trim() ||
                    'לא זמין'}
                </Descriptions.Item>
                <Descriptions.Item label='טלפון'>
                  {selectedUser.phoneNumber || 'לא זמין'}
                </Descriptions.Item>
                <Descriptions.Item label='אימייל'>
                  {selectedUser.email || 'לא זמין'}
                </Descriptions.Item>
                <Descriptions.Item label='סטטוס'>
                  {(() => {
                    const status = getUserStatus(selectedUser);
                    const statusLabel = getUserStatusLabel(status);
                    const statusColor = getUserStatusColor(status);
                    return (
                      <Tag color={statusColor}>{statusLabel}</Tag>
                    );
                  })()}
                </Descriptions.Item>
                <Descriptions.Item label='תפקיד'>
                  {selectedUser.isAdmin ? (
                    <Tag color='gold' icon={<CrownOutlined />}>
                      מנהל
                    </Tag>
                  ) : (
                    <Tag color='default'>משתמש</Tag>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label='זמן נותר'>
                  <Space>
                    <ClockCircleOutlined />
                    {formatTime(selectedUser.remainingTime || 0)}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label='תקציב הדפסות'>
                  <Space>
                    <PrinterOutlined />
                    <Text style={{ fontWeight: 600 }}>₪{selectedUser.remainingPrints || 0}</Text>
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label='נוצר'>
                  {selectedUser.createdAt
                    ? dayjs(selectedUser.createdAt).format('MMMM D, YYYY HH:mm')
                    : 'לא זמין'}
                </Descriptions.Item>
                <Descriptions.Item label='עודכן לאחרונה'>
                  {selectedUser.updatedAt
                    ? dayjs(selectedUser.updatedAt).format('MMMM D, YYYY HH:mm')
                    : 'לא זמין'}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {/* Quick Actions */}
            <Card title='פעולות מהירות'>
              <Space wrap>
                <Button 
                  icon={<MessageOutlined />} 
                  onClick={() => setSendMessageVisible(true)}
                >
                  שלח הודעה
                </Button>
                <Button 
                  icon={<EditOutlined />} 
                  onClick={() => handleAdjustBalance(selectedUser)}
                >
                  התאם יתרה
                </Button>
                {selectedUser.isAdmin ? (
                  <Button 
                    icon={<MinusCircleOutlined />} 
                    danger
                    onClick={() => handleRevokeAdmin(selectedUser)}
                  >
                    הסר הרשאות מנהל
                  </Button>
                ) : (
                  <Button 
                    icon={<CrownOutlined />} 
                    onClick={() => handleGrantAdmin(selectedUser)}
                  >
                    הענק הרשאות מנהל
                  </Button>
                )}
                {selectedUser.forceLogout !== true && (
                  <Button 
                    icon={<MinusCircleOutlined />} 
                    danger
                    onClick={() => handleKickUser(selectedUser)}
                  >
                    נתק משתמש
                  </Button>
                )}
              </Space>
            </Card>

            <Card title='היסטוריית רכישות'>
              {loadingPurchases ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <Spin />
                </div>
              ) : (
                <Table
                  columns={purchaseColumns}
                  dataSource={userPurchases}
                  rowKey='id'
                  size='small'
                  pagination={{ pageSize: 5 }}
                  scroll={{ x: 'max-content' }}
                />
              )}
            </Card>

            <Card
              title={
                <Space>
                  <MessageOutlined />
                  <span>היסטוריית הודעות</span>
                  <Button
                    type='primary'
                    size='small'
                    icon={<SendOutlined />}
                    onClick={() => setSendMessageVisible(true)}
                  >
                    שלח הודעה
                  </Button>
                </Space>
              }
            >
              {loadingMessages ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <Spin />
                </div>
              ) : (
                <Table
                  columns={messageColumns}
                  dataSource={userMessages}
                  rowKey='id'
                  size='small'
                  pagination={{ pageSize: 5 }}
                  scroll={{ x: 'max-content' }}
                  locale={{ emptyText: 'אין הודעות' }}
                />
              )}
            </Card>
          </Space>
        )}
      </Drawer>

      {/* Send Message Modal */}
      <Modal
        title={
          <Space>
            <MessageOutlined />
            <span>
              שלח הודעה {selectedUser && `ל${selectedUser.firstName} ${selectedUser.lastName}`}
            </span>
          </Space>
        }
        open={sendMessageVisible}
        onCancel={() => {
          setSendMessageVisible(false);
          messageForm.resetFields();
        }}
        footer={null}
        width={500}
        dir='rtl'
      >
        <Form form={messageForm} layout='vertical' onFinish={handleSendMessage} dir='rtl'>
          <Form.Item
            name='message'
            label='הודעה'
            rules={[
              { required: true, message: 'אנא הכנס הודעה' },
              { max: 500, message: 'ההודעה חייבת להיות פחות מ-500 תווים' },
            ]}
          >
            <Input.TextArea
              rows={4}
              placeholder='הכנס את ההודעה שלך כאן...'
              showCount
              maxLength={500}
              style={{ textAlign: 'right', direction: 'rtl' }}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setSendMessageVisible(false)}>ביטול</Button>
              <Button type='primary' htmlType='submit' icon={<SendOutlined />} loading={sending}>
                שלח הודעה
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UsersPage;
