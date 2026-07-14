import { Card, Tag, Button, Dropdown, Avatar, Typography } from 'antd';
import { motion } from 'framer-motion'; // eslint-disable-line no-unused-vars
import {
  UserOutlined,
  ClockCircleOutlined,
  PrinterOutlined,
  EyeOutlined,
  EditOutlined,
  CrownOutlined,
  MoreOutlined,
  MinusCircleOutlined,
  MessageOutlined,
  PhoneOutlined,
  MailOutlined,
  LockOutlined,
  CalendarOutlined,
  DeleteOutlined,
  SafetyOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { getUserStatus, getStatusLabel as getUserStatusLabel } from '../../constants/userStatus';
import { formatTimeHebrewCompact } from '../../utils/timeFormatter';

const { Title, Text } = Typography;

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] },
  },
};

// Color palette for user cards - vibrant and pleasant
const cardGradients = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', // Purple-Indigo
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', // Pink-Rose
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', // Blue-Cyan
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', // Green-Teal
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', // Pink-Yellow
  'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)', // Mint-Pink (light)
  'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)', // Coral-Pink
  'linear-gradient(135deg, #5ee7df 0%, #b490ca 100%)', // Teal-Purple
  'linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)', // Lavender-Cream
  'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)', // Sky-Blue
];

// Get consistent color for a user based on their ID
const getUserGradient = userId => {
  if (!userId) return cardGradients[0];
  let hash = 0;
  for (let i = 0; i < userId.length; i++) {
    hash = userId.charCodeAt(i) + ((hash << 5) - hash);
  }
  return cardGradients[Math.abs(hash) % cardGradients.length];
};

const statusConfig = {
  active: {
    color: '#10b981',
    bg: 'rgba(16, 185, 129, 0.1)',
    shadow: '0 0 0 3px rgba(16, 185, 129, 0.2)',
  },
  connected: {
    color: '#3b82f6',
    bg: 'rgba(59, 130, 246, 0.1)',
    shadow: '0 0 0 3px rgba(59, 130, 246, 0.2)',
  },
  offline: {
    color: '#9ca3af',
    bg: 'rgba(156, 163, 175, 0.1)',
    shadow: 'none',
  },
};

/**
 * One user in the Users grid: gradient header, status dot, balances, and the
 * per-user actions dropdown. Pure presentation — every mutation goes through
 * the `actions` callbacks owned by the page.
 */
const UserCard = ({ userRecord, index = 0, currentUserUid, kicking = false, actions }) => {
  const status = getUserStatus(userRecord);
  const statusLabel = getUserStatusLabel(status);
  const userName = `${userRecord.firstName || ''} ${userRecord.lastName || ''}`.trim() || 'לא זמין';
  const userGradient = getUserGradient(userRecord.uid);
  const currentStatus = statusConfig[status] || statusConfig.offline;

  const menuItems = [
    {
      key: 'view',
      icon: <EyeOutlined />,
      label: 'צפה בפרטים',
      onClick: () => actions.onView(userRecord),
    },
    {
      key: 'message',
      icon: <MessageOutlined />,
      label: 'שלח הודעה',
      onClick: () => actions.onMessage(userRecord),
    },
    {
      key: 'adjust',
      icon: <EditOutlined />,
      label: 'התאם יתרה',
      onClick: () => actions.onAdjust(userRecord),
    },
    {
      key: 'resetPassword',
      icon: <LockOutlined />,
      label: 'איפוס סיסמה',
      onClick: () => actions.onResetPassword(userRecord),
    },
    {
      key: 'verifyPhone',
      icon: <SafetyOutlined />,
      label: userRecord.phoneVerified === true ? 'טלפון מאומת' : 'אמת טלפון',
      disabled: userRecord.phoneVerified === true,
      onClick: () => actions.onVerifyPhone(userRecord),
    },
    {
      type: 'divider',
    },
    userRecord.forceLogout !== true
      ? {
          key: 'kick',
          icon: <MinusCircleOutlined />,
          label: 'נתק משתמש',
          danger: true,
          onClick: () => actions.onKick(userRecord),
          disabled: kicking,
        }
      : {
          key: 'kicked',
          icon: <MinusCircleOutlined />,
          label: 'הותקן',
          disabled: true,
        },
    userRecord.isAdmin
      ? {
          key: 'revoke',
          icon: <MinusCircleOutlined />,
          label: userRecord.uid === currentUserUid ? 'לא ניתן להסיר מעצמך' : 'הסר הרשאות מנהל',
          danger: true,
          onClick: () => actions.onRevokeAdmin(userRecord),
          disabled: userRecord.uid === currentUserUid,
        }
      : {
          key: 'grant',
          icon: <CrownOutlined />,
          label: 'הענק הרשאות מנהל',
          onClick: () => actions.onGrantAdmin(userRecord),
        },
    ...(!userRecord.isAdmin && userRecord.uid !== currentUserUid
      ? [
          { type: 'divider' },
          {
            key: 'delete',
            icon: <DeleteOutlined />,
            label: 'מחק משתמש',
            danger: true,
            onClick: () => actions.onDelete(userRecord),
          },
        ]
      : []),
  ];

  return (
    <motion.div
      variants={cardVariants}
      initial='hidden'
      animate='visible'
      transition={{ delay: index * 0.03 }}
      whileHover={{ y: -4 }}
      style={{ height: '100%' }}
    >
      <Card
        hoverable
        onClick={() => actions.onView(userRecord)}
        style={{
          borderRadius: 18,
          overflow: 'hidden',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          border: '1px solid #e8eaed',
          boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
          transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
        styles={{
          body: {
            padding: 0,
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
          },
        }}
      >
        {/* Header with gradient */}
        <div
          style={{
            background: userGradient,
            padding: '20px 16px',
            color: '#fff',
            position: 'relative',
          }}
        >
          {/* Status indicator */}
          <div
            style={{
              position: 'absolute',
              top: 14,
              right: 14,
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: currentStatus.color,
              boxShadow: currentStatus.shadow,
              animation: status === 'active' ? 'statusPulse 2s ease-in-out infinite' : 'none',
            }}
          />

          {/* Admin Badge */}
          {userRecord.isAdmin && (
            <Tag
              color='gold'
              icon={<CrownOutlined />}
              style={{
                position: 'absolute',
                top: 12,
                left: 12,
                fontWeight: 600,
                borderRadius: 8,
                fontSize: 11,
                border: 'none',
              }}
            >
              מנהל
            </Tag>
          )}

          {/* Actions dropdown */}
          <div
            onClick={e => e.stopPropagation()}
            style={{ position: 'absolute', bottom: 12, right: 12 }}
          >
            <Dropdown menu={{ items: menuItems }} trigger={['click']}>
              <Button
                type='text'
                icon={<MoreOutlined />}
                style={{
                  color: '#fff',
                  background: 'rgba(255,255,255,0.15)',
                  backdropFilter: 'blur(4px)',
                  borderRadius: 8,
                  border: '1px solid rgba(255,255,255,0.2)',
                }}
                size='small'
              />
            </Dropdown>
          </div>

          {/* User Avatar and Name */}
          <div style={{ textAlign: 'center', paddingTop: 4 }}>
            <Avatar
              size={60}
              icon={<UserOutlined />}
              style={{
                backgroundColor: 'rgba(255,255,255,0.2)',
                backdropFilter: 'blur(4px)',
                marginBottom: 12,
                border: '2px solid rgba(255,255,255,0.3)',
              }}
            />
            <Title level={5} style={{ color: '#fff', margin: 0, marginBottom: 8, fontSize: 16 }}>
              {userName}
            </Title>
            <Tag
              style={{
                background: currentStatus.bg,
                color: '#fff',
                border: 'none',
                borderRadius: 10,
                fontWeight: 500,
                fontSize: 11,
              }}
            >
              {statusLabel}
            </Tag>
          </div>
        </div>

        {/* Body */}
        <div
          style={{
            padding: 16,
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            background: '#fafbfc',
          }}
        >
          {/* Contact Info */}
          <div
            style={{
              marginBottom: 14,
              background: '#fff',
              padding: '12px 14px',
              borderRadius: 12,
              border: '1px solid #e8eaed',
            }}
          >
            {userRecord.phoneNumber && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  marginBottom: userRecord.email ? 8 : 0,
                }}
              >
                <PhoneOutlined style={{ color: '#667eea', fontSize: 14 }} />
                <Text
                  style={{
                    direction: 'ltr',
                    display: 'inline-block',
                    color: '#374151',
                    fontSize: 13,
                  }}
                >
                  {userRecord.phoneNumber}
                </Text>
              </div>
            )}
            {userRecord.email && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <MailOutlined style={{ color: '#667eea', fontSize: 14 }} />
                <Text
                  style={{ fontSize: 12, color: '#6b7280' }}
                  ellipsis={{ tooltip: userRecord.email }}
                >
                  {userRecord.email}
                </Text>
              </div>
            )}
            {!userRecord.phoneNumber && !userRecord.email && (
              <Text type='secondary' style={{ fontSize: 12, color: '#9ca3af' }}>
                אין פרטי קשר
              </Text>
            )}
          </div>

          {/* Balance Info - Enhanced styling */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '14px 16px',
                background:
                  'linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(59, 130, 246, 0.04) 100%)',
                borderRadius: 12,
                border: '1px solid rgba(59, 130, 246, 0.15)',
              }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  background: 'rgba(59, 130, 246, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <ClockCircleOutlined style={{ color: '#3b82f6', fontSize: 18 }} />
              </div>
              <div style={{ flex: 1 }}>
                <Text
                  style={{
                    color: '#3b82f6',
                    fontWeight: 700,
                    fontSize: 17,
                    display: 'block',
                    lineHeight: 1.2,
                  }}
                >
                  {formatTimeHebrewCompact(userRecord.remainingTime || 0)}
                </Text>
                <Text style={{ fontSize: 11, color: '#6b7280' }}>זמן נותר</Text>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '14px 16px',
                background:
                  'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(16, 185, 129, 0.04) 100%)',
                borderRadius: 12,
                border: '1px solid rgba(16, 185, 129, 0.15)',
              }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  background: 'rgba(16, 185, 129, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <PrinterOutlined style={{ color: '#10b981', fontSize: 18 }} />
              </div>
              <div style={{ flex: 1 }}>
                <Text
                  style={{
                    color: '#10b981',
                    fontWeight: 700,
                    fontSize: 17,
                    display: 'block',
                    lineHeight: 1.2,
                  }}
                >
                  ₪{userRecord.printBalance || 0}
                </Text>
                <Text style={{ fontSize: 11, color: '#6b7280' }}>תקציב הדפסות</Text>
              </div>
            </div>
          </div>

          {/* Footer info */}
          <div
            style={{
              paddingTop: 14,
              marginTop: 14,
              textAlign: 'center',
              borderTop: '1px solid #e8eaed',
            }}
          >
            <Text style={{ fontSize: 11, color: '#9ca3af' }}>
              <CalendarOutlined style={{ marginLeft: 4 }} />
              הצטרף:{' '}
              {userRecord.createdAt ? dayjs(userRecord.createdAt).format('DD/MM/YYYY') : 'לא זמין'}
            </Text>
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

export default UserCard;
