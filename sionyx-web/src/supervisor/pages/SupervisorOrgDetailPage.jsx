import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Card,
  Tabs,
  Table,
  Tag,
  Button,
  Spin,
  Typography,
  App,
  Modal,
  Form,
  Input,
} from 'antd';
import { StopOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { getOrgUsers, getOrgPackages, getOrgComputers } from '../services/supervisorOrgService';
import { getBlockedUsers, blockUser, unblockUser } from '../services/supervisorBlockService';
import SupervisorOperatingHoursSettings from '../components/SupervisorOperatingHoursSettings';
import { getUserStatus, getStatusLabel, getStatusColor } from '../../constants/userStatus';
import { formatTimeHebrewCompact } from '../../utils/timeFormatter';

const { Title } = Typography;

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

  const userColumns = [
    {
      title: 'שם',
      key: 'name',
      render: (_, r) =>
        `${(r.firstName || '').trim()} ${(r.lastName || '').trim()}`.trim() || r.phone || '-',
    },
    { title: 'טלפון', dataIndex: 'phone', key: 'phone', render: v => v || '-', responsive: ['sm'] },
    {
      title: 'סטטוס',
      key: 'status',
      render: (_, r) => {
        const isBlocked = blockedPhones.has(r.phone || r.phoneNumber);
        if (isBlocked) return <Tag color='error'>חסום</Tag>;
        const status = getUserStatus(r);
        return <Tag color={getStatusColor(status)}>{getStatusLabel(status)}</Tag>;
      },
    },
    {
      title: 'זמן נותר',
      key: 'remainingTime',
      render: (_, r) => formatTimeHebrewCompact(r.remainingTime || 0),
      responsive: ['md'],
    },
    {
      title: 'תקציב הדפסות',
      dataIndex: 'printBalance',
      key: 'printBalance',
      render: v => (v != null ? `₪${Number(v).toFixed(2)}` : '-'),
      responsive: ['md'],
    },
    {
      title: 'פעולות',
      key: 'actions',
      render: (_, r) => {
        const isBlocked = blockedPhones.has(r.phone || r.phoneNumber);
        return isBlocked ? (
          <Button
            type='link'
            size='small'
            icon={<CheckCircleOutlined />}
            onClick={() => handleUnblock(r)}
          >
            שחרר
          </Button>
        ) : (
          <Button
            type='link'
            size='small'
            danger
            icon={<StopOutlined />}
            onClick={() => handleBlock(r)}
          >
            חסום
          </Button>
        );
      },
    },
  ];

  const packageColumns = [
    { title: 'שם', dataIndex: 'name', key: 'name' },
    { title: 'מחיר (₪)', dataIndex: 'price', key: 'price', render: v => (v != null ? Number(v).toFixed(2) : '-') },
    { title: 'דקות', dataIndex: 'minutes', key: 'minutes', render: v => v ?? '-', responsive: ['sm'] },
    { title: 'הדפסות', dataIndex: 'prints', key: 'prints', render: v => v ?? '-', responsive: ['sm'] },
  ];

  const computerColumns = [
    { title: 'שם', key: 'name', render: (_, r) => r.name || r.computerName || r.id || '-' },
    {
      title: 'סטטוס',
      key: 'active',
      render: (_, r) => (
        <Tag color={r.isActive ? 'green' : 'default'}>
          {r.isActive ? 'פעיל' : 'לא פעיל'}
        </Tag>
      ),
    },
    {
      title: 'משתמש נוכחי',
      key: 'currentUser',
      render: (_, r) => r.currentUserId || r.currentUserName || '-',
      responsive: ['sm'],
    },
  ];

  if (loading && !users.length) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <Spin size='large' />
      </div>
    );
  }

  const tabItems = [
    {
      key: 'users',
      label: 'משתמשים',
      children: (
        <Table
          dataSource={users}
          columns={userColumns}
          rowKey='uid'
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: 'אין משתמשים' }}
          scroll={{ x: 500 }}
        />
      ),
    },
    {
      key: 'packages',
      label: 'חבילות',
      children: (
        <Table
          dataSource={packages}
          columns={packageColumns}
          rowKey='id'
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: 'אין חבילות' }}
          scroll={{ x: 400 }}
        />
      ),
    },
    {
      key: 'computers',
      label: 'מחשבים',
      children: (
        <Table
          dataSource={computers}
          columns={computerColumns}
          rowKey='id'
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: 'אין מחשבים' }}
          scroll={{ x: 400 }}
        />
      ),
    },
    {
      key: 'settings',
      label: 'שעות פעילות',
      children: orgId ? <SupervisorOperatingHoursSettings orgId={orgId} /> : null,
    },
  ];

  return (
    <div style={{ direction: 'rtl' }}>
      <Title level={4} style={{ marginBottom: 24 }}>
        ארגון: {orgId}
      </Title>

      <Card>
        <Tabs items={tabItems} />
      </Card>

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
