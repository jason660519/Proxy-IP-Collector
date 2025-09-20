import { createBrowserRouter, Navigate } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import DashboardPage from '../pages/DashboardPage';
import ProxiesPage from '../pages/ProxiesPage';
import TasksPage from '../pages/TasksPage';
import SettingsPage from '../pages/SettingsPage';
import LogsPage from '../pages/LogsPage';

/**
 * 路由配置組件
 * 定義應用的所有路由和導航結構
 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
        handle: {
          title: '儀表板',
          icon: 'dashboard'
        }
      },
      {
        path: 'proxies',
        element: <ProxiesPage />,
        handle: {
          title: '代理管理',
          icon: 'global'
        }
      },
      {
        path: 'tasks',
        element: <TasksPage />,
        handle: {
          title: '任務管理',
          icon: 'schedule'
        }
      },
      {
        path: 'settings',
        element: <SettingsPage />,
        handle: {
          title: '系統設置',
          icon: 'setting'
        }
      },
      {
        path: 'logs',
        element: <LogsPage />,
        handle: {
          title: '日誌管理',
          icon: 'file-text'
        }
      }
    ]
  }
]);

/**
 * 獲取路由配置
 * @returns 路由配置數組
 */
export const getRoutes = () => [
  {
    key: 'dashboard',
    path: '/dashboard',
    title: '儀表板',
    icon: 'dashboard',
    description: '系統概覽和統計數據'
  },
  {
    key: 'proxies',
    path: '/proxies',
    title: '代理管理',
    icon: 'global',
    description: '管理和配置代理IP'
  },
  {
    key: 'tasks',
    path: '/tasks',
    title: '任務管理',
    icon: 'schedule',
    description: '創建和管理任務'
  },
  {
    key: 'settings',
    path: '/settings',
    title: '系統設置',
    icon: 'setting',
    description: '系統配置和偏好設置'
  },
  {
    key: 'logs',
    path: '/logs',
    title: '日誌管理',
    icon: 'file-text',
    description: '查看系統日誌和事件'
  },
];

/**
 * 獲取麵包屑配置
 * @param pathname - 當前路徑
 * @returns 麵包屑數組
 */
export const getBreadcrumbs = (pathname: string) => {
  const routes = getRoutes();
  const currentRoute = routes.find(route => route.path === pathname);
  
  if (!currentRoute) {
    return [{ title: '首頁', path: '/' }];
  }

  return [
    { title: '首頁', path: '/' },
    { title: currentRoute.title, path: currentRoute.path }
  ];
};

/**
 * 檢查路徑是否有效
 * @param path - 路徑字符串
 * @returns 是否有效
 */
export const isValidPath = (path: string): boolean => {
  const validPaths = getRoutes().map(route => route.path);
  return validPaths.includes(path);
};

/**
 * 獲取頁面標題
 * @param pathname - 當前路徑
 * @returns 頁面標題
 */
export const getPageTitle = (pathname: string): string => {
  const routes = getRoutes();
  const currentRoute = routes.find(route => route.path === pathname);
  
  if (!currentRoute) {
    return 'Proxy Manager Pro';
  }

  return `${currentRoute.title} - Proxy Manager Pro`;
};

export default router;