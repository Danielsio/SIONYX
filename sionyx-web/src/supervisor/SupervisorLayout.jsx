import { useNavigate, useLocation } from 'react-router-dom';
import { Avatar, Typography, Space, theme } from 'antd';
import {
  DashboardOutlined,
  BankOutlined,
  SettingOutlined,
  StopOutlined,
  UserOutlined,
  MessageOutlined,
} from '@ant-design/icons';
import AppShell from '../components/AppShell';
import { useSupervisorAuthStore } from './store/supervisorAuthStore';
import { signOutSupervisor } from './services/supervisorAuthService';

const { Text } = Typography;

const menuItems = [
  { key: '/supervisor', icon: <DashboardOutlined />, label: 'סקירה' },
  { key: '/supervisor/organizations', icon: <BankOutlined />, label: 'ארגונים' },
  { key: '/supervisor/messages', icon: <MessageOutlined />, label: 'הודעות' },
  { key: '/supervisor/blocked', icon: <StopOutlined />, label: 'משתמשים חסומים' },
  { key: '/supervisor/settings', icon: <SettingOutlined />, label: 'הגדרות' },
];

const pageTitles = {
  '/supervisor': 'סקירה',
  '/supervisor/organizations': 'ארגונים',
  '/supervisor/messages': 'הודעות',
  '/supervisor/blocked': 'משתמשים חסומים',
  '/supervisor/settings': 'הגדרות',
};

const SupervisorLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const supervisor = useSupervisorAuthStore(state => state.supervisor);
  const logout = useSupervisorAuthStore(state => state.logout);
  const { token } = theme.useToken();

  const handleLogout = async () => {
    await signOutSupervisor();
    logout();
    navigate('/supervisor/login');
  };

  // Highlight the section even on nested routes (e.g. /organizations/:orgId).
  const selectedKey =
    menuItems
      .map(item => item.key)
      .filter(key => key !== '/supervisor')
      .find(key => location.pathname.startsWith(key)) ||
    (location.pathname === '/supervisor' ? '/supervisor' : location.pathname);

  const commands = menuItems.map(item => ({
    key: item.key,
    icon: item.icon,
    label: item.label,
    hint: 'מעבר לעמוד',
    onSelect: () => navigate(item.key),
  }));

  const headerRight = (
    <Space>
      <Avatar size={36} style={{ background: token.colorPrimary }} icon={<UserOutlined />} />
      <Text strong style={{ fontSize: 14 }}>
        {supervisor?.name || supervisor?.phone || 'מפקח'}
      </Text>
    </Space>
  );

  return (
    <AppShell
      brand='SIONYX SUPERVISOR'
      sidebarVariant='light'
      menuItems={menuItems}
      selectedKey={selectedKey}
      onNavigate={navigate}
      onLogout={handleLogout}
      headerRight={headerRight}
      pageTitles={pageTitles}
      commands={commands}
    />
  );
};

export default SupervisorLayout;
