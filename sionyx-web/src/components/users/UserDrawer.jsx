import { Drawer, Card, Descriptions, Tag, Space, Button, Dropdown, Spin, Table, Typography } from 'antd';
import {
  ClockCircleOutlined,
  PrinterOutlined,
  EditOutlined,
  CrownOutlined,
  MinusCircleOutlined,
  MessageOutlined,
  SendOutlined,
  LockOutlined,
  CalendarOutlined,
  DownloadOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import {
  getStatusLabel as getPurchaseStatusLabel,
  getStatusColor as getPurchaseStatusColor,
} from '../../constants/purchaseStatus';
import {
  getUserStatus,
  getStatusLabel as getUserStatusLabel,
  getStatusColor as getUserStatusColor,
} from '../../constants/userStatus';
import { formatTimeHebrewCompact } from '../../utils/timeFormatter';
import { exportToCSV, exportToExcel, exportToPDF } from '../../utils/csvExport';

const { Text } = Typography;

const purchaseColumns = [
  {
    title: 'תאריך',
    dataIndex: 'createdAt',
    key: 'createdAt',
    render: date => (date ? dayjs(date).format('MMM D, YYYY HH:mm') : 'לא זמין'),
  },
  {
    title: 'חבילה',
    dataIndex: 'packageName',
    key: 'packageName',
  },
  {
    title: 'סכום',
    dataIndex: 'amount',
    key: 'amount',
    render: price => {
      const numPrice = parseFloat(price) || 0;
      return `₪${numPrice.toFixed(2)}`;
    },
  },
  {
    title: 'סטטוס',
    dataIndex: 'status',
    key: 'status',
    render: status => (
      <Tag color={getPurchaseStatusColor(status)}>{getPurchaseStatusLabel(status)}</Tag>
    ),
  },
];

const messageColumns = [
  {
    title: 'הודעה',
    dataIndex: 'message',
    key: 'message',
    render: text => (
      <Text style={{ maxWidth: 200 }} ellipsis={{ tooltip: text }}>
        {text}
      </Text>
    ),
  },
  {
    title: 'סטטוס',
    dataIndex: 'read',
    key: 'status',
    render: (read, record) => (
      <Space>
        {read ? (
          <Tag color='green' icon={<ClockCircleOutlined />}>
            נקרא
          </Tag>
        ) : (
          <Tag color='orange' icon={<ClockCircleOutlined />}>
            לא נקרא
          </Tag>
        )}
        {read && record.readAt && (
          <Text type='secondary' style={{ fontSize: '12px' }}>
            {dayjs(record.readAt).format('HH:mm')}
          </Text>
        )}
      </Space>
    ),
  },
  {
    title: 'נשלח',
    dataIndex: 'timestamp',
    key: 'timestamp',
    render: timestamp => (
      <Space direction='vertical' size={0}>
        <Text>{dayjs(timestamp).format('DD/MM/YYYY')}</Text>
        <Text type='secondary' style={{ fontSize: '12px' }}>
          {dayjs(timestamp).format('HH:mm:ss')}
        </Text>
      </Space>
    ),
  },
];

/**
 * User detail drawer: profile, quick actions, purchase history (exportable),
 * and message history. Pure presentation — mutations go through `actions`.
 */
const UserDrawer = ({
  open,
  onClose,
  user,
  currentUserUid,
  purchases,
  loadingPurchases,
  messages,
  loadingMessages,
  deleting = false,
  actions,
}) => {
  const purchasesExportRows = purchases.map(p => ({
    date: p.createdAt ? dayjs(p.createdAt).format('MMM D, YYYY HH:mm') : '',
    package: p.packageName || '',
    amount: parseFloat(p.amount) || 0,
    status: p.status || '',
  }));
  const purchasesExportColumns = [
    { title: 'תאריך', dataIndex: 'date' },
    { title: 'חבילה', dataIndex: 'package' },
    { title: 'סכום', dataIndex: 'amount' },
    { title: 'סטטוס', dataIndex: 'status' },
  ];
  const purchasesExportName = `purchases-${user?.uid || 'user'}-${new Date().toISOString().split('T')[0]}`;

  return (
    <Drawer
      title='פרטי משתמש'
      placement='right'
      width={Math.min(600, window.innerWidth - 40)}
      onClose={onClose}
      open={open}
    >
      {user && (
        <Space direction='vertical' size='large' style={{ width: '100%' }}>
          <Card>
            <Descriptions column={1} bordered>
              <Descriptions.Item label='שם'>
                {`${user.firstName || ''} ${user.lastName || ''}`.trim() || 'לא זמין'}
              </Descriptions.Item>
              <Descriptions.Item label='טלפון'>{user.phoneNumber || 'לא זמין'}</Descriptions.Item>
              <Descriptions.Item label='אימייל'>{user.email || 'לא זמין'}</Descriptions.Item>
              <Descriptions.Item label='סטטוס'>
                {(() => {
                  const status = getUserStatus(user);
                  return <Tag color={getUserStatusColor(status)}>{getUserStatusLabel(status)}</Tag>;
                })()}
              </Descriptions.Item>
              <Descriptions.Item label='תפקיד'>
                {user.isAdmin ? (
                  <Tag color='gold' icon={<CrownOutlined />}>
                    מנהל
                  </Tag>
                ) : (
                  <Tag color='default'>משתמש</Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label='זמן נותר'>
                <Space>
                  <ClockCircleOutlined />
                  {formatTimeHebrewCompact(user.remainingTime || 0)}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label='תקציב הדפסות'>
                <Space>
                  <PrinterOutlined />
                  <Text style={{ fontWeight: 600 }}>₪{user.printBalance || 0}</Text>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label='תוקף זמן'>
                {user.timeExpiresAt ? (
                  <Space>
                    <CalendarOutlined
                      style={{
                        color: dayjs(user.timeExpiresAt).isBefore(dayjs()) ? '#ff4d4f' : '#fa8c16',
                      }}
                    />
                    <Text
                      style={{
                        color: dayjs(user.timeExpiresAt).isBefore(dayjs()) ? '#ff4d4f' : undefined,
                      }}
                    >
                      {dayjs(user.timeExpiresAt).isBefore(dayjs())
                        ? 'פג תוקף'
                        : dayjs(user.timeExpiresAt).format('DD/MM/YYYY')}
                    </Text>
                  </Space>
                ) : (
                  <Text type='secondary'>ללא הגבלה</Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label='נוצר'>
                {user.createdAt ? dayjs(user.createdAt).format('MMMM D, YYYY HH:mm') : 'לא זמין'}
              </Descriptions.Item>
              <Descriptions.Item label='עודכן לאחרונה'>
                {user.updatedAt ? dayjs(user.updatedAt).format('MMMM D, YYYY HH:mm') : 'לא זמין'}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* Quick Actions */}
          <Card title='פעולות מהירות'>
            <Space wrap>
              <Button icon={<MessageOutlined />} onClick={() => actions.onSendMessage()}>
                שלח הודעה
              </Button>
              <Button icon={<EditOutlined />} onClick={() => actions.onAdjust(user)}>
                התאם יתרה
              </Button>
              <Button icon={<LockOutlined />} onClick={() => actions.onResetPassword(user)}>
                איפוס סיסמה
              </Button>
              {user.isAdmin ? (
                <Button
                  icon={<MinusCircleOutlined />}
                  danger
                  onClick={() => actions.onRevokeAdmin(user)}
                  disabled={user.uid === currentUserUid}
                  title={user.uid === currentUserUid ? 'לא ניתן להסיר הרשאות מנהל מעצמך' : ''}
                >
                  {user.uid === currentUserUid ? 'לא ניתן להסיר מעצמך' : 'הסר הרשאות מנהל'}
                </Button>
              ) : (
                <Button icon={<CrownOutlined />} onClick={() => actions.onGrantAdmin(user)}>
                  הענק הרשאות מנהל
                </Button>
              )}
              {user.forceLogout !== true && (
                <Button icon={<MinusCircleOutlined />} danger onClick={() => actions.onKick(user)}>
                  נתק משתמש
                </Button>
              )}
              {!user.isAdmin && user.uid !== currentUserUid && (
                <Button
                  icon={<DeleteOutlined />}
                  danger
                  onClick={() => actions.onDelete(user)}
                  loading={deleting}
                >
                  מחק משתמש
                </Button>
              )}
            </Space>
          </Card>

          <Card
            title={
              <Space>
                <span>היסטוריית רכישות</span>
                <Dropdown
                  menu={{
                    items: [
                      {
                        key: 'csv',
                        icon: <DownloadOutlined />,
                        label: 'ייצא CSV',
                        onClick: () =>
                          exportToCSV(purchasesExportRows, purchasesExportColumns, purchasesExportName),
                      },
                      {
                        key: 'excel',
                        icon: <DownloadOutlined />,
                        label: 'ייצא Excel',
                        onClick: () =>
                          exportToExcel(purchasesExportRows, purchasesExportColumns, purchasesExportName),
                      },
                      {
                        key: 'pdf',
                        icon: <DownloadOutlined />,
                        label: 'ייצא PDF',
                        onClick: () =>
                          exportToPDF(
                            purchasesExportRows,
                            purchasesExportColumns,
                            purchasesExportName,
                            `היסטוריית רכישות - ${user?.firstName || ''} ${user?.lastName || ''}`.trim()
                          ),
                      },
                    ],
                  }}
                  trigger={['click']}
                >
                  <Button type='text' size='small' icon={<DownloadOutlined />}>
                    ייצא
                  </Button>
                </Dropdown>
              </Space>
            }
          >
            {loadingPurchases ? (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Spin />
              </div>
            ) : (
              <Table
                columns={purchaseColumns}
                dataSource={purchases}
                rowKey='id'
                size='small'
                pagination={{ pageSize: 5 }}
                scroll={{ x: 'max-content' }}
              />
            )}
          </Card>

          <Card
            title={
              <Space>
                <MessageOutlined />
                <span>היסטוריית הודעות</span>
                <Button
                  type='primary'
                  size='small'
                  icon={<SendOutlined />}
                  onClick={() => actions.onSendMessage()}
                >
                  שלח הודעה
                </Button>
              </Space>
            }
          >
            {loadingMessages ? (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Spin />
              </div>
            ) : (
              <Table
                columns={messageColumns}
                dataSource={messages}
                rowKey='id'
                size='small'
                pagination={{ pageSize: 5 }}
                scroll={{ x: 'max-content' }}
                locale={{ emptyText: 'אין הודעות' }}
              />
            )}
          </Card>
        </Space>
      )}
    </Drawer>
  );
};

export default UserDrawer;
