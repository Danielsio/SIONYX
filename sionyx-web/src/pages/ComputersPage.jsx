import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Tabs,
  Statistic,
  Row,
  Col,
  Tag,
  Button,
  Space,
  Typography,
  Spin,
  Modal,
  message,
  Badge,
} from 'antd';
import {
  DesktopOutlined,
  UserOutlined,
  LogoutOutlined,
  DeleteOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import {
  getAllComputers,
  getComputerUsageStats,
  getActiveComputerUsers,
  forceLogoutUser,
  deleteComputer,
} from '../services/computerService';
import { formatDistanceToNow } from 'date-fns';

const { Title, Text } = Typography;

const ComputersPage = () => {
  const [computers, setComputers] = useState([]);
  const [activeUsers, setActiveUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [computersResult, usersResult, statsResult] = await Promise.all([
        getAllComputers(),
        getActiveComputerUsers(),
        getComputerUsageStats(),
      ]);

      if (computersResult.success) {
        setComputers(computersResult.data);
      }

      if (usersResult.success) {
        setActiveUsers(usersResult.data);
      }

      if (statsResult.success) {
        setStats(statsResult.data);
      }
    } catch (err) {
      setError('נכשל בטעינת נתוני המחשבים');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleForceLogout = async (userId, computerId) => {
    Modal.confirm({
      title: 'התנתקות כפויה',
      content: 'האם אתה בטוח שברצונך להתנתק את המשתמש הזה?',
      okText: 'כן, התנתק',
      cancelText: 'ביטול',
      onOk: async () => {
        try {
          const result = await forceLogoutUser(userId, computerId);
          if (result.success) {
            message.success('המשתמש התנתק בהצלחה');
            await loadData();
          } else {
            message.error('נכשל בהתנתקות המשתמש: ' + result.error);
          }
        } catch (err) {
          message.error('שגיאה בהתנתקות המשתמש: ' + err.message);
        }
      },
    });
  };

  const handleDeleteComputer = async computerId => {
    Modal.confirm({
      title: 'מחיקת מחשב',
      content: 'האם אתה בטוח שברצונך למחוק את המחשב הזה? פעולה זו לא ניתנת לביטול.',
      okText: 'כן, מחק',
      cancelText: 'ביטול',
      okType: 'danger',
      onOk: async () => {
        try {
          const result = await deleteComputer(computerId);
          if (result.success) {
            message.success('המחשב נמחק בהצלחה');
            await loadData();
          } else {
            message.error('נכשל במחיקת המחשב: ' + result.error);
          }
        } catch (err) {
          message.error('שגיאה במחיקת המחשב: ' + err.message);
        }
      },
    });
  };

  const formatDuration = seconds => {
    if (!seconds) return '0s';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else if (minutes > 0) {
      return `${minutes}:${secs.toString().padStart(2, '0')}`;
    } else {
      return `${secs}s`;
    }
  };

  const formatSessionTime = loginTime => {
    if (!loginTime) return '0:00:00';
    const now = new Date();
    const login = new Date(loginTime);
    const diffMs = now - login;
    const diffSeconds = Math.floor(diffMs / 1000);
    return formatDuration(diffSeconds);
  };

  // Active Users Table Columns
  const activeUsersColumns = [
    {
      title: 'משתמש',
      dataIndex: 'userName',
      key: 'userName',
      fixed: 'right',
      width: 140,
      render: (text, record) => (
        <Space direction='vertical' size={0}>
          <Text strong style={{ whiteSpace: 'nowrap' }}>{text}</Text>
          <Text type='secondary' style={{ fontSize: '11px' }}>
            {record.userPhone}
          </Text>
        </Space>
      ),
    },
    {
      title: 'מחשב',
      dataIndex: 'computerName',
      key: 'computerName',
      width: 120,
      responsive: ['sm'],
      render: text => <Text strong>{text}</Text>,
    },
    {
      title: 'זמן פעילות',
      key: 'currentSession',
      width: 110,
      render: (_, record) => {
        if (!record.sessionActive || !record.sessionStartTime) {
          return <Text type="secondary">--</Text>;
        }
        return (
          <Text strong style={{ color: '#52c41a' }}>
            {formatSessionTime(record.sessionStartTime)}
          </Text>
        );
      },
    },
    {
      title: 'נותר',
      dataIndex: 'remainingTime',
      key: 'remainingTime',
      width: 80,
      render: time => (
        <Text style={{ color: time > 3600 ? '#52c41a' : time > 1800 ? '#faad14' : '#ff4d4f' }}>
          {formatDuration(time)}
        </Text>
      ),
    },
    {
      title: 'סטטוס',
      dataIndex: 'sessionActive',
      key: 'sessionActive',
      width: 80,
      responsive: ['md'],
      render: active => (
        <Tag color={active ? 'green' : 'default'}>{active ? 'פעיל' : 'לא פעיל'}</Tag>
      ),
    },
    {
      title: '',
      key: 'actions',
      fixed: 'left',
      width: 80,
      render: (_, record) => (
        <Button
          type='primary'
          danger
          size='small'
          icon={<LogoutOutlined />}
          onClick={() => handleForceLogout(record.userId, record.computerId)}
        >
          נתק
        </Button>
      ),
    },
  ];

  // Computer Card Component - for overview tab (uses stats.computerDetails structure)
  const ComputerCard = ({ computer }) => {
    const hasUser = !!computer.currentUserName;
    // Derive isActive from currentUserId (if user is associated, it's active)
    const isActive = !!computer.currentUserId;

    return (
      <Card
        size="small"
        style={{
          marginBottom: 12,
          borderRadius: 8,
          border: isActive ? '1px solid #52c41a' : '1px solid #d9d9d9',
        }}
        styles={{ body: { padding: '12px 16px' } }}
      >
        <Row align="middle" justify="space-between" gutter={[8, 8]}>
          {/* Computer Name & Status */}
          <Col flex="auto">
            <Space size={8}>
              <DesktopOutlined style={{ color: isActive ? '#52c41a' : '#bfbfbf', fontSize: 18 }} />
              <Text strong style={{ fontSize: 15 }}>{computer.computerName}</Text>
              <Tag 
                color={isActive ? 'success' : 'default'} 
                style={{ marginRight: 0 }}
              >
                {isActive ? 'פעיל' : 'לא פעיל'}
              </Tag>
            </Space>
          </Col>

          {/* Current User Status */}
          <Col>
            <Space size={8} align="center">
              {hasUser ? (
                <>
                  <Space size={4}>
                    <UserOutlined style={{ color: '#1890ff' }} />
                    <Text strong style={{ color: '#1890ff' }}>{computer.currentUserName}</Text>
                  </Space>
                  <Button
                    type="link"
                    danger
                    size="small"
                    icon={<LogoutOutlined />}
                    onClick={() => handleForceLogout(computer.currentUserId, computer.computerId)}
                    style={{ padding: 0, height: 'auto' }}
                  >
                    התנתק
                  </Button>
                </>
              ) : (
                <Tag icon={<CheckCircleOutlined />} color="default">
                  לא בשימוש כעת
                </Tag>
              )}
              <Button
                type="text"
                danger
                size="small"
                icon={<DeleteOutlined />}
                onClick={() => handleDeleteComputer(computer.computerId)}
              />
            </Space>
          </Col>
        </Row>
      </Card>
    );
  };

  // All Computers Card - for "כל המחשבים" tab (uses computers array structure with id field)
  const AllComputerCard = ({ computer }) => {
    // Derive isActive from currentUserId (if user is associated, it's active)
    const isActive = !!computer.currentUserId;
    const computerId = computer.id;

    return (
      <Card
        size="small"
        style={{
          marginBottom: 12,
          borderRadius: 8,
          border: isActive ? '1px solid #52c41a' : '1px solid #d9d9d9',
        }}
        styles={{ body: { padding: '12px 16px' } }}
      >
        <Row align="middle" justify="space-between">
          {/* Computer Name & Status */}
          <Col>
            <Space size={8}>
              <DesktopOutlined style={{ color: isActive ? '#52c41a' : '#bfbfbf', fontSize: 18 }} />
              <Text strong style={{ fontSize: 15 }}>{computer.computerName}</Text>
              <Tag 
                color={isActive ? 'success' : 'default'} 
                style={{ marginRight: 0 }}
              >
                {isActive ? 'פעיל' : 'לא פעיל'}
              </Tag>
            </Space>
          </Col>

          {/* Delete Button */}
          <Col>
            <Button
              type="text"
              danger
              size="small"
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteComputer(computerId)}
            />
          </Col>
        </Row>
      </Card>
    );
  };

  const tabItems = [
    {
      key: 'overview',
      label: 'סקירה כללית',
      children: (
        <Space direction='vertical' size='large' style={{ width: '100%' }}>
          {/* Active Users Table */}
          <Card
            title='משתמשים פעילים'
            extra={<Badge count={activeUsers.length} showZero color='#52c41a' />}
            styles={{ body: { padding: 0, overflow: 'hidden' } }}
          >
            <Table
              columns={activeUsersColumns}
              dataSource={activeUsers}
              rowKey={record => `${record.userId}-${record.computerId}`}
              pagination={{ pageSize: 5 }}
              locale={{ emptyText: 'אין משתמשים פעילים' }}
              size='small'
              scroll={{ x: 'max-content' }}
            />
          </Card>

          {/* Computer Cards - Responsive Layout */}
          <Card title='סקירת מחשבים'>
            {stats?.computerDetails?.length > 0 ? (
              stats.computerDetails.map(computer => (
                <ComputerCard key={computer.computerId} computer={computer} />
              ))
            ) : (
              <div style={{ textAlign: 'center', padding: '40px 0', color: '#bfbfbf' }}>
                <DesktopOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>אין מחשבים רשומים</div>
              </div>
            )}
          </Card>
        </Space>
      ),
    },
    {
      key: 'active',
      label: (
        <Space>
          משתמשים פעילים
          <Badge count={activeUsers.length} showZero color='#52c41a' />
        </Space>
      ),
      children: (
        <Table
          columns={activeUsersColumns}
          dataSource={activeUsers}
          rowKey={record => `${record.userId}-${record.computerId}`}
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: 'אין משתמשים פעילים' }}
        />
      ),
    },
    {
      key: 'computers',
      label: 'כל המחשבים',
      children: (
        <div>
          {computers.length > 0 ? (
            computers.map(computer => (
              <AllComputerCard key={computer.id} computer={computer} />
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#bfbfbf' }}>
              <DesktopOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <div>אין מחשבים רשומים</div>
            </div>
          )}
        </div>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size='large' />
        <div style={{ marginTop: 16 }}>
          <Text>טוען נתוני מחשבים...</Text>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Text type='danger'>{error}</Text>
        <br />
        <Button
          type='primary'
          icon={<ReloadOutlined />}
          onClick={loadData}
          style={{ marginTop: 16 }}
        >
          נסה שוב
        </Button>
      </div>
    );
  }

  return (
    <div style={{ direction: 'rtl' }}>
      <Space direction='vertical' size='large' style={{ width: '100%' }}>
        {/* Header */}
        <div>
          <Title level={2} style={{ marginBottom: 8 }}>
            ניהול מחשבים
          </Title>
          <Text type='secondary'>צפה ונתח מחשבים בארגון שלך</Text>
        </div>

        {/* Stats Overview */}
        {stats && (
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} lg={6}>
              <Card variant='borderless' style={{ textAlign: 'center' }}>
                <Statistic
                  title='סך מחשבים'
                  value={stats.totalComputers}
                  prefix={<DesktopOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card variant='borderless' style={{ textAlign: 'center' }}>
                <Statistic
                  title='מחשבים פעילים'
                  value={stats.activeComputers}
                  prefix={<DesktopOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card variant='borderless' style={{ textAlign: 'center' }}>
                <Statistic
                  title='בשימוש'
                  value={stats.computersWithUsers}
                  prefix={<UserOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card variant='borderless' style={{ textAlign: 'center' }}>
                <Statistic
                  title='משתמשים פעילים'
                  value={activeUsers.length}
                  prefix={<UserOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
          </Row>
        )}

        {/* Tabs */}
        <Card>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={tabItems}
            tabBarExtraContent={
              <Button icon={<ReloadOutlined />} onClick={loadData}>
                רענן
              </Button>
            }
          />
        </Card>
      </Space>
    </div>
  );
};

export default ComputersPage;
