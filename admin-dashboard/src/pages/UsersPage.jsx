import { useEffect, useState } from 'react';
import { 
  Card, 
  Table, 
  Tag, 
  Space, 
  Button, 
  Input, 
  Typography,
  Drawer,
  Descriptions,
  Badge,
  message,
  Spin,
  Modal,
  Form,
  InputNumber,
  Dropdown
} from 'antd';
import { getStatusLabel, getStatusColor } from '../constants/purchaseStatus';
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
  MinusCircleOutlined
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';
import { 
  getAllUsers, 
  getUserPurchaseHistory, 
  adjustUserBalance,
  grantAdminPermission,
  revokeAdminPermission,
  kickUser
} from '../services/userService';
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

  const user = useAuthStore((state) => state.user);
  const { users, setUsers } = useDataStore();

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    
    // Get orgId from authenticated user
    const orgId = user?.orgId || localStorage.getItem('adminOrgId');

    if (!orgId) {
      message.error('Organization ID not found. Please log in again.');
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

  const handleViewUser = async (record) => {
    setSelectedUser(record);
    setDrawerVisible(true);
    setLoadingPurchases(true);

    // Get orgId
    const orgId = user?.orgId || localStorage.getItem('adminOrgId');

    // Load user's purchase history
    const result = await getUserPurchaseHistory(orgId, record.uid);
    if (result.success) {
      setUserPurchases(result.purchases);
      console.log(`Loaded ${result.purchases.length} purchases for user ${record.uid}`);
    } else {
      console.error('Failed to load user purchases:', result.error);
    }
    setLoadingPurchases(false);
  };

  const handleAdjustBalance = (record) => {
    setAdjustingUser(record);
    // Set current values as form initial values
    form.setFieldsValue({
      minutes: Math.floor((record.remainingTime || 0) / 60), // Convert seconds to minutes
      prints: record.remainingPrints || 0
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
        prints: values.prints - currentPrints // Difference in prints
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
            remainingPrints: result.newBalance.remainingPrints
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

  const handleGrantAdmin = (record) => {
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
              isAdmin: true
            });
          }
        } else {
          message.error(result.error || 'Failed to grant admin permission');
        }
      }
    });
  };

  const handleRevokeAdmin = (record) => {
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
              isAdmin: false
            });
          }
        } else {
          message.error(result.error || 'Failed to revoke admin permission');
        }
      }
    });
  };

  const handleKickUser = (record) => {
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
      }
    });
  };

  const formatTime = (seconds) => {
    return formatTimeHebrewCompact(seconds);
  };

  const columns = [
    {
      title: 'שם',
      key: 'name',
      render: (_, record) => (
        <Space>
          <UserOutlined style={{ color: '#1890ff' }} />
          <span>{`${record.firstName || ''} ${record.lastName || ''}`.trim() || 'לא זמין'}</span>
        </Space>
      ),
      sorter: (a, b) => 
        `${a.firstName} ${a.lastName}`.localeCompare(`${b.firstName} ${b.lastName}`),
    },
    {
      title: 'מספר טלפון',
      dataIndex: 'phoneNumber',
      key: 'phoneNumber',
      render: (phone) => phone || 'לא זמין',
    },
    {
      title: 'אימייל',
      dataIndex: 'email',
      key: 'email',
      render: (email) => email || 'לא זמין',
    },
    {
      title: 'זמן נותר',
      dataIndex: 'remainingTime',
      key: 'remainingTime',
      render: (time) => (
        <Space>
          <ClockCircleOutlined />
          <Text>{formatTime(time || 0)}</Text>
        </Space>
      ),
      sorter: (a, b) => (a.remainingTime || 0) - (b.remainingTime || 0),
    },
    {
      title: 'הדפסות',
      dataIndex: 'remainingPrints',
      key: 'remainingPrints',
      render: (prints) => (
        <Space>
          <PrinterOutlined />
          <Text>{prints || 0}</Text>
        </Space>
      ),
      sorter: (a, b) => (a.remainingPrints || 0) - (b.remainingPrints || 0),
    },
    {
      title: 'סטטוס',
      dataIndex: 'isActive',
      key: 'isActive',
      render: (isActive) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? 'פעיל' : 'לא פעיל'}
        </Tag>
      ),
      filters: [
        { text: 'פעיל', value: true },
        { text: 'לא פעיל', value: false },
      ],
      onFilter: (value, record) => record.isActive === value,
    },
    {
      title: 'נוצר',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date) => date ? dayjs(date).format('MMM D, YYYY') : 'לא זמין',
      sorter: (a, b) => 
        new Date(a.createdAt || 0) - new Date(b.createdAt || 0),
    },
    {
      title: 'תפקיד',
      dataIndex: 'isAdmin',
      key: 'isAdmin',
      render: (isAdmin) => (
        isAdmin ? (
          <Tag color="gold" icon={<CrownOutlined />}>
            מנהל
          </Tag>
        ) : (
          <Tag color="default">משתמש</Tag>
        )
      ),
      filters: [
        { text: 'מנהל', value: true },
        { text: 'משתמש', value: false },
      ],
      onFilter: (value, record) => record.isAdmin === value,
    },
    {
      title: 'סטטוס התקנה',
      dataIndex: 'forceLogout',
      key: 'forceLogout',
      render: (forceLogout, record) => {
        if (forceLogout === true) {
          return (
            <Tag color="red" icon={<MinusCircleOutlined />}>
              הותקן
            </Tag>
          );
        }
        return (
          <Tag color="green">
            פעיל
          </Tag>
        );
      },
      filters: [
        { text: 'פעיל', value: false },
        { text: 'הותקן', value: true },
      ],
      onFilter: (value, record) => {
        if (value === true) return record.forceLogout === true;
        if (value === false) return record.forceLogout !== true;
        return true;
      },
    },
    {
      title: 'פעולה',
      key: 'action',
      render: (_, record) => {
        const menuItems = [
          {
            key: 'view',
            icon: <EyeOutlined />,
            label: 'צפה בפרטים',
            onClick: () => handleViewUser(record)
          },
          {
            key: 'adjust',
            icon: <EditOutlined />,
            label: 'התאם יתרה',
            onClick: () => handleAdjustBalance(record)
          },
          {
            type: 'divider'
          },
          // Only show kick button if user is not already kicked
          record.forceLogout !== true ? {
            key: 'kick',
            icon: <MinusCircleOutlined />,
            label: 'נתק משתמש',
            danger: true,
            onClick: () => handleKickUser(record),
            disabled: kicking
          } : {
            key: 'kicked',
            icon: <MinusCircleOutlined />,
            label: 'הותקן',
            disabled: true
          },
          record.isAdmin ? {
            key: 'revoke',
            icon: <MinusCircleOutlined />,
            label: 'הסר הרשאות מנהל',
            danger: true,
            onClick: () => handleRevokeAdmin(record)
          } : {
            key: 'grant',
            icon: <CrownOutlined />,
            label: 'הענק הרשאות מנהל',
            onClick: () => handleGrantAdmin(record)
          }
        ];

        return (
          <Space>
            <Button 
              type="link" 
              icon={<EyeOutlined />}
              onClick={() => handleViewUser(record)}
            >
              צפה
            </Button>
            <Dropdown menu={{ items: menuItems }} trigger={['click']}>
              <Button type="text" icon={<MoreOutlined />} />
            </Dropdown>
          </Space>
        );
      },
    },
  ];

  const purchaseColumns = [
    {
      title: 'תאריך',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date) => date ? dayjs(date).format('MMM D, YYYY HH:mm') : 'לא זמין',
    },
    {
      title: 'חבילה',
      dataIndex: 'packageName',
      key: 'packageName',
    },
    {
      title: 'סכום',
      dataIndex: 'finalPrice',
      key: 'finalPrice',
      render: (price) => `₪${price?.toFixed(2) || '0.00'}`,
    },
    {
      title: 'סטטוס',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        return <Tag color={getStatusColor(status)}>{getStatusLabel(status)}</Tag>;
      },
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
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ marginBottom: 8 }}>
              משתמשים
            </Title>
            <Text type="secondary">
              נהל וצפה בכל המשתמשים בארגון שלך
            </Text>
          </div>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={loadUsers}
            loading={loading}
          >
            רענן
          </Button>
        </div>

        {/* Search and Filters */}
        <Card>
          <Search
            placeholder="חפש לפי שם, טלפון או אימייל"
            allowClear
            size="large"
            prefix={<SearchOutlined />}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: '100%', maxWidth: 500 }}
          />
        </Card>

        {/* Users Table */}
        <Card>
          <Table
            columns={columns}
            dataSource={filteredUsers}
            rowKey="uid"
            loading={loading}
            scroll={{ x: 800 }}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `סך ${total} משתמשים`,
              responsive: true,
              showQuickJumper: false,
            }}
            size="small"
          />
        </Card>
      </Space>

      {/* Adjust Balance Modal */}
      <Modal
        title={
          <Space>
            <EditOutlined />
            <span>Adjust Balance</span>
          </Space>
        }
        open={adjustBalanceVisible}
        onOk={handleBalanceSubmit}
        onCancel={() => {
          setAdjustBalanceVisible(false);
          form.resetFields();
        }}
        confirmLoading={adjusting}
        okText="Update"
        width={500}
      >
        {adjustingUser && (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div>
              <Text strong>User: </Text>
              <Text>{`${adjustingUser.firstName} ${adjustingUser.lastName}`}</Text>
            </div>

            <Form form={form} layout="vertical">
              <Form.Item
                name="minutes"
                label="Time Balance (minutes)"
                tooltip="Edit the total minutes this user should have"
                rules={[
                  { required: true, message: 'Please enter time' },
                  { type: 'number', min: 0, message: 'Time cannot be negative' }
                ]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder="e.g., 120 (2 hours)"
                  prefix={<ClockCircleOutlined />}
                  min={0}
                />
              </Form.Item>

              <Form.Item
                name="prints"
                label="Prints Balance"
                tooltip="Edit the total prints this user should have"
                rules={[
                  { required: true, message: 'Please enter prints' },
                  { type: 'number', min: 0, message: 'Prints cannot be negative' }
                ]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder="e.g., 50"
                  prefix={<PrinterOutlined />}
                  min={0}
                />
              </Form.Item>
            </Form>

            <div style={{ padding: '8px', backgroundColor: '#e6f7ff', borderRadius: '4px', border: '1px solid #91d5ff' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                💡 Tip: Current values are shown. Edit them to set the new balance. You can increase, decrease, or set to any value.
              </Text>
            </div>
          </Space>
        )}
      </Modal>

      {/* User Detail Drawer */}
      <Drawer
        title="User Details"
        placement="right"
        width={600}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedUser && (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Card>
              <Descriptions column={1} bordered>
                <Descriptions.Item label="Name">
                  {`${selectedUser.firstName || ''} ${selectedUser.lastName || ''}`.trim() || 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Phone">
                  {selectedUser.phoneNumber || 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Email">
                  {selectedUser.email || 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Status">
                  <Badge 
                    status={selectedUser.isActive ? 'success' : 'default'} 
                    text={selectedUser.isActive ? 'Active' : 'Inactive'} 
                  />
                </Descriptions.Item>
                <Descriptions.Item label="Role">
                  {selectedUser.isAdmin ? (
                    <Tag color="gold" icon={<CrownOutlined />}>
                      Admin
                    </Tag>
                  ) : (
                    <Tag color="default">User</Tag>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="Remaining Time">
                  <Space>
                    <ClockCircleOutlined />
                    {formatTime(selectedUser.remainingTime || 0)}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="Remaining Prints">
                  <Space>
                    <PrinterOutlined />
                    {selectedUser.remainingPrints || 0}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="Created">
                  {selectedUser.createdAt 
                    ? dayjs(selectedUser.createdAt).format('MMMM D, YYYY HH:mm')
                    : 'N/A'
                  }
                </Descriptions.Item>
                <Descriptions.Item label="Last Updated">
                  {selectedUser.updatedAt 
                    ? dayjs(selectedUser.updatedAt).format('MMMM D, YYYY HH:mm')
                    : 'N/A'
                  }
                </Descriptions.Item>
              </Descriptions>
            </Card>

            <Card title="Purchase History">
              {loadingPurchases ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <Spin />
                </div>
              ) : (
                <Table
                  columns={purchaseColumns}
                  dataSource={userPurchases}
                  rowKey="id"
                  size="small"
                  pagination={{ pageSize: 5 }}
                />
              )}
            </Card>
          </Space>
        )}
      </Drawer>
    </div>
  );
};

export default UsersPage;

