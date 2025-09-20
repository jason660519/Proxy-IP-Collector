/**
 * 代理IP狀態管理
 * @description 管理代理IP的狀態，包括列表、詳情、加載狀態等
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// 代理接口
export interface Proxy {
  id: string;
  ip: string;
  port: number;
  type: string;
  protocol: string;
  country: string;
  city: string;
  location: {
    country: string;
    city: string;
  };
  anonymity: string;
  status: string;
  qualityScore: number;
  responseTime: number;
  successRate: number;
  lastChecked: string;
  source: string;
  createdAt: string;
  updatedAt: string;
}

// 代理篩選條件接口（從 filterSlice.ts 導入）
export interface ProxyFilter {
  protocol: string[];
  country: string[];
  anonymity: string[];
  status: string[];
  source: string[];
  minQualityScore: number;
  maxResponseTime: number;
  minSuccessRate: number;
  searchText: string;
}

// 分頁參數接口
export interface PaginationParams {
  page: number;
  pageSize: number;
}

// 分頁響應接口
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

interface ProxyState {
  // 代理列表
  proxies: Proxy[];
  totalCount: number;
  
  // 分頁信息
  pagination: {
    page: number;
    pageSize: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
  
  // 篩選條件
  filters: ProxyFilter;
  
  // 加載狀態
  loading: boolean;
  error: string | null;
  
  // 選中的代理
  selectedProxies: string[];
  
  // 當前查看的代理詳情
  currentProxy: Proxy | null;
  
  // 批量操作狀態
  batchOperation: {
    type: 'delete' | 'validate' | 'export' | null;
    progress: number;
    processing: boolean;
  };
}

const initialState: ProxyState = {
  proxies: [],
  totalCount: 0,
  pagination: {
    page: 1,
    pageSize: 20,
    totalPages: 0,
    hasNext: false,
    hasPrev: false,
  },
  filters: {
    protocol: [],
    country: [],
    anonymity: [],
    status: ['active'],
    source: [],
    minQualityScore: 0,
    maxResponseTime: 10000,
    minSuccessRate: 0,
    searchText: '',
  },
  loading: false,
  error: null,
  selectedProxies: [],
  currentProxy: null,
  batchOperation: {
    type: null,
    progress: 0,
    processing: false,
  },
};

const proxySlice = createSlice({
  name: 'proxy',
  initialState,
  reducers: {
    // 設置代理列表
    setProxies: (state, action: PayloadAction<PaginatedResponse<Proxy>>) => {
      state.proxies = action.payload.data;
      state.totalCount = action.payload.total;
      state.pagination = {
        page: action.payload.page,
        pageSize: action.payload.pageSize,
        totalPages: action.payload.totalPages,
        hasNext: action.payload.hasNext,
        hasPrev: action.payload.hasPrev,
      };
    },
    
    // 添加單個代理
    addProxy: (state, action: PayloadAction<Proxy>) => {
      state.proxies.unshift(action.payload);
      state.totalCount += 1;
    },
    
    // 更新代理
    updateProxy: (state, action: PayloadAction<Proxy>) => {
      const index = state.proxies.findIndex(proxy => proxy.id === action.payload.id);
      if (index !== -1) {
        state.proxies[index] = action.payload;
      }
      if (state.currentProxy?.id === action.payload.id) {
        state.currentProxy = action.payload;
      }
    },
    
    // 刪除代理
    removeProxy: (state, action: PayloadAction<string>) => {
      state.proxies = state.proxies.filter(proxy => proxy.id !== action.payload);
      state.totalCount -= 1;
      state.selectedProxies = state.selectedProxies.filter(id => id !== action.payload);
      if (state.currentProxy?.id === action.payload) {
        state.currentProxy = null;
      }
    },
    
    // 批量刪除
    removeProxies: (state, action: PayloadAction<string[]>) => {
      state.proxies = state.proxies.filter(proxy => !action.payload.includes(proxy.id));
      state.totalCount -= action.payload.length;
      state.selectedProxies = state.selectedProxies.filter(id => !action.payload.includes(id));
      if (state.currentProxy && action.payload.includes(state.currentProxy.id)) {
        state.currentProxy = null;
      }
    },
    
    // 更新篩選條件
    updateFilters: (state, action: PayloadAction<Partial<ProxyFilter>>) => {
      state.filters = { ...state.filters, ...action.payload };
      state.pagination.page = 1; // 重置到第一頁
    },
    
    // 重置篩選條件
    resetFilters: (state) => {
      state.filters = initialState.filters;
      state.pagination.page = 1;
    },
    
    // 更新分頁
    updatePagination: (state, action: PayloadAction<Partial<PaginationParams>>) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    
    // 選擇/取消選擇代理
    toggleProxySelection: (state, action: PayloadAction<string>) => {
      const index = state.selectedProxies.indexOf(action.payload);
      if (index === -1) {
        state.selectedProxies.push(action.payload);
      } else {
        state.selectedProxies.splice(index, 1);
      }
    },
    
    // 全選/取消全選
    toggleAllProxies: (state, action: PayloadAction<boolean>) => {
      if (action.payload) {
        state.selectedProxies = state.proxies.map(proxy => proxy.id);
      } else {
        state.selectedProxies = [];
      }
    },
    
    // 設置當前代理
    setCurrentProxy: (state, action: PayloadAction<Proxy | null>) => {
      state.currentProxy = action.payload;
    },
    
    // 設置加載狀態
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    
    // 設置錯誤信息
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    
    // 更新批量操作狀態
    setBatchOperation: (state, action: PayloadAction<Partial<ProxyState['batchOperation']>>) => {
      state.batchOperation = { ...state.batchOperation, ...action.payload };
    },
    
    // 重置批量操作
    resetBatchOperation: (state) => {
      state.batchOperation = initialState.batchOperation;
    },
  },
});

// 導出actions
export const {
  setProxies,
  addProxy,
  updateProxy,
  removeProxy,
  removeProxies,
  updateFilters,
  resetFilters,
  updatePagination,
  toggleProxySelection,
  toggleAllProxies,
  setCurrentProxy,
  setLoading,
  setError,
  setBatchOperation,
  resetBatchOperation,
} = proxySlice.actions;

// 導出reducer
export default proxySlice.reducer;