/**
 * 主應用組件
 * @description Proxy IP Pool Collector 的主應用組件，提供整體佈局和路由功能
 */

import React, { useEffect } from 'react';
import { ConfigProvider, theme as antdTheme } from 'antd';
import { Provider } from 'react-redux';
import { RouterProvider } from 'react-router-dom';
import { store } from './store';
import router from './routes';
import { useAppSelector } from './hooks';
import zhTW from 'antd/locale/zh_TW';
import './App.css';

/**
 * 主題配置組件
 * @description 根據 Redux 狀態提供 Ant Design 主題配置
 */
const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { theme } = useAppSelector((state) => state.theme);
  
  const themeConfig = {
    locale: zhTW,
    theme: {
      algorithm: theme === 'dark' ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
      token: {
        colorPrimary: theme === 'dark' ? '#1890ff' : '#1890ff',
        colorSuccess: '#52c41a',
        colorWarning: '#faad14',
        colorError: '#ff4d4f',
        colorInfo: '#1890ff',
        colorTextBase: theme === 'dark' ? '#ffffff' : '#000000',
        colorBgBase: theme === 'dark' ? '#0f0f0f' : '#ffffff',
        borderRadius: 6,
        wireframe: false,
      },
      components: {
        Layout: {
          headerBg: theme === 'dark' ? '#001529' : '#ffffff',
          siderBg: theme === 'dark' ? '#001529' : '#ffffff',
          triggerBg: theme === 'dark' ? '#002140' : '#f0f2f5',
          triggerColor: theme === 'dark' ? '#ffffff' : '#000000',
        },
        Menu: {
          darkItemBg: '#001529',
          darkItemHoverBg: '#002140',
          darkItemSelectedBg: '#1890ff',
          darkItemColor: '#ffffff',
          darkItemHoverColor: '#ffffff',
          darkItemSelectedColor: '#ffffff',
        },
        Card: {
          borderRadiusLG: 8,
          boxShadow: theme === 'dark' 
            ? '0 2px 8px rgba(0, 0, 0, 0.3)'
            : '0 2px 8px rgba(0, 0, 0, 0.1)',
        },
        Table: {
          borderColor: theme === 'dark' ? '#303030' : '#f0f0f0',
          headerBg: theme === 'dark' ? '#141414' : '#fafafa',
          headerColor: theme === 'dark' ? '#ffffff' : '#000000',
        },
        Input: {
          borderRadius: 6,
          colorBorder: theme === 'dark' ? '#303030' : '#d9d9d9',
        },
        Button: {
          borderRadius: 6,
          borderRadiusLG: 8,
        },
      },
    },
  };

  return (
    <ConfigProvider {...themeConfig}>
      {children}
    </ConfigProvider>
  );
};

/**
 * 應用初始化組件
 * @description 處理應用初始化邏輯
 */
const AppInitializer: React.FC = () => {
  useEffect(() => {
    // 初始化應用
    const initializeApp = async () => {
      // 設置在線狀態監聽
      const handleOnline = () => {
        store.dispatch({ type: 'app/setOnlineStatus', payload: true });
      };

      const handleOffline = () => {
        store.dispatch({ type: 'app/setOnlineStatus', payload: false });
      };

      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
      };
    };

    initializeApp();
  }, []);

  return null;
};

/**
 * 主應用組件
 * 應用程序的根組件，提供 Redux 狀態管理和路由
 */
const App: React.FC = () => {
  return (
    <Provider store={store}>
      <ThemeProvider>
        <AppInitializer />
        <RouterProvider router={router} />
      </ThemeProvider>
    </Provider>
  );
};

export default App;