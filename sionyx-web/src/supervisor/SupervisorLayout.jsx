import { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout,
  Menu,
  Avatar,
  Typography,
  Button,
  Drawer,
  Tooltip,
  Space,
  theme,
} from 'antd';
import {
  DashboardOutlined,
  BankOutlined,
  LogoutOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  SettingOutlined,
  StopOutlined,
  UserOutlined,
  MessageOutlined,
} from '@ant-design/icons';
import useIsMobile from '../hooks/useIsMobile';
import { useSupervisorAuthStore } from './store/supervisorAuthStore';
import { signOutSupervisor } from './services/supervisorAuthService';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const menuItems = [
  { key: '/supervisor', icon: <DashboardOutlined />, label: 'סקירה' },
  { key: '/supervisor/organizations', icon: <BankOutlined />, label: 'ארגונים' },
  { key: '/supervisor/messages', icon: <MessageOutlined />, label: 'הודעות' },
  { key: '/supervisor/blocked', icon: <StopOutlined />, label: 'משתמשים חסומים' },
  { key: '/supervisor/settings', icon: <SettingOutlined />, label: 'הגדרות' },
];

const SupervisorLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileDrawerVisible, setMobileDrawerVisible] = useState(false);
  const isMobile = useIsMobile();
  const navigate = useNavigate();
  const location = useLocation();
  const supervisor = useSupervisorAuthStore(state => state.supervisor);
  const logout = useSupervisorAuthStore(state => state.logout);
  const { token } = theme.useToken();

  useEffect(() => {
    if (!isMobile) setMobileDrawerVisible(false);
  }, [isMobile]);

  const handleLogout = async () => {
    await signOutSupervisor();
    logout();
    navigate('/supervisor/login');
  };

  const handleMenuClick = ({ key }) => {
    navigate(key);
    if (isMobile) setMobileDrawerVisible(false);
  };

  const selectedKey =
    location.pathname === '/supervisor'
      ? '/supervisor'
      : location.pathname.startsWith('/supervisor/organizations')
        ? '/supervisor/organizations'
        : location.pathname.startsWith('/supervisor/messages')
          ? '/supervisor/messages'
          : location.pathname.startsWith('/supervisor/blocked')
            ? '/supervisor/blocked'
            : location.pathname.startsWith('/supervisor/settings')
              ? '/supervisor/settings'
              : location.pathname;

  const toggleSidebar = () => {
    if (isMobile) {
      setMobileDrawerVisible(!mobileDrawerVisible);
    } else {
      setCollapsed(!collapsed);
    }
  };

  const renderSidebar = () => (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: token.colorBgContainer,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          padding: collapsed ? '16px 12px' : '20px 24px',
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          flexShrink: 0,
          gap: 12,
          minHeight: 72,
        }}
      >
        <div
          style={{
            width: collapsed ? 36 : 40,
            height: collapsed ? 36 : 40,
            background: token.colorPrimary,
            borderRadius: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <span
            style={{
              color: '#fff',
              fontSize: collapsed ? 16 : 18,
              fontWeight: 800,
              lineHeight: 1,
              userSelect: 'none',
            }}
          >
            S
          </span>
        </div>
        {!collapsed && (
          <Text strong style={{ fontSize: 14, letterSpacing: '0.5px' }}>
            SIONYX SUPERVISOR
          </Text>
        )}
      </div>

      <div style={{ flex: 1, padding: '16px 8px', overflowY: 'auto' }}>
        <Menu
          mode='inline'
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ border: 'none' }}
        />
      </div>

      <div
        style={{
          borderTop: `1px solid ${token.colorBorderSecondary}`,
          padding: collapsed ? '16px 8px' : '16px',
          flexShrink: 0,
        }}
      >
        <Button
          type='text'
          block
          danger
          icon={<LogoutOutlined />}
          onClick={handleLogout}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            gap: 10,
            height: 44,
            borderRadius: 10,
          }}
        >
          {!collapsed && 'התנתק'}
        </Button>
      </div>
    </div>
  );

  return (
    <Layout style={{ minHeight: '100vh', direction: 'rtl' }}>
      {!isMobile && (
        <Sider
          trigger={null}
          collapsible
          collapsed={collapsed}
          width={240}
          collapsedWidth={72}
          style={{
            overflow: 'hidden',
            height: '100vh',
            position: 'fixed',
            right: 0,
            top: 0,
            bottom: 0,
            background: token.colorBgContainer,
            borderLeft: `1px solid ${token.colorBorderSecondary}`,
            zIndex: 100,
          }}
        >
          {renderSidebar()}
        </Sider>
      )}

      {isMobile && (
        <Drawer
          title={null}
          placement='right'
          onClose={() => setMobileDrawerVisible(false)}
          open={mobileDrawerVisible}
          width={280}
          styles={{
            body: { padding: 0 },
            header: { display: 'none' },
          }}
        >
          <div style={{ height: '100%' }}>{renderSidebar()}</div>
        </Drawer>
      )}

      <Layout
        style={{
          marginRight: isMobile ? 0 : collapsed ? 72 : 240,
          transition: 'margin 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      >
        <Header
          style={{
            padding: isMobile ? '0 16px' : '0 28px',
            background: token.colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
            minHeight: 68,
            position: 'sticky',
            top: 0,
            zIndex: 50,
          }}
        >
          <Tooltip title={collapsed ? 'הרחב תפריט' : 'צמצם תפריט'}>
            <Button
              type='text'
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={toggleSidebar}
              aria-label={collapsed ? 'הרחב תפריט' : 'צמצם תפריט'}
              style={{
                fontSize: 18,
                width: 40,
                height: 40,
                borderRadius: 10,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            />
          </Tooltip>

          <Space>
            <Avatar
              size={36}
              style={{ background: token.colorPrimary }}
              icon={<UserOutlined />}
            />
            <Text strong style={{ fontSize: 14 }}>
              {supervisor?.name || supervisor?.phone || 'מפקח'}
            </Text>
          </Space>
        </Header>

        <Content
          style={{
            margin: isMobile ? 16 : 28,
            padding: isMobile ? 20 : 28,
            minHeight: 'calc(100vh - 124px)',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default SupervisorLayout;
