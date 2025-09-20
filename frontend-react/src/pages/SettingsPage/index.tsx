import React, { useState, useEffect } from 'react';
import { Card, Form, Input, InputNumber, Select, Switch, Button, Space, message, Tabs, Divider, Row, Col, Alert, Modal } from 'antd';
import { SaveOutlined, ReloadOutlined, SettingOutlined, DatabaseOutlined, NotificationOutlined, SecurityScanOutlined } from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { useDocumentTitle } from '../../hooks';
import { setUserSettings, setSystemConfig } from '../../store/slices/userSlice';
import type { UserSettings } from '../../types/proxy.types';
import './SettingsPage.css';

const { TabPane } = Tabs;
const { Option } = Select;

/**
 * 設置頁面組件
 * 提供系統設置、用戶偏好、通知設置等功能
 */
const SettingsPage: React.FC = () => {
  useDocumentTitle('系統設置');
  const dispatch = useAppDispatch();
  
  // 從 Redux store 獲取用戶設置和系統配置
  const { settings, systemConfig } = useAppSelector((state: any) => state.user);
  
  // 表單實例
  const [generalForm] = Form.useForm();
  const [systemForm] = Form.useForm();
  const [notificationForm] = Form.useForm();
  const [securityForm] = Form.useForm();
  
  // 本地狀態
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('general');
  const [testConnectionLoading, setTestConnectionLoading] = useState(false);

  // 初始化表單數據
  useEffect(() => {
    if (settings) {
      generalForm.setFieldsValue({
        language: settings.language || 'zh-CN',
        theme: settings.theme || 'light',
        autoRefresh: settings.autoRefresh || false,
        refreshInterval: settings.refreshInterval || 30,
        itemsPerPage: settings.itemsPerPage || 20,
        timezone: settings.timezone || 'Asia/Shanghai',
      });
    }

    if (systemConfig) {
      systemForm.setFieldsValue({
        baseUrl: systemConfig.api?.baseUrl || '/api',
        requestTimeout: systemConfig.api?.timeout || 30,
        retryAttempts: systemConfig.api?.retryAttempts || 3,
        retryDelay: systemConfig.api?.retryDelay || 1000,
        maxConcurrentRequests: systemConfig.proxy?.maxConcurrentChecks || 10,
        checkTimeout: systemConfig.proxy?.checkTimeout || 10000,
        proxyRotationInterval: systemConfig.proxy?.checkInterval ? systemConfig.proxy.checkInterval / 1000 : 300,
        maxRetries: systemConfig.proxy?.maxRetries || 3,
        databaseRetentionDays: systemConfig.storage?.maxProxyAge || 30,
      });
    }

    // 設置通知表單初始值
    notificationForm.setFieldsValue({
      emailNotifications: settings?.emailNotifications || false,
      emailAddress: settings?.emailAddress || '',
      desktopNotifications: settings?.desktopNotifications || false,
      soundNotifications: settings?.soundNotifications || false,
      notificationTypes: settings?.notificationTypes || ['task_completed', 'proxy_failed'],
    });

    // 設置安全表單初始值
    securityForm.setFieldsValue({
      twoFactorEnabled: settings?.twoFactorEnabled || false,
      sessionTimeout: settings?.sessionTimeout || 3600,
      passwordPolicy: settings?.passwordPolicy || 'medium',
      apiRateLimit: systemConfig?.apiRateLimit || 1000,
      corsEnabled: systemConfig?.corsEnabled || false,
      allowedOrigins: systemConfig?.allowedOrigins?.join(', ') || '',
    });
  }, [settings, systemConfig, generalForm, systemForm, notificationForm, securityForm]);

  // 保存通用設置
  const handleSaveGeneral = async (values: any) => {
    try {
      setLoading(true);
      dispatch(setUserSettings(values));
      message.success('通用設置已保存');
    } catch (error) {
      message.error('保存失敗: ' + error);
    } finally {
      setLoading(false);
    }
  };

  // 保存系統配置
  const handleSaveSystem = async (values: any) => {
    try {
      setLoading(true);
      // 將扁平的配置值轉換為正確的嵌套結構
      const systemConfigData = {
        api: {
          baseUrl: values.baseUrl || '/api',
          timeout: values.requestTimeout || 30,
          retryAttempts: values.retryAttempts || 3,
          retryDelay: values.retryDelay || 1000,
        },
        websocket: {
          enabled: systemConfig?.websocket?.enabled ?? true,
          reconnectInterval: systemConfig?.websocket?.reconnectInterval ?? 5000,
          maxReconnectAttempts: systemConfig?.websocket?.maxReconnectAttempts ?? 5,
        },
        proxy: {
          maxConcurrentChecks: values.maxConcurrentRequests || 10,
          checkTimeout: values.checkTimeout || 10000,
          checkInterval: values.proxyRotationInterval ? values.proxyRotationInterval * 1000 : 300000,
          maxRetries: values.maxRetries || 3,
        },
        storage: {
          maxProxyAge: values.databaseRetentionDays || 30,
          cleanupInterval: 24,
          backupInterval: 24,
        },
      };
      dispatch(setSystemConfig(systemConfigData));
      message.success('系統配置已保存');
    } catch (error) {
      message.error('保存失敗: ' + error);
    } finally {
      setLoading(false);
    }
  };

  // 保存通知設置
  const handleSaveNotification = async (values: any) => {
    try {
      setLoading(true);
      dispatch(setUserSettings({ ...settings, ...values }));
      message.success('通知設置已保存');
    } catch (error) {
      message.error('保存失敗: ' + error);
    } finally {
      setLoading(false);
    }
  };

  // 保存安全設置
  const handleSaveSecurity = async (values: any) => {
    try {
      setLoading(true);
      dispatch(setUserSettings({ ...settings, ...values }));
      dispatch(setSystemConfig({ ...systemConfig, ...values }));
      message.success('安全設置已保存');
    } catch (error) {
      message.error('保存失敗: ' + error);
    } finally {
      setLoading(false);
    }
  };

  // 測試數據庫連接
  const handleTestConnection = async () => {
    try {
      setTestConnectionLoading(true);
      // TODO: 實現數據庫連接測試
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success('數據庫連接測試成功');
    } catch (error) {
      message.error('數據庫連接測試失敗');
    } finally {
      setTestConnectionLoading(false);
    }
  };

  // 重置所有設置
  const handleResetAll = () => {
    Modal.confirm({
      title: '確認重置',
      content: '確定要重置所有設置到默認值嗎？此操作不可撤銷。',
      onOk: () => {
        // 重置為默認值
        const defaultSettings: UserSettings = {
          theme: 'light',
          language: 'zh-TW',
          timezone: 'Asia/Taipei',
          dateFormat: 'YYYY-MM-DD',
          timeFormat: '24h',
          notifications: {
            email: false,
            browser: false,
            taskCompleted: true,
            proxyFailed: true,
            systemAlerts: true,
          },
          dashboard: {
            autoRefresh: false,
            refreshInterval: 30,
            defaultTimeRange: '1h',
            showCharts: true,
            chartAnimations: true,
          },
        };

        const defaultSystemConfig = {
          api: {
            baseUrl: '/api',
            timeout: 30,
            retryAttempts: 3,
            retryDelay: 1000,
          },
          websocket: {
            enabled: true,
            reconnectInterval: 5000,
            maxReconnectAttempts: 5,
          },
          proxy: {
            maxConcurrentChecks: 10,
            checkTimeout: 10000,
            checkInterval: 300000,
            maxRetries: 3,
          },
          storage: {
            maxProxyAge: 7,
            cleanupInterval: 24,
            backupInterval: 24,
          },
        };

        dispatch(setUserSettings(defaultSettings));
        dispatch(setSystemConfig(defaultSystemConfig));
        message.success('所有設置已重置為默認值');
      }
    });
  };

  // 導出設置
  const handleExportSettings = () => {
    const allSettings = {
      userSettings: settings,
      systemConfig: systemConfig,
      exportTime: new Date().toISOString(),
    };

    const dataStr = JSON.stringify(allSettings, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `proxy-collector-settings-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
    message.success('設置已導出');
  };

  // 導入設置
  const handleImportSettings = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const settings = JSON.parse(e.target?.result as string);
        if (settings.userSettings) {
          dispatch(setUserSettings(settings.userSettings));
        }
        if (settings.systemConfig) {
          dispatch(setSystemConfig(settings.systemConfig));
        }
        message.success('設置已導入');
      } catch (error) {
        message.error('導入失敗: 文件格式錯誤');
      }
    };
    reader.readAsText(file);
    event.target.value = '';
  };

  return (
    <div className="settings-page">
      <Card className="settings-header-card">
        <div className="settings-header">
          <div className="settings-title">
            <SettingOutlined />
            <h2>系統設置</h2>
          </div>
          <div className="settings-actions">
            <Space>
              <Button icon={<SaveOutlined />} onClick={handleExportSettings}>
                導出設置
              </Button>
              <label className="import-button">
                <input
                  type="file"
                  accept=".json"
                  onChange={handleImportSettings}
                  style={{ display: 'none' }}
                />
                <Button icon={<ReloadOutlined />}>
                  導入設置
                </Button>
              </label>
              <Button danger onClick={handleResetAll}>
                重置所有
              </Button>
            </Space>
          </div>
        </div>
      </Card>

      <Card className="settings-content-card">
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          className="settings-tabs"
        >
          <TabPane tab={<span><SettingOutlined />通用設置</span>} key="general">
            <Form
              form={generalForm}
              layout="vertical"
              onFinish={handleSaveGeneral}
              className="settings-form"
            >
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    label="語言"
                    name="language"
                    rules={[{ required: true, message: '請選擇語言' }]}
                  >
                    <Select placeholder="選擇語言">
                      <Option value="zh-CN">中文（簡體）</Option>
                      <Option value="zh-TW">中文（繁體）</Option>
                      <Option value="en-US">English</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="主題"
                    name="theme"
                    rules={[{ required: true, message: '請選擇主題' }]}
                  >
                    <Select placeholder="選擇主題">
                      <Option value="light">淺色主題</Option>
                      <Option value="dark">深色主題</Option>
                      <Option value="auto">自動</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="時區"
                    name="timezone"
                    rules={[{ required: true, message: '請選擇時區' }]}
                  >
                    <Select placeholder="選擇時區">
                      <Option value="Asia/Shanghai">上海 (UTC+8)</Option>
                      <Option value="Asia/Taipei">台北 (UTC+8)</Option>
                      <Option value="UTC">UTC</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="每頁顯示條目數"
                    name="itemsPerPage"
                    rules={[{ required: true, message: '請輸入每頁顯示條目數' }]}
                  >
                    <InputNumber
                      min={10}
                      max={100}
                      step={10}
                      placeholder="每頁顯示條目數"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item
                    label="自動刷新"
                    name="autoRefresh"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="刷新間隔（秒）"
                    name="refreshInterval"
                    rules={[{ required: true, message: '請輸入刷新間隔' }]}
                  >
                    <InputNumber
                      min={5}
                      max={300}
                      step={5}
                      placeholder="刷新間隔"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>
                  保存通用設置
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab={<span><DatabaseOutlined />系統配置</span>} key="system">
            <Form
              form={systemForm}
              layout="vertical"
              onFinish={handleSaveSystem}
              className="settings-form"
            >
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    label="最大並發請求數"
                    name="maxConcurrentRequests"
                    rules={[{ required: true, message: '請輸入最大並發請求數' }]}
                  >
                    <InputNumber
                      min={1}
                      max={100}
                      placeholder="最大並發請求數"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="請求超時時間（秒）"
                    name="requestTimeout"
                    rules={[{ required: true, message: '請輸入請求超時時間' }]}
                  >
                    <InputNumber
                      min={5}
                      max={300}
                      placeholder="請求超時時間"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="重試次數"
                    name="retryAttempts"
                    rules={[{ required: true, message: '請輸入重試次數' }]}
                  >
                    <InputNumber
                      min={0}
                      max={10}
                      placeholder="重試次數"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="重試延遲（毫秒）"
                    name="retryDelay"
                    rules={[{ required: true, message: '請輸入重試延遲' }]}
                  >
                    <InputNumber
                      min={100}
                      max={10000}
                      step={100}
                      placeholder="重試延遲"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Divider orientation="left">代理設置</Divider>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="啟用代理輪換"
                    name="proxyRotationEnabled"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="代理輪換間隔（秒）"
                    name="proxyRotationInterval"
                    rules={[{ required: true, message: '請輸入代理輪換間隔' }]}
                  >
                    <InputNumber
                      min={10}
                      max={3600}
                      step={10}
                      placeholder="代理輪換間隔"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Divider orientation="left">數據庫設置</Divider>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="啟用數據庫清理"
                    name="databaseCleanupEnabled"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="數據保留天數"
                    name="databaseRetentionDays"
                    rules={[{ required: true, message: '請輸入數據保留天數' }]}
                  >
                    <InputNumber
                      min={1}
                      max={365}
                      placeholder="數據保留天數"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="日誌級別"
                    name="logLevel"
                    rules={[{ required: true, message: '請選擇日誌級別' }]}
                  >
                    <Select placeholder="選擇日誌級別">
                      <Option value="debug">Debug</Option>
                      <Option value="info">Info</Option>
                      <Option value="warn">Warning</Option>
                      <Option value="error">Error</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>
                    保存系統配置
                  </Button>
                  <Button onClick={handleTestConnection} loading={testConnectionLoading}>
                    測試連接
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab={<span><NotificationOutlined />通知設置</span>} key="notification">
            <Form
              form={notificationForm}
              layout="vertical"
              onFinish={handleSaveNotification}
              className="settings-form"
            >
              <Row gutter={24}>
                <Col span={24}>
                  <Form.Item
                    label="郵件通知"
                    name="emailNotifications"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="郵箱地址"
                    name="emailAddress"
                    rules={[
                      { type: 'email', message: '請輸入有效的郵箱地址' }
                    ]}
                  >
                    <Input placeholder="郵箱地址" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="桌面通知"
                    name="desktopNotifications"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="聲音通知"
                    name="soundNotifications"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item
                    label="通知類型"
                    name="notificationTypes"
                  >
                    <Select
                      mode="multiple"
                      placeholder="選擇通知類型"
                    >
                      <Option value="task_completed">任務完成</Option>
                      <Option value="task_failed">任務失敗</Option>
                      <Option value="proxy_failed">代理失敗</Option>
                      <Option value="system_error">系統錯誤</Option>
                      <Option value="proxy_expired">代理過期</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>
                  保存通知設置
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab={<span><SecurityScanOutlined />安全設置</span>} key="security">
            <Form
              form={securityForm}
              layout="vertical"
              onFinish={handleSaveSecurity}
              className="settings-form"
            >
              <Row gutter={24}>
                <Col span={24}>
                  <Alert
                    message="安全提醒"
                    description="請妥善保管您的設置信息，避免洩露敏感數據。"
                    type="warning"
                    showIcon
                    style={{ marginBottom: 24 }}
                  />
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="雙重認證"
                    name="twoFactorEnabled"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="會話超時（秒）"
                    name="sessionTimeout"
                    rules={[{ required: true, message: '請輸入會話超時時間' }]}
                  >
                    <InputNumber
                      min={300}
                      max={86400}
                      step={300}
                      placeholder="會話超時時間"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="密碼策略"
                    name="passwordPolicy"
                    rules={[{ required: true, message: '請選擇密碼策略' }]}
                  >
                    <Select placeholder="選擇密碼策略">
                      <Option value="weak">弱（至少6位）</Option>
                      <Option value="medium">中等（至少8位，包含字母和數字）</Option>
                      <Option value="strong">強（至少12位，包含大小寫、數字和特殊字符）</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="API速率限制（次/分鐘）"
                    name="apiRateLimit"
                    rules={[{ required: true, message: '請輸入API速率限制' }]}
                  >
                    <InputNumber
                      min={100}
                      max={10000}
                      step={100}
                      placeholder="API速率限制"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Divider orientation="left">CORS 設置</Divider>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="啟用 CORS"
                    name="corsEnabled"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item
                    label="允許的來源"
                    name="allowedOrigins"
                    help="多個來源請用逗號分隔，例如: http://localhost:3000, https://example.com"
                  >
                    <Input.TextArea
                      rows={3}
                      placeholder="允許的來源"
                    />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>
                  保存安全設置
                </Button>
              </Form.Item>
            </Form>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default SettingsPage;