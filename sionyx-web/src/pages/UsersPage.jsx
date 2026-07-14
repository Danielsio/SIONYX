import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion'; // eslint-disable-line no-unused-vars
import {
  Card,
  Space,
  Button,
  Input,
  Typography,
  App,
  Skeleton,
  Modal,
  Form,
  Dropdown,
  Row,
  Col,
  Empty,
  Statistic,
  Collapse,
  Segmented,
  DatePicker,
  Select,
} from 'antd';
import {
  SearchOutlined,
  UserOutlined,
  CrownOutlined,
  MinusCircleOutlined,
  SendOutlined,
  CheckCircleOutlined,
  DownloadOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { getUserStatus } from '../constants/userStatus';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';
import { useOrgId } from '../hooks/useOrgId';
import {
  getUserPurchaseHistory,
  adjustUserBalance,
  grantAdminPermission,
  revokeAdminPermission,
  kickUser,
  resetUserPassword,
  deleteUser,
  verifyUserPhone,
} from '../services/userService';
import { subscribeToUsers } from '../services/realtimeService';
import { getMessagesForUser, sendMessage } from '../services/chatService';
import { exportToCSV, exportToExcel, exportToPDF } from '../utils/csvExport';
import dayjs from 'dayjs';
import PageHeader from '../components/PageHeader';
import UserCard from '../components/users/UserCard';
import UserDrawer from '../components/users/UserDrawer';
import BalanceAdjustModal from '../components/users/BalanceAdjustModal';
import SendMessageModal from '../components/users/SendMessageModal';
import ResetPasswordModal from '../components/users/ResetPasswordModal';
import { logger } from '../utils/logger';

const { Text } = Typography;
const { Search } = Input;

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 },
  },
};

const UsersPage = () => {
  const [loading, setLoading] = useState(true);

  // Filters live in the URL (C5): refresh, back button, and shared links keep
  // the search/filter context.
  const [searchParams, setSearchParams] = useSearchParams();
  const searchText = searchParams.get('q') || '';
  const statusFilter = searchParams.get('status');
  const roleFilter = searchParams.get('role');
  const dateFrom = searchParams.get('from');
  const dateTo = searchParams.get('to');
  const dateRangeFilter = dateFrom && dateTo ? [dayjs(dateFrom), dayjs(dateTo)] : null;

  const updateFilters = patch => {
    setSearchParams(
      prev => {
        const next = new URLSearchParams(prev);
        for (const [key, value] of Object.entries(patch)) {
          if (value == null || value === '') next.delete(key);
          else next.set(key, value);
        }
        return next;
      },
      { replace: true }
    );
  };

  const [selectedUser, setSelectedUser] = useState(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [userPurchases, setUserPurchases] = useState([]);
  const [loadingPurchases, setLoadingPurchases] = useState(false);
  const [adjustBalanceVisible, setAdjustBalanceVisible] = useState(false);
  const [adjustingUser, setAdjustingUser] = useState(null);
  const [adjusting, setAdjusting] = useState(false);
  const [kicking, setKicking] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [form] = Form.useForm();

  // Chat related state
  const [userMessages, setUserMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sendMessageVisible, setSendMessageVisible] = useState(false);
  const [messageForm] = Form.useForm();
  const [sending, setSending] = useState(false);
  // When set, the send-message modal targets this list instead of selectedUser.
  const [bulkTargets, setBulkTargets] = useState(null);

  // Password reset state
  const [resetPasswordVisible, setResetPasswordVisible] = useState(false);
  const [resetPasswordUser, setResetPasswordUser] = useState(null);
  const [resettingPassword, setResettingPassword] = useState(false);
  const [resetPasswordForm] = Form.useForm();

  const user = useAuthStore(state => state.user);
  const { users, setUsers } = useDataStore();
  const { message } = App.useApp();
  const orgId = useOrgId();

  // Live subscription (C1): session state and balances update as they change —
  // admins no longer act on stale data, and mutations show up without reloads.
  useEffect(() => {
    if (!orgId) {
      message.error('מזהה ארגון לא נמצא. אנא התחבר שוב.');
      setLoading(false);
      return undefined;
    }
    const unsubscribe = subscribeToUsers(orgId, list => {
      setUsers(list);
      setLoading(false);
    });
    return unsubscribe;
  }, [orgId]); // eslint-disable-line react-hooks/exhaustive-deps

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
        message.success('יתרת המשתמש עודכנה בהצלחה');
        setAdjustBalanceVisible(false);
        form.resetFields();

        // Update selected user if viewing details
        if (selectedUser?.uid === adjustingUser.uid) {
          setSelectedUser({
            ...selectedUser,
            remainingTime: result.newBalance.remainingTime,
            printBalance: result.newBalance.printBalance,
          });
        }
      } else {
        message.error(result.error || 'נכשל בעדכון היתרה');
      }
    } catch (error) {
      logger.error('Validation failed:', error);
    } finally {
      setAdjusting(false);
    }
  };

  const handleGrantAdmin = record => {
    Modal.confirm({
      title: 'הענקת הרשאות מנהל',
      content: `האם אתה בטוח שברצונך להעניק הרשאות מנהל ל${record.firstName} ${record.lastName}?`,
      icon: <CrownOutlined style={{ color: '#faad14' }} />,
      okText: 'הענק',
      okType: 'primary',
      cancelText: 'ביטול',
      onOk: async () => {
        const result = await grantAdminPermission(orgId, record.uid);

        if (result.success) {
          message.success('הרשאות מנהל הוענקו בהצלחה');

          // Update selected user if viewing details
          if (selectedUser?.uid === record.uid) {
            setSelectedUser({
              ...selectedUser,
              isAdmin: true,
            });
          }
        } else {
          message.error(result.error || 'נכשל בהענקת הרשאות מנהל');
        }
      },
    });
  };

  const handleRevokeAdmin = record => {
    Modal.confirm({
      title: 'הסרת הרשאות מנהל',
      content: `האם אתה בטוח שברצונך להסיר הרשאות מנהל מ${record.firstName} ${record.lastName}?`,
      icon: <MinusCircleOutlined style={{ color: '#ff4d4f' }} />,
      okText: 'הסר',
      okType: 'danger',
      cancelText: 'ביטול',
      onOk: async () => {
        const result = await revokeAdminPermission(orgId, record.uid);

        if (result.success) {
          message.success('הרשאות מנהל הוסרו בהצלחה');

          // Update selected user if viewing details
          if (selectedUser?.uid === record.uid) {
            setSelectedUser({
              ...selectedUser,
              isAdmin: false,
            });
          }
        } else {
          message.error(result.error || 'נכשל בהסרת הרשאות מנהל');
        }
      },
    });
  };

  const handleKickUser = record => {
    Modal.confirm({
      title: 'ניתוק משתמש',
      content: `האם אתה בטוח שברצונך לנתק את ${record.firstName} ${record.lastName}? פעולה זו תנתק אותו מיידית.`,
      icon: <MinusCircleOutlined style={{ color: '#ff4d4f' }} />,
      okText: 'נתק משתמש',
      okType: 'danger',
      cancelText: 'ביטול',
      onOk: async () => {
        setKicking(true);
        try {
          const result = await kickUser(orgId, record.uid);

          if (result.success) {
            message.success(result.message);
          } else {
            message.error(result.error || 'נכשל בניתוק המשתמש');
          }
        } catch (error) {
          logger.error('Error kicking user:', error);
          message.error('שגיאה בניתוק המשתמש');
        } finally {
          setKicking(false);
        }
      },
    });
  };

  const handleDeleteUser = record => {
    Modal.confirm({
      title: 'מחיקת משתמש',
      content: `האם אתה בטוח שברצונך למחוק את ${record.firstName} ${record.lastName}? פעולה זו בלתי הפיכה ותמחק את חשבון המשתמש, ההודעות שלו, ואת חשבון ההתחברות.`,
      icon: <DeleteOutlined style={{ color: '#ff4d4f' }} />,
      okText: 'מחק לצמיתות',
      okType: 'danger',
      cancelText: 'ביטול',
      onOk: async () => {
        setDeleting(true);
        try {
          const result = await deleteUser(orgId, record.uid);
          if (result.success) {
            message.success(result.message);
            setDrawerVisible(false);
            setSelectedUser(null);
          } else {
            message.error(result.error || 'נכשל במחיקת המשתמש');
          }
        } catch (error) {
          logger.error('Error deleting user:', error);
          message.error('שגיאה במחיקת המשתמש');
        } finally {
          setDeleting(false);
        }
      },
    });
  };

  const handleSendMessageToUser = record => {
    setSelectedUser(record);
    setSendMessageVisible(true);
  };

  const handleVerifyPhone = async record => {
    const result = await verifyUserPhone(orgId, record.uid, true);
    if (result.success) {
      message.success('הטלפון אומת. המשתמש יכול להתחיל הפעלה בקיוסק.');
      if (selectedUser?.uid === record.uid) {
        setSelectedUser({ ...selectedUser, phoneVerified: true });
      }
    } else {
      message.error(result.error || 'נכשל באימות הטלפון');
    }
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
    const targets = bulkTargets ?? (selectedUser ? [selectedUser] : []);
    if (!user?.uid || targets.length === 0) {
      message.error('שגיאה: לא ניתן לזהות את השולח');
      return;
    }
    try {
      const { message: messageText } = values;
      setSending(true);

      const results = await Promise.allSettled(
        targets.map(t => sendMessage(orgId, t.uid, messageText, user.uid))
      );
      const failed = results.filter(r => r.status === 'rejected' || !r.value?.success).length;

      if (failed === 0) {
        message.success(
          targets.length === 1 ? 'הודעה נשלחה בהצלחה' : `ההודעה נשלחה ל-${targets.length} משתמשים`
        );
      } else {
        message.warning(`נשלחו ${targets.length - failed} הודעות, ${failed} נכשלו`);
      }
      setSendMessageVisible(false);
      messageForm.resetFields();
      setBulkTargets(null);

      // Reload messages if viewing user details (single-target send only)
      if (!bulkTargets && drawerVisible && selectedUser) {
        const messageResult = await getMessagesForUser(orgId, selectedUser.uid);
        if (messageResult.success) {
          setUserMessages(messageResult.messages);
        }
      }
    } catch (error) {
      logger.error('Error sending message:', error);
      message.error('שגיאה בשליחת ההודעה');
    } finally {
      setSending(false);
    }
  };

  // One actions object shared by the card grid and the detail drawer.
  const userActions = {
    onView: handleViewUser,
    onMessage: handleSendMessageToUser,
    onAdjust: handleAdjustBalance,
    onResetPassword: handleResetPassword,
    onVerifyPhone: handleVerifyPhone,
    onKick: handleKickUser,
    onGrantAdmin: handleGrantAdmin,
    onRevokeAdmin: handleRevokeAdmin,
    onDelete: handleDeleteUser,
    onSendMessage: () => setSendMessageVisible(true),
  };

  // Filter users: text search AND status AND date AND role
  const filteredUsers = users.filter(u => {
    if (searchText) {
      const search = searchText.toLowerCase();
      const matchesSearch =
        (u.firstName?.toLowerCase() || '').includes(search) ||
        (u.lastName?.toLowerCase() || '').includes(search) ||
        (u.phoneNumber?.toLowerCase() || '').includes(search) ||
        (u.email?.toLowerCase() || '').includes(search);
      if (!matchesSearch) return false;
    }
    if (statusFilter) {
      if (getUserStatus(u) !== statusFilter) return false;
    }
    if (dateRangeFilter && dateRangeFilter[0] && dateRangeFilter[1]) {
      const created = u.createdAt ? dayjs(u.createdAt) : null;
      if (!created || created.isBefore(dateRangeFilter[0], 'day') || created.isAfter(dateRangeFilter[1], 'day')) {
        return false;
      }
    }
    if (roleFilter === 'admin' && !u.isAdmin) return false;
    if (roleFilter === 'user' && u.isAdmin) return false;
    return true;
  });

  const usersExportData = filteredUsers.map(u => ({
    name: `${u.firstName || ''} ${u.lastName || ''}`.trim(),
    phone: u.phoneNumber || '',
    email: u.email || '',
    remainingTime: Math.floor((u.remainingTime || 0) / 60),
    printBalance: u.printBalance || 0,
    status: getUserStatus(u),
  }));
  const usersExportColumns = [
    { title: 'שם', dataIndex: 'name' },
    { title: 'טלפון', dataIndex: 'phone' },
    { title: 'אימייל', dataIndex: 'email' },
    { title: 'זמן נותר (דקות)', dataIndex: 'remainingTime' },
    { title: 'תקציב הדפסות', dataIndex: 'printBalance' },
    { title: 'סטטוס', dataIndex: 'status' },
  ];

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
        <PageHeader
          title='משתמשים'
          subtitle='נהל וצפה בכל המשתמשים בארגון שלך'
          actions={
            <Space>
              <Button
                icon={<SendOutlined />}
                disabled={filteredUsers.length === 0}
                onClick={() => {
                  setBulkTargets(filteredUsers);
                  setSendMessageVisible(true);
                }}
              >
                הודעה למסוננים ({filteredUsers.length})
              </Button>
              <Dropdown
                menu={{
                  items: [
                    {
                      key: 'csv',
                      icon: <DownloadOutlined />,
                      label: 'ייצא CSV',
                      onClick: () =>
                        exportToCSV(usersExportData, usersExportColumns, `users-${new Date().toISOString().split('T')[0]}`),
                    },
                    {
                      key: 'excel',
                      icon: <DownloadOutlined />,
                      label: 'ייצא Excel',
                      onClick: () =>
                        exportToExcel(usersExportData, usersExportColumns, `users-${new Date().toISOString().split('T')[0]}`),
                    },
                    {
                      key: 'pdf',
                      icon: <DownloadOutlined />,
                      label: 'ייצא PDF',
                      onClick: () =>
                        exportToPDF(usersExportData, usersExportColumns, `users-${new Date().toISOString().split('T')[0]}`, 'ייצוא משתמשים'),
                    },
                  ],
                }}
                trigger={['click']}
              >
                <Button icon={<DownloadOutlined />}>ייצא</Button>
              </Dropdown>
            </Space>
          }
        />

        {/* Stats Row */}
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={6}>
            <Card
              variant='borderless'
              style={{
                borderRadius: 14,
                background:
                  'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%)',
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
                background:
                  'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%)',
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
                background:
                  'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%)',
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
                background:
                  'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(102, 126, 234, 0.05) 100%)',
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

        {/* Search & Filters */}
        <Card
          variant='borderless'
          style={{ borderRadius: 14 }}
          styles={{ body: { padding: '16px 20px' } }}
        >
          <Collapse
            ghost
            items={[
              {
                key: 'filters',
                label: 'סינון וחיפוש',
                children: (
                  <Space direction='vertical' size='middle' style={{ width: '100%' }}>
                    <Search
                      placeholder='חפש לפי שם, טלפון או אימייל...'
                      allowClear
                      size='large'
                      prefix={<SearchOutlined style={{ color: '#9ca3af' }} />}
                      value={searchText}
                      onChange={e => updateFilters({ q: e.target.value })}
                      style={{ width: '100%' }}
                    />
                    <Space wrap size='middle'>
                      <Space>
                        <Text type='secondary'>סטטוס:</Text>
                        <Segmented
                          value={statusFilter ?? 'all'}
                          onChange={v => updateFilters({ status: v === 'all' ? null : v })}
                          options={[
                            { label: 'הכל', value: 'all' },
                            { label: 'פעיל', value: 'active' },
                            { label: 'מושהה', value: 'connected' },
                            { label: 'לא פעיל', value: 'offline' },
                          ]}
                        />
                      </Space>
                      <Space>
                        <Text type='secondary'>תאריך הצטרפות:</Text>
                        <DatePicker.RangePicker
                          value={dateRangeFilter}
                          onChange={range =>
                            updateFilters({
                              from: range?.[0]?.format('YYYY-MM-DD') ?? null,
                              to: range?.[1]?.format('YYYY-MM-DD') ?? null,
                            })
                          }
                          placeholder={['מ-', 'עד']}
                        />
                      </Space>
                      <Space>
                        <Text type='secondary'>תפקיד:</Text>
                        <Select
                          value={roleFilter ?? 'all'}
                          onChange={v => updateFilters({ role: v === 'all' ? null : v })}
                          style={{ minWidth: 100 }}
                          options={[
                            { label: 'הכל', value: 'all' },
                            { label: 'מנהל', value: 'admin' },
                            { label: 'משתמש', value: 'user' },
                          ]}
                        />
                      </Space>
                    </Space>
                  </Space>
                ),
              },
            ]}
          />
        </Card>

        {/* Users Grid */}
        {loading ? (
          <Row gutter={[20, 20]}>
            {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
              <Col key={i} xs={24} sm={12} lg={8} xl={6}>
                <Card style={{ borderRadius: 18, overflow: 'hidden' }}>
                  <div style={{ background: 'linear-gradient(135deg, #e8eaed 0%, #f0f2f5 100%)', height: 140, borderRadius: '18px 18px 0 0' }} />
                  <div style={{ padding: 16 }}>
                    <Skeleton active avatar paragraph={{ rows: 3 }} />
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        ) : filteredUsers.length === 0 ? (
          <Card variant='borderless' style={{ borderRadius: 14 }}>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <Text type='secondary'>
                  {searchText ? 'לא נמצאו משתמשים תואמים' : 'אין משתמשים'}
                </Text>
              }
            />
          </Card>
        ) : (
          <motion.div variants={containerVariants} initial='hidden' animate='visible'>
            <Row gutter={[20, 20]}>
              {filteredUsers.map((userRecord, index) => (
                <Col key={userRecord.uid} xs={24} sm={12} lg={8} xl={6}>
                  <UserCard
                    userRecord={userRecord}
                    index={index}
                    currentUserUid={user?.uid}
                    kicking={kicking}
                    actions={userActions}
                  />
                </Col>
              ))}
            </Row>
          </motion.div>
        )}
      </Space>

      <BalanceAdjustModal
        open={adjustBalanceVisible}
        user={adjustingUser}
        form={form}
        onOk={handleBalanceSubmit}
        onCancel={() => {
          setAdjustBalanceVisible(false);
          form.resetFields();
        }}
        confirmLoading={adjusting}
      />

      <UserDrawer
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        user={selectedUser}
        currentUserUid={user?.uid}
        purchases={userPurchases}
        loadingPurchases={loadingPurchases}
        messages={userMessages}
        loadingMessages={loadingMessages}
        deleting={deleting}
        actions={userActions}
      />

      <SendMessageModal
        open={sendMessageVisible}
        onCancel={() => {
          setSendMessageVisible(false);
          messageForm.resetFields();
          setBulkTargets(null);
        }}
        onFinish={handleSendMessage}
        form={messageForm}
        sending={sending}
        bulkCount={bulkTargets ? bulkTargets.length : null}
        targetName={
          selectedUser ? `${selectedUser.firstName} ${selectedUser.lastName}` : null
        }
      />

      <ResetPasswordModal
        open={resetPasswordVisible}
        user={resetPasswordUser}
        form={resetPasswordForm}
        onOk={handleResetPasswordSubmit}
        onCancel={() => {
          setResetPasswordVisible(false);
          resetPasswordForm.resetFields();
          setResetPasswordUser(null);
        }}
        confirmLoading={resettingPassword}
      />
    </motion.div>
  );
};

export default UsersPage;
