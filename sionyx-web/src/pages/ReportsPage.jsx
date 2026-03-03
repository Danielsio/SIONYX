import { useEffect, useState, useMemo, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Card,
  Row,
  Col,
  Typography,
  Space,
  Skeleton,
  Empty,
  Button,
  Table,
  DatePicker,
  Segmented,
  Dropdown,
  Tag,
  Statistic,
} from 'antd';
import dayjs from 'dayjs';
import 'dayjs/locale/he';
import isBetween from 'dayjs/plugin/isBetween';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  DollarOutlined,
  DownloadOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
  FileTextOutlined,
  ShoppingCartOutlined,
  CalendarOutlined,
  RiseOutlined,
  CrownOutlined,
} from '@ant-design/icons';
import { useOrgId } from '../hooks/useOrgId';
import { getOrganizationStats } from '../services/organizationService';
import { exportToCSV, exportToExcel, exportToPDF } from '../utils/csvExport';
import { logger } from '../utils/logger';

dayjs.extend(isBetween);
dayjs.locale('he');

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] } },
};

const PRESETS = {
  today: 'היום',
  week: 'השבוע',
  month: 'החודש',
  last30: '30 ימים',
  custom: 'טווח מותאם',
};

const getPresetRange = preset => {
  const now = dayjs();
  switch (preset) {
    case 'today':
      return [now.startOf('day'), now.endOf('day')];
    case 'week':
      return [now.startOf('week'), now.endOf('day')];
    case 'month':
      return [now.startOf('month'), now.endOf('day')];
    case 'last30':
      return [now.subtract(30, 'day').startOf('day'), now.endOf('day')];
    default:
      return [now.subtract(30, 'day').startOf('day'), now.endOf('day')];
  }
};

const ReportsPage = () => {
  const [loading, setLoading] = useState(true);
  const [allPurchases, setAllPurchases] = useState([]);
  const [preset, setPreset] = useState('last30');
  const [customRange, setCustomRange] = useState(null);
  const orgId = useOrgId();

  const dateRange = useMemo(() => {
    if (preset === 'custom' && customRange) return customRange;
    return getPresetRange(preset);
  }, [preset, customRange]);

  const loadData = useCallback(async () => {
    if (!orgId) return;
    setLoading(true);
    try {
      const result = await getOrganizationStats(orgId);
      if (result.success && result.stats?.purchases) {
        setAllPurchases(result.stats.purchases);
      }
    } catch (err) {
      logger.error('Failed to load reports data:', err);
    }
    setLoading(false);
  }, [orgId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const filteredPurchases = useMemo(() => {
    if (!allPurchases.length) return [];
    const [start, end] = dateRange;
    return allPurchases.filter(p => {
      if (p.status !== 'completed') return false;
      const d = dayjs(p.createdAt);
      return d.isAfter(start) && d.isBefore(end);
    });
  }, [allPurchases, dateRange]);

  const stats = useMemo(() => {
    const totalRevenue = filteredPurchases.reduce((s, p) => s + (parseFloat(p.amount) || 0), 0);
    const count = filteredPurchases.length;
    const avg = count > 0 ? totalRevenue / count : 0;

    const byPackage = {};
    filteredPurchases.forEach(p => {
      const name = p.packageName || 'אחר';
      byPackage[name] = (byPackage[name] || 0) + (parseFloat(p.amount) || 0);
    });
    const topPackage = Object.entries(byPackage).sort((a, b) => b[1] - a[1])[0];

    return { totalRevenue, count, avg, topPackage };
  }, [filteredPurchases]);

  const chartData = useMemo(() => {
    const [start, end] = dateRange;
    const days = end.diff(start, 'day') + 1;
    const byDate = {};
    for (let i = 0; i < days; i++) {
      const d = start.add(i, 'day').format('YYYY-MM-DD');
      byDate[d] = { dateKey: d, date: dayjs(d).format('dd DD/MM'), revenue: 0, count: 0 };
    }
    filteredPurchases.forEach(p => {
      const d = dayjs(p.createdAt).format('YYYY-MM-DD');
      if (byDate[d]) {
        byDate[d].revenue += parseFloat(p.amount) || 0;
        byDate[d].count++;
      }
    });
    return Object.values(byDate).sort((a, b) => a.dateKey.localeCompare(b.dateKey));
  }, [filteredPurchases, dateRange]);

  const columns = [
    {
      title: 'תאריך',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: v => dayjs(v).format('DD/MM/YYYY HH:mm'),
      sorter: (a, b) => dayjs(a.createdAt).unix() - dayjs(b.createdAt).unix(),
      defaultSortOrder: 'descend',
    },
    {
      title: 'חבילה',
      dataIndex: 'packageName',
      key: 'packageName',
      render: v => v || 'אחר',
    },
    {
      title: 'סכום',
      dataIndex: 'amount',
      key: 'amount',
      render: v => `₪${parseFloat(v || 0).toFixed(2)}`,
      sorter: (a, b) => (parseFloat(a.amount) || 0) - (parseFloat(b.amount) || 0),
    },
    {
      title: 'סטטוס',
      dataIndex: 'status',
      key: 'status',
      render: v => (
        <Tag color={v === 'completed' ? 'green' : v === 'pending' ? 'orange' : 'red'}>
          {v === 'completed' ? 'הושלם' : v === 'pending' ? 'ממתין' : 'נכשל'}
        </Tag>
      ),
    },
    {
      title: 'מזהה עסקה',
      dataIndex: 'transactionId',
      key: 'transactionId',
      render: v => v || '—',
      ellipsis: true,
    },
  ];

  const exportColumns = [
    { title: 'תאריך', dataIndex: 'formattedDate' },
    { title: 'חבילה', dataIndex: 'packageName' },
    { title: 'סכום', dataIndex: 'formattedAmount' },
    { title: 'סטטוס', dataIndex: 'statusLabel' },
    { title: 'מזהה עסקה', dataIndex: 'transactionId' },
  ];

  const exportData = filteredPurchases.map(p => ({
    ...p,
    formattedDate: dayjs(p.createdAt).format('DD/MM/YYYY HH:mm'),
    formattedAmount: `₪${parseFloat(p.amount || 0).toFixed(2)}`,
    statusLabel: p.status === 'completed' ? 'הושלם' : p.status === 'pending' ? 'ממתין' : 'נכשל',
    packageName: p.packageName || 'אחר',
    transactionId: p.transactionId || '—',
  }));

  const exportMenuItems = [
    {
      key: 'csv',
      icon: <FileTextOutlined />,
      label: 'CSV',
      onClick: () => exportToCSV(exportData, exportColumns, `דוח-הכנסות-${dayjs().format('YYYY-MM-DD')}`),
    },
    {
      key: 'excel',
      icon: <FileExcelOutlined />,
      label: 'Excel',
      onClick: () => exportToExcel(exportData, exportColumns, `דוח-הכנסות-${dayjs().format('YYYY-MM-DD')}`),
    },
    {
      key: 'pdf',
      icon: <FilePdfOutlined />,
      label: 'PDF',
      onClick: () => exportToPDF(exportData, exportColumns, `דוח-הכנסות-${dayjs().format('YYYY-MM-DD')}`, 'דוח הכנסות'),
    },
  ];

  if (loading) {
    return (
      <div style={{ direction: 'rtl' }}>
        <Skeleton active paragraph={{ rows: 1 }} style={{ marginBottom: 24 }} />
        <Row gutter={[20, 20]}>
          {[1, 2, 3, 4].map(i => (
            <Col key={i} xs={24} sm={12} lg={6}>
              <Card style={{ borderRadius: 16 }}>
                <Skeleton active paragraph={{ rows: 2 }} />
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    );
  }

  return (
    <motion.div style={{ direction: 'rtl' }} variants={containerVariants} initial='hidden' animate='visible'>
      <Space direction='vertical' size={24} style={{ width: '100%' }}>
        {/* Header */}
        <motion.div variants={itemVariants} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <Title level={2} style={{ marginBottom: 8, fontWeight: 700, color: '#1f2937' }}>
              דוחות הכנסות
            </Title>
            <Text style={{ color: '#6b7280', fontSize: 15 }}>
              ניתוח הכנסות ורכישות לתקופה נבחרת
            </Text>
          </div>
          <Space wrap>
            <Segmented
              value={preset}
              options={Object.entries(PRESETS).map(([k, v]) => ({ label: v, value: k }))}
              onChange={setPreset}
            />
            {preset === 'custom' && (
              <RangePicker
                value={customRange}
                onChange={setCustomRange}
                format='DD/MM/YYYY'
              />
            )}
            <Dropdown menu={{ items: exportMenuItems }} disabled={filteredPurchases.length === 0}>
              <Button icon={<DownloadOutlined />}>ייצוא</Button>
            </Dropdown>
          </Space>
        </motion.div>

        {/* Summary Stats */}
        <Row gutter={[20, 20]}>
          <Col xs={24} sm={12} lg={6}>
            <motion.div variants={itemVariants}>
              <Card bordered={false} style={{ borderRadius: 16, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                <Statistic
                  title={<span style={{ color: 'rgba(255,255,255,0.85)' }}>סה&quot;כ הכנסות</span>}
                  value={stats.totalRevenue}
                  precision={2}
                  prefix='₪'
                  valueStyle={{ color: '#fff', fontWeight: 700, fontSize: 28 }}
                />
              </Card>
            </motion.div>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <motion.div variants={itemVariants}>
              <Card bordered={false} style={{ borderRadius: 16 }}>
                <Statistic
                  title='סה"כ רכישות'
                  value={stats.count}
                  prefix={<ShoppingCartOutlined style={{ color: '#667eea' }} />}
                  valueStyle={{ fontWeight: 700 }}
                />
              </Card>
            </motion.div>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <motion.div variants={itemVariants}>
              <Card bordered={false} style={{ borderRadius: 16 }}>
                <Statistic
                  title='ממוצע לרכישה'
                  value={stats.avg}
                  precision={2}
                  prefix='₪'
                  suffix={<RiseOutlined style={{ color: '#10b981' }} />}
                  valueStyle={{ fontWeight: 700 }}
                />
              </Card>
            </motion.div>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <motion.div variants={itemVariants}>
              <Card bordered={false} style={{ borderRadius: 16 }}>
                <Statistic
                  title='חבילה מובילה'
                  value={stats.topPackage ? stats.topPackage[0] : '—'}
                  prefix={<CrownOutlined style={{ color: '#faad14' }} />}
                  valueStyle={{ fontWeight: 700, fontSize: 18 }}
                />
                {stats.topPackage && (
                  <Text type='secondary' style={{ fontSize: 13 }}>₪{stats.topPackage[1].toFixed(2)}</Text>
                )}
              </Card>
            </motion.div>
          </Col>
        </Row>

        {/* Revenue Trend Chart */}
        <motion.div variants={itemVariants}>
          <Card
            title={
              <Space>
                <DollarOutlined style={{ color: '#667eea' }} />
                <span>מגמת הכנסות</span>
              </Space>
            }
            bordered={false}
            style={{ borderRadius: 16 }}
          >
            {chartData.length > 0 ? (
              <ResponsiveContainer width='100%' height={300}>
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id='reportRevGradient' x1='0' y1='0' x2='0' y2='1'>
                      <stop offset='0%' stopColor='#667eea' stopOpacity={1} />
                      <stop offset='100%' stopColor='#667eea' stopOpacity={0.15} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray='3 3' stroke='#e5e7eb' />
                  <XAxis dataKey='date' tick={{ fontSize: 12, fill: '#6b7280' }} />
                  <YAxis tick={{ fontSize: 12, fill: '#6b7280' }} tickFormatter={v => `₪${v}`} />
                  <RechartsTooltip
                    formatter={(value, name) => [
                      name === 'revenue' ? `₪${Number(value).toFixed(2)}` : value,
                      name === 'revenue' ? 'הכנסה' : 'רכישות',
                    ]}
                  />
                  <Area type='monotone' dataKey='revenue' stroke='#764ba2' strokeWidth={2} fill='url(#reportRevGradient)' />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <Empty description='אין נתונים בטווח הנבחר' image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ padding: 40 }} />
            )}
          </Card>
        </motion.div>

        {/* Purchases Table */}
        <motion.div variants={itemVariants}>
          <Card
            title={
              <Space>
                <CalendarOutlined style={{ color: '#667eea' }} />
                <span>רכישות בתקופה</span>
                {filteredPurchases.length > 0 && (
                  <Tag color='blue'>{filteredPurchases.length}</Tag>
                )}
              </Space>
            }
            bordered={false}
            style={{ borderRadius: 16 }}
          >
            <Table
              dataSource={filteredPurchases}
              columns={columns}
              rowKey={r => r.id || r.transactionId || Math.random()}
              pagination={{ pageSize: 15, showSizeChanger: true, showTotal: total => `סה"כ ${total} רכישות` }}
              size='middle'
              locale={{ emptyText: <Empty description='אין רכישות בטווח הנבחר' image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
            />
          </Card>
        </motion.div>
      </Space>
    </motion.div>
  );
};

export default ReportsPage;
