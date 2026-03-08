import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Typography,
  Statistic,
  Spin,
  Tag,
  Empty,
  App,
} from 'antd';
import {
  BankOutlined,
  UserOutlined,
  TeamOutlined,
  DollarOutlined,
  StopOutlined,
} from '@ant-design/icons';
import { getSupervisorOrgs } from '../services/supervisorOrgService';

const { Title, Text } = Typography;

const SupervisorDashboardPage = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({ organizations: [], blockedUsersCount: 0 });
  const navigate = useNavigate();
  const { message } = App.useApp();

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      const result = await getSupervisorOrgs();
      if (result.success) {
        setData({
          organizations: result.organizations || [],
          blockedUsersCount: result.blockedUsersCount || 0,
        });
      } else {
        message.error(result.error || 'שגיאה בטעינת הנתונים');
      }
      setLoading(false);
    };
    load();
  }, [message]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <Spin size='large' />
      </div>
    );
  }

  const orgs = data.organizations || [];
  const totalOrgs = orgs.length;
  const totalUsers = orgs.reduce((s, o) => s + (o.userCount || 0), 0);
  const activeSessions = orgs.reduce((s, o) => s + (o.activeUsers || 0), 0);
  const totalRevenue = orgs.reduce((s, o) => s + (o.totalRevenue || 0), 0);
  const blockedUsers = data.blockedUsersCount || 0;

  const stats = [
    { title: 'סה״כ ארגונים', value: totalOrgs, icon: <BankOutlined /> },
    { title: 'סה״כ משתמשים', value: totalUsers, icon: <UserOutlined /> },
    { title: 'הפעלות פעילות', value: activeSessions, icon: <TeamOutlined /> },
    { title: 'הכנסות', value: totalRevenue.toFixed(2), suffix: '₪', icon: <DollarOutlined /> },
    { title: 'משתמשים חסומים', value: blockedUsers, icon: <StopOutlined /> },
  ];

  return (
    <div style={{ direction: 'rtl' }}>
      <Title level={3} style={{ marginBottom: 24, color: 'rgba(255,255,255,0.9)' }}>
        סקירה כללית
      </Title>

      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        {stats.map((s, i) => (
          <Col xs={24} sm={12} lg={8} xl={undefined} key={i}>
            <Card
              style={{
                background: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.2)',
              }}
            >
              <Statistic
                title={<Text style={{ color: 'rgba(255,255,255,0.7)' }}>{s.title}</Text>}
                value={s.value}
                suffix={s.suffix}
                prefix={s.icon}
                prefixStyle={{ color: '#6366f1', marginLeft: 8 }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Title level={4} style={{ marginBottom: 16, color: 'rgba(255,255,255,0.9)' }}>
        ארגונים בפיקוח
      </Title>

      {orgs.length === 0 ? (
        <Card>
          <Empty description='אין ארגונים בפיקוח' />
        </Card>
      ) : (
        <Row gutter={[16, 16]}>
          {orgs.map(org => (
            <Col xs={24} sm={12} lg={8} key={org.orgId}>
              <Card
                hoverable
                onClick={() => navigate(`/supervisor/organizations/${org.orgId}`)}
                style={{
                  background: 'rgba(26, 16, 48, 0.6)',
                  border: '1px solid rgba(99, 102, 241, 0.2)',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <Text strong style={{ fontSize: 16, color: 'rgba(255,255,255,0.9)' }}>
                    {org.name || org.orgId}
                  </Text>
                  <Tag color={org.status === 'active' ? 'green' : 'default'}>
                    {org.status === 'active' ? 'פעיל' : org.status || 'לא ידוע'}
                  </Tag>
                </div>
                <Row gutter={8}>
                  <Col span={8}>
                    <Text type='secondary' style={{ fontSize: 12 }}>משתמשים: </Text>
                    <Text style={{ color: 'rgba(255,255,255,0.85)' }}>{org.userCount || 0}</Text>
                  </Col>
                  <Col span={8}>
                    <Text type='secondary' style={{ fontSize: 12 }}>פעילים: </Text>
                    <Text style={{ color: 'rgba(255,255,255,0.85)' }}>{org.activeUsers || 0}</Text>
                  </Col>
                  <Col span={8}>
                    <Text type='secondary' style={{ fontSize: 12 }}>הכנסות: </Text>
                    <Text style={{ color: 'rgba(255,255,255,0.85)' }}>
                      {(org.totalRevenue || 0).toFixed(2)} ₪
                    </Text>
                  </Col>
                </Row>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
};

export default SupervisorDashboardPage;
