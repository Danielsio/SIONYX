import { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Avatar, Dropdown, Typography, Space, Badge, Drawer, Button } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  AppstoreOutlined,
  LogoutOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
  PhoneOutlined,
  MessageOutlined,
  DesktopOutlined,
  DollarOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { signOut } from '../services/authService';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const MainLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileDrawerVisible, setMobileDrawerVisible] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore(state => state.user);
  const logout = useAuthStore(state => state.logout);

  // Check if device is mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth >= 768) {
        setMobileDrawerVisible(false);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleLogout = async () => {
    await signOut();
    logout();
    navigate('/admin/login');
  };

  const handleMenuClick = ({ key }) => {
    navigate(key);
    if (isMobile) {
      setMobileDrawerVisible(false);
    }
  };

  const toggleSidebar = () => {
    if (isMobile) {
      setMobileDrawerVisible(!mobileDrawerVisible);
    } else {
      setCollapsed(!collapsed);
    }
  };

  const menuItems = [
    {
      key: '/admin',
      icon: <DashboardOutlined />,
      label: 'סקירה כללית',
    },
    {
      key: '/admin/users',
      icon: <UserOutlined />,
      label: 'משתמשים',
    },
    {
      key: '/admin/packages',
      icon: <AppstoreOutlined />,
      label: 'חבילות',
    },
    {
      key: '/admin/messages',
      icon: <MessageOutlined />,
      label: 'הודעות',
    },
    {
      key: '/admin/computers',
      icon: <DesktopOutlined />,
      label: 'מחשבים',
    },
    {
      key: '/admin/pricing',
      icon: <DollarOutlined />,
      label: 'מחירי הדפסה',
    },
  ];

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'פרופיל',
      disabled: true,
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'הגדרות',
      disabled: true,
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'התנתק',
      onClick: handleLogout,
      danger: true,
    },
  ];

  const renderSidebar = () => (
    <>
      <div
        style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: collapsed ? 20 : 24,
          fontWeight: 'bold',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          gap: collapsed ? 0 : 8,
        }}
      >
        <img
          src='/logo.png'
          alt='SIONYX Logo'
          style={{
            height: collapsed ? 24 : 32,
            width: collapsed ? 24 : 32,
            objectFit: 'contain',
          }}
        />
        {!collapsed && <span>SIONYX</span>}
      </div>

      <Menu
        theme='dark'
        mode='inline'
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        style={{ marginTop: 16 }}
      />
    </>
  );

  return (
    <Layout style={{ minHeight: '100vh', direction: 'rtl' }}>
      {/* Desktop Sidebar */}
      {!isMobile && (
        <Sider
          trigger={null}
          collapsible
          collapsed={collapsed}
          style={{
            overflow: 'auto',
            height: '100vh',
            position: 'fixed',
            right: 0,
            top: 0,
            bottom: 0,
          }}
        >
          {renderSidebar()}
        </Sider>
      )}

      {/* Mobile Drawer */}
      {isMobile && (
        <Drawer
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <img
                src='/logo.png'
                alt='SIONYX Logo'
                style={{
                  height: 24,
                  width: 24,
                  objectFit: 'contain',
                }}
              />
              <span>SIONYX</span>
            </div>
          }
          placement='right'
          onClose={() => setMobileDrawerVisible(false)}
          open={mobileDrawerVisible}
          width={280}
          bodyStyle={{ padding: 0 }}
          headerStyle={{
            background: '#001529',
            color: '#fff',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <div style={{ background: '#001529', height: '100%' }}>{renderSidebar()}</div>
        </Drawer>
      )}

      <Layout
        style={{
          marginRight: isMobile ? 0 : collapsed ? 80 : 200,
          transition: 'all 0.2s',
        }}
      >
        <Header
          style={{
            padding: isMobile ? '0 16px' : '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,21,41,.08)',
            minHeight: 64,
          }}
        >
          <div>
            <MenuUnfoldOutlined
              style={{ fontSize: 18, cursor: 'pointer' }}
              onClick={toggleSidebar}
            />
          </div>

          <Space size={isMobile ? 'small' : 'middle'} wrap>
            {!isMobile && (
              <Space>
                <Text type='secondary'>ארגון:</Text>
                <Badge status='success' />
                <Text strong>{user?.orgId || 'לא ידוע'}</Text>
              </Space>
            )}

            <Dropdown menu={{ items: userMenuItems }} placement='bottomRight'>
              <Space style={{ cursor: 'pointer' }}>
                <Avatar style={{ backgroundColor: '#667eea' }} icon={<UserOutlined />} />
                {!isMobile && (
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                    }}
                  >
                    <Text style={{ fontSize: 14 }}>
                      {user?.displayName || 'Admin'}
                    </Text>
                    {user?.phone && (
                      <Text type='secondary' style={{ fontSize: 12 }}>
                        <PhoneOutlined style={{ marginRight: 4 }} />
                        {user.phone}
                      </Text>
                    )}
                  </div>
                )}
              </Space>
            </Dropdown>

            {/* Prominent Logout Button */}
            <Button
              type='text'
              danger
              icon={<LogoutOutlined />}
              onClick={handleLogout}
              style={{ 
                display: 'flex', 
                alignItems: 'center',
                gap: 4,
              }}
            >
              {!isMobile && 'התנתק'}
            </Button>
          </Space>
        </Header>

        <Content
          style={{
            margin: isMobile ? '16px' : '24px',
            padding: isMobile ? 16 : 24,
            minHeight: 'calc(100vh - 112px)',
            background: '#f0f2f5',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
