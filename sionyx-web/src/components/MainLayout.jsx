import { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Avatar, Dropdown, Typography, Space, Badge, Drawer, Button, Tooltip } from 'antd';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DashboardOutlined,
  UserOutlined,
  AppstoreOutlined,
  LogoutOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  SettingOutlined,
  PhoneOutlined,
  MessageOutlined,
  DesktopOutlined,
  HomeOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { signOut } from '../services/authService';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

// Sidebar gradient background
const sidebarStyle = {
  background: 'linear-gradient(180deg, #1a1f36 0%, #151929 100%)',
};

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

  const handleBackToHome = () => {
    navigate('/');
  };

  const handleMenuClick = ({ key }) => {
    if (key === 'logout') {
      handleLogout();
      return;
    }
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

  // Main navigation menu items
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
      key: '/admin/settings',
      icon: <SettingOutlined />,
      label: 'הגדרות',
    },
  ];

  // User profile dropdown items (without logout - logout is in sidebar)
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
  ];

  const renderSidebar = () => (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%',
      ...sidebarStyle,
    }}>
      {/* Logo */}
      <motion.div
        initial={false}
        animate={{ 
          padding: collapsed ? '16px 12px' : '20px 24px',
        }}
        transition={{ duration: 0.2 }}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          flexShrink: 0,
          gap: 12,
          minHeight: 72,
        }}
      >
        <motion.div
          animate={{ 
            width: collapsed ? 36 : 40,
            height: collapsed ? 36 : 40,
          }}
          transition={{ duration: 0.2 }}
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)',
          }}
        >
          <img
            src='/logo.png'
            alt='SIONYX'
            style={{
              height: collapsed ? 20 : 24,
              width: collapsed ? 20 : 24,
              objectFit: 'contain',
              filter: 'brightness(0) invert(1)',
            }}
          />
        </motion.div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.15 }}
            >
              <Text style={{ 
                color: '#fff', 
                fontSize: 20, 
                fontWeight: 700,
                letterSpacing: '0.5px',
              }}>
                SIONYX
              </Text>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Main Menu */}
      <div style={{ flex: 1, padding: '16px 8px', overflowY: 'auto' }}>
        <Menu
          theme='dark'
          mode='inline'
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ 
            background: 'transparent',
            border: 'none',
          }}
        />
      </div>

      {/* Bottom Section - Logout */}
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
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(239, 68, 68, 0.15)';
            e.currentTarget.style.color = '#ef4444';
          }}
          onMouseLeave={(e) => {
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
      {/* Desktop Sidebar */}
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
            boxShadow: '-4px 0 24px rgba(0, 0, 0, 0.12)',
            zIndex: 100,
          }}
        >
          {renderSidebar()}
        </Sider>
      )}

      {/* Mobile Drawer */}
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
          <div style={{ height: '100%' }}>
            {renderSidebar()}
          </div>
        </Drawer>
      )}

      <Layout
        style={{
          marginRight: isMobile ? 0 : collapsed ? 72 : 240,
          transition: 'margin 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
          background: '#f8f9fc',
        }}
      >
        <Header
          style={{
            padding: isMobile ? '0 16px' : '0 28px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06)',
            minHeight: 68,
            position: 'sticky',
            top: 0,
            zIndex: 50,
          }}
        >
          {/* Left side - Menu toggle + Back to home */}
          <Space size='middle'>
            <Tooltip title={collapsed ? 'הרחב תפריט' : 'צמצם תפריט'}>
              <Button
                type='text'
                icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                onClick={toggleSidebar}
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

            <Tooltip title='חזרה לדף הראשי'>
              <Button
                type='default'
                icon={<HomeOutlined />}
                onClick={handleBackToHome}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  borderRadius: 10,
                  height: 40,
                  paddingLeft: 16,
                  paddingRight: 16,
                  border: '1px solid #e8eaed',
                }}
              >
                {!isMobile && 'דף הבית'}
              </Button>
            </Tooltip>
          </Space>

          {/* Right side - Org info + User avatar */}
          <Space size={isMobile ? 'small' : 'middle'}>
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
                <Text style={{ fontWeight: 600, color: '#667eea' }}>
                  {user?.orgId || 'ארגון'}
                </Text>
              </div>
            )}

            <Dropdown 
              menu={{ items: userMenuItems }} 
              placement='bottomRight'
              disabled={userMenuItems.every(item => item.disabled)}
            >
              <Space 
                style={{ 
                  cursor: 'pointer',
                  padding: '6px 12px',
                  borderRadius: 12,
                  transition: 'background 0.2s',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#f4f5f7'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <Avatar 
                  size={40}
                  style={{ 
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)',
                  }} 
                  icon={<UserOutlined />} 
                />
                {!isMobile && (
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                    }}
                  >
                    <Text style={{ fontSize: 14, fontWeight: 600, color: '#1f2937' }}>
                      {user?.displayName || 'מנהל'}
                    </Text>
                    {user?.phone && (
                      <Text type='secondary' style={{ fontSize: 12 }}>
                        <PhoneOutlined style={{ marginLeft: 4 }} />
                        {user.phone}
                      </Text>
                    )}
                  </div>
                )}
              </Space>
            </Dropdown>
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
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Outlet />
          </motion.div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
