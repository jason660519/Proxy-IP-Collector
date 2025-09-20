/**
 * 用戶設置狀態管理
 * @description 管理用戶偏好設置和系統配置
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// 用戶設置接口
export interface UserSettings {
  theme: 'light' | 'dark' | 'auto';
  language: 'zh-TW' | 'en' | 'zh-CN';
  timezone: string;
  dateFormat: string;
  timeFormat: '12h' | '24h';
  notifications: {
    email: boolean;
    browser: boolean;
    taskCompleted: boolean;
    proxyFailed: boolean;
    systemAlerts: boolean;
  };
  dashboard: {
    autoRefresh: boolean;
    refreshInterval: number;
    defaultTimeRange: string;
    showCharts: boolean;
    chartAnimations: boolean;
  };
}

interface UserState {
  // 用戶信息
  user: {
    id: string;
    username: string;
    email: string;
    avatar?: string;
    role: 'admin' | 'user';
    lastLogin: string;
  } | null;
  
  // 用戶設置
  settings: UserSettings;
  
  // 系統配置
  systemConfig: {
    // API配置
    api: {
      baseUrl: string;
      timeout: number;
      retryAttempts: number;
      retryDelay: number;
    };
    
    // WebSocket配置
    websocket: {
      enabled: boolean;
      reconnectInterval: number;
      maxReconnectAttempts: number;
    };
    
    // 代理配置
    proxy: {
      maxConcurrentChecks: number;
      checkTimeout: number;
      checkInterval: number;
      maxRetries: number;
    };
    
    // 存儲配置
    storage: {
      maxProxyAge: number; // 天
      cleanupInterval: number; // 小時
      backupInterval: number; // 小時
    };
  };
  
  // 應用狀態
  appState: {
    isOnline: boolean;
    isAuthenticated: boolean;
    lastSyncTime: string | null;
    version: string;
  };
  
  // 加載狀態
  loading: boolean;
  error: string | null;
}

const initialState: UserState = {
  user: null,
  
  settings: {
    theme: 'light',
    language: 'zh-TW',
    timezone: 'Asia/Taipei',
    dateFormat: 'YYYY-MM-DD',
    timeFormat: '24h',
    notifications: {
      email: false,
      browser: true,
      taskCompleted: true,
      proxyFailed: true,
      systemAlerts: true,
    },
    dashboard: {
      autoRefresh: true,
      refreshInterval: 30,
      defaultTimeRange: '24h',
      showCharts: true,
      chartAnimations: true,
    },
  },
  
  systemConfig: {
    api: {
      baseUrl: '/api',
      timeout: 30000,
      retryAttempts: 3,
      retryDelay: 1000,
    },
    
    websocket: {
      enabled: true,
      reconnectInterval: 5000,
      maxReconnectAttempts: 5,
    },
    
    proxy: {
      maxConcurrentChecks: 10,
      checkTimeout: 10000,
      checkInterval: 300000, // 5分鐘
      maxRetries: 3,
    },
    
    storage: {
      maxProxyAge: 7, // 7天
      cleanupInterval: 24, // 24小時
      backupInterval: 24, // 24小時
    },
  },
  
  appState: {
    isOnline: true,
    isAuthenticated: false,
    lastSyncTime: null,
    version: '1.0.0',
  },
  
  loading: false,
  error: null,
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    // 設置用戶信息
    setUser: (state, action: PayloadAction<UserState['user']>) => {
      state.user = action.payload;
      state.appState.isAuthenticated = !!action.payload;
    },
    
    // 更新用戶信息
    updateUser: (state, action: PayloadAction<Partial<NonNullable<UserState['user']>>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
    
    // 登出
    logout: (state) => {
      state.user = null;
      state.appState.isAuthenticated = false;
      state.appState.lastSyncTime = null;
    },
    
    // 更新用戶設置
    updateSettings: (state, action: PayloadAction<Partial<UserSettings>>) => {
      state.settings = { ...state.settings, ...action.payload };
    },
    
    // 更新主題
    updateTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.settings.theme = action.payload;
    },
    
    // 更新語言
    updateLanguage: (state, action: PayloadAction<'zh-TW' | 'en' | 'zh-CN'>) => {
      state.settings.language = action.payload;
    },
    
    // 更新系統配置
    updateSystemConfig: (state, action: PayloadAction<Partial<UserState['systemConfig']>>) => {
      state.systemConfig = { ...state.systemConfig, ...action.payload };
    },
    
    // 更新API配置
    updateApiConfig: (state, action: PayloadAction<Partial<UserState['systemConfig']['api']>>) => {
      state.systemConfig.api = { ...state.systemConfig.api, ...action.payload };
    },
    
    // 更新WebSocket配置
    updateWebsocketConfig: (state, action: PayloadAction<Partial<UserState['systemConfig']['websocket']>>) => {
      state.systemConfig.websocket = { ...state.systemConfig.websocket, ...action.payload };
    },
    
    // 更新代理配置
    updateProxyConfig: (state, action: PayloadAction<Partial<UserState['systemConfig']['proxy']>>) => {
      state.systemConfig.proxy = { ...state.systemConfig.proxy, ...action.payload };
    },
    
    // 更新應用狀態
    updateAppState: (state, action: PayloadAction<Partial<UserState['appState']>>) => {
      state.appState = { ...state.appState, ...action.payload };
    },
    
    // 設置在線狀態
    setOnlineStatus: (state, action: PayloadAction<boolean>) => {
      state.appState.isOnline = action.payload;
    },
    
    // 更新最後同步時間
    updateLastSyncTime: (state) => {
      state.appState.lastSyncTime = new Date().toISOString();
    },
    
    // 加載用戶設置
    loadUserSettings: (state, action: PayloadAction<Partial<UserState>>) => {
      return { ...state, ...action.payload };
    },
    
    // 重置設置
    resetSettings: (state) => {
      state.settings = initialState.settings;
    },
    
    // 重置系統配置
    resetSystemConfig: (state) => {
      state.systemConfig = initialState.systemConfig;
    },
    
    // 設置用戶設置（完全替換）
    setUserSettings: (state, action: PayloadAction<UserSettings>) => {
      state.settings = action.payload;
    },
    
    // 設置系統配置（完全替換）
    setSystemConfig: (state, action: PayloadAction<UserState['systemConfig']>) => {
      state.systemConfig = action.payload;
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
  setUser,
  updateUser,
  logout,
  updateSettings,
  updateTheme,
  updateLanguage,
  updateSystemConfig,
  updateApiConfig,
  updateWebsocketConfig,
  updateProxyConfig,
  updateAppState,
  setOnlineStatus,
  updateLastSyncTime,
  loadUserSettings,
  resetSettings,
  resetSystemConfig,
  setUserSettings,
  setSystemConfig,
  setLoading,
  setError,
} = userSlice.actions;

// 導出reducer
export default userSlice.reducer;