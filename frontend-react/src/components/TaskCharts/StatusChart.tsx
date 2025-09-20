import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import type { Task } from '../../types/task.types';
import './TaskCharts.css';

interface StatusChartProps {
  tasks: Task[];
  loading?: boolean;
}

/**
 * 任務狀態分布圖表組件
 * 使用餅圖展示任務狀態分布情況
 */
export const StatusChart: React.FC<StatusChartProps> = ({ tasks, loading = false }) => {
  // 統計各狀態的任務數量
  const statusData = React.useMemo(() => {
    const statusCount = tasks.reduce((acc: Record<string, number>, task) => {
      acc[task.status] = (acc[task.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(statusCount).map(([status, count]) => ({
      name: getStatusLabel(status),
      value: count,
      status,
    }));
  }, [tasks]);

  // 獲取狀態標籤
  const getStatusLabel = (status: string): string => {
    const statusMap: Record<string, string> = {
      pending: '待處理',
      running: '運行中',
      completed: '已完成',
      failed: '失敗',
      cancelled: '已取消',
    };
    return statusMap[status] || status;
  };

  // 狀態顏色映射
  const statusColors: Record<string, string> = {
    pending: '#faad14',
    running: '#1890ff',
    completed: '#52c41a',
    failed: '#f5222d',
    cancelled: '#d9d9d9',
  };

  if (loading) {
    return <div className="chart-loading">加載中...</div>;
  }

  if (tasks.length === 0) {
    return <div className="chart-empty">暫無數據</div>;
  }

  return (
    <div className="status-chart">
      <h3>任務狀態分布</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={statusData}
            cx="50%"
            cy="50%"
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
            label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
          >
            {statusData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={statusColors[entry.status] || '#8884d8'} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => [`${value} 個`, '數量']} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};