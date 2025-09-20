import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { Task } from '../../types';
import './TaskDashboard.css';

interface TaskDashboardProps {
  tasks: Task[];
  loading?: boolean;
}

/**
 * 任務儀表板組件
 * 提供任務數據的綜合可視化展示，包括多種圖表類型
 */
export const TaskDashboard: React.FC<TaskDashboardProps> = ({ tasks, loading = false }) => {
  const statusChartRef = useRef<HTMLDivElement>(null);
  const typeChartRef = useRef<HTMLDivElement>(null);
  const statusChartInstance = useRef<echarts.ECharts | null>(null);
  const typeChartInstance = useRef<echarts.ECharts | null>(null);

  /**
   * 初始化圖表
   */
  useEffect(() => {
    if (!statusChartRef.current || !typeChartRef.current) return;

    // 創建圖表實例
    statusChartInstance.current = echarts.init(statusChartRef.current);
    typeChartInstance.current = echarts.init(typeChartRef.current);

    // 清理函數
    return () => {
      if (statusChartInstance.current) {
        statusChartInstance.current.dispose();
        statusChartInstance.current = null;
      }
      if (typeChartInstance.current) {
        typeChartInstance.current.dispose();
        typeChartInstance.current = null;
      }
    };
  }, []);

  /**
   * 更新圖表數據
   */
  useEffect(() => {
    if (!statusChartInstance.current || !typeChartInstance.current || loading) return;

    // 統計數據
    const statusData = {
      pending: tasks.filter(t => t.status === 'pending').length,
      running: tasks.filter(t => t.status === 'running').length,
      completed: tasks.filter(t => t.status === 'completed').length,
      failed: tasks.filter(t => t.status === 'failed').length,
    };

    const typeData = {
      health_check: tasks.filter(t => t.type === 'health_check').length,
      proxy_test: tasks.filter(t => t.type === 'proxy_test').length,
      data_collection: tasks.filter(t => t.type === 'data_collection').length,
    };

    // 狀態分布圖表配置
    const statusOption: echarts.EChartsOption = {
      title: {
        text: '任務狀態分布',
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold',
        },
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)',
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        data: ['待處理', '運行中', '已完成', '失敗'],
      },
      series: [
        {
          name: '任務狀態',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['60%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: true,
            formatter: '{b}\n{c}',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
            },
          },
          data: [
            { value: statusData.pending, name: '待處理', itemStyle: { color: '#f39c12' } },
            { value: statusData.running, name: '運行中', itemStyle: { color: '#3498db' } },
            { value: statusData.completed, name: '已完成', itemStyle: { color: '#27ae60' } },
            { value: statusData.failed, name: '失敗', itemStyle: { color: '#e74c3c' } },
          ],
        },
      ],
    };

    // 任務類型圖表配置
    const typeOption: echarts.EChartsOption = {
      title: {
        text: '任務類型分布',
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold',
        },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: ['健康檢查', '代理測試', '數據收集'],
        axisTick: {
          alignWithLabel: true,
        },
      },
      yAxis: {
        type: 'value',
        name: '任務數量',
      },
      series: [
        {
          name: '任務數量',
          type: 'bar',
          barWidth: '60%',
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
          },
          data: [
            {
              value: typeData.health_check,
              name: '健康檢查',
              itemStyle: { color: '#e67e22' },
            },
            {
              value: typeData.proxy_test,
              name: '代理測試',
              itemStyle: { color: '#9b59b6' },
            },
            {
              value: typeData.data_collection,
              name: '數據收集',
              itemStyle: { color: '#1abc9c' },
            },
          ],
        },
      ],
    };

    // 設置圖表選項
    statusChartInstance.current.setOption(statusOption);
    typeChartInstance.current.setOption(typeOption);

    // 響應式調整
    const handleResize = () => {
      if (statusChartInstance.current) {
        statusChartInstance.current.resize();
      }
      if (typeChartInstance.current) {
        typeChartInstance.current.resize();
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [tasks, loading]);

  if (loading) {
    return (
      <div className="task-dashboard">
        <div className="dashboard-loading">
          <div className="loading-spinner"></div>
          <span>載入儀表板中...</span>
        </div>
      </div>
    );
  }

  // 計算關鍵指標
  const totalTasks = tasks.length;
  const runningTasks = tasks.filter(t => t.status === 'running').length;
  const completedTasks = tasks.filter(t => t.status === 'completed').length;
  const successRate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  return (
    <div className="task-dashboard">
      <div className="dashboard-header">
        <h2>任務儀表板</h2>
      </div>

      {/* 關鍵指標卡片 */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon total">📊</div>
          <div className="metric-content">
            <div className="metric-value">{totalTasks}</div>
            <div className="metric-label">總任務數</div>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon running">⚡</div>
          <div className="metric-content">
            <div className="metric-value">{runningTasks}</div>
            <div className="metric-label">運行中</div>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon completed">✅</div>
          <div className="metric-content">
            <div className="metric-value">{completedTasks}</div>
            <div className="metric-label">已完成</div>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon success">📈</div>
          <div className="metric-content">
            <div className="metric-value">{successRate}%</div>
            <div className="metric-label">成功率</div>
          </div>
        </div>
      </div>

      {/* 圖表網格 */}
      <div className="charts-grid">
        <div className="chart-card">
          <div ref={statusChartRef} className="chart-container"></div>
        </div>
        <div className="chart-card">
          <div ref={typeChartRef} className="chart-container"></div>
        </div>
      </div>
    </div>
  );
};

export default TaskDashboard;