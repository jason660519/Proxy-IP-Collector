/**
 * 通知系統狀態管理
 * @description 管理系統通知、消息和提醒
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// 系統通知接口
export interface SystemNotification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  level: 'low' | 'medium' | 'high' | 'critical';
  read: boolean;
  createdAt: string;
  actions?: Array<{
    label: string;
    action: string;
    type: 'button' | 'link';
  }>;
}

// 使用別名
export type Notification = SystemNotification;

interface NotificationState {
  // 通知列表
  notifications: Notification[];
  
  // 未讀通知數量
  unreadCount: number;
  
  // 通知設置
  settings: {
    enabled: boolean;
    soundEnabled: boolean;
    desktopEnabled: boolean;
    emailEnabled: boolean;
    
    // 通知類型設置
    types: {
      info: boolean;
      success: boolean;
      warning: boolean;
      error: boolean;
    };
    
    // 通知級別設置
    levels: {
      low: boolean;
      medium: boolean;
      high: boolean;
      critical: boolean;
    };
    
    // 通知頻率限制
    rateLimit: {
      enabled: boolean;
      maxPerMinute: number;
      maxPerHour: number;
    };
  };
  
  // UI狀態
  isNotificationPanelOpen: boolean;
  autoHideDelay: number; // 毫秒
  maxNotifications: number;
  
  // 加載狀態
  loading: boolean;
  error: string | null;
}

const initialState: NotificationState = {
  notifications: [],
  unreadCount: 0,
  
  settings: {
    enabled: true,
    soundEnabled: true,
    desktopEnabled: false,
    emailEnabled: false,
    
    types: {
      info: true,
      success: true,
      warning: true,
      error: true,
    },
    
    levels: {
      low: true,
      medium: true,
      high: true,
      critical: true,
    },
    
    rateLimit: {
      enabled: true,
      maxPerMinute: 10,
      maxPerHour: 100,
    },
  },
  
  isNotificationPanelOpen: false,
  autoHideDelay: 5000, // 5秒
  maxNotifications: 50,
  
  loading: false,
  error: null,
};

const notificationSlice = createSlice({
  name: 'notification',
  initialState,
  reducers: {
    // 添加通知
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id' | 'createdAt' | 'read'>>) => {
      const notification: Notification = {
        ...action.payload,
        id: Date.now().toString(),
        createdAt: new Date().toISOString(),
        read: false,
      };
      
      // 檢查通知限制
      if (state.notifications.length >= state.maxNotifications) {
        // 移除最舊的通知
        state.notifications.pop();
      }
      
      // 添加到列表開頭
      state.notifications.unshift(notification);
      
      // 更新未讀數量
      if (!notification.read) {
        state.unreadCount += 1;
      }
      
      // 播放聲音通知
      if (state.settings.soundEnabled && state.settings.types[notification.type as keyof typeof state.settings.types]) {
        // 這裡可以調用播放聲音的函數
        // playNotificationSound(notification.type);
      }
      
      // 顯示桌面通知
      if (state.settings.desktopEnabled && state.settings.types[notification.type as keyof typeof state.settings.types]) {
        // 這裡可以調用顯示桌面通知的函數
        // showDesktopNotification(notification);
      }
    },
    
    // 批量添加通知
    addNotifications: (state, action: PayloadAction<Array<Omit<Notification, 'id' | 'createdAt' | 'read'>>>) => {
      const newNotifications = action.payload.map(notification => ({
        ...notification,
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        createdAt: new Date().toISOString(),
        read: false,
      }));
      
      state.notifications.unshift(...newNotifications);
      
      // 限制通知數量
      if (state.notifications.length > state.maxNotifications) {
        state.notifications = state.notifications.slice(0, state.maxNotifications);
      }
      
      // 更新未讀數量
      state.unreadCount = state.notifications.filter((n: Notification) => !n.read).length;
    },
    
    // 標記通知為已讀
    markAsRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find((n: Notification) => n.id === action.payload);
      if (notification && !notification.read) {
        notification.read = true;
        state.unreadCount = Math.max(0, state.unreadCount - 1);
      }
    },
    
    // 標記所有通知為已讀
    markAllAsRead: (state) => {
      state.notifications.forEach((notification: Notification) => {
        notification.read = true;
      });
      state.unreadCount = 0;
    },
    
    // 刪除通知
    removeNotification: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find((n: Notification) => n.id === action.payload);
      if (notification) {
        if (!notification.read) {
          state.unreadCount = Math.max(0, state.unreadCount - 1);
        }
        state.notifications = state.notifications.filter((n: Notification) => n.id !== action.payload);
      }
    },
    
    // 清除所有通知
    clearAllNotifications: (state) => {
      state.notifications = [];
      state.unreadCount = 0;
    },
    
    // 清除特定類型的通知
    clearNotificationsByType: (state, action: PayloadAction<Notification['type']>) => {
      const type = action.payload;
      state.notifications = state.notifications.filter((notification: Notification) => {
        if (notification.type === type) {
          if (!notification.read) {
            state.unreadCount = Math.max(0, state.unreadCount - 1);
          }
          return false;
        }
        return true;
      });
    },
    
    // 清除已讀通知
    clearReadNotifications: (state) => {
      state.notifications = state.notifications.filter((notification: Notification) => !notification.read);
    },
    
    // 更新通知設置
    updateNotificationSettings: (state, action: PayloadAction<Partial<NotificationState['settings']>>) => {
      state.settings = { ...state.settings, ...action.payload };
    },
    
    // 更新通知類型設置
    updateNotificationTypes: (state, action: PayloadAction<Partial<NotificationState['settings']['types']>>) => {
      state.settings.types = { ...state.settings.types, ...action.payload };
    },
    
    // 更新通知級別設置
    updateNotificationLevels: (state, action: PayloadAction<Partial<NotificationState['settings']['levels']>>) => {
      state.settings.levels = { ...state.settings.levels, ...action.payload };
    },
    
    // 切換通知面板
    toggleNotificationPanel: (state) => {
      state.isNotificationPanelOpen = !state.isNotificationPanelOpen;
    },
    
    // 設置通知面板狀態
    setNotificationPanelOpen: (state, action: PayloadAction<boolean>) => {
      state.isNotificationPanelOpen = action.payload;
    },
    
    // 設置自動隱藏延遲
    setAutoHideDelay: (state, action: PayloadAction<number>) => {
      state.autoHideDelay = action.payload;
    },
    
    // 設置最大通知數量
    setMaxNotifications: (state, action: PayloadAction<number>) => {
      state.maxNotifications = action.payload;
    },
    
    // 設置加載狀態
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    
    // 設置錯誤信息
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

// 導出actions
export const {
  addNotification,
  addNotifications,
  markAsRead,
  markAllAsRead,
  removeNotification,
  clearAllNotifications,
  clearNotificationsByType,
  clearReadNotifications,
  updateNotificationSettings,
  updateNotificationTypes,
  updateNotificationLevels,
  toggleNotificationPanel,
  setNotificationPanelOpen,
  setAutoHideDelay,
  setMaxNotifications,
  setLoading,
  setError,
} = notificationSlice.actions;

// 導出reducer
export default notificationSlice.reducer;