/**
 * 圖表組件模塊
 * 提供各種數據可視化圖表組件，基於 Apache ECharts
 */

import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

/**
 * 餅圖組件屬性接口
 */
interface PieChartProps {
  /** 圖表數據 */
  data: Array<{ name: string; value: number }>;
  /** 圖表標題 */
  title?: string;
  /** 圖表高度 */
  height?: number;
  /** 額外配置選項 */
  options?: echarts.EChartsOption;
}

/**
 * 餅圖組件
 * 用於顯示代理狀態、任務狀態等分類數據
 */
export const PieChart: React.FC<PieChartProps> = ({
  data,
  title,
  height = 300,
  options = {},
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // 初始化圖表
    chartInstance.current = echarts.init(chartRef.current);

    // 配置選項
    const defaultOptions: echarts.EChartsOption = {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 14,
          fontWeight: 'normal',
        },
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)',
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        top: 'middle',
      },
      series: [
        {
          name: title || '數據',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: false,
            position: 'center',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '16',
              fontWeight: 'bold',
            },
          },
          labelLine: {
            show: false,
          },
          data: data,
        },
      ],
    };

    // 合併配置
    const finalOptions = { ...defaultOptions, ...options };
    chartInstance.current.setOption(finalOptions);

    // 響應式調整
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, [data, title, options]);

  return <div ref={chartRef} style={{ width: '100%', height }} />;
};

/**
 * 折線圖組件屬性接口
 */
interface LineChartProps {
  /** X軸數據 */
  xAxisData: string[];
  /** 系列數據 */
  series: Array<{
    name: string;
    data: number[];
    color?: string;
  }>;
  /** 圖表標題 */
  title?: string;
  /** 圖表高度 */
  height?: number;
  /** 額外配置選項 */
  options?: echarts.EChartsOption;
}

/**
 * 折線圖組件
 * 用於顯示代理響應時間、任務執行趨勢等時間序列數據
 */
export const LineChart: React.FC<LineChartProps> = ({
  xAxisData,
  series,
  title,
  height = 300,
  options = {},
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // 初始化圖表
    chartInstance.current = echarts.init(chartRef.current);

    // 配置選項
    const defaultOptions: echarts.EChartsOption = {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 14,
          fontWeight: 'normal',
        },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        data: series.map(s => s.name),
        top: 30,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: xAxisData,
      },
      yAxis: {
        type: 'value',
      },
      series: series.map(s => ({
        name: s.name,
        type: 'line',
        smooth: true,
        data: s.data,
        itemStyle: {
          color: s.color,
        },
        lineStyle: {
          width: 2,
        },
      })),
    };

    // 合併配置
    const finalOptions = { ...defaultOptions, ...options };
    chartInstance.current.setOption(finalOptions);

    // 響應式調整
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, [xAxisData, series, title, options]);

  return <div ref={chartRef} style={{ width: '100%', height }} />;
};

/**
 * 柱狀圖組件屬性接口
 */
interface BarChartProps {
  /** X軸數據 */
  xAxisData: string[];
  /** 系列數據 */
  series: Array<{
    name: string;
    data: number[];
    color?: string;
  }>;
  /** 圖表標題 */
  title?: string;
  /** 圖表高度 */
  height?: number;
  /** 額外配置選項 */
  options?: echarts.EChartsOption;
}

/**
 * 柱狀圖組件
 * 用於顯示代理來源分布、任務類型分布等分類數據
 */
export const BarChart: React.FC<BarChartProps> = ({
  xAxisData,
  series,
  title,
  height = 300,
  options = {},
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // 初始化圖表
    chartInstance.current = echarts.init(chartRef.current);

    // 配置選項
    const defaultOptions: echarts.EChartsOption = {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 14,
          fontWeight: 'normal',
        },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      legend: {
        data: series.map(s => s.name),
        top: 30,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: xAxisData,
        axisTick: {
          alignWithLabel: true,
        },
      },
      yAxis: {
        type: 'value',
      },
      series: series.map(s => ({
        name: s.name,
        type: 'bar',
        barWidth: '60%',
        data: s.data,
        itemStyle: {
          color: s.color,
          borderRadius: [4, 4, 0, 0],
        },
      })),
    };

    // 合併配置
    const finalOptions = { ...defaultOptions, ...options };
    chartInstance.current.setOption(finalOptions);

    // 響應式調整
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, [xAxisData, series, title, options]);

  return <div ref={chartRef} style={{ width: '100%', height }} />;
};

/**
 * 儀表板統計卡片組件屬性接口
 */
interface StatCardProps {
  /** 卡片標題 */
  title: string;
  /** 數值 */
  value: string | number;
  /** 單位 */
  unit?: string;
  /** 趨勢 */
  trend?: 'up' | 'down' | 'stable';
  /** 趨勢值 */
  trendValue?: string;
  /** 圖標 */
  icon: React.ReactNode;
  /** 顏色 */
  color?: string;
  /** 額外樣式 */
  style?: React.CSSProperties;
}

/**
 * 儀表板統計卡片組件
 * 用於顯示關鍵指標數據
 */
export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  unit,
  trend,
  trendValue,
  icon,
  color,
  style,
}) => {
  const trendIcon = {
    up: '↗',
    down: '↘',
    stable: '→',
  }[trend || 'stable'];

  const trendColor = {
    up: '#52c41a',
    down: '#ff4d4f',
    stable: '#d9d9d9',
  }[trend || 'stable'];

  const cardStyle = {
    ...style,
    ...(color && { borderLeftColor: color }),
  };

  return (
    <div className="stat-card" style={cardStyle}>
      <div className="stat-card-icon" style={color ? { color } : {}}>{icon}</div>
      <div className="stat-card-content">
        <div className="stat-card-title">{title}</div>
        <div className="stat-card-value">
          {value}
          {unit && <span className="stat-card-unit">{unit}</span>}
        </div>
        {trend && trendValue && (
          <div className="stat-card-trend" style={{ color: trendColor }}>
            {trendIcon} {trendValue}
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * 圖表加載狀態組件
 */
export const ChartLoading: React.FC = () => (
  <div className="chart-loading">
    <div className="chart-loading-spinner" />
    <div className="chart-loading-text">加載中...</div>
  </div>
);

/**
 * 圖表錯誤狀態組件
 */
interface ChartErrorProps {
  message?: string;
  onRetry?: () => void;
}

export const ChartError: React.FC<ChartErrorProps> = ({ 
  message = '圖表加載失敗', 
  onRetry 
}) => (
  <div className="chart-error">
    <div className="chart-error-icon">⚠️</div>
    <div className="chart-error-message">{message}</div>
    {onRetry && (
      <button className="chart-error-retry" onClick={onRetry}>
        重試
      </button>
    )}
  </div>
);