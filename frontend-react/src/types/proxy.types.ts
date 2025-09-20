/**
 * 代理IP類型定義
 * @description 定義代理IP的數據結構和相關類型
 */

/**
 * 代理IP協議類型
 */
export type ProxyProtocol = 'http' | 'https' | 'socks4' | 'socks5';

/**
 * 匿名度等級
 */
export type AnonymityLevel = 'transparent' | 'anonymous' | 'elite';

/**
 * 代理IP狀態
 */
export type ProxyStatus = 'active' | 'inactive' | 'checking' | 'failed';

/**
 * 代理IP來源網站
 */
export type ProxySource = 
  | '89ip.cn'
  | 'kuaidaili.com'
  | 'proxylist.geonode.com'
  | 'proxydb.net'
  | 'proxynova.com'
  | 'spys.one'
  | 'free-proxy-list.net'
  | 'manual';

/**
 * 代理IP基礎接口
 */
export interface Proxy {
  id: string;
  ip: string;
  port: number;
  protocol: ProxyProtocol;
  country: string;
  countryCode: string;
  anonymity: AnonymityLevel;
  status: ProxyStatus;
  responseTime: number; // 毫秒
  successRate: number; // 0-1 之間的小數
  lastChecked: string; // ISO 8601 格式
  lastSuccess: string; // ISO 8601 格式
  source: ProxySource;
  qualityScore: number; // 0-1 之間的質量評分
  uptime: number; // 正常運行時間百分比
  totalRequests: number; // 總請求數
  successfulRequests: number; // 成功請求數
  createdAt: string; // 創建時間
  updatedAt: string; // 更新時間
  // 額外屬性，用於UI顯示
  type?: string; // 代理類型（http/https/socks4/socks5）
  location?: {
    country: string;
    city: string;
    flag?: string;
  }; // 位置信息
  usageCount?: number; // 使用次數
  tags?: string[]; // 標籤
  isActive?: boolean; // 是否活動
  isRotating?: boolean; // 是否輪換中
}

/**
 * 代理IP篩選條件
 */
export interface ProxyFilter {
  protocol?: ProxyProtocol[];
  country?: string[];
  anonymity?: AnonymityLevel[];
  status?: ProxyStatus[];
  source?: ProxySource[];
  minQualityScore?: number;
  maxResponseTime?: number;
  minSuccessRate?: number;
  searchText?: string;
  dateRange?: {
    start: string;
    end: string;
  };
}

/**
 * 分頁參數
 */
export interface PaginationParams {
  page: number;
  pageSize: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

/**
 * API響應分頁數據
 */
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

/**
 * 代理IP統計數據
 */
export interface ProxyStats {
  totalProxies: number;
  activeProxies: number;
  inactiveProxies: number;
  checkingProxies: number;
  averageResponseTime: number;
  averageSuccessRate: number;
  averageQualityScore: number;
  protocolDistribution: Record<ProxyProtocol, number>;
  anonymityDistribution: Record<AnonymityLevel, number>;
  countryDistribution: Record<string, number>;
  sourceDistribution: Record<ProxySource, number>;
  dailyStats: DailyStats[];
}

/**
 * 儀表板統計數據（別名，與 ProxyStats 相同）
 */
export type DashboardStats = ProxyStats;

/**
 * 每日統計數據
 */
export interface DailyStats {
  date: string;
  totalProxies: number;
  activeProxies: number;
  newProxies: number;
  failedProxies: number;
  averageResponseTime: number;
  averageSuccessRate: number;
}

/**
 * 圖表數據接口
 */
export interface ChartData {
  name: string;
  value: number;
  color?: string;
}

/**
 * 系統狀態接口
 */
export interface SystemStatus {
  isRunning: boolean;
  uptime: number;
  memoryUsage: number;
  cpuUsage: number;
  activeConnections: number;
  totalRequests: number;
  errorRate: number;
}



/**
 * 系統任務類型（代理系統專用）
 */
export type SystemTaskType = 'fetch' | 'validate' | 'cleanup' | 'export' | 'import';

// 導入任務相關類型
import type { TaskStatus, TaskType } from './task.types';

// 重新導出任務相關類型
export type { TaskStatus, TaskType } from './task.types';
export type { Task } from './task.types';

/**
 * 創建任務請求接口
 */
export interface CreateTaskRequest {
  name: string;
  description?: string;
  type: TaskType;
  config?: Record<string, any>;
  schedule?: string;
  priority?: number;
}

/**
 * 系統任務
 */
export interface SystemTask {
  id: string;
  type: SystemTaskType;
  status: TaskStatus;
  name: string;
  description: string;
  progress: number; // 0-100
  totalItems?: number;
  processedItems?: number;
  startedAt?: string;
  completedAt?: string;
  estimatedTime?: number; // 預估剩餘時間（秒）
  error?: string;
  createdAt: string;
}

/**
 * 通知類型
 */
export type NotificationType = 'info' | 'success' | 'warning' | 'error';

/**
 * 圖表數據
 */
export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }[];
}

/**
 * 系統狀態
 */
export interface SystemStatus {
  isOnline: boolean;
  version: string;
  uptime: number;
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  cpu: {
    usage: number;
    cores: number;
  };
  disk: {
    used: number;
    total: number;
    percentage: number;
  };
  lastBackup: string;
  activeConnections: number;
}
export interface SystemNotification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
  actions?: NotificationAction[];
}

/**
 * 通知操作
 */
export interface NotificationAction {
  label: string;
  action: string;
  type?: 'primary' | 'default' | 'danger';
}

/**
 * 用戶設置
 */
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
    refreshInterval: number; // 秒
    defaultTimeRange: string;
    showCharts: boolean;
    chartAnimations: boolean;
  };
}