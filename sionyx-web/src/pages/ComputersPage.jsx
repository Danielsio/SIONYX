import React, { useState, useEffect } from 'react';
import {
  Card,
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
  ClockCircleOutlined,
  PhoneOutlined,
  DownOutlined,
  UpOutlined,
} from '@ant-design/icons';
import {
  getAllComputers,
  getComputerUsageStats,
  getActiveComputerUsers,
  forceLogoutUser,
  deleteComputer,
} from '../services/computerService';
import {
  getUserStatus,
  getStatusLabel,
  getStatusColor,
} from '../constants/userStatus';
import { useAuthStore } from '../store/authStore';

const { Title, Text } = Typography;

const ComputersPage = () => {
  const [computers, setComputers] = useState([]);
  const [activeUsers, setActiveUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  const user = useAuthStore(state => state.user);
  
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

  const formatSessionTime = sessionStartTime => {
    if (!sessionStartTime) return '0:00:00';
    const now = new Date();
    const login = new Date(sessionStartTime);
    const diffMs = now - login;
    const diffSeconds = Math.floor(diffMs / 1000);
    return formatDuration(diffSeconds);
  };

  // User Card Component - for active users display
  const UserCard = ({ user }) => {
    const [expanded, setExpanded] = useState(false);
    const remainingColor = user.remainingTime > 3600 ? '#52c41a' : user.remainingTime > 1800 ? '#faad14' : '#ff4d4f';
    
    // Use centralized status logic - map activeUsers data to getUserStatus format
    // Users in activeUsers list are always logged in (isLoggedIn: true)
    const userStatus = getUserStatus({
      isLoggedIn: true,  // They're in activeUsers, so they're logged in
      isSessionActive: user.sessionActive,
    });
    const statusLabel = getStatusLabel(userStatus);
    const statusColor = getStatusColor(userStatus);

    return (
      <Card
        size="small"
        style={{
          marginBottom: 12,
          borderRadius: 8,
          border: user.sessionActive ? '1px solid #52c41a' : '1px solid #d9d9d9',
          cursor: 'pointer',
        }}
        styles={{ body: { padding: '12px 16px' } }}
        onClick={() => setExpanded(!expanded)}
      >
        {/* Main Row - Always Visible */}
        <Row align="middle" justify="space-between" gutter={[8, 8]}>
          {/* User Name & Status */}
          <Col flex="auto">
            <Space size={8}>
              <UserOutlined style={{ color: '#1890ff', fontSize: 18 }} />
              <Text strong style={{ fontSize: 15 }}>{user.userName}</Text>
              <Tag 
                color={statusColor} 
                style={{ marginRight: 0 }}
              >
                {statusLabel}
              </Tag>
            </Space>
          </Col>

          {/* Quick Info & Actions */}
          <Col>
            <Space size={8} align="center">
              {/* Remaining Time */}
              <Tag 
                icon={<ClockCircleOutlined />} 
                color={user.remainingTime > 1800 ? 'default' : 'error'}
                style={{ marginRight: 0 }}
              >
                {formatDuration(user.remainingTime)}
              </Tag>
              
              {/* Logout Button */}
              <Button
                type="link"
                danger
                size="small"
                icon={<LogoutOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  handleForceLogout(user.userId, user.computerId);
                }}
                style={{ padding: 0, height: 'auto' }}
              >
                נתק
              </Button>
              
              {/* Expand Icon */}
              {expanded ? (
                <UpOutlined style={{ color: '#bfbfbf', fontSize: 12 }} />
              ) : (
                <DownOutlined style={{ color: '#bfbfbf', fontSize: 12 }} />
              )}
            </Space>
          </Col>
        </Row>

        {/* Expanded Details */}
        {expanded && (
          <div style={{ 
            marginTop: 12, 
            paddingTop: 12, 
            borderTop: '1px solid #f0f0f0' 
          }}>
            <Row gutter={[16, 8]}>
              <Col xs={12} sm={8}>
                <Space size={4}>
                  <DesktopOutlined style={{ color: '#8c8c8c' }} />
                  <Text type="secondary">מחשב:</Text>
                  <Text strong>{user.computerName}</Text>
                </Space>
              </Col>
              <Col xs={12} sm={8}>
                <Space size={4}>
                  <PhoneOutlined style={{ color: '#8c8c8c' }} />
                  <Text type="secondary">טלפון:</Text>
                  <Text>{user.userPhone}</Text>
                </Space>
              </Col>
              <Col xs={12} sm={8}>
                <Space size={4}>
                  <ClockCircleOutlined style={{ color: '#8c8c8c' }} />
                  <Text type="secondary">זמן פעילות:</Text>
                  <Text strong style={{ color: '#52c41a' }}>
                    {user.sessionActive && user.sessionStartTime 
                      ? formatSessionTime(user.sessionStartTime) 
                      : '--'}
                  </Text>
                </Space>
              </Col>
            </Row>
          </div>
        )}
      </Card>
    );
  };

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
          {/* Active Users Cards */}
          <Card
            title='משתמשים פעילים'
            extra={<Badge count={activeUsers.length} showZero color='#52c41a' />}
          >
            {activeUsers.length > 0 ? (
              activeUsers.map(user => (
                <UserCard key={`${user.userId}-${user.computerId}`} user={user} />
              ))
            ) : (
              <div style={{ textAlign: 'center', padding: '40px 0', color: '#bfbfbf' }}>
                <UserOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>אין משתמשים פעילים</div>
              </div>
            )}
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
        <div>
          {activeUsers.length > 0 ? (
            activeUsers.map(user => (
              <UserCard key={`${user.userId}-${user.computerId}`} user={user} />
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#bfbfbf' }}>
              <UserOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <div>אין משתמשים פעילים</div>
            </div>
          )}
        </div>
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
