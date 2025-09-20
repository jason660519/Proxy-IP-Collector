/**
 * 儀表板頁面
 * @description 顯示系統概覽和統計數據
 */

import React, { useEffect } from 'react';
import { Row, Col, Card, Progress, Table, Tag, Button } from 'antd';
import {
  GlobalOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons';
import { useAppSelector, useAppDispatch } from '../../hooks';
import { useDocumentTitle } from '../../hooks';
import { formatNumber, formatPercentage, formatDuration } from '../../utils/format';
import { StatCard, LineChart, PieChart } from '../../components/Charts';
import { useNavigate } from 'react-router-dom';
import { Task } from '../../types/task.types';
import './DashboardPage.css';

/**
 * 儀表板頁面組件
 */
const DashboardPage: React.FC = () => {
  useDocumentTitle('儀表板');
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  
  // 獲取狀態數據
  const dashboard = useAppSelector((state) => state.dashboard);
  const proxies = useAppSelector((state) => state.proxy.proxies);
  const tasks = useAppSelector((state) => state.task.taskQueue || []);

  // 計算統計數據
  const totalProxies = proxies.length;
  const activeProxies = proxies.filter(p => p.status === 'active').length;
  const successRate = totalProxies > 0 ? (activeProxies / totalProxies) * 100 : 0;
  
  const runningTasks = tasks.filter((t: Task) => t.status === 'running').length;

  // 獲取最新的統計數據
  useEffect(() => {
    dispatch({ type: 'dashboard/fetchStatistics' });
    
    // 設置自動刷新
    const interval = setInterval(() => {
      if (dashboard.autoRefresh) {
        dispatch({ type: 'dashboard/fetchStatistics' });
      }
    }, dashboard.refreshInterval);

    return () => clearInterval(interval);
  }, [dispatch, dashboard.autoRefresh, dashboard.refreshInterval]);

  // 最近代理數據表格列配置
  const recentProxiesColumns = [
    {
      title: 'IP地址',
      dataIndex: 'ip',
      key: 'ip',
      width: 120,
    },
    {
      title: '端口',
      dataIndex: 'port',
      key: 'port',
      width: 80,
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const color = status === 'active' ? 'success' : status === 'inactive' ? 'warning' : 'error';
        const text = status === 'active' ? '活動' : status === 'inactive' ? '非活動' : '失效';
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '響應時間',
      dataIndex: 'responseTime',
      key: 'responseTime',
      width: 100,
      render: (time: number) => `${time}ms`,
    },
    {
      title: '位置',
      dataIndex: 'location',
      key: 'location',
      width: 120,
      render: (location: { country: string; city: string }) => 
        location ? `${location.country} - ${location.city}` : '-',
    },
    {
      title: '最後檢查',
      dataIndex: 'lastChecked',
      key: 'lastChecked',
      width: 150,
      render: (timestamp: number) => formatDuration(Date.now() - timestamp),
    },
  ];

  // 最近任務數據表格列配置
  const recentTasksColumns = [
    {
      title: '任務名稱',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const color = status === 'completed' ? 'success' : status === 'running' ? 'processing' : 'error';
        const text = status === 'completed' ? '已完成' : status === 'running' ? '運行中' : '失敗';
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '進度',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress: number) => <Progress percent={progress} size="small" />,
    },
    {
      title: '開始時間',
      dataIndex: 'startTime',
      key: 'startTime',
      width: 180,
      render: (timestamp: number) => new Date(timestamp).toLocaleString('zh-TW'),
    },
  ];

  return (
    <div className="dashboard-page">
      {/* 統計卡片區域 */}
      <Row gutter={[16, 16]} className="stat-cards-row">
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="代理總數"
            value={formatNumber(totalProxies)}
            icon={<GlobalOutlined />}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="活動代理"
            value={`${formatNumber(activeProxies)} / ${formatNumber(totalProxies)}`}
            icon={<CheckCircleOutlined />}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="運行任務"
            value={formatNumber(runningTasks)}
            icon={<ClockCircleOutlined />}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="成功率"
            value={formatPercentage(successRate, 1)}
            icon={successRate >= 80 ? <RiseOutlined /> : <FallOutlined />}
          />
        </Col>
      </Row>

      {/* 圖表區域 */}
      <Row gutter={[16, 16]} className="charts-row">
        <Col xs={24} lg={12}>
          <Card title="代理數量趨勢" className="chart-card">
            <LineChart
              xAxisData={dashboard.charts.dailyStats?.map((item: any) => item.name) || []}
              series={[
                {
                  name: '代理數量',
                  data: dashboard.charts.dailyStats?.map((item: any) => item.value) || [],
                  color: '#1890ff',
                },
              ]}
              height={300}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="代理類型分佈" className="chart-card">
            <PieChart
              data={dashboard.charts.sourceDistribution || []}
              height={300}
            />
          </Card>
        </Col>
      </Row>

      {/* 數據表格區域 */}
      <Row gutter={[16, 16]} className="tables-row">
        <Col xs={24} lg={12}>
          <Card
            title="最近代理"
            extra={
              <Button type="link" onClick={() => navigate('/proxies')}>
                查看全部
              </Button>
            }
            className="recent-proxies-card"
          >
            <Table
              columns={recentProxiesColumns}
              dataSource={proxies.slice(0, 5)}
              pagination={false}
              size="small"
              rowKey="id"
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card
            title="最近任務"
            extra={
              <Button type="link" onClick={() => navigate('/tasks')}>
                查看全部
              </Button>
            }
            className="recent-tasks-card"
          >
            <Table
              columns={recentTasksColumns}
              dataSource={tasks.slice(0, 5)}
              pagination={false}
              size="small"
              rowKey="id"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DashboardPage;