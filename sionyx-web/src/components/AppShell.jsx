import { useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Layout, Menu, Typography, Drawer, Button, Tooltip, theme } from 'antd';
import { motion } from 'framer-motion'; // eslint-disable-line no-unused-vars
import {
  LogoutOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import useBreakpoint from '../hooks/useBreakpoint';
import CommandPalette from './CommandPalette';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

// Admin sidebar keeps the dark brand panel; supervisor uses the theme surface.
const darkSidebarStyle = {
  background: 'linear-gradient(180deg, #1a1f36 0%, #151929 100%)',
};

/**
 * The one shell both consoles share (admin + supervisor): fixed RTL sidebar,
 * mobile drawer, sticky header, ⌘K command palette, responsive tiers
 * (tablet auto-collapses the sidebar; ultrawide caps content at 1440px),
 * per-route document.title, and a 120ms enter-only page transition.
 */
const AppShell = ({
  brand,
  sidebarVariant = 'dark',
  menuItems,
  selectedKey,
  onNavigate,
  onLogout,
  headerLeft = null,
  headerRight = null,
  pageTitles = {},
  commands = [],
  getDynamicCommands,
  contentBackground,
}) => {
  const { isMobile, isTablet } = useBreakpoint();
  const [collapsed, setCollapsed] = useState(isTablet);
  const [mobileDrawerVisible, setMobileDrawerVisible] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const location = useLocation();
  const { token } = theme.useToken();
  const darkSidebar = sidebarVariant === 'dark';

  useEffect(() => {
    if (!isMobile) setMobileDrawerVisible(false);
  }, [isMobile]);

  // Tablets get more content room by default; expanding stays one click away.
  useEffect(() => {
    setCollapsed(isTablet);
  }, [isTablet]);

  useEffect(() => {
    const title = pageTitles[location.pathname];
    document.title = title ? `SIONYX · ${title}` : 'SIONYX';
  }, [location.pathname, pageTitles]);

  useEffect(() => {
    const onKey = e => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setPaletteOpen(open => !open);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const handleMenuClick = ({ key }) => {
    onNavigate(key);
    if (isMobile) setMobileDrawerVisible(false);
  };

  const toggleSidebar = () => {
    if (isMobile) setMobileDrawerVisible(v => !v);
    else setCollapsed(v => !v);
  };

  const sidebarBackground = darkSidebar
    ? darkSidebarStyle
    : { background: token.colorBgContainer };

  const renderSidebar = () => (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        ...sidebarBackground,
      }}
    >
      {/* Logo */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          padding: collapsed ? '16px 12px' : '20px 24px',
          borderBottom: darkSidebar
            ? '1px solid rgba(255, 255, 255, 0.08)'
            : `1px solid ${token.colorBorderSecondary}`,
          flexShrink: 0,
          gap: 12,
          minHeight: 72,
        }}
      >
        <div
          style={{
            width: collapsed ? 36 : 40,
            height: collapsed ? 36 : 40,
            background: darkSidebar
              ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
              : token.colorPrimary,
            borderRadius: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
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
            strong
            style={{
              color: darkSidebar ? '#fff' : undefined,
              fontSize: brand.length > 10 ? 14 : 20,
              fontWeight: 700,
              letterSpacing: '0.5px',
              whiteSpace: 'nowrap',
            }}
          >
            {brand}
          </Text>
        )}
      </div>

      {/* Menu */}
      <div style={{ flex: 1, padding: '16px 8px', overflowY: 'auto' }}>
        <Menu
          theme={darkSidebar ? 'dark' : 'light'}
          mode='inline'
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ background: 'transparent', border: 'none' }}
        />
      </div>

      {/* Logout */}
      <div
        style={{
          borderTop: darkSidebar
            ? '1px solid rgba(255, 255, 255, 0.08)'
            : `1px solid ${token.colorBorderSecondary}`,
          padding: collapsed ? '16px 8px' : '16px',
          flexShrink: 0,
        }}
      >
        <Button
          type='text'
          block
          danger={!darkSidebar}
          className={darkSidebar ? 'sidebar-logout' : undefined}
          icon={<LogoutOutlined />}
          onClick={onLogout}
          style={{
            color: darkSidebar ? 'rgba(255, 255, 255, 0.65)' : undefined,
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
            ...sidebarBackground,
            ...(darkSidebar
              ? { boxShadow: '-4px 0 24px rgba(0, 0, 0, 0.12)' }
              : { borderLeft: `1px solid ${token.colorBorderSecondary}` }),
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
          styles={{ body: { padding: 0 }, header: { display: 'none' } }}
        >
          <div style={{ height: '100%' }}>{renderSidebar()}</div>
        </Drawer>
      )}

      <Layout
        style={{
          marginRight: isMobile ? 0 : collapsed ? 72 : 240,
          transition: 'margin 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
          ...(contentBackground ? { background: contentBackground } : {}),
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
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Tooltip title={collapsed ? 'הרחב תפריט' : 'צמצם תפריט'}>
              <Button
                type='text'
                icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                onClick={toggleSidebar}
                aria-label={collapsed ? 'הרחב תפריט' : 'צמצם תפריט'}
                style={{ fontSize: 18, width: 40, height: 40, borderRadius: 10 }}
              />
            </Tooltip>

            <Tooltip title='חיפוש מהיר (Ctrl+K)'>
              <Button
                type='text'
                icon={<SearchOutlined />}
                onClick={() => setPaletteOpen(true)}
                aria-label='חיפוש מהיר'
                style={{ fontSize: 17, width: 40, height: 40, borderRadius: 10 }}
              />
            </Tooltip>

            {headerLeft}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>{headerRight}</div>
        </Header>

        <Content
          style={{
            margin: isMobile ? 16 : 28,
            padding: isMobile ? 4 : 0,
            minHeight: 'calc(100vh - 124px)',
            background: 'transparent',
          }}
        >
          {/* Ultrawide screens: content caps at 1440px instead of stretching. */}
          <div style={{ maxWidth: 1440, margin: '0 auto', width: '100%' }}>
            {/* Enter-only fade: exit animations add dead time to navigation. */}
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.12 }}
            >
              <Outlet />
            </motion.div>
          </div>
        </Content>
      </Layout>

      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        commands={commands}
        getDynamicCommands={getDynamicCommands}
      />
    </Layout>
  );
};

export default AppShell;
