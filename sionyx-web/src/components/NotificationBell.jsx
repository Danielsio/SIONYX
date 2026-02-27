import { Badge, Button, Popover, Empty } from 'antd';
import {
  BellOutlined,
  MessageOutlined,
  UserOutlined,
  SettingOutlined,
  CheckOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/he';
import { useNotificationStore } from '../store/notificationStore';

dayjs.extend(relativeTime);
dayjs.locale('he');

const TYPE_ICONS = {
  message: <MessageOutlined style={{ color: '#1890ff' }} />,
  user: <UserOutlined style={{ color: '#52c41a' }} />,
  system: <SettingOutlined style={{ color: '#8c8c8c' }} />,
};

const NotificationBell = ({ darkMode }) => {
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotificationStore();

  const content = (
    <div style={{ width: 320, maxHeight: 400, direction: 'rtl' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 12,
          paddingBottom: 8,
          borderBottom: '1px solid #f0f0f0',
        }}
      >
        <span style={{ fontWeight: 600, fontSize: 14 }}>התראות</span>
        {unreadCount > 0 && (
          <Button type="link" size="small" icon={<CheckOutlined />} onClick={markAllAsRead}>
            סמן הכל כנקרא
          </Button>
        )}
      </div>
      <div style={{ maxHeight: 320, overflowY: 'auto' }}>
        {notifications.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="אין התראות"
            style={{ padding: '24px 0' }}
          />
        ) : (
          notifications.map(n => (
            <div
              key={n.id}
              role="button"
              tabIndex={0}
              onClick={() => !n.read && markAsRead(n.id)}
              onKeyDown={e => e.key === 'Enter' && !n.read && markAsRead(n.id)}
              style={{
                display: 'flex',
                gap: 12,
                padding: 12,
                borderBottom: '1px solid #f5f5f5',
                cursor: n.read ? 'default' : 'pointer',
                background: n.read ? 'transparent' : 'rgba(24, 144, 255, 0.04)',
                margin: '0 -12px',
              }}
            >
              <span style={{ fontSize: 18, flexShrink: 0 }}>
                {TYPE_ICONS[n.type] || TYPE_ICONS.system}
              </span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 13,
                    color: '#1f2937',
                    fontWeight: n.read ? 400 : 500,
                  }}
                >
                  {n.message}
                </div>
                <div style={{ fontSize: 11, color: '#8c8c8c', marginTop: 2 }}>
                  {n.timestamp ? dayjs(n.timestamp).fromNow() : ''}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );

  return (
    <Popover
      content={content}
      trigger="click"
      placement="bottomRight"
      overlayStyle={{ zIndex: 1050 }}
    >
      <Badge count={unreadCount} size="small" offset={[-4, 4]}>
        <Button
          type="text"
          icon={<BellOutlined style={{ fontSize: 18 }} />}
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          aria-label="התראות"
        />
      </Badge>
    </Popover>
  );
};

export default NotificationBell;
