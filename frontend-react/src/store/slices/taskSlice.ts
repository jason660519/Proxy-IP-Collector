/**
 * 任務管理狀態管理
 * @description 管理系統任務的執行狀態和進度
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Task, TaskStatus } from '../../types';

interface TaskState {
  // 當前任務
  currentTask: Task | null;
  
  // 任務隊列
  taskQueue: Task[];
  
  // 歷史任務
  taskHistory: Task[];
  
  // 任務統計
  stats: {
    totalTasks: number;
    completedTasks: number;
    failedTasks: number;
    runningTasks: number;
    pendingTasks: number;
  };
  
  // 加載狀態
  loading: boolean;
  error: string | null;
  
  // 任務設置
  settings: {
    maxConcurrentTasks: number;
    retryAttempts: number;
    retryDelay: number;
    autoRetry: boolean;
    taskTimeout: number;
  };
  
  // UI狀態
  isTaskPanelOpen: boolean;
  autoRefresh: boolean;
  refreshInterval: number; // 秒
}

const initialState: TaskState = {
  currentTask: null,
  taskQueue: [],
  taskHistory: [],
  stats: {
    totalTasks: 0,
    completedTasks: 0,
    failedTasks: 0,
    runningTasks: 0,
    pendingTasks: 0,
  },
  loading: false,
  error: null,
  settings: {
    maxConcurrentTasks: 5,
    retryAttempts: 3,
    retryDelay: 5000,
    autoRetry: true,
    taskTimeout: 30000,
  },
  isTaskPanelOpen: false,
  autoRefresh: true,
  refreshInterval: 5,
};

const taskSlice = createSlice({
  name: 'task',
  initialState,
  reducers: {
    // 添加新任務到隊列
    addTask: (state, action: PayloadAction<Omit<Task, 'id' | 'createdAt' | 'updatedAt' | 'status'>>) => {
      const newTask: Task = {
        ...action.payload,
        id: Date.now().toString(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        status: 'pending',
        progress: 0,
        result: null,
        error: null,
        attempts: 0,
      };
      state.taskQueue.push(newTask);
      state.stats.totalTasks += 1;
      state.stats.pendingTasks += 1;
    },
    
    // 批量添加任務
    addTasks: (state, action: PayloadAction<Array<Omit<Task, 'id' | 'createdAt' | 'updatedAt' | 'status'>>>) => {
      const newTasks = action.payload.map(task => ({
        ...task,
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        status: 'pending' as TaskStatus,
        progress: 0,
        result: null,
        error: null,
        attempts: 0,
      }));
      state.taskQueue.push(...newTasks);
      state.stats.totalTasks += newTasks.length;
      state.stats.pendingTasks += newTasks.length;
    },
    
    // 開始執行任務
    startTask: (state, action: PayloadAction<string>) => {
      const task = state.taskQueue.find(t => t.id === action.payload);
      if (task) {
        task.status = 'running';
        task.updatedAt = new Date().toISOString();
        state.currentTask = task;
        state.stats.pendingTasks -= 1;
        state.stats.runningTasks += 1;
      }
    },
    
    // 更新任務進度
    updateTaskProgress: (state, action: PayloadAction<{ taskId: string; progress: number; message?: string }>) => {
      const { taskId, progress, message } = action.payload;
      const task = state.taskQueue.find(t => t.id === taskId);
      if (task) {
        task.progress = progress;
        if (message) {
          task.message = message;
        }
        task.updatedAt = new Date().toISOString();
        if (state.currentTask?.id === taskId) {
          state.currentTask = task;
        }
      }
    },
    
    // 完成任務
    completeTask: (state, action: PayloadAction<{ taskId: string; result?: any; message?: string }>) => {
      const { taskId, result, message } = action.payload;
      const taskIndex = state.taskQueue.findIndex(t => t.id === taskId);
      if (taskIndex !== -1) {
        const task = state.taskQueue[taskIndex];
        task.status = 'completed';
        task.progress = 100;
        task.result = result;
        if (message) {
          task.message = message;
        }
        task.updatedAt = new Date().toISOString();
        
        // 移動到歷史記錄
        state.taskHistory.unshift(task);
        state.taskQueue.splice(taskIndex, 1);
        
        // 更新統計
        state.stats.runningTasks -= 1;
        state.stats.completedTasks += 1;
        
        // 清除當前任務
        if (state.currentTask?.id === taskId) {
          state.currentTask = null;
        }
      }
    },
    
    // 任務失敗
    failTask: (state, action: PayloadAction<{ taskId: string; error: string; retry?: boolean }>) => {
      const { taskId, error, retry } = action.payload;
      const taskIndex = state.taskQueue.findIndex(t => t.id === taskId);
      if (taskIndex !== -1) {
        const task = state.taskQueue[taskIndex];
        task.status = 'failed';
        task.error = error;
        task.attempts = (task.attempts || 0) + 1;
        task.updatedAt = new Date().toISOString();
        
        if (!retry || (task.attempts || 0) >= state.settings.retryAttempts) {
          // 移動到歷史記錄
          state.taskHistory.unshift(task);
          state.taskQueue.splice(taskIndex, 1);
          
          // 更新統計
          state.stats.runningTasks -= 1;
          state.stats.failedTasks += 1;
          
          // 清除當前任務
          if (state.currentTask?.id === taskId) {
            state.currentTask = null;
          }
        } else {
          // 重試任務
          task.status = 'pending';
          task.progress = 0;
        }
      }
    },
    
    // 取消任務
    cancelTask: (state, action: PayloadAction<string>) => {
      const taskIndex = state.taskQueue.findIndex(t => t.id === action.payload);
      if (taskIndex !== -1) {
        const task = state.taskQueue[taskIndex];
        const originalStatus = task.status; // 保存原始狀態
        task.status = 'cancelled';
        task.updatedAt = new Date().toISOString();
        
        // 移動到歷史記錄
        state.taskHistory.unshift(task);
        state.taskQueue.splice(taskIndex, 1);
        
        // 更新統計
        if (originalStatus === 'running') {
          state.stats.runningTasks -= 1;
        } else if (originalStatus === 'pending') {
          state.stats.pendingTasks -= 1;
        }
        
        // 清除當前任務
        if (state.currentTask?.id === action.payload) {
          state.currentTask = null;
        }
      }
    },
    
    // 清除已完成/失敗的任務
    clearCompletedTasks: (state) => {
      state.taskHistory = state.taskHistory.filter(
        task => task.status !== 'completed' && task.status !== 'failed' && task.status !== 'cancelled'
      );
    },
    
    // 更新任務設置
    updateTaskSettings: (state, action: PayloadAction<Partial<TaskState['settings']>>) => {
      state.settings = { ...state.settings, ...action.payload };
    },
    
    // 切換任務面板
    toggleTaskPanel: (state) => {
      state.isTaskPanelOpen = !state.isTaskPanelOpen;
    },
    
    // 設置任務面板狀態
    setTaskPanelOpen: (state, action: PayloadAction<boolean>) => {
      state.isTaskPanelOpen = action.payload;
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
  addTask,
  addTasks,
  startTask,
  updateTaskProgress,
  completeTask,
  failTask,
  cancelTask,
  clearCompletedTasks,
  updateTaskSettings,
  toggleTaskPanel,
  setTaskPanelOpen,
  toggleAutoRefresh,
  setAutoRefresh,
  setRefreshInterval,
  setLoading,
  setError,
} = taskSlice.actions;

// 導出reducer
export default taskSlice.reducer;