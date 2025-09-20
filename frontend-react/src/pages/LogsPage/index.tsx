import React, { useState } from 'react';
import { Card, Button, Table, Tag, Input, Select, Space } from 'antd';
import { useDocumentTitle } from '../../hooks';
import { proxyApi } from '../../services/proxyApi';
import './LogsPage.css';

const { Search } = Input;
const { Option } = Select;

/**
 * 日誌查看頁面組件
 * 提供系統日誌的查看、篩選和管理功能
 */
const LogsPage: React.FC = () => {
  useDocumentTitle('日誌查看');
  
  const [searchText, setSearchText] = useState('');
  const [logLevel, setLogLevel] = useState<string>('all');
  const [service, setService] = useState<string>('all');
  const [dateRange, setDateRange] = useState<string>('today');
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  
  // 獲取日誌數據
  const { data: logsData, refetch, isLoading } = proxyApi.endpoints.getLogs.useQuery({
    level: logLevel !== 'all' ? logLevel : undefined,
    service: service !== 'all' ? service : undefined,
    dateRange,
    search: searchText || undefined,
  }, {
    refetchOnMountOrArgChange: true,
    refetchOnFocus: true,
    pollingInterval: autoRefresh ? 5000 : undefined,
  });

  // 日誌等級顏色映射
  const getLogLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error': return 'red';
      case 'warn': return 'orange';
      case 'info': return 'blue';
      case 'debug': return 'green';
      default: return 'default';
    }
  };

  // 表格列配置
  const columns = [
    {
      title: '時間',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp: string) => new Date(timestamp).toLocaleString('zh-CN'),
    },
    {
      title: '等級',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: string) => (
        <Tag color={getLogLevelColor(level)}>
          {level.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '服務',
      dataIndex: 'service',
      key: 'service',
      width: 120,
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
    {
      title: '詳情',
      key: 'details',
      width: 80,
      render: (_: any) => (
        <Button type="link" size="small">
          查看
        </Button>
      ),
    },
  ];

  // 手動刷新
  const handleRefresh = () => {
    refetch();
  };

  // 清除日誌
  const handleClearLogs = async () => {
    if (window.confirm('確定要清除所有日誌嗎？此操作不可恢復。')) {
      try {
        await proxyApi.endpoints.clearLogs.initiate();
        refetch();
      } catch (error) {
        console.error('清除日誌失敗:', error);
      }
    }
  };

  // 導出日誌
  const handleExportLogs = () => {
    if (!logsData || logsData.length === 0) {
      alert('沒有日誌可導出');
      return;
    }

    const csvContent = [
      ['時間', '等級', '服務', '消息'].join(','),
      ...logsData.map((log: any) => [
        new Date(log.timestamp).toLocaleString('zh-CN'),
        log.level,
        log.service,
        `"${log.message.replace(/"/g, '""')}"`
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `logs_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  return (
    <div className="logs-page">
      <div className="logs-header">
        <h1>日誌查看</h1>
        <div className="logs-actions">
          <Button
            type="primary"
            onClick={handleRefresh}
            loading={isLoading}
          >
            刷新
          </Button>
          <Button onClick={handleExportLogs}>
            導出
          </Button>
          <Button danger onClick={handleClearLogs}>
            清除日誌
          </Button>
        </div>
      </div>

      {/* 篩選器 */}
      <Card className="logs-filter-card">
        <Space size="middle" wrap>
          <Search
            placeholder="搜索日誌內容"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
          />
          <Select
            value={logLevel}
            onChange={setLogLevel}
            style={{ width: 120 }}
            placeholder="日誌等級"
          >
            <Option value="all">全部等級</Option>
            <Option value="error">錯誤</Option>
            <Option value="warn">警告</Option>
            <Option value="info">信息</Option>
            <Option value="debug">調試</Option>
          </Select>
          <Select
            value={service}
            onChange={setService}
            style={{ width: 120 }}
            placeholder="服務類型"
          >
            <Option value="all">全部服務</Option>
            <Option value="proxy">代理服務</Option>
            <Option value="task">任務服務</Option>
            <Option value="system">系統服務</Option>
          </Select>
          <Select
            value={dateRange}
            onChange={setDateRange}
            style={{ width: 120 }}
            placeholder="時間範圍"
          >
            <Option value="today">今天</Option>
            <Option value="week">最近一周</Option>
            <Option value="month">最近一月</Option>
            <Option value="all">全部時間</Option>
          </Select>
          <div className="auto-refresh-toggle">
            <label>
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              自動刷新
            </label>
          </div>
        </Space>
      </Card>

      {/* 日誌列表 */}
      <Card className="logs-table-card">
        <Table
          columns={columns}
          dataSource={logsData || []}
          loading={isLoading}
          rowKey="id"
          pagination={{
            pageSize: 50,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 條日誌`,
          }}
          scroll={{ y: 600 }}
        />
      </Card>
    </div>
  );
};

export default LogsPage;