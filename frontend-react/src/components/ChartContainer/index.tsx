/**
 * 圖表容器組件
 * @description 封裝 Apache ECharts 的圖表組件
 */

import React, { useRef, useEffect, useState } from 'react';
import * as echarts from 'echarts';
import { Card, Empty, Spin } from 'antd';
import './ChartContainer.css';

interface ChartData {
  name: string;
  value: number | number[];
  [key: string]: any;
}

interface ChartContainerProps {
  title: string;
  type: 'line' | 'bar' | 'pie' | 'scatter' | 'gauge';
  data: ChartData[];
  height?: number;
  loading?: boolean;
  options?: echarts.EChartsOption;
}

/**
 * 圖表容器組件
 */
const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  type,
  data,
  height = 300,
  loading = false,
  options = {},
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [isEmpty, setIsEmpty] = useState(data.length === 0);

  // 生成圖表配置
  const generateChartOption = (): echarts.EChartsOption => {
    const baseOption: echarts.EChartsOption = {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 14,
          fontWeight: 'normal',
        },
      },
      tooltip: {
        trigger: type === 'pie' ? 'item' : 'axis',
        formatter: (params: any) => {
          if (type === 'pie') {
            return `${params.name}: ${params.value} (${params.percent}%)`;
          }
          return `${params[0].name}: ${params[0].value}`;
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: type !== 'pie' ? {
        type: 'category',
        data: data.map(item => item.name),
        axisLabel: {
          rotate: data.length > 10 ? 45 : 0,
        },
      } : undefined,
      yAxis: type !== 'pie' ? {
        type: 'value',
      } : undefined,
      series: [] as any[],
    };

    // 根據圖表類型生成系列數據
    switch (type) {
      case 'line':
        baseOption.series = [{
          type: 'line' as const,
          data: data.map(item => item.value),
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            width: 2,
          },
          areaStyle: {
            opacity: 0.1,
          },
        }] as any[];
        break;

      case 'bar':
        baseOption.series = [{
          type: 'bar' as const,
          data: data.map(item => item.value),
          barWidth: '60%',
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
          },
        }] as any[];
        break;

      case 'pie':
        baseOption.series = [{
          type: 'pie' as const,
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 6,
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
              fontSize: 20,
              fontWeight: 'bold',
            },
          },
          labelLine: {
            show: false,
          },
          data: data,
        }] as any[];
        break;

      case 'scatter':
        baseOption.series = [{
          type: 'scatter' as const,
          data: data.map(item => [item.name, item.value] as [string, number]),
          symbolSize: 10,
        }] as any[];
        break;

      case 'gauge':
        baseOption.series = [{
          type: 'gauge' as const,
          progress: {
            show: true,
            width: 18,
          },
          axisLine: {
            lineStyle: {
              width: 18,
            },
          },
          axisTick: {
            show: false,
          },
          splitLine: {
            length: 15,
            lineStyle: {
              width: 2,
              color: '#999',
            },
          },
          axisLabel: {
            distance: 25,
            color: '#999',
            fontSize: 12,
          },
          anchor: {
            show: true,
            showAbove: true,
            size: 25,
            itemStyle: {
              borderWidth: 10,
            },
          },
          title: {
            show: false,
          },
          detail: {
            valueAnimation: true,
            fontSize: 30,
            offsetCenter: [0, '70%'],
          },
          data: data,
        }] as any[];
        break;
    }

    return { ...baseOption, ...options };
  };

  // 初始化圖表
  useEffect(() => {
    if (chartRef.current && !isEmpty && !loading) {
      chartInstance.current = echarts.init(chartRef.current);
      const option = generateChartOption();
      chartInstance.current.setOption(option);

      // 響應式調整
      const resizeHandler = () => {
        chartInstance.current?.resize();
      };
      window.addEventListener('resize', resizeHandler);

      return () => {
        window.removeEventListener('resize', resizeHandler);
        chartInstance.current?.dispose();
      };
    }
  }, [data, type, title, loading, options, isEmpty]);

  // 更新圖表數據
  useEffect(() => {
    if (chartInstance.current && !isEmpty) {
      const option = generateChartOption();
      chartInstance.current.setOption(option);
    }
  }, [data, isEmpty]);

  // 檢查數據是否為空
  useEffect(() => {
    setIsEmpty(data.length === 0);
  }, [data]);

  if (loading) {
    return (
      <Card title={title} className="chart-container">
        <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Spin size="large" />
        </div>
      </Card>
    );
  }

  if (isEmpty) {
    return (
      <Card title={title} className="chart-container">
        <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Empty description="暫無數據" />
        </div>
      </Card>
    );
  }

  return (
    <Card title={title} className="chart-container">
      <div ref={chartRef} style={{ width: '100%', height }} />
    </Card>
  );
};

export default ChartContainer;