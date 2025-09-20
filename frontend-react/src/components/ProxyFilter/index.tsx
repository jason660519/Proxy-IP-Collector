/**
 * 代理篩選組件
 * @description 提供代理IP的高級篩選功能
 */

import React, { useState, useEffect } from 'react';
import {
  Drawer,
  Form,
  Input,
  Select,
  Slider,
  Button,
  Space,
  Tag,
  Row,
  Col,
  Divider,
  Modal,
} from 'antd';
import {
  FilterOutlined,
} from '@ant-design/icons';
import { useAppSelector, useAppDispatch } from '../../hooks';
import { ProxyFilter as FilterType } from '../../types/proxy.types';
import './ProxyFilter.css';

const { Option } = Select;

interface ProxyFilterProps {
  visible: boolean;
  onClose: () => void;
}

/**
 * 代理篩選組件
 * 提供多維度的代理篩選功能
 */
const ProxyFilter: React.FC<ProxyFilterProps> = ({ visible, onClose }) => {
  const dispatch = useAppDispatch();
  const [form] = Form.useForm();
  
  // 獲取狀態
  const currentFilter = useAppSelector((state) => state.filter);
  const savedFilters = useAppSelector((state) => state.filter.savedFilters);
  
  const [loading, setLoading] = useState(false);
  const [saveModalVisible, setSaveModalVisible] = useState(false);
  const [filterName, setFilterName] = useState('');

  // 初始化表單
  useEffect(() => {
    if (visible) {
      form.setFieldsValue(currentFilter);
    }
  }, [visible, currentFilter, form]);

  // 應用篩選
  const handleApply = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      
      await dispatch({
        type: 'filter/updateFilter',
        payload: values,
      });
      
      onClose();
    } catch (error) {
      console.error('篩選參數驗證失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  // 重置篩選
  const handleReset = () => {
    form.resetFields();
    dispatch({
      type: 'filter/resetFilter',
    });
  };

  // 保存篩選模板
  const handleSaveFilter = async () => {
    try {
      const values = await form.validateFields();
      if (!filterName.trim()) {
        return;
      }
      
      await dispatch({
        type: 'filter/saveFilterTemplate',
        payload: {
          name: filterName,
          filters: values,
        },
      });
      
      setSaveModalVisible(false);
      setFilterName('');
    } catch (error) {
      console.error('保存篩選模板失敗:', error);
    }
  };

  // 應用保存的篩選
  const handleApplySavedFilter = (filter: any) => {
    form.setFieldsValue(filter);
  };

  // 刪除保存的篩選
  const handleDeleteSavedFilter = (name: string) => {
    dispatch({
      type: 'filter/deleteFilterTemplate',
      payload: name,
    });
  };

  // 快速篩選選項
  const quickFilters: Array<{
    name: string;
    filter: FilterType;
    color: string;
  }> = [
    {
      name: '活動代理',
      filter: { status: ['active'] },
      color: 'green',
    },
    {
      name: '失效代理',
      filter: { status: ['failed'] },
      color: 'red',
    },
    {
      name: '快速響應',
      filter: { maxResponseTime: 1000 },
      color: 'blue',
    },
    {
      name: '高匿名',
      filter: { anonymity: ['elite'] },
      color: 'purple',
    },
    {
      name: 'SOCKS5',
      filter: { protocol: ['socks5' as const] },
      color: 'orange',
    },
  ];

  return (
    <>
      <Drawer
        title="代理篩選"
        placement="right"
        width={400}
        onClose={onClose}
        visible={visible}
        className="proxy-filter-drawer"
        footer={
          <div className="filter-drawer-footer">
            <Space>
              <Button onClick={handleReset}>重置</Button>
              <Button onClick={onClose}>取消</Button>
              <Button
                type="primary"
                loading={loading}
                onClick={handleApply}
                icon={<FilterOutlined />}
              >
                應用篩選
              </Button>
            </Space>
          </div>
        }
      >
        <Form
          form={form}
          layout="vertical"
          className="proxy-filter-form"
        >
          {/* 快速篩選 */}
          <div className="quick-filters">
            <div className="quick-filters-title">快速篩選</div>
            <Space wrap>
              {quickFilters.map((filter) => (
                <Tag
                  key={filter.name}
                  color={filter.color as any}
                  className="quick-filter-tag"
                  onClick={() => handleApplySavedFilter(filter.filter)}
                >
                  {filter.name}
                </Tag>
              ))}
            </Space>
          </div>

          <Divider />

          {/* 保存的篩選模板 */}
          {savedFilters.length > 0 && (
            <div className="saved-filters">
              <div className="saved-filters-title">
                <span>保存的篩選</span>
                <Button
                  type="link"
                  size="small"
                  onClick={() => setSaveModalVisible(true)}
                >
                  保存當前
                </Button>
              </div>
              <Space wrap>
                {savedFilters.map((saved) => (
                  <div key={saved.name} className="saved-filter-item">
                    <Tag
                      closable
                      onClose={() => handleDeleteSavedFilter(saved.name)}
                      className="saved-filter-tag"
                      onClick={() => handleApplySavedFilter(saved.filters)}
                    >
                      {saved.name}
                    </Tag>
                  </div>
                ))}
              </Space>
              <Divider />
            </div>
          )}

          {/* 基本篩選 */}
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="protocol" label="代理類型">
                <Select
                  mode="multiple"
                  placeholder="選擇類型"
                  allowClear
                >
                  <Option value="http">HTTP</Option>
                  <Option value="https">HTTPS</Option>
                  <Option value="socks4">SOCKS4</Option>
                  <Option value="socks5">SOCKS5</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="status" label="狀態">
                <Select
                  mode="multiple"
                  placeholder="選擇狀態"
                  allowClear
                >
                  <Option value="active">活動</Option>
                  <Option value="inactive">非活動</Option>
                  <Option value="failed">失效</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="anonymity" label="匿名級別">
                <Select
                  mode="multiple"
                  placeholder="選擇匿名級別"
                  allowClear
                >
                  <Option value="elite">高匿名</Option>
                  <Option value="anonymous">匿名</Option>
                  <Option value="transparent">透明</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="country" label="國家/地區">
                <Input placeholder="例如: US, CN, JP" />
              </Form.Item>
            </Col>
          </Row>

          {/* 響應時間篩選 */}
          <Form.Item
            name="maxResponseTime"
            label="最大響應時間 (ms)"
            className="response-time-filter"
          >
            <Slider
              min={0}
              max={10000}
              step={100}
              marks={{
                0: '0ms',
                5000: '5s',
                10000: '10s',
              }}
            />
          </Form.Item>

          {/* 成功率篩選 */}
          <Form.Item
            name="minSuccessRate"
            label="最小成功率 (%)"
            className="success-rate-filter"
          >
            <Slider
              min={0}
              max={100}
              step={1}
              marks={{
                0: '0%',
                50: '50%',
                100: '100%',
              }}
            />
          </Form.Item>

          {/* 來源篩選 */}
          <Form.Item name="source" label="來源">
            <Select
              mode="multiple"
              placeholder="選擇來源"
              allowClear
            >
              <Option value="89ip.cn">89ip.cn</Option>
              <Option value="kuaidaili.com">kuaidaili.com</Option>
              <Option value="proxylist.geonode.com">proxylist.geonode.com</Option>
              <Option value="proxydb.net">proxydb.net</Option>
              <Option value="proxynova.com">proxynova.com</Option>
              <Option value="spys.one">spys.one</Option>
              <Option value="free-proxy-list.net">free-proxy-list.net</Option>
              <Option value="manual">手動添加</Option>
            </Select>
          </Form.Item>

          {/* 高級選項 */}
          <div className="advanced-options">
            <Divider orientation="left">高級選項</Divider>
            
            <Form.Item name="minQualityScore" label="最小質量評分">
              <Slider
                min={0}
                max={1}
                step={0.1}
                marks={{
                  0: '0',
                  0.5: '0.5',
                  1: '1',
                }}
              />
            </Form.Item>

            <Form.Item name="searchText" label="搜索關鍵詞">
              <Input placeholder="IP地址、位置等" />
            </Form.Item>
          </div>
        </Form>
      </Drawer>

      {/* 保存篩選模態框 */}
      <Modal
        title="保存篩選模板"
        visible={saveModalVisible}
        onCancel={() => setSaveModalVisible(false)}
        onOk={handleSaveFilter}
        okText="保存"
        cancelText="取消"
      >
        <Input
          placeholder="輸入模板名稱"
          value={filterName}
          onChange={(e) => setFilterName(e.target.value)}
          onPressEnter={handleSaveFilter}
        />
      </Modal>
    </>
  );
};

export default ProxyFilter;