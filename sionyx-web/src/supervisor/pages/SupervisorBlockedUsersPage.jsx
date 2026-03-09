import { useEffect, useState } from 'react';
import { Card, Row, Col, Button, Spin, App, Typography, Empty, Tag, theme } from 'antd';
import { CheckCircleOutlined, StopOutlined, PhoneOutlined } from '@ant-design/icons';
import { getBlockedUsers, unblockUser } from '../services/supervisorBlockService';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const SupervisorBlockedUsersPage = () => {
  const [loading, setLoading] = useState(true);
  const [blockedUsers, setBlockedUsers] = useState([]);
  const [unblockingPhone, setUnblockingPhone] = useState(null);
  const { message } = App.useApp();
  const { token } = theme.useToken();

  const loadData = async () => {
    setLoading(true);
    const result = await getBlockedUsers();
    if (result.success) {
      setBlockedUsers(result.blockedUsers || []);
    } else {
      message.error(result.error || 'שגיאה בטעינת המשתמשים החסומים');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUnblock = async phone => {
    setUnblockingPhone(phone);
    const result = await unblockUser(phone);
    if (result?.success !== false) {
      message.success('המשתמש שוחרר מחסימה');
      loadData();
    } else {
      message.error(result?.error || 'שגיאה בשחרור חסימה');
    }
    setUnblockingPhone(null);
  };

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
        <StopOutlined style={{ marginLeft: 8 }} />
        משתמשים חסומים
      </Title>

      {blockedUsers.length === 0 ? (
        <Card size='small'>
          <Empty description='אין משתמשים חסומים' />
        </Card>
      ) : (
        <Row gutter={[12, 12]}>
          {blockedUsers.map(user => (
            <Col xs={24} sm={12} key={user.phone}>
              <Card size='small' styles={{ body: { padding: 16 } }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Text strong>{user.userName || user.name || user.phone}</Text>
                  <Tag color='error'>חסום</Tag>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <PhoneOutlined style={{ fontSize: 12, color: token.colorTextTertiary }} />
                    <Text type='secondary' style={{ fontSize: 13 }}>{user.phone}</Text>
                  </div>
                  {user.reason && (
                    <Text type='secondary' style={{ fontSize: 12 }}>
                      סיבה: {user.reason}
                    </Text>
                  )}
                  {user.blockedAt && (
                    <Text type='secondary' style={{ fontSize: 12 }}>
                      {dayjs(user.blockedAt).format('DD/MM/YYYY HH:mm')}
                    </Text>
                  )}
                </div>

                <Button
                  type='primary'
                  size='small'
                  block
                  icon={<CheckCircleOutlined />}
                  loading={unblockingPhone === user.phone}
                  onClick={() => handleUnblock(user.phone)}
                >
                  שחרר חסימה
                </Button>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
};

export default SupervisorBlockedUsersPage;
