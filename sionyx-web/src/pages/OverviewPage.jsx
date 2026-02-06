import { useEffect, useState } from 'react';
import { Card, Row, Col, Typography, Space, Spin, Empty, App, Tag, Avatar } from 'antd';
import { motion } from 'framer-motion';
import {
  UserOutlined,
  AppstoreOutlined,
  ShoppingCartOutlined,
  ClockCircleOutlined,
  DollarOutlined,
  DesktopOutlined,
  PrinterOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';
import { useOrgId } from '../hooks/useOrgId';
import { getOrganizationStats } from '../services/organizationService';
import { getPrintPricing } from '../services/pricingService';
import { formatMinutesHebrew } from '../utils/timeFormatter';
import { getAllUsers } from '../services/userService';
import { getUserStatus, getStatusLabel, getStatusColor } from '../constants/userStatus';
import StatCard, { MiniStatCard } from '../components/StatCard';

const { Title, Text } = Typography;

// Animation variants for staggered children
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.25, 0.46, 0.45, 0.94],
    },
  },
};

const OverviewPage = () => {
  const [loading, setLoading] = useState(true);
  const [pricing, setPricing] = useState({
    blackAndWhitePrice: 1.0,
    colorPrice: 3.0,
  });
  const [recentUsers, setRecentUsers] = useState([]);
  const user = useAuthStore(state => state.user);
  const { stats, setStats } = useDataStore();
  const { message } = App.useApp();
  const orgId = useOrgId();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);

    if (!orgId) {
      console.error('Organization ID not found');
      setLoading(false);
      return;
    }

    console.log('Loading data for organization:', orgId);

    // Load statistics
    const statsResult = await getOrganizationStats(orgId);
    if (statsResult.success) {
      setStats(statsResult.stats);
    } else {
      console.error('Failed to load stats:', statsResult.error);
    }

    // Load pricing
    const pricingResult = await getPrintPricing(orgId);
    if (pricingResult.success) {
      setPricing(pricingResult.pricing);
    } else {
      console.error('Failed to load pricing:', pricingResult.error);
    }

    // Load recently active users
    const usersResult = await getAllUsers(orgId);
    if (usersResult.success) {
      // Filter and sort by last activity
      const activeUsers = usersResult.users
        .filter(u => u.isSessionActive || u.currentComputerId)
        .sort((a, b) => {
          const dateA = new Date(a.lastActivity || a.updatedAt || 0);
          const dateB = new Date(b.lastActivity || b.updatedAt || 0);
          return dateB - dateA;
        })
        .slice(0, 5);
      setRecentUsers(activeUsers);
    }

    setLoading(false);
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size='large' />
      </div>
    );
  }

  const formatTime = minutes => {
    return formatMinutesHebrew(minutes);
  };

  return (
    <App>
      <motion.div 
        style={{ direction: 'rtl' }}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <Space direction='vertical' size={28} style={{ width: '100%' }}>
          {/* Header */}
          <motion.div variants={itemVariants}>
            <Title level={2} style={{ marginBottom: 8, fontWeight: 700, color: '#1f2937' }}>
              סקירה כללית
            </Title>
            <Text style={{ color: '#6b7280', fontSize: 15 }}>
              שלום! הנה סיכום הפעילות של{' '}
              <Text 
                style={{ 
                  color: '#667eea', 
                  fontWeight: 600,
                  background: 'rgba(102, 126, 234, 0.1)',
                  padding: '2px 8px',
                  borderRadius: 6,
                }}
              >
                {user?.orgId || 'הארגון שלך'}
              </Text>
            </Text>
          </motion.div>

          {/* Main Statistics Cards */}
          <Row gutter={[20, 20]}>
            <Col xs={24} sm={12} lg={6}>
              <StatCard
                title='סך משתמשים'
                value={stats?.usersCount || 0}
                icon={<UserOutlined />}
                color='success'
                delay={0}
              />
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <StatCard
                title='חבילות פעילות'
                value={stats?.packagesCount || 0}
                icon={<AppstoreOutlined />}
                color='info'
                delay={0.08}
              />
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <StatCard
                title='סך רכישות'
                value={stats?.purchasesCount || 0}
                icon={<ShoppingCartOutlined />}
                color='warning'
                delay={0.16}
              />
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <StatCard
                title='הכנסות'
                value={stats?.totalRevenue || 0}
                prefix='₪'
                precision={2}
                icon={<DollarOutlined />}
                color='primary'
                variant='gradient'
                delay={0.24}
              />
            </Col>
          </Row>

          {/* Additional Info Cards */}
          <Row gutter={[20, 20]}>
            <Col xs={24} lg={8}>
              <motion.div variants={itemVariants}>
                <Card 
                  title={
                    <Space>
                      <ClockCircleOutlined style={{ color: '#667eea' }} />
                      <span>סטטיסטיקות זמן</span>
                    </Space>
                  }
                  variant='borderless'
                  style={{ height: '100%', borderRadius: 16 }}
                  styles={{ body: { padding: 24 } }}
                >
                  <Space direction='vertical' size='large' style={{ width: '100%' }}>
                    <MiniStatCard
                      label='סך זמן שנרכש'
                      value={formatTime(stats?.totalTimeMinutes || 0)}
                      icon={<ClockCircleOutlined />}
                      color='primary'
                    />
                    <Text type='secondary' style={{ fontSize: 13, display: 'block' }}>
                      הזמן המצטבר שנרכש על ידי כל המשתמשים בארגון
                    </Text>
                  </Space>
                </Card>
              </motion.div>
            </Col>

            <Col xs={24} lg={8}>
              <motion.div variants={itemVariants}>
                <Card 
                  title={
                    <Space>
                      <PrinterOutlined style={{ color: '#667eea' }} />
                      <span>מחירי הדפסה</span>
                    </Space>
                  }
                  variant='borderless'
                  style={{ height: '100%', borderRadius: 16 }}
                  styles={{ body: { padding: 24 } }}
                >
                  <Space direction='vertical' size={16} style={{ width: '100%' }}>
                    <MiniStatCard
                      label='שחור-לבן לעמוד'
                      value={`₪${pricing.blackAndWhitePrice.toFixed(2)}`}
                      icon={<PrinterOutlined />}
                      color='info'
                    />
                    <MiniStatCard
                      label='צבעוני לעמוד'
                      value={`₪${pricing.colorPrice.toFixed(2)}`}
                      icon={<PrinterOutlined />}
                      color='success'
                    />
                  </Space>
                </Card>
              </motion.div>
            </Col>

            <Col xs={24} lg={8}>
              <motion.div variants={itemVariants}>
                <Card 
                  title={
                    <Space>
                      <AppstoreOutlined style={{ color: '#667eea' }} />
                      <span>פרטי ארגון</span>
                    </Space>
                  }
                  variant='borderless'
                  style={{ height: '100%', borderRadius: 16 }}
                  styles={{ body: { padding: 24 } }}
                >
                  <Space direction='vertical' size={20} style={{ width: '100%' }}>
                    <div>
                      <Text type='secondary' style={{ fontSize: 13, display: 'block', marginBottom: 4 }}>
                        מזהה ארגון
                      </Text>
                      <Text strong style={{ fontSize: 16 }}>{user?.orgId || 'לא זמין'}</Text>
                    </div>
                    <div>
                      <Text type='secondary' style={{ fontSize: 13, display: 'block', marginBottom: 4 }}>
                        אימייל מנהל
                      </Text>
                      <Text strong style={{ fontSize: 16 }}>{user?.email || 'לא זמין'}</Text>
                    </div>
                  </Space>
                </Card>
              </motion.div>
            </Col>
          </Row>

          {/* Recently Active Users */}
          <motion.div variants={itemVariants}>
            <Card 
              title={
                <Space>
                  <UserOutlined style={{ color: '#10b981' }} />
                  <span>משתמשים פעילים</span>
                  {recentUsers.length > 0 && (
                    <Tag color='green' style={{ marginRight: 8 }}>
                      {recentUsers.length}
                    </Tag>
                  )}
                </Space>
              }
              variant='borderless'
              style={{ borderRadius: 16 }}
            >
              {recentUsers.length > 0 ? (
                <Row gutter={[16, 16]}>
                  {recentUsers.map((u, index) => {
                    const status = getUserStatus(u);
                    const statusColors = {
                      active: { bg: 'linear-gradient(135deg, #10b981, #34d399)', border: '#10b981' },
                      connected: { bg: 'linear-gradient(135deg, #3b82f6, #60a5fa)', border: '#3b82f6' },
                      offline: { bg: '#9ca3af', border: '#d1d5db' },
                    };
                    const colors = statusColors[status] || statusColors.offline;
                    
                    return (
                      <Col key={u.uid} xs={24} sm={12} lg={8} xl={6}>
                        <motion.div
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05 }}
                        >
                          <Card 
                            size='small' 
                            style={{ 
                              borderRadius: 14,
                              borderRight: `4px solid ${colors.border}`,
                              background: '#fff',
                              transition: 'all 0.2s',
                            }}
                            hoverable
                            styles={{ body: { padding: '14px 16px' } }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                              <Avatar
                                size={44}
                                style={{
                                  flexShrink: 0,
                                  background: colors.bg,
                                  boxShadow: `0 4px 12px ${colors.border}40`,
                                }}
                                icon={<UserOutlined />}
                              />
                              <div style={{ flex: 1, minWidth: 0 }}>
                                <Text 
                                  strong 
                                  style={{ 
                                    display: 'block', 
                                    fontSize: 14,
                                    whiteSpace: 'nowrap',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    color: '#1f2937',
                                  }}
                                >
                                  {`${u.firstName || ''} ${u.lastName || ''}`.trim() || 'לא זמין'}
                                </Text>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
                                  <Tag 
                                    color={getStatusColor(status)} 
                                    style={{ 
                                      margin: 0, 
                                      fontSize: 11,
                                      borderRadius: 6,
                                    }}
                                  >
                                    {getStatusLabel(status)}
                                  </Tag>
                                  {u.currentComputerName && (
                                    <Text type='secondary' style={{ fontSize: 11 }}>
                                      <DesktopOutlined style={{ marginLeft: 4 }} />
                                      {u.currentComputerName}
                                    </Text>
                                  )}
                                </div>
                              </div>
                            </div>
                          </Card>
                        </motion.div>
                      </Col>
                    );
                  })}
                </Row>
              ) : (
                <Empty
                  description='אין משתמשים פעילים כרגע'
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              )}
            </Card>
          </motion.div>

          {/* Quick Statistics */}
          <motion.div variants={itemVariants}>
            <Card 
              title={
                <Space>
                  <DollarOutlined style={{ color: '#667eea' }} />
                  <span>סטטיסטיקות מהירות</span>
                </Space>
              }
              variant='borderless'
              style={{ borderRadius: 16 }}
            >
              {stats && stats.usersCount > 0 ? (
                <Row gutter={[20, 20]}>
                  <Col xs={24} sm={8}>
                    <MiniStatCard
                      label='זמן ממוצע למשתמש'
                      value={formatTime(Math.round((stats.totalTimeMinutes || 0) / stats.usersCount))}
                      icon={<ClockCircleOutlined />}
                      color='primary'
                    />
                  </Col>
                  <Col xs={24} sm={8}>
                    <MiniStatCard
                      label='הכנסה ממוצעת לרכישה'
                      value={`₪${stats.purchasesCount > 0 ? ((stats.totalRevenue || 0) / stats.purchasesCount).toFixed(2) : '0.00'}`}
                      icon={<DollarOutlined />}
                      color='success'
                    />
                  </Col>
                  <Col xs={24} sm={8}>
                    <MiniStatCard
                      label='רכישות למשתמש'
                      value={((stats.purchasesCount || 0) / stats.usersCount).toFixed(1)}
                      icon={<ShoppingCartOutlined />}
                      color='warning'
                    />
                  </Col>
                </Row>
              ) : (
                <Empty description='אין נתונים זמינים עדיין' image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )}
            </Card>
          </motion.div>
        </Space>
      </motion.div>
    </App>
  );
};

export default OverviewPage;
