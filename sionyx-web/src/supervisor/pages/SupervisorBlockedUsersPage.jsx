import { useEffect, useState } from 'react';
import { Table, Button, Spin, App } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';
import { getBlockedUsers, unblockUser } from '../services/supervisorBlockService';
import dayjs from 'dayjs';

const SupervisorBlockedUsersPage = () => {
  const [loading, setLoading] = useState(true);
  const [blockedUsers, setBlockedUsers] = useState([]);
  const [unblockingPhone, setUnblockingPhone] = useState(null);
  const { message } = App.useApp();

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

  const columns = [
    {
      title: 'שם',
      key: 'name',
      render: (_, r) => r.userName || r.name || '-',
    },
    {
      title: 'טלפון',
      dataIndex: 'phone',
      key: 'phone',
    },
    {
      title: 'סיבה',
      dataIndex: 'reason',
      key: 'reason',
      render: v => v || '-',
    },
    {
      title: 'תאריך חסימה',
      dataIndex: 'blockedAt',
      key: 'blockedAt',
      render: v => (v ? dayjs(v).format('DD/MM/YYYY HH:mm') : '-'),
    },
    {
      title: 'פעולות',
      key: 'actions',
      render: (_, r) => (
        <Button
          type='primary'
          size='small'
          icon={<CheckCircleOutlined />}
          loading={unblockingPhone === r.phone}
          onClick={() => handleUnblock(r.phone)}
        >
          שחרר חסימה
        </Button>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <Spin size='large' />
      </div>
    );
  }

  return (
    <div style={{ direction: 'rtl' }}>
      <Table
        dataSource={blockedUsers}
        columns={columns}
        rowKey='phone'
        pagination={{ pageSize: 10 }}
        locale={{ emptyText: 'אין משתמשים חסומים' }}
      />
    </div>
  );
};

export default SupervisorBlockedUsersPage;
