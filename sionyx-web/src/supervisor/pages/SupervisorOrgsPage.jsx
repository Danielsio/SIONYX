import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Row, Col, Spin, Tag, Typography, App, Badge, Empty, theme } from 'antd';
import { BankOutlined, UserOutlined, TeamOutlined, RightOutlined } from '@ant-design/icons';
import { getSupervisorOrgs } from '../services/supervisorOrgService';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const SupervisorOrgsPage = () => {
  const [loading, setLoading] = useState(true);
  const [organizations, setOrganizations] = useState([]);
  const navigate = useNavigate();
  const { message } = App.useApp();
  const { token } = theme.useToken();

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      const result = await getSupervisorOrgs();
      if (result.success) {
        setOrganizations(result.organizations || []);
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

  return (
    <div style={{ direction: 'rtl', maxWidth: 960, margin: '0 auto' }}>
      <Title level={3} style={{ marginBottom: 24 }}>
        <BankOutlined style={{ marginLeft: 8 }} />
        ארגונים
      </Title>

      {organizations.length === 0 ? (
        <Card size='small'>
          <Empty description='אין ארגונים בפיקוח' />
        </Card>
      ) : (
        <Row gutter={[12, 12]}>
          {organizations.map(org => (
            <Col xs={24} sm={12} key={org.orgId}>
              <Card
                hoverable
                size='small'
                onClick={() => navigate(`/supervisor/organizations/${org.orgId}`)}
                style={{ cursor: 'pointer' }}
                styles={{ body: { padding: 16 } }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
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

                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                  <Badge
                    color={token.colorSuccess}
                    text={<Text type='secondary' style={{ fontSize: 12 }}>{org.userCount || 0} משתמשים</Text>}
                  />
                  <Badge
                    color={token.colorInfo}
                    text={<Text type='secondary' style={{ fontSize: 12 }}>{org.activeUsers || 0} פעילים</Text>}
                  />
                  {org.createdAt && (
                    <Text type='secondary' style={{ fontSize: 12 }}>
                      {dayjs(org.createdAt).format('DD/MM/YYYY')}
                    </Text>
                  )}
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
};

export default SupervisorOrgsPage;
