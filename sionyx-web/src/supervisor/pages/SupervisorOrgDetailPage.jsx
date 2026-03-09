import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Card,
  Tabs,
  Tag,
  Button,
  Spin,
  Typography,
  App,
  Modal,
  Form,
  Input,
  Row,
  Col,
  Empty,
  Space,
  theme,
} from 'antd';
import {
  StopOutlined,
  CheckCircleOutlined,
  UserOutlined,
  PhoneOutlined,
  DesktopOutlined,
  ShoppingOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { getOrgUsers, getOrgPackages, getOrgComputers } from '../services/supervisorOrgService';
import { getBlockedUsers, blockUser, unblockUser } from '../services/supervisorBlockService';
import SupervisorOperatingHoursSettings from '../components/SupervisorOperatingHoursSettings';
import { getUserStatus, getStatusLabel, getStatusColor } from '../../constants/userStatus';
import { formatTimeHebrewCompact } from '../../utils/timeFormatter';

const { Title, Text } = Typography;

const SupervisorOrgDetailPage = () => {
  const { orgId } = useParams();
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [packages, setPackages] = useState([]);
  const [computers, setComputers] = useState([]);
  const [blockedPhones, setBlockedPhones] = useState(new Set());
  const [blockModalOpen, setBlockModalOpen] = useState(false);
  const [blockingUser, setBlockingUser] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const { token } = theme.useToken();

  const loadData = async () => {
    if (!orgId) return;
    setLoading(true);
    const [usersRes, packagesRes, computersRes, blockedRes] = await Promise.all([
      getOrgUsers(orgId),
      getOrgPackages(orgId),
      getOrgComputers(orgId),
      getBlockedUsers(),
    ]);
    if (usersRes.success) setUsers(usersRes.users || []);
    if (packagesRes.success) setPackages(packagesRes.packages || []);
    if (computersRes.success) setComputers(computersRes.computers || []);
    if (blockedRes.success) {
      const phones = new Set((blockedRes.blockedUsers || []).map(b => b.phone));
      setBlockedPhones(phones);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [orgId]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleBlock = user => {
    setBlockingUser(user);
    form.setFieldsValue({ reason: '' });
    setBlockModalOpen(true);
  };

  const handleBlockSubmit = async () => {
    if (!blockingUser || submitting) return;
    setSubmitting(true);
    const values = await form.validateFields();
    const result = await blockUser(
      blockingUser.phone || blockingUser.phoneNumber,
      values.reason || 'חסימה על ידי מפקח',
      `${blockingUser.firstName || ''} ${blockingUser.lastName || ''}`.trim() || blockingUser.phone
    );
    if (result?.success !== false) {
      message.success('המשתמש נחסם');
      setBlockModalOpen(false);
      setBlockingUser(null);
      loadData();
    } else {
      message.error(result?.error || 'שגיאה בחסימה');
    }
    setSubmitting(false);
  };

  const handleUnblock = async user => {
    const phone = user.phone || user.phoneNumber;
    const result = await unblockUser(phone);
    if (result?.success !== false) {
      message.success('המשתמש שוחרר מחסימה');
      loadData();
    } else {
      message.error(result?.error || 'שגיאה בשחרור חסימה');
    }
  };

  const getUserName = r =>
    `${(r.firstName || '').trim()} ${(r.lastName || '').trim()}`.trim() || r.phone || '-';

  if (loading && !users.length) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <Spin size='large' />
      </div>
    );
  }

  const renderUsers = () => {
    if (users.length === 0) return <Empty description='אין משתמשים' />;
    return (
      <Row gutter={[12, 12]}>
        {users.map(r => {
          const isBlocked = blockedPhones.has(r.phone || r.phoneNumber);
          const status = getUserStatus(r);
          return (
            <Col xs={24} sm={12} key={r.uid}>
              <Card size='small' styles={{ body: { padding: 12 } }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Space size={6}>
                    <UserOutlined style={{ color: token.colorPrimary }} />
                    <Text strong style={{ fontSize: 13 }}>{getUserName(r)}</Text>
                  </Space>
                  {isBlocked ? (
                    <Tag color='error'>חסום</Tag>
                  ) : (
                    <Tag color={getStatusColor(status)}>{getStatusLabel(status)}</Tag>
                  )}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginBottom: 8 }}>
                  {r.phone && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <PhoneOutlined style={{ fontSize: 11, color: token.colorTextTertiary }} />
                      <Text type='secondary' style={{ fontSize: 12 }}>{r.phone}</Text>
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 12 }}>
                    <Text type='secondary' style={{ fontSize: 12 }}>
                      זמן: {formatTimeHebrewCompact(r.remainingTime || 0)}
                    </Text>
                    {r.printBalance != null && (
                      <Text type='secondary' style={{ fontSize: 12 }}>
                        הדפסות: ₪{Number(r.printBalance).toFixed(2)}
                      </Text>
                    )}
                  </div>
                </div>
                {isBlocked ? (
                  <Button
                    size='small'
                    block
                    icon={<CheckCircleOutlined />}
                    onClick={() => handleUnblock(r)}
                  >
                    שחרר חסימה
                  </Button>
                ) : (
                  <Button
                    size='small'
                    block
                    danger
                    icon={<StopOutlined />}
                    onClick={() => handleBlock(r)}
                  >
                    חסום
                  </Button>
                )}
              </Card>
            </Col>
          );
        })}
      </Row>
    );
  };

  const renderPackages = () => {
    if (packages.length === 0) return <Empty description='אין חבילות' />;
    return (
      <Row gutter={[12, 12]}>
        {packages.map(pkg => (
          <Col xs={24} sm={12} lg={8} key={pkg.id}>
            <Card size='small' styles={{ body: { padding: 12 } }}>
              <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }}>
                <ShoppingOutlined style={{ marginLeft: 6, color: token.colorPrimary }} />
                {pkg.name}
              </Text>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <Text type='secondary' style={{ fontSize: 12 }}>
                  מחיר: ₪{pkg.price != null ? Number(pkg.price).toFixed(2) : '-'}
                </Text>
                {pkg.minutes != null && (
                  <Text type='secondary' style={{ fontSize: 12 }}>
                    דקות: {pkg.minutes}
                  </Text>
                )}
                {pkg.prints != null && (
                  <Text type='secondary' style={{ fontSize: 12 }}>
                    הדפסות: {pkg.prints}
                  </Text>
                )}
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    );
  };

  const renderComputers = () => {
    if (computers.length === 0) return <Empty description='אין מחשבים' />;
    return (
      <Row gutter={[12, 12]}>
        {computers.map(c => (
          <Col xs={24} sm={12} lg={8} key={c.id}>
            <Card size='small' styles={{ body: { padding: 12 } }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Space size={6}>
                  <DesktopOutlined style={{ color: token.colorPrimary }} />
                  <Text strong style={{ fontSize: 13 }}>{c.name || c.computerName || c.id || '-'}</Text>
                </Space>
                <Tag color={c.isActive ? 'green' : 'default'}>
                  {c.isActive ? 'פעיל' : 'לא פעיל'}
                </Tag>
              </div>
              {(c.currentUserId || c.currentUserName) && (
                <Text type='secondary' style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
                  משתמש: {c.currentUserName || c.currentUserId}
                </Text>
              )}
            </Card>
          </Col>
        ))}
      </Row>
    );
  };

  const tabItems = [
    { key: 'users', label: `משתמשים (${users.length})`, children: renderUsers() },
    { key: 'packages', label: `חבילות (${packages.length})`, children: renderPackages() },
    { key: 'computers', label: `מחשבים (${computers.length})`, children: renderComputers() },
    {
      key: 'settings',
      label: 'שעות פעילות',
      children: orgId ? <SupervisorOperatingHoursSettings orgId={orgId} /> : null,
    },
  ];

  return (
    <div style={{ direction: 'rtl', maxWidth: 960, margin: '0 auto' }}>
      <Title level={4} style={{ marginBottom: 24 }}>
        ארגון: {orgId}
      </Title>

      <Tabs items={tabItems} />

      <Modal
        title='חסימת משתמש'
        open={blockModalOpen}
        onOk={handleBlockSubmit}
        confirmLoading={submitting}
        onCancel={() => {
          setBlockModalOpen(false);
          setBlockingUser(null);
        }}
        okText='חסום'
        cancelText='ביטול'
      >
        <Form form={form} layout='vertical'>
          <Form.Item name='reason' label='סיבת חסימה'>
            <Input.TextArea rows={3} placeholder='הזן סיבה (אופציונלי)' />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SupervisorOrgDetailPage;
