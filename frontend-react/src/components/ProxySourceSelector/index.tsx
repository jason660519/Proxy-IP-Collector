import React, { useState, useEffect } from 'react';
import { Select, Card, Tag, Space, Typography, Descriptions, Alert, Button, Tooltip, Modal } from 'antd';
import { useGetAvailableSourcesQuery } from '@/services/proxyApi';
import { getProxySourceTemplate } from '@/utils/proxySourceTemplates';
import { SettingOutlined } from '@ant-design/icons';

const { Option } = Select;
const { Text, Title } = Typography;



interface ProxySourceSelectorProps {
  value?: string;
  onChange?: (sourceName: string, config: any) => void;
  disabled?: boolean;
}

/**
 * 代理來源選擇器組件
 * 
 * 提供圖形化界面選擇代理來源，並自動生成對應的配置
 */
const ProxySourceSelector: React.FC<ProxySourceSelectorProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [sourceDetails, setSourceDetails] = useState<any | null>(null);

  // 獲取可用的代理來源列表
  const { data: sourcesData, isLoading, error } = useGetAvailableSourcesQuery();

  useEffect(() => {
    if (value && sourcesData?.sources) {
      const source = sourcesData.sources.find((s: any) => s.name === value);
      if (source) {
        setSelectedSource(value);
        setSourceDetails(source);
      }
    }
  }, [value, sourcesData]);

  const handleSourceChange = (sourceName: string) => {
    setSelectedSource(sourceName);
    
    if (sourcesData?.sources) {
      const source = sourcesData.sources.find((s: any) => s.name === sourceName);
      if (source) {
        setSourceDetails(source);
        
        // 首先嘗試使用預設配置模板
        const template = getProxySourceTemplate(sourceName);
        if (template && onChange) {
          onChange(sourceName, template.config);
        } else {
          // 如果沒有模板，生成基本配置
          const config = generateDefaultConfig(source);
          
          // 通知父組件
          if (onChange) {
            onChange(sourceName, config);
          }
        }
      }
    }
  };

  const generateDefaultConfig = (source: any) => {
    const baseConfig = {
      source_type: source.source_type,
      rate_limit: source.rate_limit,
      timeout: source.timeout,
      retry_count: source.retry_count,
    };

    switch (source.source_type) {
      case 'web_scraping':
        return {
          ...baseConfig,
          base_url: source.base_url,
          page_range: [1, 10],
        };
      
      case 'api':
        return {
          ...baseConfig,
          api_endpoint: source.api_endpoint,
          page_range: [1, 5],
          limit_per_page: 50,
        };
      
      case 'playwright':
        return {
          ...baseConfig,
          base_url: source.base_url,
          use_playwright: true,
        };
      
      default:
        return baseConfig;
    }
  };

  const getSourceTypeColor = (type: string) => {
    switch (type) {
      case 'web_scraping':
        return 'blue';
      case 'api':
        return 'green';
      case 'playwright':
        return 'orange';
      default:
        return 'default';
    }
  };

  const getSourceTypeText = (type: string) => {
    switch (type) {
      case 'web_scraping':
        return '網頁爬蟲';
      case 'api':
        return 'API接口';
      case 'playwright':
        return '瀏覽器模擬';
      default:
        return type;
    }
  };

  const showConfigDetails = () => {
    if (!selectedSource) return;
    
    const template = getProxySourceTemplate(selectedSource);
    if (template) {
      // 顯示配置詳情對話框或彈出層
      Modal.info({
        title: `配置模板詳情 - ${template.name}`,
        width: 600,
        content: (
          <div style={{ marginTop: 16 }}>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="來源類型">
                <Tag color="blue">{template.source_type}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="描述">
                {template.description}
              </Descriptions.Item>
              <Descriptions.Item label="預設配置">
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: '8px', 
                  borderRadius: '4px',
                  fontSize: '12px',
                  maxHeight: '200px',
                  overflow: 'auto'
                }}>
                  {JSON.stringify(template.config, null, 2)}
                </pre>
              </Descriptions.Item>
            </Descriptions>
          </div>
        ),
      });
    }
  };

  if (error) {
    return (
      <Alert
        message="加載代理來源失敗"
        description="無法獲取可用的代理來源列表"
        type="error"
        showIcon
      />
    );
  }

  return (
    <div style={{ marginBottom: 16 }}>
      <Title level={5} style={{ marginBottom: 8 }}>
        選擇代理來源
      </Title>
      
      <Select
        style={{ width: '100%', marginBottom: 16 }}
        placeholder="請選擇代理來源"
        value={selectedSource}
        onChange={handleSourceChange}
        loading={isLoading}
        disabled={disabled}
        size="large"
        suffixIcon={
          selectedSource ? (
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <Tooltip title="查看配置詳情">
                <Button
                  type="text"
                  icon={<SettingOutlined />}
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    showConfigDetails();
                  }}
                  style={{ marginRight: 8 }}
                />
              </Tooltip>
              {/* 保留默認的下拉箭頭 */}
            </div>
          ) : undefined
        }
      >
        {sourcesData?.sources?.map((source: any) => (
          <Option key={source.name} value={source.name}>
            <Space>
              {source.name}
              <Tag color={getSourceTypeColor(source.source_type)}>
                {getSourceTypeText(source.source_type)}
              </Tag>
              {!source.enabled && <Tag color="red">已禁用</Tag>}
            </Space>
          </Option>
        ))}
      </Select>

      {sourceDetails && (
        <Card size="small" title="來源詳情" style={{ marginTop: 8 }}>
          <Descriptions column={2} size="small">
            <Descriptions.Item label="名稱">
              <Text strong>{sourceDetails.name}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="類型">
              <Tag color={getSourceTypeColor(sourceDetails.source_type)}>
                {getSourceTypeText(sourceDetails.source_type)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="描述">
              {sourceDetails.description}
            </Descriptions.Item>
            <Descriptions.Item label="狀態">
              <Tag color={sourceDetails.enabled ? 'green' : 'red'}>
                {sourceDetails.enabled ? '啟用' : '禁用'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="速率限制">
              {sourceDetails.rate_limit} 秒
            </Descriptions.Item>
            <Descriptions.Item label="超時時間">
              {sourceDetails.timeout} 秒
            </Descriptions.Item>
            <Descriptions.Item label="重試次數">
              {sourceDetails.retry_count} 次
            </Descriptions.Item>
          </Descriptions>

          {sourceDetails.base_url && (
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">基礎URL：</Text>
              <Text code>{sourceDetails.base_url}</Text>
            </div>
          )}

          {sourceDetails.api_endpoint && (
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">API端點：</Text>
              <Text code>{sourceDetails.api_endpoint}</Text>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default ProxySourceSelector;