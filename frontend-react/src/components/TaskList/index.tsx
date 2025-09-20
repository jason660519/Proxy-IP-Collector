import React, { useState } from 'react';
import { Button, Card } from '../index';
import { Task, TaskStatus } from '../../types/task.types';
import './TaskList.css';

export interface TaskListProps {
  /**
   * 任務列表
   */
  tasks: Task[];
  /**
   * 是否加載中
   */
  loading?: boolean;
  /**
   * 任務點擊事件
   */
  onTaskClick?: (task: Task) => void;
  /**
   * 開始任務事件
   */
  onStartTask?: (taskId: string) => void;
  /**
   * 停止任務事件
   */
  onStopTask?: (taskId: string) => void;
  /**
   * 刪除任務事件
   */
  onDeleteTask?: (taskId: string) => void;
  /**
   * 編輯任務事件
   */
  onEditTask?: (task: Task) => void;
  /**
   * 自定義類名
   */
  className?: string;
  /**
   * 空狀態自定義內容
   */
  emptyText?: string;
}

/**
 * 任務狀態標籤組件
 */
const TaskStatusTag: React.FC<{ status: TaskStatus }> = ({ status }) => {
  const statusConfig = {
    pending: { text: '待執行', className: 'status-pending' },
    running: { text: '運行中', className: 'status-running' },
    completed: { text: '已完成', className: 'status-completed' },
    failed: { text: '失敗', className: 'status-failed' },
    cancelled: { text: '已取消', className: 'status-cancelled' },
    paused: { text: '已暫停', className: 'status-paused' },
  };

  const config = statusConfig[status] || statusConfig.pending;

  return <span className={`status-tag ${config.className}`}>{config.text}</span>;
};

/**
 * 任務類型標籤組件
 */
const TaskTypeTag: React.FC<{ type: string }> = ({ type }) => {
  const typeConfig = {
    proxy_collection: { text: '代理收集', className: 'type-collection' },
    proxy_validation: { text: '代理驗證', className: 'type-validation' },
    data_export: { text: '數據導出', className: 'type-export' },
    system_maintenance: { text: '系統維護', className: 'type-maintenance' },
  };

  const config = typeConfig[type as keyof typeof typeConfig] || { text: type, className: 'type-default' };

  return <span className={`type-tag ${config.className}`}>{config.text}</span>;
};

/**
 * 任務列表組件
 * 顯示和管理任務列表
 */
export const TaskList: React.FC<TaskListProps> = ({
  tasks,
  loading = false,
  onTaskClick,
  onStartTask,
  onStopTask,
  onDeleteTask,
  onEditTask,
  className = '',
  emptyText = '暫無任務',
}) => {
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());

  const toggleTaskExpansion = (taskId: string) => {
    setExpandedTasks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTaskActions = (task: Task) => {
    const actions = [];

    if (task.status === 'pending' || task.status === 'failed') {
      actions.push(
        <Button
          key="start"
          type="primary"
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            onStartTask?.(task.id);
          }}
        >
          開始
        </Button>
      );
    }

    if (task.status === 'running') {
      actions.push(
        <Button
          key="stop"
          type="danger"
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            onStopTask?.(task.id);
          }}
        >
          停止
        </Button>
      );
    }

    actions.push(
      <Button
        key="edit"
        type="secondary"
        size="small"
        onClick={(e) => {
          e.stopPropagation();
          onEditTask?.(task);
        }}
      >
        編輯
      </Button>
    );

    if (task.status !== 'running') {
      actions.push(
        <Button
          key="delete"
          type="danger"
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            if (confirm(`確定要刪除任務「${task.name}」嗎？`)) {
              onDeleteTask?.(task.id);
            }
          }}
        >
          刪除
        </Button>
      );
    }

    return actions;
  };

  if (loading) {
    return (
      <Card className={`task-list-loading ${className}`}>
        <div className="task-list-empty">
          <div className="loading-spinner"></div>
          <p>加載中...</p>
        </div>
      </Card>
    );
  }

  if (!tasks || tasks.length === 0) {
    return (
      <Card className={`task-list-empty ${className}`}>
        <div className="task-list-empty">
          <div className="empty-icon">📋</div>
          <p>{emptyText}</p>
        </div>
      </Card>
    );
  }

  return (
    <div className={`task-list ${className}`}>
      {tasks.map((task) => {
        const isExpanded = expandedTasks.has(task.id);
        const hasError = task.status === 'failed' && task.error;

        return (
          <Card
            key={task.id}
            className={`task-item ${task.status === 'running' ? 'task-running' : ''}`}
            hoverable
            onClick={() => onTaskClick?.(task)}
          >
            <div className="task-header">
              <div className="task-info">
                <h3 className="task-name">{task.name}</h3>
                <div className="task-meta">
                  <TaskTypeTag type={task.type} />
                  <TaskStatusTag status={task.status} />
                  <span className="task-priority">優先級: {task.priority}</span>
                </div>
              </div>
              <div className="task-actions">
                {getTaskActions(task)}
              </div>
            </div>

            {task.description && (
              <div className="task-description">
                <p>{task.description}</p>
              </div>
            )}

            <div className="task-details">
              <div className="task-timestamps">
                <span className="task-time">
                  創建時間: {formatDate(task.createdAt)}
                </span>
                {task.updatedAt !== task.createdAt && (
                  <span className="task-time">
                    更新時間: {formatDate(task.updatedAt)}
                  </span>
                )}
                {task.startedAt && (
                  <span className="task-time">
                    開始時間: {formatDate(task.startedAt)}
                  </span>
                )}
                {task.completedAt && (
                  <span className="task-time">
                    完成時間: {formatDate(task.completedAt)}
                  </span>
                )}
              </div>

              {task.progress !== undefined && task.progress >= 0 && (
                <div className="task-progress">
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${Math.min(task.progress, 100)}%` }}
                    />
                  </div>
                  <span className="progress-text">{task.progress}%</span>
                </div>
              )}

              {hasError && (
                <div className="task-error">
                  <button
                    className="error-toggle"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleTaskExpansion(task.id);
                    }}
                  >
                    {isExpanded ? '隱藏錯誤信息' : '查看錯誤信息'}
                  </button>
                  {isExpanded && (
                    <div className="error-details">
                      <pre>{task.error}</pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>
        );
      })}
    </div>
  );
};

export default TaskList;