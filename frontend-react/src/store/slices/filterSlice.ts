/**
 * 篩選條件狀態管理
 * @description 管理代理列表的篩選條件和排序設置
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// 代理篩選條件接口
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

// 排序配置接口
export interface SortConfig {
  field: string;
  order: 'asc' | 'desc';
}

interface FilterState {
  // 當前篩選條件
  filters: ProxyFilter;
  
  // 排序配置
  sortConfig: SortConfig;
  
  // 保存的篩選模板
  savedFilters: Array<{
    id: string;
    name: string;
    filters: ProxyFilter;
    createdAt: string;
  }>;
  
  // 快速篩選選項
  quickFilters: Array<{
    id: string;
    name: string;
    icon: string;
    filters: Partial<ProxyFilter>;
  }>;
  
  // UI狀態
  isFilterPanelOpen: boolean;
  isAdvancedMode: boolean;
}

const initialState: FilterState = {
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
  
  sortConfig: {
    field: 'qualityScore',
    order: 'desc',
  },
  
  savedFilters: [],
  
  quickFilters: [
    {
      id: 'high-quality',
      name: '高品質代理',
      icon: '⭐',
      filters: {
        minQualityScore: 80,
        minSuccessRate: 90,
        maxResponseTime: 2000,
      },
    },
    {
      id: 'fast-proxies',
      name: '快速代理',
      icon: '⚡',
      filters: {
        maxResponseTime: 1000,
        status: ['active'],
      },
    },
    {
      id: 'elite-proxies',
      name: '高匿代理',
      icon: '🥷',
      filters: {
        anonymity: ['elite'],
        status: ['active'],
      },
    },
    {
      id: 'recently-added',
      name: '最近添加',
      icon: '🆕',
      filters: {
        status: ['active'],
      },
    },
  ],
  
  isFilterPanelOpen: false,
  isAdvancedMode: false,
};

const filterSlice = createSlice({
  name: 'filter',
  initialState,
  reducers: {
    // 更新篩選條件
    setFilters: (state, action: PayloadAction<ProxyFilter>) => {
      state.filters = action.payload;
    },
    
    // 更新部分篩選條件
    updateFilters: (state, action: PayloadAction<Partial<ProxyFilter>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    
    // 重置篩選條件
    resetFilters: (state) => {
      state.filters = initialState.filters;
    },
    
    // 更新排序配置
    setSortConfig: (state, action: PayloadAction<SortConfig>) => {
      state.sortConfig = action.payload;
    },
    
    // 更新排序字段
    updateSortField: (state, action: PayloadAction<SortConfig['field']>) => {
      state.sortConfig.field = action.payload;
    },
    
    // 切換排序順序
    toggleSortOrder: (state) => {
      state.sortConfig.order = state.sortConfig.order === 'asc' ? 'desc' : 'asc';
    },
    
    // 保存篩選模板
    saveFilterTemplate: (state, action: PayloadAction<{ name: string; filters: ProxyFilter }>) => {
      const template = {
        id: Date.now().toString(),
        name: action.payload.name,
        filters: action.payload.filters,
        createdAt: new Date().toISOString(),
      };
      state.savedFilters.push(template);
    },
    
    // 刪除篩選模板
    removeFilterTemplate: (state, action: PayloadAction<string>) => {
      state.savedFilters = state.savedFilters.filter(template => template.id !== action.payload);
    },
    
    // 應用篩選模板
    applyFilterTemplate: (state, action: PayloadAction<string>) => {
      const template = state.savedFilters.find(t => t.id === action.payload);
      if (template) {
        state.filters = template.filters;
      }
    },
    
    // 應用快速篩選
    applyQuickFilter: (state, action: PayloadAction<string>) => {
      const quickFilter = state.quickFilters.find(f => f.id === action.payload);
      if (quickFilter) {
        state.filters = { ...state.filters, ...quickFilter.filters };
      }
    },
    
    // 切換篩選面板
    toggleFilterPanel: (state) => {
      state.isFilterPanelOpen = !state.isFilterPanelOpen;
    },
    
    // 設置篩選面板狀態
    setFilterPanelOpen: (state, action: PayloadAction<boolean>) => {
      state.isFilterPanelOpen = action.payload;
    },
    
    // 切換高級模式
    toggleAdvancedMode: (state) => {
      state.isAdvancedMode = !state.isAdvancedMode;
    },
    
    // 設置高級模式
    setAdvancedMode: (state, action: PayloadAction<boolean>) => {
      state.isAdvancedMode = action.payload;
    },
  },
});

// 導出actions
export const {
  setFilters,
  updateFilters,
  resetFilters,
  setSortConfig,
  updateSortField,
  toggleSortOrder,
  saveFilterTemplate,
  removeFilterTemplate,
  applyFilterTemplate,
  applyQuickFilter,
  toggleFilterPanel,
  setFilterPanelOpen,
  toggleAdvancedMode,
  setAdvancedMode,
} = filterSlice.actions;

// 導出reducer
export default filterSlice.reducer;