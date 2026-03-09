import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, Spin, Tag, Typography, App } from 'antd';
import { getSupervisorOrgs } from '../services/supervisorOrgService';
import dayjs from 'dayjs';

const { Title } = Typography;

const SupervisorOrgsPage = () => {
  const [loading, setLoading] = useState(true);
  const [organizations, setOrganizations] = useState([]);
  const navigate = useNavigate();
  const { message } = App.useApp();

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

  const columns = [
    {
      title: 'שם',
      dataIndex: 'name',
      key: 'name',
      render: (_, record) => record.name || record.orgId,
    },
    {
      title: 'סטטוס',
      dataIndex: 'status',
      key: 'status',
      render: status => (
        <Tag color={status === 'active' ? 'green' : 'default'}>
          {status === 'active' ? 'פעיל' : status || 'לא ידוע'}
        </Tag>
      ),
    },
    {
      title: 'משתמשים',
      dataIndex: 'userCount',
      key: 'userCount',
      align: 'center',
    },
    {
      title: 'פעילים',
      dataIndex: 'activeUsers',
      key: 'activeUsers',
      align: 'center',
    },
    {
      title: 'הכנסות (₪)',
      dataIndex: 'totalRevenue',
      key: 'totalRevenue',
      align: 'left',
      render: v => (v != null ? Number(v).toFixed(2) : '0.00'),
    },
    {
      title: 'תאריך יצירה',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: v => (v ? dayjs(v).format('DD/MM/YYYY') : '-'),
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
      <Title level={3} style={{ marginBottom: 24 }}>
        ארגונים
      </Title>
      <Table
        dataSource={organizations}
        columns={columns}
        rowKey='orgId'
        onRow={record => ({
          onClick: () => navigate(`/supervisor/organizations/${record.orgId}`),
          style: { cursor: 'pointer' },
        })}
        pagination={{ pageSize: 10 }}
        locale={{ emptyText: 'אין ארגונים בפיקוח' }}
        scroll={{ x: 600 }}
      />
    </div>
  );
};

export default SupervisorOrgsPage;
