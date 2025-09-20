import React, { useState, useEffect } from 'react';
import { useAppDispatch } from '../../hooks';
import { useDocumentTitle } from '../../hooks';
import { TaskForm, TaskList, Card, Button, TaskCharts, TaskStats, TaskFilter, TaskDashboard } from '../../components';
import { proxyApi } from '../../services/proxyApi';
import websocket, { WebSocketMessageType } from '../../services/websocket';
import type { Task, TaskStatus, TaskType, CreateTaskRequest } from '../../services/proxyApi';
import type { TaskStatus as FilterTaskStatus, TaskType as FilterTaskType } from '../../components/TaskFilter';
import './TasksPage.css';

/**
 * 任務管理頁面組件
 * 提供任務的創建、管理、監控等功能
 */
const TasksPage: React.FC = () => {
  useDocumentTitle('任務管理');
  const dispatch = useAppDispatch();
  
  // 本地狀態管理
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [filterStatus, setFilterStatus] = useState<FilterTaskStatus>('all');
  const [filterType, setFilterType] = useState<FilterTaskType>('all');
  const [searchText, setSearchText] = useState('');

  // 獲取任務數據
  const { data: tasksData, refetch, isLoading } = proxyApi.endpoints.getTasks.useQuery({}, {
    refetchOnMountOrArgChange: true,
    refetchOnFocus: true,
  });

  // 篩選後的任務數據
  const filteredTasks = React.useMemo(() => {
    if (!tasksData) return [];
    
    return tasksData.filter((task: Task) => {
      const matchesSearch = !searchText || 
        task.name.toLowerCase().includes(searchText.toLowerCase()) ||
        task.description?.toLowerCase().includes(searchText.toLowerCase());
      
      const matchesStatus = filterStatus === 'all' || task.status === filterStatus as TaskStatus;
      const matchesType = filterType === 'all' || task.type === filterType as TaskType;
      
      return matchesSearch && matchesStatus && matchesType;
    });
  }, [tasksData, searchText, filterStatus, filterType]);

  // 統計數據
  const statistics = React.useMemo(() => {
    const total = filteredTasks.length;
    const running = filteredTasks.filter((t: Task) => t.status === 'running').length;
    const completed = filteredTasks.filter((t: Task) => t.status === 'completed').length;
    const failed = filteredTasks.filter((t: Task) => t.status === 'failed').length;
    const pending = filteredTasks.filter((t: Task) => t.status === 'pending').length;
    
    return { total, running, completed, failed, pending };
  }, [filteredTasks]);

  // WebSocket 連接和實時更新
  useEffect(() => {
    const handleTaskUpdate = (data: any) => {
      if (data.type === 'task_update') {
        refetch();
      }
    };

    websocket.registerHandler(WebSocketMessageType.TASK_PROGRESS, handleTaskUpdate);
    websocket.registerHandler(WebSocketMessageType.TASK_COMPLETED, handleTaskUpdate);
    websocket.registerHandler(WebSocketMessageType.TASK_FAILED, handleTaskUpdate);
    
    return () => {
      websocket.unregisterHandler(WebSocketMessageType.TASK_PROGRESS, handleTaskUpdate);
      websocket.unregisterHandler(WebSocketMessageType.TASK_COMPLETED, handleTaskUpdate);
      websocket.unregisterHandler(WebSocketMessageType.TASK_FAILED, handleTaskUpdate);
    };
  }, [refetch]);

  // 處理任務操作
  const handleTaskAction = async (action: string, taskId: string) => {
    try {
      switch (action) {
        case 'start':
          await dispatch(proxyApi.endpoints.startTask.initiate(taskId));
          break;
        case 'stop':
          await dispatch(proxyApi.endpoints.cancelTask.initiate(taskId));
          break;
        case 'delete':
          if (confirm('確定要刪除這個任務嗎？')) {
            await dispatch(proxyApi.endpoints.deleteTask.initiate(taskId));
          }
          break;
        case 'rerun':
          await dispatch(proxyApi.endpoints.rerunTask.initiate(taskId));
          break;
        default:
          break;
      }
      refetch();
    } catch (error) {
      console.error('任務操作失敗:', error);
    }
  };

  // 處理任務表單提交
  const handleTaskSubmit = async (taskData: Partial<Task>) => {
    try {
      if (editingTask) {
        // 更新任務
        await dispatch(proxyApi.endpoints.updateTask.initiate({
          id: editingTask.id,
          ...taskData
        } as any));
      } else {
        // 創建新任務 - 確保有必需的 name 屬性
        const createTaskData: CreateTaskRequest = {
          name: taskData.name || '新任務',
          type: taskData.type || 'proxy_test',
          description: taskData.description || '',
          config: taskData.config || {},
          schedule: taskData.schedule || undefined,
        };
        await dispatch(proxyApi.endpoints.createTask.initiate(createTaskData));
      }
      
      setShowForm(false);
      setEditingTask(null);
      refetch();
    } catch (error) {
      console.error('保存任務失敗:', error);
    }
  };

  // 處理編輯任務
  const handleEditTask = (task: Task | undefined) => {
    if (task) {
      setEditingTask(task);
      setShowForm(true);
    }
  };

  // 取消表單
  const handleCancelForm = () => {
    setShowForm(false);
    setEditingTask(null);
  };

  return (
    <div className="tasks-page">
      <div className="tasks-header">
        <h1>任務管理</h1>
        <div className="tasks-actions">
          <Button
            type="primary"
            onClick={() => setShowForm(true)}
          >
            新建任務
          </Button>
        </div>
      </div>

      {/* 任務儀表板 */}
      <TaskDashboard tasks={filteredTasks} loading={isLoading} />

      {/* 統計卡片 */}
      <TaskStats stats={statistics} loading={isLoading} />

      {/* 圖表可視化 */}
      <TaskCharts tasks={filteredTasks} loading={isLoading} />

      {/* 篩選器 */}
      <TaskFilter
        searchText={searchText}
        filterStatus={filterStatus}
        filterType={filterType}
        onSearchChange={setSearchText}
        onStatusChange={setFilterStatus}
        onTypeChange={setFilterType}
        loading={isLoading}
      />

      {/* 任務列表 */}
      <TaskList
        tasks={filteredTasks}
        loading={isLoading}
        onStartTask={(taskId) => handleTaskAction('start', taskId)}
        onStopTask={(taskId) => handleTaskAction('stop', taskId)}
        onDeleteTask={(taskId) => handleTaskAction('delete', taskId)}
        onEditTask={handleEditTask}
      />

      {/* 任務表單模態框 */}
      {showForm && (
        <div className="task-form-modal">
          <div className="task-form-backdrop" onClick={handleCancelForm} />
          <div className="task-form-container">
            <Card className="task-form-card">
              <div className="task-form-header">
                <h2>{editingTask ? '編輯任務' : '新建任務'}</h2>
                <button
                  className="close-button"
                  onClick={handleCancelForm}
                >
                  ×
                </button>
              </div>
              <TaskForm
                task={editingTask || undefined}
                onSubmit={handleTaskSubmit}
                onCancel={handleCancelForm}
              />
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default TasksPage;