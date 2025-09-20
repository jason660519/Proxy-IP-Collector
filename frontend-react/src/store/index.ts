/**
 * Redux Store 配置
 * @description 配置Redux Toolkit狀態管理系統
 */

import { configureStore } from '@reduxjs/toolkit';
import proxySlice from './slices/proxySlice';
import filterSlice from './slices/filterSlice';
import dashboardSlice from './slices/dashboardSlice';
import taskSlice from './slices/taskSlice';
import notificationSlice from './slices/notificationSlice';
import userSlice from './slices/userSlice';
import themeSlice from './slices/themeSlice';
import { proxyApi } from '../services/proxyApi';

export const store = configureStore({
  reducer: {
    // 同步狀態
    proxy: proxySlice,
    filter: filterSlice,
    dashboard: dashboardSlice,
    task: taskSlice,
    notification: notificationSlice,
    user: userSlice,
    theme: themeSlice,
    
    // RTK Query API
    [proxyApi.reducerPath]: proxyApi.reducer,
  },
  
  // 中間件配置
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }).concat(proxyApi.middleware),
});

// 導出RootState和AppDispatch類型
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// 導出store實例
export default store;