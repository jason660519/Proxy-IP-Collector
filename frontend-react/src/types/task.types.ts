/**
 * 任務相關類型定義
 */

/**
 * 任務狀態枚舉
 */
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused';

/**
 * 任務類型枚舉
 */
export type TaskType = 'health_check' | 'proxy_test' | 'data_collection' | 'system_maintenance' | 'custom';

/**
 * 任務代理信息接口
 */
export interface TaskProxy {
  id: string;
  ip: string;
  port: number;
  protocol: string;
  status: 'active' | 'inactive' | 'error';
  responseTime?: number;
  location?: string;
  anonymity?: string;
  lastChecked?: string;
}

/**
 * 任務接口
 */
export interface Task {
  id: string;
  name: string;
  description?: string;
  type: TaskType;
  status: TaskStatus;
  proxyList?: TaskProxy[];
  createdAt: string;
  updatedAt: string;
  startedAt?: string;
  completedAt?: string;
  progress?: number;
  errorCount?: number;
  successCount?: number;
  totalCount?: number;
  config?: Record<string, any>;
  schedule?: string;
  priority?: number;
  message?: string;
  result?: any;
  error?: string | null;
  attempts?: number;
}