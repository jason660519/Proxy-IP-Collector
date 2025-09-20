/**
 * 代理管理頁面
 * @description 管理和查看代理IP的頁面
 */

import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Button,
  Space,
  Input,
  Select,
  Tag,
  Modal,
  Form,
  Row,
  Col,
  Badge,
  Tooltip,
  Popconfirm,
  message,
  Typography,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  DeleteOutlined,
  EditOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import { useAppSelector, useAppDispatch } from '../../hooks';
import { useDocumentTitle } from '../../hooks';
import { StatCard, PieChart, BarChart } from '../../components/Charts';
import ProxyFilter from '../../components/ProxyFilter';
import { formatTime, isValidIP, isValidPort } from '../../utils/format';
import './ProxiesPage.css';

const { Search } = Input;
const { Option } = Select;
const { Text } = Typography;

/**
 * 代理管理頁面組件
 */
const ProxiesPage: React.FC = () => {
  useDocumentTitle('代理管理');
  const dispatch = useAppDispatch();
  
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [filterVisible, setFilterVisible] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProxy, setEditingProxy] = useState<any>(null);
  const [form] = Form.useForm();

  // 獲取狀態數據
  const proxies = useAppSelector((state) => state.proxy.proxies);
  const filter = useAppSelector((state) => state.filter);
  const pagination = useAppSelector((state) => state.proxy.pagination);
  const totalCount = useAppSelector((state) => state.proxy.totalCount);
  // 加載代理數據
  useEffect(() => {
    loadProxies();
  }, [filter, pagination.page, pagination.pageSize]);

  // 加載代理數據
  const loadProxies = async () => {
    setLoading(true);
    try {
      await dispatch({
        type: 'proxy/fetchProxies',
        payload: {
          page: pagination.page,
          pageSize: pagination.pageSize,
          filter: filter,
        },
      });
    } catch (error) {
      message.error('加載代理數據失敗');
    } finally {
      setLoading(false);
    }
  };

  // 處理搜索
  const handleSearch = (value: string) => {
    dispatch({
      type: 'filter/updateSearch',
      payload: value,
    });
  };

  // 處理表格選擇
  const handleSelectChange = (newSelectedRowKeys: React.Key[]) => {
    setSelectedRowKeys(newSelectedRowKeys);
  };

  // 批量刪除
  const handleBatchDelete = async () => {
    try {
      await dispatch({
        type: 'proxy/deleteProxies',
        payload: selectedRowKeys,
      });
      message.success(`成功刪除 ${selectedRowKeys.length} 個代理`);
      setSelectedRowKeys([]);
    } catch (error) {
      message.error('刪除失敗');
    }
  };

  // 批量測試
  const handleBatchTest = async () => {
    try {
      await dispatch({
        type: 'proxy/testProxies',
        payload: selectedRowKeys,
      });
      message.success('開始批量測試');
    } catch (error) {
      message.error('測試失敗');
    }
  };

  // 刪除單個代理
  const handleDelete = async (id: string) => {
    try {
      await dispatch({
        type: 'proxy/removeProxy',
        payload: id,
      });
      message.success('代理刪除成功');
    } catch (error) {
      message.error('刪除失敗');
    }
  };

  // 導出代理
  const handleExport = () => {
    const data = proxies.map(proxy => ({
      IP: proxy.ip,
      Port: proxy.port,
      Type: proxy.type,
      Status: proxy.status,
      'Response Time': proxy.responseTime,
      Location: proxy.location ? `${proxy.location.country} - ${proxy.location.city}` : 'Unknown',
    }));

    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map(row => Object.values(row).join(','))
    ].join('\n');

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `proxies_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
  };

  // 顯示添加/編輯模態框
  const showModal = (proxy?: any) => {
    setEditingProxy(proxy);
    if (proxy) {
      form.setFieldsValue(proxy);
    } else {
      form.resetFields();
    }
    setModalVisible(true);
  };

  // 處理表單提交
  const handleSubmit = async (values: any) => {
    try {
      if (editingProxy) {
        await dispatch({
          type: 'proxy/updateProxy',
          payload: { ...editingProxy, ...values },
        });
        message.success('代理更新成功');
      } else {
        await dispatch({
          type: 'proxy/addProxy',
          payload: values,
        });
        message.success('代理添加成功');
      }
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('操作失敗');
    }
  };

  // 表格列配置
  const columns = [
    {
      title: 'IP地址',
      dataIndex: 'ip',
      key: 'ip',
      width: 140,
      sorter: (a: any, b: any) => a.ip.localeCompare(b.ip),
      render: (text: string, record: any) => (
        <Space>
          <Badge
            status={record.status === 'active' ? 'success' : record.status === 'inactive' ? 'warning' : 'error'}
            text={text}
          />
        </Space>
      ),
    },
    {
      title: '端口',
      dataIndex: 'port',
      key: 'port',
      width: 80,
      sorter: (a: any, b: any) => a.port - b.port,
    },
    {
      title: '類型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      filters: [
        { text: 'HTTP', value: 'http' },
        { text: 'HTTPS', value: 'https' },
        { text: 'SOCKS4', value: 'socks4' },
        { text: 'SOCKS5', value: 'socks5' },
      ],
      onFilter: (value: any, record: any) => record.type === value,
      render: (type: string) => (
        <Tag color="blue">{type.toUpperCase()}</Tag>
      ),
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      filters: [
        { text: '活動', value: 'active' },
        { text: '非活動', value: 'inactive' },
        { text: '失效', value: 'failed' },
      ],
      onFilter: (value: any, record: any) => record.status === value,
      render: (status: string) => {
        const icons = {
          active: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
          inactive: <ClockCircleOutlined style={{ color: '#faad14' }} />,
          failed: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
        };
        const texts = {
          active: '活動',
          inactive: '非活動',
          failed: '失效',
        };
        return (
          <Space>
            {icons[status as keyof typeof icons]}
            <span>{texts[status as keyof typeof texts]}</span>
          </Space>
        );
      },
    },
    {
      title: '響應時間',
      dataIndex: 'responseTime',
      key: 'responseTime',
      width: 120,
      sorter: (a: any, b: any) => a.responseTime - b.responseTime,
      render: (time: number) => (
        <Text type={time < 1000 ? 'success' : time < 3000 ? 'warning' : 'danger'}>
          {time}ms
        </Text>
      ),
    },
    {
      title: '位置',
      dataIndex: 'location',
      key: 'location',
      width: 150,
      render: (location: { country: string; city: string }) => (
        <Space>
          <GlobalOutlined />
          <span>{location ? `${location.country} - ${location.city}` : '-'}</span>
        </Space>
      ),
    },
    {
      title: '最後檢查',
      dataIndex: 'lastChecked',
      key: 'lastChecked',
      width: 150,
      sorter: (a: any, b: any) => a.lastChecked - b.lastChecked,
      render: (timestamp: number) => formatTime(timestamp),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right' as const,
      render: (_: any, record: any) => (
        <Space size="small">
          <Tooltip title="編輯">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => showModal(record)}
            />
          </Tooltip>
          <Popconfirm
            title="確定要刪除這個代理嗎？"
            onConfirm={() => handleDelete(record.id)}
            okText="確定"
            cancelText="取消"
          >
            <Tooltip title="刪除">
              <Button
                type="text"
                danger
                size="small"
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="proxies-page">
      {/* 統計卡片區域 */}
      <Row gutter={[16, 16]} className="stat-cards-row">
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="代理總數"
            value={proxies.length}
            icon={<GlobalOutlined />}
            color="#1890ff"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="活動代理"
            value={proxies.filter(p => p.status === 'active').length}
            icon={<CheckCircleOutlined />}
            color="#52c41a"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="非活動代理"
            value={proxies.filter(p => p.status === 'inactive').length}
            icon={<ClockCircleOutlined />}
            color="#faad14"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="失效代理"
            value={proxies.filter(p => p.status === 'failed').length}
            icon={<CloseCircleOutlined />}
            color="#ff4d4f"
          />
        </Col>
      </Row>

      {/* 圖表區域 */}
      <Row gutter={[16, 16]} className="charts-row">
        <Col xs={24} lg={12}>
          <Card title="代理狀態分佈" className="chart-card">
            <PieChart
              data={[
                { name: '活動', value: proxies.filter(p => p.status === 'active').length },
                { name: '非活動', value: proxies.filter(p => p.status === 'inactive').length },
                { name: '失效', value: proxies.filter(p => p.status === 'failed').length },
              ]}
              height={300}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="代理類型分佈" className="chart-card">
            <BarChart
              xAxisData={['HTTP', 'HTTPS', 'SOCKS4', 'SOCKS5']}
              series={[
                {
                  name: '數量',
                  data: [
                    proxies.filter(p => p.type === 'http').length,
                    proxies.filter(p => p.type === 'https').length,
                    proxies.filter(p => p.type === 'socks4').length,
                    proxies.filter(p => p.type === 'socks5').length,
                  ],
                  color: '#1890ff',
                },
              ]}
              height={300}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        {/* 操作欄 */}
        <div className="proxies-toolbar">
          <Space>
            <Search
              placeholder="搜索IP地址或位置"
              allowClear
              enterButton={<SearchOutlined />}
              style={{ width: 300 }}
              onSearch={handleSearch}
            />
            <Button icon={<FilterOutlined />} onClick={() => setFilterVisible(true)}>
              篩選
            </Button>
          </Space>

          <Space>
            <Button icon={<PlusOutlined />} type="primary" onClick={() => showModal()}>
              添加代理
            </Button>
            {selectedRowKeys.length > 0 && (
              <>
                <Popconfirm
                  title={`確定要刪除選中的 ${selectedRowKeys.length} 個代理嗎？`}
                  onConfirm={handleBatchDelete}
                  okText="確定"
                  cancelText="取消"
                >
                  <Button danger icon={<DeleteOutlined />}>
                    批量刪除
                  </Button>
                </Popconfirm>
                <Button onClick={handleBatchTest}>
                  批量測試
                </Button>
              </>
            )}
            <Button icon={<ExportOutlined />} onClick={handleExport}>
              導出
            </Button>
          </Space>
        </div>

        {/* 統計信息 */}
        <div className="proxies-stats">
          <Space size="large">
            <span>總數: <strong>{proxies.length}</strong></span>
            <span>活動: <strong style={{ color: '#52c41a' }}>{proxies.filter(p => p.status === 'active').length}</strong></span>
            <span>非活動: <strong style={{ color: '#faad14' }}>{proxies.filter(p => p.status === 'inactive').length}</strong></span>
            <span>失效: <strong style={{ color: '#ff4d4f' }}>{proxies.filter(p => p.status === 'failed').length}</strong></span>
          </Space>
        </div>

        {/* 代理表格 */}
      <Table
          rowKey="id"
          rowSelection={{
            selectedRowKeys,
            onChange: handleSelectChange,
          }}
          columns={columns}
          dataSource={proxies}
          loading={loading}
          pagination={{
            current: pagination.page,
        pageSize: pagination.pageSize,
            total: totalCount,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 條`,
            onChange: (page, pageSize) => {
              dispatch({
                type: 'proxy/updatePagination',
                payload: { current: page, pageSize },
              });
            },
          }}
          scroll={{ x: 1200 }}
          className="proxies-table"
        />
      </Card>

      {/* 篩選面板 */}
      <ProxyFilter
        visible={filterVisible}
        onClose={() => setFilterVisible(false)}
      />

      {/* 添加/編輯模態框 */}
      <Modal
        title={editingProxy ? '編輯代理' : '添加代理'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            type: 'http',
            status: 'active',
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="ip"
                label="IP地址"
                rules={[
                  { required: true, message: '請輸入IP地址' },
                  { validator: (_, value) => {
                    if (!value || isValidIP(value)) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('IP地址格式不正確'));
                  }}
                ]}
              >
                <Input placeholder="例如: 192.168.1.1" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="port"
                label="端口"
                rules={[
                  { required: true, message: '請輸入端口' },
                  { validator: (_, value) => {
                    if (!value || isValidPort(value)) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('端口必須在1-65535之間'));
                  }}
                ]}
              >
                <Input type="number" placeholder="例如: 8080" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="type"
                label="類型"
                rules={[{ required: true, message: '請選擇代理類型' }]}
              >
                <Select>
                  <Option value="http">HTTP</Option>
                  <Option value="https">HTTPS</Option>
                  <Option value="socks4">SOCKS4</Option>
                  <Option value="socks5">SOCKS5</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="status"
                label="狀態"
                rules={[{ required: true, message: '請選擇狀態' }]}
              >
                <Select>
                  <Option value="active">活動</Option>
                  <Option value="inactive">非活動</Option>
                  <Option value="failed">失效</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Space style={{ float: 'right' }}>
              <Button onClick={() => setModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit">
                {editingProxy ? '更新' : '添加'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ProxiesPage;