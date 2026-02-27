import { useEffect, useState, useMemo, useRef, useCallback } from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Space,
  Skeleton,
  Empty,
  App,
  Tag,
  Avatar,
  Alert,
  Button,
  Drawer,
  Switch,
  Segmented,
} from 'antd';
import { motion } from 'framer-motion';
import dayjs from 'dayjs';
import 'dayjs/locale/he';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

dayjs.locale('he');
import {
  UserOutlined,
  AppstoreOutlined,
  ShoppingCartOutlined,
  ClockCircleOutlined,
  DollarOutlined,
  DesktopOutlined,
  PrinterOutlined,
  ReloadOutlined,
  SettingOutlined,
  PercentageOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';
import { useOrgId } from '../hooks/useOrgId';
import { getOrganizationStats } from '../services/organizationService';
import { getPrintPricing } from '../services/pricingService';
import { getComputerUsageStats } from '../services/computerService';
import { formatMinutesHebrew } from '../utils/timeFormatter';
import { getAllUsers } from '../services/userService';
import { getUserStatus, getStatusLabel, getStatusColor } from '../constants/userStatus';
import StatCard, { MiniStatCard } from '../components/StatCard';
import { logger } from '../utils/logger';

const { Title, Text } = Typography;

const DASHBOARD_WIDGETS_KEY = 'dashboard-widgets';

const WIDGET_DEFINITIONS = {
  mainStats: { label: 'כרטיסי סטטיסטיקה ראשיים', default: true },
  revenueChart: { label: 'מגמת הכנסות', default: true },
  packageChart: { label: 'הכנסות לפי חבילה', default: true },
  timeStats: { label: 'סטטיסטיקות זמן', default: true },
  pricing: { label: 'מחירי הדפסה', default: true },
  orgInfo: { label: 'פרטי ארגון', default: true },
  activeUsers: { label: 'משתמשים פעילים', default: true },
  quickStats: { label: 'סטטיסטיקות מהירות', default: true },
  computerUtilization: { label: 'ניצול מחשבים', default: true },
  revenuePerUser: { label: 'הכנסה למשתמש', default: true },
  activeUsersCount: { label: 'מספר משתמשים פעילים', default: true },
  newUsers: { label: 'משתמשים חדשים', default: true },
  completedVsPending: { label: 'יחס רכישות הושלמו/ממתינות', default: true },
};

const loadWidgetVisibility = () => {
  try {
    const stored = localStorage.getItem(DASHBOARD_WIDGETS_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return { ...Object.fromEntries(Object.keys(WIDGET_DEFINITIONS).map(k => [k, WIDGET_DEFINITIONS[k].default])), ...parsed };
    }
  } catch (_) {}
  return Object.fromEntries(Object.keys(WIDGET_DEFINITIONS).map(k => [k, WIDGET_DEFINITIONS[k].default]));
};

const saveWidgetVisibility = visibility => {
  try {
    localStorage.setItem(DASHBOARD_WIDGETS_KEY, JSON.stringify(visibility));
  } catch (_) {}
};

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
  const [error, setError] = useState(null);
  const [pricing, setPricing] = useState({
    blackAndWhitePrice: 1.0,
    colorPrice: 3.0,
  });
  const [recentUsers, setRecentUsers] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [computerStats, setComputerStats] = useState(null);
  const [revenueRangeDays, setRevenueRangeDays] = useState(7);
  const [widgetVisibility, setWidgetVisibility] = useState(loadWidgetVisibility);
  const [settingsDrawerOpen, setSettingsDrawerOpen] = useState(false);
  const isMounted = useRef(true);
  const user = useAuthStore(state => state.user);
  const { stats, setStats } = useDataStore();
  const orgId = useOrgId();

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    if (!orgId) {
      logger.error('Organization ID not found');
      setError('מזהה ארגון לא נמצא. אנא התחבר שוב.');
      setLoading(false);
      return;
    }

    logger.info('Loading data for organization:', orgId);

    const errors = [];

    const [statsResult, pricingResult, usersResult, computerResult] = await Promise.all([
      getOrganizationStats(orgId),
      getPrintPricing(orgId),
      getAllUsers(orgId),
      getComputerUsageStats(),
    ]);

    if (!isMounted.current) return;

    if (statsResult.success) {
      setStats(statsResult.stats);
    } else {
      logger.error('Failed to load stats:', statsResult.error);
      errors.push('סטטיסטיקות');
    }

    if (pricingResult.success) {
      setPricing(pricingResult.pricing);
    } else {
      logger.error('Failed to load pricing:', pricingResult.error);
      errors.push('מחירי הדפסה');
    }

    if (usersResult.success) {
      const usersList = usersResult.users;
      setAllUsers(usersList);
      const activeUsers = usersList
        .filter(u => u.isSessionActive || u.currentComputerId)
        .sort((a, b) => {
          const dateA = new Date(a.lastActivity || a.updatedAt || 0);
          const dateB = new Date(b.lastActivity || b.updatedAt || 0);
          return dateB - dateA;
        })
        .slice(0, 5);
      setRecentUsers(activeUsers);
    } else {
      errors.push('משתמשים פעילים');
    }

    if (computerResult.success && computerResult.data) {
      setComputerStats(computerResult.data);
    }

    if (errors.length > 0) {
      setError(`שגיאה בטעינת: ${errors.join(', ')}`);
    }

    setLoading(false);
  }, [orgId, setStats]);

  useEffect(() => {
    isMounted.current = true;
    loadData();
    return () => {
      isMounted.current = false;
    };
  }, [loadData]);

  const handleWidgetToggle = (key, checked) => {
    const next = { ...widgetVisibility, [key]: checked };
    setWidgetVisibility(next);
    saveWidgetVisibility(next);
  };

  // Real revenue data: group completed purchases by date
  const revenueChartData = useMemo(() => {
    const purchases = stats?.purchases || [];
    const days = revenueRangeDays;
    const completed = purchases.filter(p => p.status === 'completed' && p.amount);
    const byDate = {};
    for (let i = 0; i < days; i++) {
      const d = dayjs().subtract(days - 1 - i, 'day').format('YYYY-MM-DD');
      byDate[d] = { dateKey: d, date: dayjs(d).format('dd DD/MM'), dateFull: dayjs(d).format('dddd DD MMMM'), revenue: 0 };
    }
    completed.forEach(p => {
      const d = dayjs(p.createdAt).format('YYYY-MM-DD');
      if (byDate[d] !== undefined) {
        byDate[d].revenue += parseFloat(p.amount) || 0;
      }
    });
    return Object.values(byDate).sort((a, b) => a.dateKey.localeCompare(b.dateKey));
  }, [stats?.purchases, revenueRangeDays]);

  // Revenue by package (amount, not count)
  const packageChartData = useMemo(() => {
    const purchases = stats?.purchases || [];
    const completed = purchases.filter(p => p.status === 'completed' && p.amount);
    const byPackage = {};
    completed.forEach(p => {
      const name = p.packageName || 'אחר';
      byPackage[name] = (byPackage[name] || 0) + (parseFloat(p.amount) || 0);
    });
    return Object.entries(byPackage)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
  }, [stats?.purchases]);

  // Derived metrics for new cards
  const activeUsersCount = useMemo(() => {
    const users = recentUsers.length ? recentUsers : [];
    if (users.length > 0) return users.length;
    return stats?.usersCount ? 0 : 0;
  }, [recentUsers, stats?.usersCount]);

  const allUsersForMetrics = useMemo(() => {
    const active = recentUsers;
    const total = stats?.usersCount || 0;
    return { active, total };
  }, [recentUsers, stats?.usersCount]);

  const newUsersCounts = useMemo(() => {
    const purchases = stats?.purchases || [];
    const users = recentUsers;
    const now = dayjs();
    const weekAgo = now.subtract(7, 'day');
    const monthAgo = now.subtract(30, 'day');
    let week = 0;
    let month = 0;
    users.forEach(u => {
      const created = u.createdAt ? dayjs(u.createdAt) : null;
      if (created && created.isAfter(weekAgo)) week++;
      if (created && created.isAfter(monthAgo)) month++;
    });
    return { week, month };
  }, [recentUsers]);

  const completedVsPendingCounts = useMemo(() => {
    const purchases = stats?.purchases || [];
    let completed = 0;
    let pending = 0;
    purchases.forEach(p => {
      if (p.status === 'completed') completed++;
      else if (p.status === 'pending') pending++;
    });
    return { completed, pending };
  }, [stats?.purchases]);

  if (loading) {
    return (
      <div style={{ direction: 'rtl' }}>
        <Skeleton active paragraph={{ rows: 1 }} style={{ marginBottom: 24 }} />
        <Row gutter={[20, 20]}>
          {[1, 2, 3, 4].map(i => (
            <Col key={i} xs={24} sm={12} lg={6}>
              <Card style={{ borderRadius: 16 }}>
                <Skeleton active paragraph={{ rows: 2 }} />
              </Card>
            </Col>
          ))}
        </Row>
        <Row gutter={[20, 20]} style={{ marginTop: 20 }}>
          {[1, 2, 3].map(i => (
            <Col key={i} xs={24} lg={8}>
              <Card style={{ borderRadius: 16 }}>
                <Skeleton active paragraph={{ rows: 4 }} />
              </Card>
            </Col>
          ))}
        </Row>
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
        initial='hidden'
        animate='visible'
      >
        <Space direction='vertical' size={28} style={{ width: '100%' }}>
          {/* Error Banner */}
          {error && (
            <Alert
              message='שגיאה בטעינת נתונים'
              description={error}
              type='error'
              showIcon
              closable
              action={
                <Button size='small' icon={<ReloadOutlined />} onClick={loadData}>
                  נסה שוב
                </Button>
              }
              style={{ borderRadius: 12 }}
            />
          )}

          {/* Header */}
          <motion.div variants={itemVariants} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
            <div>
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
            </div>
            <Button
              type='text'
              icon={<SettingOutlined />}
              onClick={() => setSettingsDrawerOpen(true)}
              style={{ fontSize: 18 }}
              aria-label='הגדרות לוח בקרה'
            />
          </motion.div>

          <Drawer
            title='התאמת לוח בקרה'
            placement='left'
            open={settingsDrawerOpen}
            onClose={() => setSettingsDrawerOpen(false)}
            width={320}
            styles={{ body: { padding: '16px 24px' } }}
          >
            <Space direction='vertical' size={16} style={{ width: '100%' }}>
              {Object.entries(WIDGET_DEFINITIONS).map(([key, def]) => (
                <div key={key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text>{def.label}</Text>
                  <Switch
                    checked={widgetVisibility[key] !== false}
                    onChange={checked => handleWidgetToggle(key, checked)}
                  />
                </div>
              ))}
            </Space>
          </Drawer>

          {/* Main Statistics Cards */}
          {widgetVisibility.mainStats !== false && (
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
          )}

          {/* Charts Row */}
          {(widgetVisibility.revenueChart !== false || widgetVisibility.packageChart !== false) && (
          <Row gutter={[20, 20]}>
            {widgetVisibility.revenueChart !== false && (
            <Col xs={24} lg={16}>
              <motion.div variants={itemVariants}>
                <Card
                  title={
                    <Space>
                      <DollarOutlined style={{ color: '#667eea' }} />
                      <span>מגמת הכנסות</span>
                      <Segmented
                        size='small'
                        value={revenueRangeDays}
                        options={[
                          { label: '7 ימים', value: 7 },
                          { label: '30 ימים', value: 30 },
                        ]}
                        onChange={v => setRevenueRangeDays(v)}
                      />
                    </Space>
                  }
                  bordered={false}
                  style={{ height: '100%', borderRadius: 16 }}
                  styles={{ body: { padding: 24 } }}
                >
                  <ResponsiveContainer width='100%' height={280}>
                    <AreaChart data={revenueChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id='colorRevenue' x1='0' y1='0' x2='0' y2='1'>
                          <stop offset='0%' stopColor='#667eea' stopOpacity={1} />
                          <stop offset='100%' stopColor='#667eea' stopOpacity={0.2} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray='3 3' stroke='#e5e7eb' />
                      <XAxis dataKey='date' tick={{ fontSize: 12, fill: '#6b7280' }} />
                      <YAxis tick={{ fontSize: 12, fill: '#6b7280' }} tickFormatter={v => `₪${v}`} />
                      <RechartsTooltip
                        formatter={value => [`₪${Number(value).toFixed(2)}`, 'הכנסה']}
                        labelFormatter={label => revenueChartData.find(d => d.date === label)?.dateFull || label}
                      />
                      <Area
                        type='monotone'
                        dataKey='revenue'
                        stroke='#764ba2'
                        strokeWidth={2}
                        fill='url(#colorRevenue)'
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </Card>
              </motion.div>
            </Col>
            )}
            {widgetVisibility.packageChart !== false && (
            <Col xs={24} lg={8}>
              <motion.div variants={itemVariants}>
                <Card
                  title={
                    <Space>
                      <AppstoreOutlined style={{ color: '#667eea' }} />
                      <span>הכנסות לפי חבילה</span>
                    </Space>
                  }
                  bordered={false}
                  style={{ height: '100%', borderRadius: 16 }}
                  styles={{ body: { padding: 24 } }}
                >
                  {packageChartData.length > 0 ? (
                    <ResponsiveContainer width='100%' height={280}>
                      <PieChart>
                        <Pie
                          data={packageChartData}
                          cx='50%'
                          cy='45%'
                          innerRadius={50}
                          outerRadius={85}
                          paddingAngle={3}
                          dataKey='value'
                        >
                          {packageChartData.map((_, index) => (
                            <Cell key={index} fill={['#667eea', '#764ba2', '#52c41a', '#faad14', '#ff4d4f'][index % 5]} />
                          ))}
                        </Pie>
                        <RechartsTooltip formatter={(value, name) => [`₪${Number(value).toFixed(2)}`, name]} />
                        <Legend
                          verticalAlign='bottom'
                          iconType='circle'
                          iconSize={10}
                          formatter={(value, entry) => {
                            const item = packageChartData.find(d => d.name === value);
                            const total = packageChartData.reduce((s, d) => s + d.value, 0);
                            const pct = total > 0 ? Math.round((item?.value || 0) / total * 100) : 0;
                            return `${value} (₪${(item?.value || 0).toFixed(0)}) ${pct}%`;
                          }}
                          wrapperStyle={{ fontSize: 12, direction: 'rtl' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <Empty description='אין רכישות עדיין' image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ padding: '80px 0' }} />
                  )}
                </Card>
              </motion.div>
            </Col>
            )}
          </Row>
          )}

          {/* Additional Info Cards */}
          {(widgetVisibility.timeStats !== false || widgetVisibility.pricing !== false || widgetVisibility.orgInfo !== false) && (
          <Row gutter={[20, 20]}>
            {widgetVisibility.timeStats !== false && (
            <Col xs={24} lg={8}>
              <motion.div variants={itemVariants}>
                <Card
                  title={
                    <Space>
                      <ClockCircleOutlined style={{ color: '#667eea' }} />
                      <span>סטטיסטיקות זמן</span>
                    </Space>
                  }
                  bordered={false}
                  style={{ height: '100%', borderRadius: 16 }}
                  styles={{ body: { padding: 24 } }}
                >
                  <Space direction='vertical' size='middle' style={{ width: '100%' }}>
                    <MiniStatCard
                      label='סך זמן שנרכש'
                      value={formatTime(stats?.totalTimeMinutes || 0)}
                      icon={<ClockCircleOutlined />}
                      color='primary'
                    />
                    <MiniStatCard
                      label='זמן ממוצע למשתמש'
                      value={stats?.usersCount > 0
                        ? formatTime(Math.round((stats.totalTimeMinutes || 0) / stats.usersCount))
                        : '0 דקות'}
                      icon={<UserOutlined />}
                      color='success'
                    />
                  </Space>
                </Card>
              </motion.div>
            </Col>
            )}

            {widgetVisibility.pricing !== false && (
            <Col xs={24} lg={8}>
              <motion.div variants={itemVariants}>
                <Card
                  title={
                    <Space>
                      <PrinterOutlined style={{ color: '#667eea' }} />
                      <span>מחירי הדפסה</span>
                    </Space>
                  }
                  bordered={false}
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
            )}

            {widgetVisibility.orgInfo !== false && (
            <Col xs={24} lg={8}>
              <motion.div variants={itemVariants}>
                <Card
                  title={
                    <Space>
                      <AppstoreOutlined style={{ color: '#667eea' }} />
                      <span>פרטי ארגון</span>
                    </Space>
                  }
                  bordered={false}
                  style={{ height: '100%', borderRadius: 16 }}
                  styles={{ body: { padding: 24 } }}
                >
                  <Space direction='vertical' size={20} style={{ width: '100%' }}>
                    <div>
                      <Text
                        type='secondary'
                        style={{ fontSize: 13, display: 'block', marginBottom: 4 }}
                      >
                        מזהה ארגון
                      </Text>
                      <Text strong style={{ fontSize: 16 }}>
                        {user?.orgId || 'לא זמין'}
                      </Text>
                    </div>
                    <div>
                      <Text
                        type='secondary'
                        style={{ fontSize: 13, display: 'block', marginBottom: 4 }}
                      >
                        אימייל מנהל
                      </Text>
                      <Text strong style={{ fontSize: 16 }}>
                        {user?.email || 'לא זמין'}
                      </Text>
                    </div>
                  </Space>
                </Card>
              </motion.div>
            </Col>
            )}
          </Row>
          )}

          {/* New metrics row: computer utilization, revenue per user, active users, new users, completed vs pending */}
          {(widgetVisibility.computerUtilization !== false || widgetVisibility.revenuePerUser !== false || widgetVisibility.activeUsersCount !== false || widgetVisibility.newUsers !== false || widgetVisibility.completedVsPending !== false) && (
          <Row gutter={[20, 20]}>
            {widgetVisibility.computerUtilization !== false && (
            <Col xs={24} sm={12} lg={8}>
              <motion.div variants={itemVariants}>
                <Card
                  title={
                    <Space>
                      <DesktopOutlined style={{ color: '#667eea' }} />
                      <span>ניצול מחשבים</span>
                    </Space>
                  }
                  bordered={false}
                  style={{ height: '100%', borderRadius: 16 }}
                  styles={{ body: { padding: 24 } }}
                >
                  {computerStats && computerStats.totalComputers > 0 ? (
                    <MiniStatCard
                      label='מחשבים פעילים מתוך סה"כ'
                      value={`${Math.round((computerStats.activeComputers / computerStats.totalComputers) * 100)}%`}
                      icon={<PercentageOutlined />}
                      color='info'
                    />
                  ) : (
                    <Empty description='אין מחשבים רשומים' image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ padding: 24 }} />
                  )}
                </Card>
              </motion.div>
            </Col>
            )}
            {widgetVisibility.revenuePerUser !== false && (
            <Col xs={24} sm={12} lg={8}>
              <motion.div variants={itemVariants}>
                <Card
                  title={
                    <Space>
                      <DollarOutlined style={{ color: '#667eea' }} />
                      <span>הכנסה למשתמש</span>
                    </Space>
                  }
                  bordered={false}
                  style={{ height: '100%', borderRadius: 16 }}
                  styles={{ body: { padding: 24 } }}
                >
                  <MiniStatCard
                    label='סה"כ הכנסות / משתמשים'
                    value={stats?.usersCount > 0 ? `₪${((stats?.totalRevenue || 0) / stats.usersCount).toFixed(2)}` : '₪0.00'}
                    icon={<DollarOutlined />}
                    color='success'
                  />
                </Card>
              </motion.div>
            </Col>
            )}
            {widgetVisibility.activeUsersCount !== false && (
            <Col xs={24} sm={12} lg={8}>
              <motion.div variants={itemVariants}>
                <Card
                  title={
                    <Space>
                      <TeamOutlined style={{ color: '#667eea' }} />
                      <span>משתמשים פעילים</span>
                    </Space>
                  }
                  bordered={false}
                  style={{ height: '100%', borderRadius: 16 }}
                  styles={{ body: { padding: 24 } }}
                >
                  <MiniStatCard
                    label='משתמשים עם סשן פעיל או מחובר למחשב'
                    value={activeUsersCount}
                    icon={<UserOutlined />}
                    color='success'
                  />
                </Card>
              </motion.div>
            </Col>
            )}
            {widgetVisibility.newUsers !== false && (
            <Col xs={24} sm={12} lg={8}>
              <motion.div variants={itemVariants}>
                <Card
                  title={
                    <Space>
                      <UserOutlined style={{ color: '#667eea' }} />
                      <span>משתמשים חדשים</span>
                    </Space>
                  }
                  bordered={false}
                  style={{ height: '100%', borderRadius: 16 }}
                  styles={{ body: { padding: 24 } }}
                >
                  <Space direction='vertical' size={12} style={{ width: '100%' }}>
                    <MiniStatCard
                      label='השבוע (7 ימים)'
                      value={newUsersCounts.week}
                      icon={<UserOutlined />}
                      color='primary'
                    />
                    <MiniStatCard
                      label='החודש (30 ימים)'
                      value={newUsersCounts.month}
                      icon={<UserOutlined />}
                      color='info'
                    />
                  </Space>
                </Card>
              </motion.div>
            </Col>
            )}
            {widgetVisibility.completedVsPending !== false && (
            <Col xs={24} sm={12} lg={8}>
              <motion.div variants={itemVariants}>
                <Card
                  title={
                    <Space>
                      <ShoppingCartOutlined style={{ color: '#667eea' }} />
                      <span>יחס רכישות</span>
                    </Space>
                  }
                  bordered={false}
                  style={{ height: '100%', borderRadius: 16 }}
                  styles={{ body: { padding: 24 } }}
                >
                  <MiniStatCard
                    label='הושלמו / ממתינות'
                    value={`${completedVsPendingCounts.completed} / ${completedVsPendingCounts.pending}`}
                    icon={<ShoppingCartOutlined />}
                    color='warning'
                  />
                </Card>
              </motion.div>
            </Col>
            )}
          </Row>
          )}

          {/* Recently Active Users */}
          {widgetVisibility.activeUsers !== false && (
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
                      active: {
                        bg: 'linear-gradient(135deg, #10b981, #34d399)',
                        border: '#10b981',
                      },
                      connected: {
                        bg: 'linear-gradient(135deg, #3b82f6, #60a5fa)',
                        border: '#3b82f6',
                      },
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
                                <div
                                  style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 8,
                                    marginTop: 6,
                                  }}
                                >
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
                <Empty description='אין משתמשים פעילים כרגע' image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )}
            </Card>
          </motion.div>
          )}

          {/* Quick Statistics */}
          {widgetVisibility.quickStats !== false && (
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
                      value={formatTime(
                        Math.round((stats.totalTimeMinutes || 0) / stats.usersCount)
                      )}
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
                      value={`${((stats.purchasesCount || 0) / stats.usersCount).toFixed(1)} רכישות`}
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
          )}
        </Space>
      </motion.div>
    </App>
  );
};

export default OverviewPage;
