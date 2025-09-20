/**
 * API服務配置
 * @description 使用RTK Query創建API服務，管理代理相關的API請求
 */

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { 
  Proxy, 
  ProxyFilter, 
  PaginatedResponse, 
  DashboardStats, 
  ChartData, 
  SystemStatus,
  Task,
  TaskType,
  TaskStatus,
  CreateTaskRequest
} from '@/types/proxy.types';
import { RootState } from '@/store';

/**
 * 代理API服務
 * @description 提供代理相關的API端點
 */
export const proxyApi = createApi({
  reducerPath: 'proxyApi',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api',
    prepareHeaders: (headers, { getState }) => {
      // 從store獲取用戶token
      const token = (getState() as RootState).user.user?.id;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  
  tagTypes: ['Proxy', 'Dashboard', 'Task', 'Stats', 'Logs'],
  
  endpoints: (builder) => ({
    // 代理相關端點
    
    /**
     * 獲取代理列表
     */
    getProxies: builder.query<PaginatedResponse<Proxy>, {
      page?: number;
      pageSize?: number;
      filters?: ProxyFilter;
      sortBy?: string;
      sortOrder?: 'asc' | 'desc';
    }>({
      query: (params) => ({
        url: '/proxies',
        params: {
          page: params.page || 1,
          pageSize: params.pageSize || 20,
          ...params.filters,
          sortBy: params.sortBy,
          sortOrder: params.sortOrder,
        },
      }),
      providesTags: (result) => 
        result ? 
          [
            ...result.data.map(({ id }) => ({ type: 'Proxy' as const, id })),
            { type: 'Proxy', id: 'LIST' },
          ] : 
          [{ type: 'Proxy', id: 'LIST' }],
    }),
    
    /**
     * 獲取單個代理
     */
    getProxy: builder.query<Proxy, string>({
      query: (id) => `/proxies/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Proxy', id }],
    }),
    
    /**
     * 創建代理
     */
    createProxy: builder.mutation<Proxy, Partial<Proxy>>({
      query: (proxy) => ({
        url: '/proxies',
        method: 'POST',
        body: proxy,
      }),
      invalidatesTags: [{ type: 'Proxy', id: 'LIST' }],
    }),
    
    /**
     * 更新代理
     */
    updateProxy: builder.mutation<Proxy, { id: string; data: Partial<Proxy> }>({
      query: ({ id, data }) => ({
        url: `/proxies/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (_result, _error, { id }) => [{ type: 'Proxy', id }],
    }),
    
    /**
     * 刪除代理
     */
    deleteProxy: builder.mutation<void, string>({
      query: (id) => ({
        url: `/proxies/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: [{ type: 'Proxy', id: 'LIST' }],
    }),
    
    /**
     * 批量刪除代理
     */
    deleteProxies: builder.mutation<void, string[]>({
      query: (ids) => ({
        url: '/proxies/batch',
        method: 'DELETE',
        body: { ids },
      }),
      invalidatesTags: [{ type: 'Proxy', id: 'LIST' }],
    }),
    
    /**
     * 驗證代理
     */
    validateProxy: builder.mutation<Proxy, string>({
      query: (id) => ({
        url: `/proxies/${id}/validate`,
        method: 'POST',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Proxy', id }],
    }),
    
    /**
     * 批量驗證代理
     */
    validateProxies: builder.mutation<Task, string[]>({
      query: (ids) => ({
        url: '/proxies/validate-batch',
        method: 'POST',
        body: { ids },
      }),
      invalidatesTags: [{ type: 'Task', id: 'LIST' }],
    }),
    
    /**
     * 導出代理
     */
    exportProxies: builder.mutation<Blob, {
      format: 'csv' | 'json' | 'txt';
      filters?: ProxyFilter;
      ids?: string[];
    }>({
      query: (params) => ({
        url: '/proxies/export',
        method: 'POST',
        body: params,
        responseHandler: (response) => response.blob(),
      }),
    }),
    
    /**
     * 導入代理
     */
    importProxies: builder.mutation<{
      success: number;
      failed: number;
      errors: string[];
    }, FormData>({
      query: (formData) => ({
        url: '/proxies/import',
        method: 'POST',
        body: formData,
      }),
      invalidatesTags: [{ type: 'Proxy', id: 'LIST' }],
    }),
    
    // 儀表板相關端點
    
    /**
     * 獲取儀表板統計數據
     */
    getDashboardStats: builder.query<DashboardStats, void>({
      query: () => '/dashboard/stats',
      providesTags: ['Stats'],
    }),
    
    /**
     * 獲取圖表數據
     */
    getChartData: builder.query<{
      qualityDistribution: ChartData[];
      responseTimeTrend: ChartData[];
      successRateTrend: ChartData[];
      sourceDistribution: ChartData[];
      hourlyStats: ChartData[];
      dailyStats: ChartData[];
    }, { timeRange: string }>({
      query: (params) => ({
        url: '/dashboard/charts',
        params,
      }),
      providesTags: ['Dashboard'],
    }),
    
    /**
     * 獲取系統狀態
     */
    getSystemStatus: builder.query<SystemStatus, void>({
      query: () => '/dashboard/system-status',
      providesTags: ['Dashboard'],
    }),
    
    // 任務相關端點
    
    /**
     * 獲取任務列表
     */
    getTasks: builder.query<Task[], { status?: TaskStatus; type?: TaskType }>({
      query: (params) => ({
        url: '/tasks',
        params,
      }),
      providesTags: ['Task'],
    }),
    
    /**
     * 創建任務
     */
    createTask: builder.mutation<Task, CreateTaskRequest>({
      query: (task) => ({
        url: '/tasks',
        method: 'POST',
        body: task,
      }),
      invalidatesTags: [{ type: 'Task', id: 'LIST' }],
    }),
    
    /**
     * 獲取任務詳情
     */
    getTask: builder.query<Task, string>({
      query: (id) => `/tasks/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Task', id }],
    }),
    
    /**
     * 取消任務
     */
    cancelTask: builder.mutation<void, string>({
      query: (id) => ({
        url: `/tasks/${id}/cancel`,
        method: 'POST',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Task', id }],
    }),
    
    /**
     * 重新運行任務
     */
    rerunTask: builder.mutation<Task, string>({
      query: (id) => ({
        url: `/tasks/${id}/rerun`,
        method: 'POST',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Task', id }],
    }),
    
    /**
     * 刪除任務
     */
    deleteTask: builder.mutation<void, string>({
      query: (id) => ({
        url: `/tasks/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Task', id }],
    }),

    /**
     * 開始任務
     */
    startTask: builder.mutation<Task, string>({
      query: (id) => ({
        url: `/tasks/${id}/start`,
        method: 'POST',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Task', id }],
    }),

    /**
     * 更新任務
     */
    updateTask: builder.mutation<Task, { id: string; [key: string]: any }>({
      query: ({ id, ...updates }) => ({
        url: `/tasks/${id}`,
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: (_result, _error, { id }) => [{ type: 'Task', id }],
    }),

    // 日誌相關端點
    
    /**
     * 獲取日誌列表
     */
    getLogs: builder.query<any[], {
      level?: string;
      service?: string;
      dateRange?: string;
      search?: string;
      page?: number;
      pageSize?: number;
    }>({
      query: (params) => ({
        url: '/logs',
        params,
      }),
      providesTags: ['Logs'],
    }),
    
    /**
     * 清除日誌
     */
    clearLogs: builder.mutation<void, void>({
      query: () => ({
        url: '/logs',
        method: 'DELETE',
      }),
      invalidatesTags: ['Logs'],
    }),
  }),
});

// 導出自定義hook
export const {
  // 代理相關
  useGetProxiesQuery,
  useGetProxyQuery,
  useCreateProxyMutation,
  useUpdateProxyMutation,
  useDeleteProxyMutation,
  useDeleteProxiesMutation,
  useValidateProxyMutation,
  useValidateProxiesMutation,
  useExportProxiesMutation,
  useImportProxiesMutation,
  
  // 儀表板相關
  useGetDashboardStatsQuery,
  useGetChartDataQuery,
  useGetSystemStatusQuery,
  
  // 任務相關
  useGetTasksQuery,
  useCreateTaskMutation,
  useGetTaskQuery,
  useCancelTaskMutation,
  useRerunTaskMutation,
  useDeleteTaskMutation,
  useStartTaskMutation,
  useUpdateTaskMutation,
  
  // 日誌相關
  useGetLogsQuery,
  useClearLogsMutation,
} = proxyApi;

// 導出API實例
export default proxyApi;

// 重新導出類型供其他組件使用
export type { Task, TaskStatus, TaskType, CreateTaskRequest } from '@/types/proxy.types';