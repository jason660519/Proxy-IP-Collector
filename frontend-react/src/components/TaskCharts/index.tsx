import React, { useState } from 'react';
import { StatusChart } from './StatusChart';
import { TaskTrendChart } from './TaskTrendChart';
import type { Task } from '../../types/task.types';
import './TaskCharts.css';

interface TaskChartsContainerProps {
  tasks: Task[];
  loading?: boolean;
}

/**
 * 任務圖表容器組件
 * 提供多種圖表視圖選項，包括狀態分布和趨勢分析
 */
export const TaskCharts: React.FC<TaskChartsContainerProps> = ({ tasks, loading = false }) => {
  const [activeChart, setActiveChart] = useState<'status' | 'trend'>('status');

  return (
    <div className="task-charts-container">
      <div className="charts-header">
        <h2>數據可視化</h2>
        <div className="chart-tabs">
          <button
            className={`chart-tab ${activeChart === 'status' ? 'active' : ''}`}
            onClick={() => setActiveChart('status')}
          >
            狀態分布
          </button>
          <button
            className={`chart-tab ${activeChart === 'trend' ? 'active' : ''}`}
            onClick={() => setActiveChart('trend')}
          >
            趨勢分析
          </button>
        </div>
      </div>

      <div className="charts-content">
        {activeChart === 'status' && <StatusChart tasks={tasks} loading={loading} />}
        {activeChart === 'trend' && <TaskTrendChart tasks={tasks} loading={loading} />}
      </div>
    </div>
  );
};

export default TaskCharts;