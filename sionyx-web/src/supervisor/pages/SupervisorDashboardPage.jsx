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
  Badge,
  theme,
} from 'antd';
import {
  BankOutlined,
  UserOutlined,
  TeamOutlined,
  StopOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { getSupervisorOrgs } from '../services/supervisorOrgService';

const { Title, Text } = Typography;

const SupervisorDashboardPage = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({ organizations: [], blockedUsersCount: 0 });
  const navigate = useNavigate();
  const { message } = App.useApp();
  const { token } = theme.useToken();

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
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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
  const blockedUsers = data.blockedUsersCount || 0;

  const stats = [
    { title: 'ארגונים', value: totalOrgs, icon: <BankOutlined />, color: token.colorPrimary },
    { title: 'משתמשים', value: totalUsers, icon: <UserOutlined />, color: token.colorSuccess },
    { title: 'פעילים', value: activeSessions, icon: <TeamOutlined />, color: token.colorInfo },
    { title: 'חסומים', value: blockedUsers, icon: <StopOutlined />, color: token.colorError },
  ];

  return (
    <div style={{ direction: 'rtl', maxWidth: 960, margin: '0 auto' }}>
      <Title level={3} style={{ marginBottom: 24 }}>סקירה כללית</Title>

      <Row gutter={[12, 12]} style={{ marginBottom: 32 }}>
        {stats.map((s, i) => (
          <Col xs={12} sm={6} key={i}>
            <Card
              size='small'
              style={{ borderTop: `3px solid ${s.color}` }}
              styles={{ body: { padding: '16px 12px' } }}
            >
              <Statistic
                title={<Text type='secondary' style={{ fontSize: 12 }}>{s.title}</Text>}
                value={s.value}
                prefix={s.icon}
                valueStyle={{ fontSize: 24 }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Title level={4} style={{ marginBottom: 16 }}>ארגונים בפיקוח</Title>

      {orgs.length === 0 ? (
        <Card size='small'>
          <Empty description='אין ארגונים בפיקוח' />
        </Card>
      ) : (
        <Row gutter={[12, 12]}>
          {orgs.map(org => (
            <Col xs={24} sm={12} key={org.orgId}>
              <Card
                hoverable
                size='small'
                onClick={() => navigate(`/supervisor/organizations/${org.orgId}`)}
                style={{ cursor: 'pointer' }}
                styles={{ body: { padding: 16 } }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <BankOutlined style={{ fontSize: 18, color: token.colorPrimary }} />
                    <Text strong>{org.name || org.orgId}</Text>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Tag color={org.status === 'active' ? 'green' : 'default'}>
                      {org.status === 'active' ? 'פעיל' : org.status || 'לא ידוע'}
                    </Tag>
                    <RightOutlined style={{ fontSize: 12, color: token.colorTextTertiary }} />
                  </div>
                </div>
                <div style={{ marginTop: 12, display: 'flex', gap: 16 }}>
                  <Badge
                    color={token.colorSuccess}
                    text={<Text type='secondary' style={{ fontSize: 12 }}>{org.userCount || 0} משתמשים</Text>}
                  />
                  <Badge
                    color={token.colorInfo}
                    text={<Text type='secondary' style={{ fontSize: 12 }}>{org.activeUsers || 0} פעילים</Text>}
                  />
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
};

export default SupervisorDashboardPage;
