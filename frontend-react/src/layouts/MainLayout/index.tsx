/**
 * 主佈局組件 - 應用程序的主要佈局結構
 * 包含側邊欄導航、頂部工具欄和內容區域
 */

import React, { useState } from 'react';
import { Layout, Menu, Avatar, Badge, Button, Drawer, Dropdown, Space, notification, theme, MenuProps } from 'antd';
import { 
  DashboardOutlined, 
  GlobalOutlined, 
  ScheduleOutlined, 
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  UserOutlined,
  LogoutOutlined,
  InfoCircleOutlined,
  MenuOutlined
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../hooks';
import { toggleSidebar } from '../../store/slices/themeSlice';
import { logout } from '../../store/slices/userSlice';
import NotificationPanel from '../../components/NotificationPanel';
import './MainLayout.css';

const { Header, Sider, Content } = Layout;

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  const { collapsed } = useAppSelector((state) => state.theme);
  const { user } = useAppSelector((state) => state.user);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  
  const { token } = theme.useToken();
  const notifications = useAppSelector((state) => state.notification.notifications);
  const unreadCount = notifications.filter(n => !n.read).length;

  // 獲取當前選中的菜單項
  const selectedKeys = [location.pathname.split('/')[1] || 'dashboard'];

  // 處理菜單點擊
  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
    if (drawerVisible) {
      setDrawerVisible(false);
    }
  };

  // 處理用戶菜單操作
  const handleUserMenuClick = ({ key }: { key: string }) => {
    switch (key) {
      case 'profile':
        navigate('/settings');
        break;
      case 'logout':
        dispatch(logout());
        navigate('/login');
        notification.success({
          message: '登出成功',
          description: '您已成功登出系統',
        });
        break;
    }
  };

  // 用戶下拉菜單項
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '個人資料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系統設置',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登錄',
      danger: true,
    },
  ] as MenuProps['items'];

  // 響應式處理
  const handleMobileMenuClick = () => {
    setDrawerVisible(true);
  };

  // 側邊欄菜單項
  const menuItems: MenuProps['items'] = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '儀表板',
    },
    {
      key: '/proxies',
      icon: <GlobalOutlined />,
      label: '代理管理',
    },
    {
      key: '/tasks',
      icon: <ScheduleOutlined />,
      label: '任務管理',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系統設置',
    },
    {
      key: '/about',
      icon: <InfoCircleOutlined />,
      label: '關於',
    },
  ] as MenuProps['items'];

  return (
    <Layout className="main-layout" style={{ minHeight: '100vh' }}>
      {/* 桌面端側邊欄 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        theme="dark"
        width={240}
        className="main-sider"
        breakpoint="md"
        onBreakpoint={(broken) => {
          if (broken) {
            dispatch(toggleSidebar());
          }
        }}
      >
        <div className="logo-container">
          <div className="logo">
            {collapsed ? 'PIC' : 'Proxy IP Collector'}
          </div>
        </div>
        
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={selectedKeys}
          items={menuItems}
          onClick={handleMenuClick}
          className="main-menu"
        />
      </Sider>

      <Layout className="site-layout">
        <Header
          style={{
            padding: '0 24px',
            background: token.colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: `1px solid ${token.colorBorder}`,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => dispatch(toggleSidebar())}
              style={{
                fontSize: '16px',
                width: 64,
                height: 64,
              }}
            />
            {/* 移動端菜單按鈕 */}
            <Button
              type="text"
              icon={<MenuOutlined />}
              onClick={handleMobileMenuClick}
              className="mobile-menu-trigger"
              style={{ display: 'none' }}
            />
          </div>

          <Space size="large">
            <Badge count={unreadCount} size="small">
              <Button
                type="text"
                icon={<BellOutlined />}
                onClick={() => setNotificationOpen(true)}
                style={{ fontSize: '16px' }}
              />
            </Badge>

            <Dropdown
              menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
              placement="bottomRight"
              arrow
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar
                  size="small"
                  icon={<UserOutlined />}
                  src={user?.avatar}
                />
                <span style={{ fontSize: '14px' }}>
                  {user?.username || '用戶'}
                </span>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: token.colorBgContainer,
            borderRadius: token.borderRadius,
          }}
        >
          <Outlet />
        </Content>
      </Layout>

      {/* 移動端抽屜菜單 */}
      <Drawer
        title="菜單"
        placement="left"
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        className="mobile-drawer"
      >
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={selectedKeys}
          items={menuItems}
          onClick={handleMenuClick}
          className="mobile-menu"
        />
      </Drawer>

      <NotificationPanel
        visible={notificationOpen}
        onClose={() => setNotificationOpen(false)}
      />
    </Layout>
  );
};

export default MainLayout;