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
    { title: 'סה״כ ארגונים', value: totalOrgs, icon: <BankOutlined /> },
    { title: 'סה״כ משתמשים', value: totalUsers, icon: <UserOutlined /> },
    { title: 'הפעלות פעילות', value: activeSessions, icon: <TeamOutlined /> },
    { title: 'משתמשים חסומים', value: blockedUsers, icon: <StopOutlined /> },
  ];

  return (
    <div style={{ direction: 'rtl' }}>
      <Title level={3} style={{ marginBottom: 24 }}>
        סקירה כללית
      </Title>

      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        {stats.map((s, i) => (
          <Col xs={24} sm={12} lg={8} key={i}>
            <Card>
              <Statistic
                title={s.title}
                value={s.value}
                suffix={s.suffix}
                prefix={s.icon}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Title level={4} style={{ marginBottom: 16 }}>
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
                style={{ cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <Text strong style={{ fontSize: 16 }}>
                    {org.name || org.orgId}
                  </Text>
                  <Tag color={org.status === 'active' ? 'green' : 'default'}>
                    {org.status === 'active' ? 'פעיל' : org.status || 'לא ידוע'}
                  </Tag>
                </div>
                <Row gutter={8}>
                  <Col span={12}>
                    <Text type='secondary' style={{ fontSize: 12 }}>משתמשים: </Text>
                    <Text>{org.userCount || 0}</Text>
                  </Col>
                  <Col span={12}>
                    <Text type='secondary' style={{ fontSize: 12 }}>פעילים: </Text>
                    <Text>{org.activeUsers || 0}</Text>
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
