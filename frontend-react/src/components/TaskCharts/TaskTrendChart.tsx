import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { Task } from '../../types/task.types';
import './TaskCharts.css';

interface TaskTrendChartProps {
  tasks: Task[];
  loading?: boolean;
}

/**
 * 任務趨勢圖表組件
 * 展示任務創建和完成的時間趨勢
 */
export const TaskTrendChart: React.FC<TaskTrendChartProps> = ({ tasks, loading = false }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  /**
   * 初始化圖表
   */
  useEffect(() => {
    if (!chartRef.current) return;

    // 創建圖表實例
    chartInstance.current = echarts.init(chartRef.current);

    // 清理函數
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, []);

  /**
   * 更新圖表數據
   */
  useEffect(() => {
    if (!chartInstance.current || loading) return;

    // 按日期分組統計任務
    const dateGroups = new Map<string, { created: number; completed: number }>();
    
    tasks.forEach(task => {
      const date = new Date(task.createdAt).toLocaleDateString('zh-CN');
      if (!dateGroups.has(date)) {
        dateGroups.set(date, { created: 0, completed: 0 });
      }
      const group = dateGroups.get(date)!;
      group.created++;
      if (task.status === 'completed') {
        group.completed++;
      }
    });

    // 排序日期
    const sortedDates = Array.from(dateGroups.keys()).sort((a, b) => {
      return new Date(a).getTime() - new Date(b).getTime();
    });

    // 獲取最近7天的數據
    const recentDates = sortedDates.slice(-7);
    const createdData = recentDates.map(date => dateGroups.get(date)?.created || 0);
    const completedData = recentDates.map(date => dateGroups.get(date)?.completed || 0);

    // 圖表配置
    const option: echarts.EChartsOption = {
      title: {
        text: '任務趨勢分析',
        left: 'center',
        textStyle: {
          fontSize: 18,
          fontWeight: 'bold',
        },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          label: {
            backgroundColor: '#6a7985',
          },
        },
      },
      legend: {
        data: ['新建任務', '完成任務'],
        bottom: 10,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: recentDates,
        axisLabel: {
          rotate: 45,
        },
      },
      yAxis: {
        type: 'value',
        name: '任務數量',
        nameTextStyle: {
          padding: [0, 0, 0, 50],
        },
      },
      series: [
        {
          name: '新建任務',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          sampling: 'average',
          itemStyle: {
            color: '#3498db',
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(52, 152, 219, 0.3)' },
              { offset: 1, color: 'rgba(52, 152, 219, 0.1)' },
            ]),
          },
          data: createdData,
        },
        {
          name: '完成任務',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          sampling: 'average',
          itemStyle: {
            color: '#27ae60',
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(39, 174, 96, 0.3)' },
              { offset: 1, color: 'rgba(39, 174, 96, 0.1)' },
            ]),
          },
          data: completedData,
        },
      ],
    };

    // 設置圖表選項
    chartInstance.current.setOption(option);

    // 響應式調整
    const handleResize = () => {
      if (chartInstance.current) {
        chartInstance.current.resize();
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [tasks, loading]);

  if (loading) {
    return (
      <div className="task-charts">
        <div className="charts-loading">
          <div className="loading-spinner"></div>
          <span>載入圖表中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="task-charts">
      <div ref={chartRef} className="chart-container"></div>
    </div>
  );
};

export default TaskTrendChart;