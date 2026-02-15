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
  Statistic,
} from 'antd';
import { motion } from 'framer-motion';
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
  LockOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';
import { useOrgId } from '../hooks/useOrgId';
import {
  getAllUsers,
  getUserPurchaseHistory,
  adjustUserBalance,
  grantAdminPermission,
  revokeAdminPermission,
  kickUser,
  resetUserPassword,
} from '../services/userService';
import { getMessagesForUser, sendMessage } from '../services/chatService';
import { formatTimeHebrewCompact } from '../utils/timeFormatter';
import dayjs from 'dayjs';
import StatCard from '../components/StatCard';
import { logger } from '../utils/logger';

const { Title, Text } = Typography;
const { Search } = Input;

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] },
  },
};

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

  // Password reset state
  const [resetPasswordVisible, setResetPasswordVisible] = useState(false);
  const [resetPasswordUser, setResetPasswordUser] = useState(null);
  const [resettingPassword, setResettingPassword] = useState(false);
  const [resetPasswordForm] = Form.useForm();

  const user = useAuthStore(state => state.user);
  const { users, setUsers } = useDataStore();
  const { message } = App.useApp();
  const orgId = useOrgId();

  useEffect(() => {
    loadUsers();
  }, [orgId]);

  const loadUsers = async () => {
    setLoading(true);

    if (!orgId) {
      message.error('מזהה ארגון לא נמצא. אנא התחבר שוב.');
      setLoading(false);
      return;
    }

    logger.info('Loading users for organization:', orgId);

    const result = await getAllUsers(orgId);

    if (result.success) {
      setUsers(result.users);
      logger.info(`Loaded ${result.users.length} users`);
    } else {
      message.error(result.error || 'Failed to load users');
      logger.error('Failed to load users:', result.error);
    }

    setLoading(false);
  };

  const handleViewUser = async record => {
    setSelectedUser(record);
    setDrawerVisible(true);
    setLoadingPurchases(true);
    setLoadingMessages(true);

    // Load user's purchase history
    const purchaseResult = await getUserPurchaseHistory(orgId, record.uid);
    if (purchaseResult.success) {
      setUserPurchases(purchaseResult.purchases);
      logger.info(`Loaded ${purchaseResult.purchases.length} purchases for user ${record.uid}`);
    } else {
      logger.error('Failed to load user purchases:', purchaseResult.error);
    }
    setLoadingPurchases(false);

    // Load user's messages
    const messageResult = await getMessagesForUser(orgId, record.uid);
    if (messageResult.success) {
      setUserMessages(messageResult.messages);
      logger.info(`Loaded ${messageResult.messages.length} messages for user ${record.uid}`);
    } else {
      logger.error('Failed to load user messages:', messageResult.error);
    }
    setLoadingMessages(false);
  };

  const handleAdjustBalance = record => {
    setAdjustingUser(record);
    // Set current values as form initial values
    form.setFieldsValue({
      minutes: Math.floor((record.remainingTime || 0) / 60), // Convert seconds to minutes
      prints: record.printBalance || 0,
    });
    setAdjustBalanceVisible(true);
  };

  const handleBalanceSubmit = async () => {
    try {
      const values = await form.validateFields();
      setAdjusting(true);

      // Calculate the difference between new values and current values
      const currentTimeMinutes = Math.floor((adjustingUser.remainingTime || 0) / 60);
      const currentPrints = adjustingUser.printBalance || 0;

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
            printBalance: result.newBalance.printBalance,
          });
        }
      } else {
        message.error(result.error || 'Failed to update balance');
      }
    } catch (error) {
      logger.error('Validation failed:', error);
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
          const result = await kickUser(orgId, record.uid);

          if (result.success) {
            message.success(result.message);
            await loadUsers();
          } else {
            message.error(result.error || 'Failed to kick user');
          }
        } catch (error) {
          logger.error('Error kicking user:', error);
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

  const handleResetPassword = record => {
    setResetPasswordUser(record);
    setResetPasswordVisible(true);
  };

  const handleResetPasswordSubmit = async () => {
    try {
      const values = await resetPasswordForm.validateFields();
      
      if (values.newPassword !== values.confirmPassword) {
        message.error('הסיסמאות אינן תואמות');
        return;
      }

      setResettingPassword(true);

      const result = await resetUserPassword(orgId, resetPasswordUser.uid, values.newPassword);

      if (result.success) {
        message.success(result.message || 'הסיסמה אופסה בהצלחה');
        setResetPasswordVisible(false);
        resetPasswordForm.resetFields();
        setResetPasswordUser(null);
      } else {
        message.error(result.error || 'שגיאה באיפוס הסיסמה');
      }
    } catch (error) {
      logger.error('Password reset validation failed:', error);
    } finally {
      setResettingPassword(false);
    }
  };

  const handleSendMessage = async values => {
    if (!user?.uid) {
      message.error('שגיאה: לא ניתן לזהות את השולח');
      return;
    }
    try {
      const { message: messageText } = values;
      setSending(true);

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
      logger.error('Error sending message:', error);
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

  // User Card Component - Enhanced with premium styling
  const UserCard = ({ userRecord, index = 0 }) => {
    const status = getUserStatus(userRecord);
    const statusColor = getUserStatusColor(status);
    const statusLabel = getUserStatusLabel(status);
    const userName = `${userRecord.firstName || ''} ${userRecord.lastName || ''}`.trim() || 'לא זמין';
    const userGradient = getUserGradient(userRecord.uid);

    // Status configuration
    const statusConfig = {
      active: { 
        color: '#10b981', 
        bg: 'rgba(16, 185, 129, 0.1)',
        shadow: '0 0 0 3px rgba(16, 185, 129, 0.2)',
      },
      connected: { 
        color: '#3b82f6', 
        bg: 'rgba(59, 130, 246, 0.1)',
        shadow: '0 0 0 3px rgba(59, 130, 246, 0.2)',
      },
      offline: { 
        color: '#9ca3af', 
        bg: 'rgba(156, 163, 175, 0.1)',
        shadow: 'none',
      },
    };
    const currentStatus = statusConfig[status] || statusConfig.offline;

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
        key: 'resetPassword',
        icon: <LockOutlined />,
        label: 'איפוס סיסמה',
        onClick: () => handleResetPassword(userRecord),
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
            label: userRecord.uid === user?.uid ? 'לא ניתן להסיר מעצמך' : 'הסר הרשאות מנהל',
            danger: true,
            onClick: () => handleRevokeAdmin(userRecord),
            disabled: userRecord.uid === user?.uid,
          }
        : {
            key: 'grant',
            icon: <CrownOutlined />,
            label: 'הענק הרשאות מנהל',
            onClick: () => handleGrantAdmin(userRecord),
          },
    ];

    return (
      <motion.div
        variants={cardVariants}
        initial="hidden"
        animate="visible"
        transition={{ delay: index * 0.03 }}
        whileHover={{ y: -4 }}
        style={{ height: '100%' }}
      >
        <Card
          hoverable
          onClick={() => handleViewUser(userRecord)}
          style={{
            borderRadius: 18,
            overflow: 'hidden',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            border: '1px solid #e8eaed',
            boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
            transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
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
              background: userGradient,
              padding: '20px 16px',
              color: '#fff',
              position: 'relative',
            }}
          >
            {/* Status indicator */}
            <div
              style={{
                position: 'absolute',
                top: 14,
                right: 14,
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: currentStatus.color,
                boxShadow: currentStatus.shadow,
                animation: status === 'active' ? 'statusPulse 2s ease-in-out infinite' : 'none',
              }}
            />

            {/* Admin Badge */}
            {userRecord.isAdmin && (
              <Tag
                color='gold'
                icon={<CrownOutlined />}
                style={{
                  position: 'absolute',
                  top: 12,
                  left: 12,
                  fontWeight: 600,
                  borderRadius: 8,
                  fontSize: 11,
                  border: 'none',
                }}
              >
                מנהל
              </Tag>
            )}
            
            {/* Actions dropdown */}
            <div 
              onClick={e => e.stopPropagation()} 
              style={{ position: 'absolute', bottom: 12, right: 12 }}
            >
              <Dropdown menu={{ items: menuItems }} trigger={['click']}>
                <Button
                  type='text'
                  icon={<MoreOutlined />}
                  style={{ 
                    color: '#fff', 
                    background: 'rgba(255,255,255,0.15)',
                    backdropFilter: 'blur(4px)',
                    borderRadius: 8,
                    border: '1px solid rgba(255,255,255,0.2)',
                  }}
                  size='small'
                />
              </Dropdown>
            </div>

            {/* User Avatar and Name */}
            <div style={{ textAlign: 'center', paddingTop: 4 }}>
              <Avatar
                size={60}
                icon={<UserOutlined />}
                style={{ 
                  backgroundColor: 'rgba(255,255,255,0.2)',
                  backdropFilter: 'blur(4px)',
                  marginBottom: 12,
                  border: '2px solid rgba(255,255,255,0.3)',
                }}
              />
              <Title level={5} style={{ color: '#fff', margin: 0, marginBottom: 8, fontSize: 16 }}>
                {userName}
              </Title>
              <Tag 
                style={{ 
                  background: currentStatus.bg,
                  color: '#fff',
                  border: 'none',
                  borderRadius: 10,
                  fontWeight: 500,
                  fontSize: 11,
                }}
              >
                {statusLabel}
              </Tag>
            </div>
          </div>

          {/* Body */}
          <div style={{ padding: 16, flex: 1, display: 'flex', flexDirection: 'column', background: '#fafbfc' }}>
            {/* Contact Info */}
            <div 
              style={{ 
                marginBottom: 14, 
                background: '#fff', 
                padding: '12px 14px', 
                borderRadius: 12, 
                border: '1px solid #e8eaed',
              }}
            >
              {userRecord.phoneNumber && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: userRecord.email ? 8 : 0 }}>
                  <PhoneOutlined style={{ color: '#667eea', fontSize: 14 }} />
                  <Text style={{ direction: 'ltr', display: 'inline-block', color: '#374151', fontSize: 13 }}>
                    {userRecord.phoneNumber}
                  </Text>
                </div>
              )}
              {userRecord.email && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <MailOutlined style={{ color: '#667eea', fontSize: 14 }} />
                  <Text 
                    style={{ fontSize: 12, color: '#6b7280' }}
                    ellipsis={{ tooltip: userRecord.email }}
                  >
                    {userRecord.email}
                  </Text>
                </div>
              )}
              {!userRecord.phoneNumber && !userRecord.email && (
                <Text type='secondary' style={{ fontSize: 12, color: '#9ca3af' }}>אין פרטי קשר</Text>
              )}
            </div>

            {/* Balance Info - Enhanced styling */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '14px 16px',
                  background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(59, 130, 246, 0.04) 100%)',
                  borderRadius: 12,
                  border: '1px solid rgba(59, 130, 246, 0.15)',
                }}
              >
                <div 
                  style={{ 
                    width: 36, 
                    height: 36, 
                    borderRadius: 10, 
                    background: 'rgba(59, 130, 246, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <ClockCircleOutlined style={{ color: '#3b82f6', fontSize: 18 }} />
                </div>
                <div style={{ flex: 1 }}>
                  <Text style={{ color: '#3b82f6', fontWeight: 700, fontSize: 17, display: 'block', lineHeight: 1.2 }}>
                    {formatTime(userRecord.remainingTime || 0)}
                  </Text>
                  <Text style={{ fontSize: 11, color: '#6b7280' }}>זמן נותר</Text>
                </div>
              </div>
              
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '14px 16px',
                  background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(16, 185, 129, 0.04) 100%)',
                  borderRadius: 12,
                  border: '1px solid rgba(16, 185, 129, 0.15)',
                }}
              >
                <div 
                  style={{ 
                    width: 36, 
                    height: 36, 
                    borderRadius: 10, 
                    background: 'rgba(16, 185, 129, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <PrinterOutlined style={{ color: '#10b981', fontSize: 18 }} />
                </div>
                <div style={{ flex: 1 }}>
                  <Text style={{ color: '#10b981', fontWeight: 700, fontSize: 17, display: 'block', lineHeight: 1.2 }}>
                    ₪{userRecord.printBalance || 0}
                  </Text>
                  <Text style={{ fontSize: 11, color: '#6b7280' }}>תקציב הדפסות</Text>
                </div>
              </div>
            </div>

            {/* Footer info */}
            <div 
              style={{ 
                paddingTop: 14, 
                marginTop: 14, 
                textAlign: 'center',
                borderTop: '1px solid #e8eaed',
              }}
            >
              <Text style={{ fontSize: 11, color: '#9ca3af' }}>
                <CalendarOutlined style={{ marginLeft: 4 }} />
                הצטרף: {userRecord.createdAt ? dayjs(userRecord.createdAt).format('DD/MM/YYYY') : 'לא זמין'}
              </Text>
            </div>
          </div>
        </Card>
      </motion.div>
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

  // Calculate user statistics
  const activeUsers = users.filter(u => getUserStatus(u) === 'active').length;
  const connectedUsers = users.filter(u => getUserStatus(u) === 'connected').length;
  const adminUsers = users.filter(u => u.isAdmin).length;
  const totalUsers = users.length;

  return (
    <motion.div 
      style={{ direction: 'rtl' }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Space direction='vertical' size={24} style={{ width: '100%' }}>
        {/* Header */}
        <motion.div 
          className='page-header'
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 16,
          }}
        >
          <div>
            <Title level={2} style={{ margin: 0, fontWeight: 700, color: '#1f2937' }}>
              משתמשים
            </Title>
            <Text style={{ color: '#6b7280', fontSize: 14 }}>
              נהל וצפה בכל המשתמשים בארגון שלך
            </Text>
          </div>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={loadUsers} 
            loading={loading}
            style={{ 
              borderRadius: 10,
              height: 40,
              paddingLeft: 20,
              paddingRight: 20,
            }}
          >
            רענן
          </Button>
        </motion.div>

        {/* Stats Row */}
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={6}>
            <Card 
              variant='borderless' 
              style={{ 
                borderRadius: 14,
                background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%)',
                border: '1px solid rgba(16, 185, 129, 0.15)',
              }}
              styles={{ body: { padding: '16px 20px' } }}
            >
              <Statistic
                title={<Text style={{ color: '#6b7280', fontSize: 12 }}>פעילים</Text>}
                value={activeUsers}
                valueStyle={{ color: '#10b981', fontWeight: 700, fontSize: 28 }}
                prefix={<CheckCircleOutlined style={{ fontSize: 20, marginLeft: 8 }} />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card 
              variant='borderless' 
              style={{ 
                borderRadius: 14,
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%)',
                border: '1px solid rgba(59, 130, 246, 0.15)',
              }}
              styles={{ body: { padding: '16px 20px' } }}
            >
              <Statistic
                title={<Text style={{ color: '#6b7280', fontSize: 12 }}>מחוברים</Text>}
                value={connectedUsers}
                valueStyle={{ color: '#3b82f6', fontWeight: 700, fontSize: 28 }}
                prefix={<UserOutlined style={{ fontSize: 20, marginLeft: 8 }} />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card 
              variant='borderless' 
              style={{ 
                borderRadius: 14,
                background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%)',
                border: '1px solid rgba(245, 158, 11, 0.15)',
              }}
              styles={{ body: { padding: '16px 20px' } }}
            >
              <Statistic
                title={<Text style={{ color: '#6b7280', fontSize: 12 }}>מנהלים</Text>}
                value={adminUsers}
                valueStyle={{ color: '#f59e0b', fontWeight: 700, fontSize: 28 }}
                prefix={<CrownOutlined style={{ fontSize: 20, marginLeft: 8 }} />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card 
              variant='borderless' 
              style={{ 
                borderRadius: 14,
                background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(102, 126, 234, 0.05) 100%)',
                border: '1px solid rgba(102, 126, 234, 0.15)',
              }}
              styles={{ body: { padding: '16px 20px' } }}
            >
              <Statistic
                title={<Text style={{ color: '#6b7280', fontSize: 12 }}>סה"כ</Text>}
                value={totalUsers}
                valueStyle={{ color: '#667eea', fontWeight: 700, fontSize: 28 }}
                prefix={<UserOutlined style={{ fontSize: 20, marginLeft: 8 }} />}
              />
            </Card>
          </Col>
        </Row>

        {/* Search */}
        <Card 
          variant='borderless' 
          style={{ borderRadius: 14 }}
          styles={{ body: { padding: '16px 20px' } }}
        >
          <Search
            placeholder='חפש לפי שם, טלפון או אימייל...'
            allowClear
            size='large'
            prefix={<SearchOutlined style={{ color: '#9ca3af' }} />}
            onChange={e => setSearchText(e.target.value)}
            style={{ 
              width: '100%', 
              maxWidth: 500,
            }}
          />
        </Card>

        {/* Users Grid */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: 80 }}>
            <Spin size='large' />
            <div style={{ marginTop: 20 }}>
              <Text style={{ color: '#6b7280' }}>טוען משתמשים...</Text>
            </div>
          </div>
        ) : filteredUsers.length === 0 ? (
          <Card variant='borderless' style={{ borderRadius: 14 }}>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <Text style={{ color: '#6b7280' }}>
                  {searchText ? 'לא נמצאו משתמשים תואמים' : 'אין משתמשים'}
                </Text>
              }
            />
          </Card>
        ) : (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <Row gutter={[20, 20]}>
              {filteredUsers.map((userRecord, index) => (
                <Col key={userRecord.uid} xs={24} sm={12} lg={8} xl={6}>
                  <UserCard userRecord={userRecord} index={index} />
                </Col>
              ))}
            </Row>
          </motion.div>
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
                    <Text style={{ fontWeight: 600 }}>₪{selectedUser.printBalance || 0}</Text>
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label='תוקף זמן'>
                  {selectedUser.timeExpiresAt ? (
                    <Space>
                      <CalendarOutlined style={{ 
                        color: dayjs(selectedUser.timeExpiresAt).isBefore(dayjs()) 
                          ? '#ff4d4f' 
                          : '#fa8c16' 
                      }} />
                      <Text style={{ 
                        color: dayjs(selectedUser.timeExpiresAt).isBefore(dayjs()) 
                          ? '#ff4d4f' 
                          : undefined 
                      }}>
                        {dayjs(selectedUser.timeExpiresAt).isBefore(dayjs()) 
                          ? 'פג תוקף' 
                          : dayjs(selectedUser.timeExpiresAt).format('DD/MM/YYYY')}
                      </Text>
                    </Space>
                  ) : (
                    <Text type='secondary'>ללא הגבלה</Text>
                  )}
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
                <Button 
                  icon={<LockOutlined />} 
                  onClick={() => handleResetPassword(selectedUser)}
                >
                  איפוס סיסמה
                </Button>
                {selectedUser.isAdmin ? (
                  <Button 
                    icon={<MinusCircleOutlined />} 
                    danger
                    onClick={() => handleRevokeAdmin(selectedUser)}
                    disabled={selectedUser.uid === user?.uid}
                    title={selectedUser.uid === user?.uid ? 'לא ניתן להסיר הרשאות מנהל מעצמך' : ''}
                  >
                    {selectedUser.uid === user?.uid ? 'לא ניתן להסיר מעצמך' : 'הסר הרשאות מנהל'}
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

      {/* Reset Password Modal */}
      <Modal
        title={
          <Space>
            <LockOutlined />
            <span>
              איפוס סיסמה {resetPasswordUser && `ל${resetPasswordUser.firstName} ${resetPasswordUser.lastName}`}
            </span>
          </Space>
        }
        open={resetPasswordVisible}
        onOk={handleResetPasswordSubmit}
        onCancel={() => {
          setResetPasswordVisible(false);
          resetPasswordForm.resetFields();
          setResetPasswordUser(null);
        }}
        confirmLoading={resettingPassword}
        okText='אפס סיסמה'
        cancelText='ביטול'
        width={450}
        dir='rtl'
      >
        {resetPasswordUser && (
          <Space direction='vertical' size='large' style={{ width: '100%' }}>
            <div
              style={{
                padding: '12px',
                backgroundColor: '#fff7e6',
                borderRadius: '8px',
                border: '1px solid #ffd591',
              }}
            >
              <Text>
                <strong>שים לב:</strong> הסיסמה החדשה תיכנס לתוקף מיד. 
                וודא שאתה מעביר את הסיסמה החדשה למשתמש בצורה מאובטחת.
              </Text>
            </div>

            <Form form={resetPasswordForm} layout='vertical' dir='rtl'>
              <Form.Item
                name='newPassword'
                label='סיסמה חדשה'
                rules={[
                  { required: true, message: 'אנא הכנס סיסמה חדשה' },
                  { min: 6, message: 'הסיסמה חייבת להכיל לפחות 6 תווים' },
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder='לפחות 6 תווים'
                />
              </Form.Item>

              <Form.Item
                name='confirmPassword'
                label='אשר סיסמה'
                rules={[
                  { required: true, message: 'אנא אשר את הסיסמה' },
                  { min: 6, message: 'הסיסמה חייבת להכיל לפחות 6 תווים' },
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder='הכנס שוב את הסיסמה'
                />
              </Form.Item>
            </Form>
          </Space>
        )}
      </Modal>
    </motion.div>
  );
};

export default UsersPage;
