import React, { useState, useEffect } from 'react';
import { Input } from '../../components/Input';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import './TaskFilter.css';

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused' | 'all';
export type TaskType = 'proxy_collection' | 'proxy_validation' | 'data_export' | 'system_maintenance' | 'all';

interface TaskFilterProps {
  searchText: string;
  filterStatus: TaskStatus;
  filterType: TaskType;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: TaskStatus) => void;
  onTypeChange: (value: TaskType) => void;
  loading?: boolean;
}

/**
 * 任務過濾器組件
 * 提供任務搜索和篩選功能
 */
export const TaskFilter: React.FC<TaskFilterProps> = ({
  searchText,
  filterStatus,
  filterType,
  onSearchChange,
  onStatusChange,
  onTypeChange,
  loading
}) => {
  const [localSearchText, setLocalSearchText] = useState(searchText);

  // 防抖搜索
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      onSearchChange(localSearchText);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [localSearchText, onSearchChange]);

  // 同步外部搜索文本變化
  useEffect(() => {
    setLocalSearchText(searchText);
  }, [searchText]);

  const handleReset = () => {
    setLocalSearchText('');
    onSearchChange('');
    onStatusChange('all');
    onTypeChange('all');
  };

  return (
    <Card className="task-filter">
      <div className="filter-row">
        <div className="filter-group">
          <label htmlFor="keyword">關鍵詞搜索</label>
          <Input
            id="keyword"
            type="text"
            placeholder="搜索任務名稱、ID或描述..."
            value={localSearchText}
            onChange={(value) => setLocalSearchText(value)}
            disabled={loading}
            className="filter-input"
            prefix="🔍"
          />
        </div>

        <div className="filter-group">
          <label htmlFor="status">任務狀態</label>
          <select
            id="status"
            value={filterStatus}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => onStatusChange(e.target.value as TaskStatus)}
            disabled={loading}
            className="filter-select"
          >
            <option value="all">全部狀態</option>
            <option value="pending">待執行</option>
            <option value="running">運行中</option>
            <option value="completed">已完成</option>
            <option value="failed">失敗</option>
            <option value="cancelled">已取消</option>
            <option value="paused">已暫停</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="type">任務類型</label>
          <select
            id="type"
            value={filterType}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => onTypeChange(e.target.value as TaskType)}
            disabled={loading}
            className="filter-select"
          >
            <option value="all">全部類型</option>
            <option value="proxy_collection">代理收集</option>
            <option value="proxy_validation">代理驗證</option>
            <option value="data_export">數據導出</option>
            <option value="system_maintenance">系統維護</option>
          </select>
        </div>

        <div className="filter-group filter-actions">
          <Button
            type="secondary"
            onClick={handleReset}
            disabled={loading}
          >
            重置
          </Button>
        </div>
      </div>
    </Card>
  );
};