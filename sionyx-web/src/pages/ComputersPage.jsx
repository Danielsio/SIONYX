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
  Empty,
  Modal,
  message,
  Tooltip,
  Badge,
} from 'antd';
import {
  DesktopOutlined,
  UserOutlined,
  ClockCircleOutlined,
  LogoutOutlined,
  DeleteOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import {
  getAllComputers,
  getComputerUsageStats,
  getActiveComputerUsers,
  forceLogoutUser,
  updateComputer,
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

  const formatTime = timeString => {
    if (!timeString) return 'לעולם לא';
    try {
      return formatDistanceToNow(new Date(timeString), { addSuffix: true });
    } catch {
      return 'תאריך לא תקין';
    }
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
      render: (text, record) => (
        <Space direction='vertical' size={0}>
          <Text strong>{text}</Text>
          <Text type='secondary' style={{ fontSize: '12px' }}>
            {record.userPhone}
          </Text>
        </Space>
      ),
    },
    {
      title: 'מחשב',
      dataIndex: 'computerName',
      key: 'computerName',
      render: (text, record) => (
        <Space direction='vertical' size={0}>
          <Text strong>{text}</Text>
          <Text type='secondary' style={{ fontSize: '12px' }}>
            {record.computerLocation}
          </Text>
        </Space>
      ),
    },
    {
      title: 'זמן הפעלה נוכחי',
      key: 'currentSession',
      render: (_, record) => (
        <Space direction='vertical' size={0}>
          <Text strong style={{ color: '#52c41a', fontSize: '16px' }}>
            {formatSessionTime(record.loginTime)}
          </Text>
          <Text type='secondary' style={{ fontSize: '12px' }}>
            התחבר ב: {formatTime(record.loginTime)}
          </Text>
        </Space>
      ),
    },
    {
      title: 'זמן נותר',
      dataIndex: 'remainingTime',
      key: 'remainingTime',
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
      render: active => (
        <Tag color={active ? 'green' : 'default'}>{active ? 'פעיל' : 'לא פעיל'}</Tag>
      ),
    },
    {
      title: 'פעולות',
      key: 'actions',
      render: (_, record) => (
        <Button
          type='text'
          danger
          icon={<LogoutOutlined />}
          onClick={() => handleForceLogout(record.userId, record.computerId)}
        >
          התנתק
        </Button>
      ),
    },
  ];

  // Computers Table Columns
  const computersColumns = [
    {
      title: 'שם המחשב',
      dataIndex: 'computerName',
      key: 'computerName',
      render: (text, record) => (
        <Space direction='vertical' size={0}>
          <Text strong>{text}</Text>
          <Text type='secondary' style={{ fontSize: '12px' }}>
            {record.location || 'ללא מיקום'}
          </Text>
        </Space>
      ),
    },
    {
      title: 'כתובת MAC',
      dataIndex: 'macAddress',
      key: 'macAddress',
      render: text => <Text code>{text || 'לא ידוע'}</Text>,
    },
    {
      title: 'כתובת IP',
      dataIndex: ['networkInfo', 'local_ip'],
      key: 'ip',
      render: text => <Text code>{text || 'לא ידוע'}</Text>,
    },
    {
      title: 'מערכת הפעלה',
      dataIndex: 'osInfo',
      key: 'os',
      render: osInfo => (
        <Text>
          {osInfo?.system || 'לא ידוע'} {osInfo?.release || ''}
        </Text>
      ),
    },
    {
      title: 'סטטוס',
      dataIndex: 'isActive',
      key: 'isActive',
      render: active => (
        <Tag color={active ? 'green' : 'default'}>{active ? 'פעיל' : 'לא פעיל'}</Tag>
      ),
    },
    {
      title: 'נראה לאחרונה',
      dataIndex: 'lastSeen',
      key: 'lastSeen',
      render: time => <Text type='secondary'>{formatTime(time)}</Text>,
    },
    {
      title: 'פעולות',
      key: 'actions',
      render: (_, record) => (
        <Button
          type='text'
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleDeleteComputer(record.id)}
        >
          מחק
        </Button>
      ),
    },
  ];

  // Overview Table Columns
  const overviewColumns = [
    {
      title: 'מחשב',
      dataIndex: 'computerName',
      key: 'computerName',
      render: (text, record) => (
        <Space direction='vertical' size={0}>
          <Text strong>{text}</Text>
          <Text type='secondary' style={{ fontSize: '12px' }}>
            {record.macAddress}
          </Text>
        </Space>
      ),
    },
    {
      title: 'מיקום',
      dataIndex: 'location',
      key: 'location',
      render: text => <Text>{text || 'לא צוין'}</Text>,
    },
    {
      title: 'סטטוס',
      dataIndex: 'isActive',
      key: 'isActive',
      render: active => (
        <Tag color={active ? 'green' : 'default'}>{active ? 'פעיל' : 'לא פעיל'}</Tag>
      ),
    },
    {
      title: 'משתמש נוכחי',
      dataIndex: 'currentUserName',
      key: 'currentUser',
      render: text => <Text>{text || 'זמין'}</Text>,
    },
    {
      title: 'נראה לאחרונה',
      dataIndex: 'lastSeen',
      key: 'lastSeen',
      render: time => <Text type='secondary'>{formatTime(time)}</Text>,
    },
    {
      title: 'פעולות',
      key: 'actions',
      render: (_, record) =>
        record.currentUserId && (
          <Button
            type='text'
            danger
            icon={<LogoutOutlined />}
            onClick={() => handleForceLogout(record.currentUserId, record.computerId)}
          >
            התנתק
          </Button>
        ),
    },
  ];

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
          >
            <Table
              columns={activeUsersColumns}
              dataSource={activeUsers}
              rowKey={record => `${record.userId}-${record.computerId}`}
              pagination={{ pageSize: 5 }}
              locale={{ emptyText: 'אין משתמשים פעילים' }}
              size='small'
            />
          </Card>

          {/* Computer Overview Table */}
          <Card title='סקירת מחשבים'>
            <Table
              columns={overviewColumns}
              dataSource={stats?.computerDetails || []}
              rowKey='computerId'
              pagination={{ pageSize: 10 }}
              locale={{ emptyText: 'אין נתונים זמינים' }}
            />
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
        <Table
          columns={computersColumns}
          dataSource={computers}
          rowKey='id'
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: 'אין מחשבים זמינים' }}
        />
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
