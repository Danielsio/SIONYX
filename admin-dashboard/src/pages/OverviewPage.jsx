import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Typography, Space, Spin, Empty } from 'antd';
import {
  UserOutlined,
  AppstoreOutlined,
  ShoppingCartOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';
import { getOrganizationStats } from '../services/organizationService';
import { formatMinutesHebrew } from '../utils/timeFormatter';

const { Title, Text } = Typography;

const OverviewPage = () => {
  const [loading, setLoading] = useState(true);
  const user = useAuthStore((state) => state.user);
  const { stats, setStats } = useDataStore();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    
    // Get orgId from authenticated user
    const orgId = user?.orgId || localStorage.getItem('adminOrgId');

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

    setLoading(false);
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    );
  }

  const formatTime = (minutes) => {
    return formatMinutesHebrew(minutes);
  };

  return (
    <div style={{ direction: 'rtl' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header */}
        <div>
          <Title level={2} style={{ marginBottom: 8 }}>
            סקירה כללית של לוח הבקרה
          </Title>
          <Text type="secondary">
            ברוך השב! הנה מה שקורה עם <Text code>{user?.orgId || 'הארגון שלך'}</Text>.
          </Text>
        </div>

        {/* Statistics Cards */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card variant="borderless">
              <Statistic
                title="סך משתמשים"
                value={stats?.usersCount || 0}
                prefix={<UserOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card variant="borderless">
              <Statistic
                title="חבילות"
                value={stats?.packagesCount || 0}
                prefix={<AppstoreOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card variant="borderless">
              <Statistic
                title="סך רכישות"
                value={stats?.purchasesCount || 0}
                prefix={<ShoppingCartOutlined />}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card variant="borderless">
              <Statistic
                title="הכנסות"
                value={stats?.totalRevenue || 0}
                prefix="₪"
                precision={2}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Additional Info */}
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card 
              title="סטטיסטיקות זמן" 
              variant="borderless"
              extra={<ClockCircleOutlined />}
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Text type="secondary">סך זמן שנרכש</Text>
                  <br />
                  <Text strong style={{ fontSize: 24 }}>
                    {formatTime(stats?.totalTimeMinutes || 0)}
                  </Text>
                </div>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  זה מייצג את הזמן המצטבר שנרכש על ידי כל המשתמשים בארגון שלך.
                </Text>
              </Space>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card 
              title="מידע על הארגון" 
              variant="borderless"
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Text type="secondary">מזהה ארגון</Text>
                  <br />
                  <Text strong>{user?.orgId || 'לא זמין'}</Text>
                </div>
                <div>
                  <Text type="secondary">שם הארגון</Text>
                  <br />
                  <Text strong code>{user?.orgId || 'לא זמין'}</Text>
                </div>
                <div>
                  <Text type="secondary">אימייל מנהל</Text>
                  <br />
                  <Text strong>{user?.email || 'לא זמין'}</Text>
                </div>
              </Space>
            </Card>
          </Col>
        </Row>

        {/* Quick Actions or Recent Activity */}
        <Card title="סטטיסטיקות מהירות" variant="borderless">
          {stats && stats.usersCount > 0 ? (
            <Row gutter={16}>
              <Col span={8}>
                <div style={{ textAlign: 'center', padding: '20px 0' }}>
                  <Text type="secondary">זמן ממוצע למשתמש</Text>
                  <br />
                  <Title level={4}>
                    {formatTime(Math.round((stats.totalTimeMinutes || 0) / stats.usersCount))}
                  </Title>
                </div>
              </Col>
              <Col span={8}>
                <div style={{ textAlign: 'center', padding: '20px 0' }}>
                  <Text type="secondary">הכנסה ממוצעת לרכישה</Text>
                  <br />
                  <Title level={4}>
                    ₪{stats.purchasesCount > 0 
                      ? ((stats.totalRevenue || 0) / stats.purchasesCount).toFixed(2)
                      : '0.00'
                    }
                  </Title>
                </div>
              </Col>
              <Col span={8}>
                <div style={{ textAlign: 'center', padding: '20px 0' }}>
                  <Text type="secondary">רכישות למשתמש</Text>
                  <br />
                  <Title level={4}>
                    {((stats.purchasesCount || 0) / stats.usersCount).toFixed(1)}
                  </Title>
                </div>
              </Col>
            </Row>
          ) : (
            <Empty 
              description="אין נתונים זמינים עדיין"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </Card>
      </Space>
    </div>
  );
};

export default OverviewPage;

