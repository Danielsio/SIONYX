import { useNavigate, useLocation } from 'react-router-dom';
import { Avatar, Typography, Space, Button, Tooltip } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  AppstoreOutlined,
  SettingOutlined,
  PhoneOutlined,
  MessageOutlined,
  DesktopOutlined,
  HomeOutlined,
  BulbOutlined,
  BulbFilled,
  NotificationOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import AppShell from './AppShell';
import NotificationBell from './NotificationBell';
import useBreakpoint from '../hooks/useBreakpoint';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';
import { signOut } from '../services/authService';

const { Text } = Typography;

const pageTitles = {
  '/admin': 'סקירה כללית',
  '/admin/users': 'משתמשים',
  '/admin/packages': 'חבילות',
  '/admin/messages': 'הודעות',
  '/admin/computers': 'מחשבים',
  '/admin/announcements': 'הודעות מערכת',
  '/admin/reports': 'דוחות',
  '/admin/settings': 'הגדרות',
};

const menuItems = [
  { key: '/admin', icon: <DashboardOutlined />, label: 'סקירה כללית' },
  { key: '/admin/users', icon: <UserOutlined />, label: 'משתמשים' },
  { key: '/admin/packages', icon: <AppstoreOutlined />, label: 'חבילות' },
  { key: '/admin/messages', icon: <MessageOutlined />, label: 'הודעות' },
  { key: '/admin/computers', icon: <DesktopOutlined />, label: 'מחשבים' },
  { key: '/admin/announcements', icon: <NotificationOutlined />, label: 'הודעות מערכת' },
  { key: '/admin/reports', icon: <BarChartOutlined />, label: 'דוחות' },
  { key: '/admin/settings', icon: <SettingOutlined />, label: 'הגדרות' },
];

const MainLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isMobile } = useBreakpoint();
  const user = useAuthStore(state => state.user);
  const logout = useAuthStore(state => state.logout);
  const darkMode = useAuthStore(state => state.darkMode);
  const toggleDarkMode = useAuthStore(state => state.toggleDarkMode);
  const users = useDataStore(state => state.users);

  const handleLogout = async () => {
    await signOut();
    logout();
    navigate('/admin/login');
  };

  // ⌘K: navigation commands + live user lookup (from the store's live list).
  const commands = menuItems.map(item => ({
    key: item.key,
    icon: item.icon,
    label: item.label,
    hint: 'מעבר לעמוד',
    onSelect: () => navigate(item.key),
  }));

  const getDynamicCommands = query => {
    const q = query.toLowerCase();
    return users
      .filter(
        u =>
          `${u.firstName || ''} ${u.lastName || ''}`.toLowerCase().includes(q) ||
          (u.phoneNumber || '').includes(query)
      )
      .slice(0, 5)
      .map(u => ({
        key: `user-${u.uid}`,
        icon: <UserOutlined />,
        label: `${u.firstName || ''} ${u.lastName || ''}`.trim() || u.phoneNumber,
        hint: `משתמש · ${u.phoneNumber || ''}`,
        onSelect: () =>
          navigate(
            `/admin/users?q=${encodeURIComponent(
              `${u.firstName || ''} ${u.lastName || ''}`.trim() || u.phoneNumber || ''
            )}`
          ),
      }));
  };

  const headerLeft = (
    <>
      <Tooltip title='חזרה לדף הראשי'>
        <Button
          type='default'
          icon={<HomeOutlined />}
          onClick={() => navigate('/')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            borderRadius: 10,
            height: 40,
            paddingLeft: 16,
            paddingRight: 16,
          }}
        >
          {!isMobile && 'דף הבית'}
        </Button>
      </Tooltip>

      <Tooltip title={darkMode ? 'מצב בהיר' : 'מצב כהה'}>
        <Button
          type='text'
          icon={darkMode ? <BulbFilled /> : <BulbOutlined />}
          onClick={toggleDarkMode}
          aria-label={darkMode ? 'מצב בהיר' : 'מצב כהה'}
          style={{ fontSize: 18, width: 40, height: 40, borderRadius: 10 }}
        />
      </Tooltip>

      <Tooltip title='התראות'>
        <NotificationBell darkMode={darkMode} />
      </Tooltip>
    </>
  );

  const headerRight = (
    <>
      {!isMobile && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 14px',
            background: 'rgba(102, 126, 234, 0.08)',
            borderRadius: 10,
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: '#10b981',
              boxShadow: '0 0 0 3px rgba(16, 185, 129, 0.2)',
            }}
          />
          <Text style={{ fontWeight: 600, color: '#667eea' }}>{user?.orgId || 'ארגון'}</Text>
        </div>
      )}

      <Space style={{ padding: '6px 12px' }}>
        <Avatar size={40} style={{ background: '#667eea' }} icon={<UserOutlined />} />
        {!isMobile && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
            <Text style={{ fontSize: 14, fontWeight: 600 }}>
              {user?.firstName ? `${user.firstName} ${user.lastName || ''}`.trim() : 'מנהל'}
            </Text>
            {(user?.phone || user?.phoneNumber) && (
              <Text type='secondary' style={{ fontSize: 12 }}>
                <PhoneOutlined style={{ marginLeft: 4 }} />
                {user.phone || user.phoneNumber}
              </Text>
            )}
          </div>
        )}
      </Space>
    </>
  );

  return (
    <AppShell
      brand='SIONYX'
      sidebarVariant='dark'
      menuItems={menuItems}
      selectedKey={location.pathname}
      onNavigate={navigate}
      onLogout={handleLogout}
      headerLeft={headerLeft}
      headerRight={headerRight}
      pageTitles={pageTitles}
      commands={commands}
      getDynamicCommands={getDynamicCommands}
      contentBackground={darkMode ? '#141414' : '#f8f9fc'}
    />
  );
};

export default MainLayout;
