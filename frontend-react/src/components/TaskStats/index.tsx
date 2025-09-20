import React from 'react';
import { Card } from '../../components/Card';
import './TaskStats.css';

interface TaskStats {
  total: number;
  running: number;
  completed: number;
  failed: number;
  pending: number;
}

interface TaskStatsProps {
  stats: TaskStats;
  loading?: boolean;
}

/**
 * 任務統計組件
 * 顯示任務的總體統計信息
 */
export const TaskStats: React.FC<TaskStatsProps> = ({ stats, loading }) => {
  if (loading) {
    return (
      <div className="tasks-stats">
        {[1, 2, 3, 4, 5].map((i) => (
          <Card key={i} className="stat-card stat-card-loading">
            <div className="stat-content">
              <div className="stat-number-loading"></div>
              <div className="stat-label-loading"></div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="tasks-stats">
      <Card className="stat-card">
        <div className="stat-content">
          <div className="stat-number">{stats.total}</div>
          <div className="stat-label">總任務數</div>
        </div>
      </Card>
      
      <Card className="stat-card">
        <div className="stat-content">
          <div className="stat-number running">{stats.running}</div>
          <div className="stat-label">運行中</div>
        </div>
      </Card>
      
      <Card className="stat-card">
        <div className="stat-content">
          <div className="stat-number completed">{stats.completed}</div>
          <div className="stat-label">已完成</div>
        </div>
      </Card>
      
      <Card className="stat-card">
        <div className="stat-content">
          <div className="stat-number">{stats.pending}</div>
          <div className="stat-label">待執行</div>
        </div>
      </Card>
      
      <Card className="stat-card">
        <div className="stat-content">
          <div className="stat-number failed">{stats.failed}</div>
          <div className="stat-label">失敗</div>
        </div>
      </Card>
    </div>
  );
};