/**
 * 儀表板狀態管理
 * @description 管理儀表板的統計數據和圖表數據
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// 圖表數據接口
export interface ChartData {
  name: string;
  value: number;
  timestamp?: string;
  [key: string]: any;
}

// 儀表板統計數據接口
export interface DashboardStats {
  totalProxies: number;
  activeProxies: number;
  inactiveProxies: number;
  averageResponseTime: number;
  averageSuccessRate: number;
  totalSources: number;
  activeSources: number;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
}

// 系統狀態接口
export interface SystemStatus {
  isRunning: boolean;
  uptime: number;
  memoryUsage: number;
  cpuUsage: number;
  diskUsage: number;
  activeConnections: number;
  queueSize: number;
  lastUpdateTime: string;
}

interface DashboardState {
  // 統計數據
  stats: DashboardStats;
  
  // 圖表數據
  charts: {
    qualityDistribution: ChartData[];
    responseTimeTrend: ChartData[];
    successRateTrend: ChartData[];
    sourceDistribution: ChartData[];
    hourlyStats: ChartData[];
    dailyStats: ChartData[];
  };
  
  // 系統狀態
  systemStatus: SystemStatus;
  
  // 加載狀態
  loading: boolean;
  error: string | null;
  
  // 自動刷新
  autoRefresh: boolean;
  refreshInterval: number; // 秒
  
  // 時間範圍
  timeRange: '1h' | '6h' | '24h' | '7d' | '30d';
}

const initialState: DashboardState = {
  stats: {
    totalProxies: 0,
    activeProxies: 0,
    inactiveProxies: 0,
    averageResponseTime: 0,
    averageSuccessRate: 0,
    totalSources: 0,
    activeSources: 0,
    totalRequests: 0,
    successfulRequests: 0,
    failedRequests: 0,
  },
  
  charts: {
    qualityDistribution: [],
    responseTimeTrend: [],
    successRateTrend: [],
    sourceDistribution: [],
    hourlyStats: [],
    dailyStats: [],
  },
  
  systemStatus: {
    isRunning: false,
    uptime: 0,
    memoryUsage: 0,
    cpuUsage: 0,
    diskUsage: 0,
    activeConnections: 0,
    queueSize: 0,
    lastUpdateTime: new Date().toISOString(),
  },
  
  loading: false,
  error: null,
  autoRefresh: true,
  refreshInterval: 30, // 30秒
  timeRange: '24h',
};

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    // 設置統計數據
    setStats: (state, action: PayloadAction<DashboardStats>) => {
      state.stats = action.payload;
    },
    
    // 更新部分統計數據
    updateStats: (state, action: PayloadAction<Partial<DashboardStats>>) => {
      state.stats = { ...state.stats, ...action.payload };
    },
    
    // 設置圖表數據
    setChartData: (state, action: PayloadAction<{
      chartType: keyof DashboardState['charts'];
      data: ChartData[];
    }>) => {
      state.charts[action.payload.chartType] = action.payload.data;
    },
    
    // 批量設置圖表數據
    setChartsData: (state, action: PayloadAction<Partial<DashboardState['charts']>>) => {
      state.charts = { ...state.charts, ...action.payload };
    },
    
    // 設置系統狀態
    setSystemStatus: (state, action: PayloadAction<SystemStatus>) => {
      state.systemStatus = action.payload;
    },
    
    // 更新系統狀態
    updateSystemStatus: (state, action: PayloadAction<Partial<SystemStatus>>) => {
      state.systemStatus = { ...state.systemStatus, ...action.payload };
    },
    
    // 設置加載狀態
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    
    // 設置錯誤信息
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    
    // 切換自動刷新
    toggleAutoRefresh: (state) => {
      state.autoRefresh = !state.autoRefresh;
    },
    
    // 設置自動刷新
    setAutoRefresh: (state, action: PayloadAction<boolean>) => {
      state.autoRefresh = action.payload;
    },
    
    // 設置刷新間隔
    setRefreshInterval: (state, action: PayloadAction<number>) => {
      state.refreshInterval = action.payload;
    },
    
    // 設置時間範圍
    setTimeRange: (state, action: PayloadAction<DashboardState['timeRange']>) => {
      state.timeRange = action.payload;
    },
    
    // 重置到初始狀態
    resetDashboard: (state) => {
      return { ...initialState, autoRefresh: state.autoRefresh, refreshInterval: state.refreshInterval };
    },
  },
});

// 導出actions
export const {
  setStats,
  updateStats,
  setChartData,
  setChartsData,
  setSystemStatus,
  updateSystemStatus,
  setLoading,
  setError,
  toggleAutoRefresh,
  setAutoRefresh,
  setRefreshInterval,
  setTimeRange,
  resetDashboard,
} = dashboardSlice.actions;

// 導出reducer
export default dashboardSlice.reducer;