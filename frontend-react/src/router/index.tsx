/**
 * 路由配置
 * @description 定義應用的所有路由配置
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import DashboardPage from '../pages/DashboardPage';
import ProxiesPage from '../pages/ProxiesPage';
import TasksPage from '../pages/TasksPage';
import SettingsPage from '../pages/SettingsPage';
import LogsPage from '../pages/LogsPage';

/**
 * 路由配置接口
 */
interface RouteConfig {
  path: string;
  element: React.ReactNode;
  title: string;
  icon: string;
}

/**
 * 路由配置數組
 */
export const routes: RouteConfig[] = [
  {
    path: '/dashboard',
    element: <DashboardPage />,
    title: '儀表板',
    icon: 'dashboard',
  },
  {
    path: '/proxies',
    element: <ProxiesPage />,
    title: '代理管理',
    icon: 'global',
  },
  {
    path: '/tasks',
    element: <TasksPage />,
    title: '任務管理',
    icon: 'schedule',
  },
  {
    path: '/logs',
    element: <LogsPage />,
    title: '日誌查看',
    icon: 'file-text',
  },
  {
    path: '/settings',
    element: <SettingsPage />,
    title: '系統設置',
    icon: 'setting',
  },
];

/**
 * 應用路由組件
 */
const AppRouter: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/" element={<MainLayout />}>
        {routes.map((route) => (
          <Route key={route.path} path={route.path} element={route.element} />
        ))}
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default AppRouter;