import { useEffect, useState, useMemo } from 'react';
import { motion } from 'framer-motion'; // eslint-disable-line no-unused-vars
import { Card, Space, Table, Tag, Input, Button, Dropdown, Empty, Skeleton } from 'antd';
import {
  HistoryOutlined,
  SearchOutlined,
  DownloadOutlined,
  DesktopOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { getSessionLogs } from '../services/sessionLogService';
import { exportToCSV, exportToExcel, exportToPDF } from '../utils/csvExport';
import { formatMinutesHebrew } from '../utils/timeFormatter';
import { logger } from '../utils/logger';

const reasonLabels = {
  user: 'סיום יזום',
  expired: 'נגמר הזמן',
  logout: 'התנתקות',
  hours: 'סגירת שעות פעילות',
  error: 'שגיאה',
};

const SessionLogsReport = ({ orgId, usersById = {} }) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!orgId) return;
    let active = true;
    setLoading(true);
    getSessionLogs(orgId)
      .then(res => {
        if (!active) return;
        if (res.success) setLogs(res.logs);
        else logger.error('Session logs load failed:', res.error);
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [orgId]);

  const enriched = useMemo(
    () =>
      logs.map(l => {
        const u = usersById[l.userId];
        const userName = u
          ? `${u.firstName || ''} ${u.lastName || ''}`.trim() || u.phoneNumber || l.userId
          : l.userId;
        return { ...l, userName };
      }),
    [logs, usersById]
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return enriched;
    return enriched.filter(
      l =>
        l.userName.toLowerCase().includes(q) ||
        (l.computerName || '').toLowerCase().includes(q)
    );
  }, [enriched, search]);

  const columns = [
    {
      title: 'משתמש',
      dataIndex: 'userName',
      key: 'userName',
    },
    {
      title: 'מחשב',
      dataIndex: 'computerName',
      key: 'computerName',
      render: name => (
        <Space size={4}>
          <DesktopOutlined style={{ color: '#667eea' }} />
          {name || '—'}
        </Space>
      ),
    },
    {
      title: 'התחלה',
      dataIndex: 'startTime',
      key: 'startTime',
      render: t => (t ? dayjs(t).format('DD/MM/YYYY HH:mm') : '—'),
      sorter: (a, b) => new Date(a.startTime || 0) - new Date(b.startTime || 0),
    },
    {
      title: 'סיום',
      dataIndex: 'endTime',
      key: 'endTime',
      render: t => (t ? dayjs(t).format('DD/MM/YYYY HH:mm') : '—'),
      defaultSortOrder: 'descend',
      sorter: (a, b) => new Date(a.endTime || 0) - new Date(b.endTime || 0),
    },
    {
      title: 'זמן שנוצל',
      dataIndex: 'usedSeconds',
      key: 'usedSeconds',
      render: s => formatMinutesHebrew(Math.round((s || 0) / 60)),
      sorter: (a, b) => (a.usedSeconds || 0) - (b.usedSeconds || 0),
    },
    {
      title: 'סיבת סיום',
      dataIndex: 'reason',
      key: 'reason',
      render: r => <Tag>{reasonLabels[r] || r || '—'}</Tag>,
    },
  ];

  const exportRows = filtered.map(l => ({
    user: l.userName,
    computer: l.computerName || '',
    start: l.startTime ? dayjs(l.startTime).format('DD/MM/YYYY HH:mm') : '',
    end: l.endTime ? dayjs(l.endTime).format('DD/MM/YYYY HH:mm') : '',
    usedMinutes: Math.round((l.usedSeconds || 0) / 60),
    reason: reasonLabels[l.reason] || l.reason || '',
  }));
  const exportColumns = [
    { title: 'משתמש', dataIndex: 'user' },
    { title: 'מחשב', dataIndex: 'computer' },
    { title: 'התחלה', dataIndex: 'start' },
    { title: 'סיום', dataIndex: 'end' },
    { title: 'דקות שנוצלו', dataIndex: 'usedMinutes' },
    { title: 'סיבת סיום', dataIndex: 'reason' },
  ];
  const exportName = `session-logs-${new Date().toISOString().split('T')[0]}`;

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
      <Card
        title={
          <Space>
            <HistoryOutlined style={{ color: '#667eea' }} />
            <span>יומן הפעלות</span>
            {filtered.length > 0 && <Tag color='blue'>{filtered.length}</Tag>}
          </Space>
        }
        extra={
          <Space>
            <Input
              allowClear
              prefix={<SearchOutlined />}
              placeholder='חפש משתמש או מחשב'
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ width: 200 }}
            />
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'csv',
                    icon: <DownloadOutlined />,
                    label: 'ייצא CSV',
                    onClick: () => exportToCSV(exportRows, exportColumns, exportName),
                  },
                  {
                    key: 'excel',
                    icon: <DownloadOutlined />,
                    label: 'ייצא Excel',
                    onClick: () => exportToExcel(exportRows, exportColumns, exportName),
                  },
                  {
                    key: 'pdf',
                    icon: <DownloadOutlined />,
                    label: 'ייצא PDF',
                    onClick: () => exportToPDF(exportRows, exportColumns, exportName, 'יומן הפעלות'),
                  },
                ],
              }}
              trigger={['click']}
              disabled={filtered.length === 0}
            >
              <Button icon={<DownloadOutlined />}>ייצא</Button>
            </Dropdown>
          </Space>
        }
        bordered={false}
        style={{ borderRadius: 16 }}
      >
        {loading ? (
          <Skeleton active paragraph={{ rows: 5 }} />
        ) : (
          <Table
            dataSource={filtered}
            columns={columns}
            rowKey='id'
            size='middle'
            pagination={{ pageSize: 15, showSizeChanger: true, showTotal: t => `סה"כ ${t} הפעלות` }}
            scroll={{ x: 'max-content' }}
            locale={{
              emptyText: (
                <Empty
                  description='אין הפעלות מתועדות עדיין'
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              ),
            }}
          />
        )}
      </Card>
    </motion.div>
  );
};

export default SessionLogsReport;
