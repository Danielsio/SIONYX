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
} from 'antd';
import {
  DashboardOutlined,
  BankOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  SettingOutlined,
  StopOutlined,
} from '@ant-design/icons';
import useIsMobile from '../hooks/useIsMobile';
import { useSupervisorAuthStore } from './store/supervisorAuthStore';
import { signOutSupervisor } from './services/supervisorAuthService';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const sidebarStyle = {
  background: 'linear-gradient(180deg, #1a1030 0%, #0f0a1f 100%)',
};

const menuItems = [
  { key: '/supervisor', icon: <DashboardOutlined />, label: 'סקירה' },
  { key: '/supervisor/organizations', icon: <BankOutlined />, label: 'ארגונים' },
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
        ...sidebarStyle,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          padding: collapsed ? '16px 12px' : '20px 24px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          flexShrink: 0,
          gap: 12,
          minHeight: 72,
        }}
      >
        <div
          style={{
            width: collapsed ? 36 : 40,
            height: collapsed ? 36 : 40,
            background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
            borderRadius: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)',
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
          <Text
            style={{
              color: '#fff',
              fontSize: 14,
              fontWeight: 700,
              letterSpacing: '0.5px',
            }}
          >
            SIONYX SUPERVISOR
          </Text>
        )}
      </div>

      <div style={{ flex: 1, padding: '16px 8px', overflowY: 'auto' }}>
        <Menu
          theme='dark'
          mode='inline'
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{
            background: 'transparent',
            border: 'none',
          }}
        />
      </div>

      <div
        style={{
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          padding: collapsed ? '16px 8px' : '16px',
          flexShrink: 0,
        }}
      >
        <Button
          type='text'
          block
          icon={<LogoutOutlined />}
          onClick={handleLogout}
          style={{
            color: 'rgba(255, 255, 255, 0.65)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            gap: 10,
            height: 44,
            borderRadius: 10,
            transition: 'all 0.2s',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(239, 68, 68, 0.15)';
            e.currentTarget.style.color = '#ef4444';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = 'rgba(255, 255, 255, 0.65)';
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
            ...sidebarStyle,
            boxShadow: '-4px 0 24px rgba(0, 0, 0, 0.2)',
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
          background: '#0f0a1f',
        }}
      >
        <Header
          style={{
            padding: isMobile ? '0 16px' : '0 28px',
            background: 'linear-gradient(90deg, #1a1030 0%, #0f0a1f 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.2)',
            minHeight: 68,
            position: 'sticky',
            top: 0,
            zIndex: 50,
            borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
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
                color: 'rgba(255, 255, 255, 0.85)',
              }}
            />
          </Tooltip>

          <Space
            style={{
              padding: '6px 12px',
              borderRadius: 12,
              background: 'rgba(99, 102, 241, 0.15)',
            }}
          >
            <Avatar
              size={36}
              style={{
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                boxShadow: '0 2px 8px rgba(99, 102, 241, 0.3)',
              }}
              icon={<UserOutlined />}
            />
            <Text style={{ color: '#fff', fontWeight: 600, fontSize: 14 }}>
              {supervisor?.name || supervisor?.phone || 'מפקח'}
            </Text>
          </Space>
        </Header>

        <Content
          style={{
            margin: isMobile ? 16 : 28,
            padding: isMobile ? 20 : 28,
            minHeight: 'calc(100vh - 124px)',
            background: 'transparent',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default SupervisorLayout;
