/**
 * 代理卡片組件
 * @description 以卡片形式展示代理信息的組件
 */

import React from 'react';
import { Card, Tag, Badge, Space, Button, Tooltip, Progress } from 'antd';
import {
  GlobalOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ThunderboltOutlined,
  WifiOutlined,
  DeleteOutlined,
  EditOutlined,
} from '@ant-design/icons';
import { Proxy } from '../../types/proxy.types';
import { formatTime } from '../../utils/format';
import './ProxyCard.css';

interface ProxyCardProps {
  proxy: Proxy;
  selected?: boolean;
  onSelect?: (proxy: Proxy) => void;
  onEdit?: (proxy: Proxy) => void;
  onDelete?: (proxy: Proxy) => void;
  onTest?: (proxy: Proxy) => void;
}

/**
 * 代理卡片組件
 * 以卡片形式展示代理的詳細信息
 */
const ProxyCard: React.FC<ProxyCardProps> = ({
  proxy,
  selected = false,
  onSelect,
  onEdit,
  onDelete,
  onTest,
}) => {
  // 獲取狀態顏色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  // 獲取狀態文本
  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return '活動';
      case 'inactive':
        return '非活動';
      case 'failed':
        return '失效';
      default:
        return '未知';
    }
  };

  // 獲取響應時間顏色
  const getResponseTimeColor = (time: number) => {
    if (time < 1000) return '#52c41a'; // 綠色
    if (time < 3000) return '#faad14'; // 橙色
    return '#ff4d4f'; // 紅色
  };

  // 獲取成功率進度條顏色
  const getSuccessRateColor = (rate: number) => {
    if (rate >= 90) return '#52c41a';
    if (rate >= 70) return '#faad14';
    return '#ff4d4f';
  };

  // 獲取類型顏色
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'http':
        return 'blue';
      case 'https':
        return 'green';
      case 'socks4':
        return 'orange';
      case 'socks5':
        return 'purple';
      default:
        return 'default';
    }
  };

  return (
    <Card
      className={`proxy-card ${selected ? 'selected' : ''}`}
      hoverable
      onClick={() => onSelect?.(proxy)}
      actions={[
        <Tooltip title="測試連接" key="test">
          <Button
            type="text"
            icon={<ThunderboltOutlined />}
            onClick={(e) => {
              e.stopPropagation();
              onTest?.(proxy);
            }}
          />
        </Tooltip>,
        <Tooltip title="編輯" key="edit">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={(e) => {
              e.stopPropagation();
              onEdit?.(proxy);
            }}
          />
        </Tooltip>,
        <Tooltip title="刪除" key="delete">
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={(e) => {
              e.stopPropagation();
              onDelete?.(proxy);
            }}
          />
        </Tooltip>,
      ]}
    >
      {/* 卡片頭部 */}
      <div className="proxy-card-header">
        <div className="proxy-info">
          <div className="proxy-ip">
            <Badge
              status={getStatusColor(proxy.status) as any}
              text={proxy.ip}
            />
          </div>
          <div className="proxy-port">
            <WifiOutlined /> {proxy.port}
          </div>
        </div>
        <div className="proxy-status">
          <Tag color={getStatusColor(proxy.status)}>
            {getStatusText(proxy.status)}
          </Tag>
        </div>
      </div>

      {/* 卡片內容 */}
      <div className="proxy-card-body">
        <Space direction="vertical" style={{ width: '100%' }} size="small">
          {/* 代理類型 */}
          <div className="proxy-type">
            <span className="label">類型：</span>
            {proxy.type && (
              <Tag color={getTypeColor(proxy.type)}>
                {proxy.type.toUpperCase()}
              </Tag>
            )}
          </div>

          {/* 響應時間 */}
          <div className="proxy-response-time">
            <span className="label">響應時間：</span>
            <span
              className="value"
              style={{ color: getResponseTimeColor(proxy.responseTime) }}
            >
              {proxy.responseTime}ms
            </span>
          </div>

          {/* 位置信息 */}
          {proxy.location && (
            <div className="proxy-location">
              <span className="label">位置：</span>
              <Space size="small">
                <GlobalOutlined />
                <span className="value">
                  {proxy.location.country} - {proxy.location.city}
                </span>
                {proxy.location.flag && (
                  <img
                    src={proxy.location.flag}
                    alt="flag"
                    className="flag-icon"
                  />
                )}
              </Space>
            </div>
          )}

          {/* 成功率 */}
          {proxy.successRate !== undefined && (
            <div className="proxy-success-rate">
              <div className="success-rate-header">
                <span className="label">成功率：</span>
                <span className="value">{proxy.successRate}%</span>
              </div>
              <Progress
                percent={proxy.successRate}
                strokeColor={getSuccessRateColor(proxy.successRate)}
                size="small"
                showInfo={false}
              />
            </div>
          )}

          {/* 使用次數 */}
          {proxy.usageCount !== undefined && (
            <div className="proxy-usage">
              <span className="label">使用次數：</span>
              <span className="value">{proxy.usageCount}</span>
            </div>
          )}

          {/* 最後檢查時間 */}
          <div className="proxy-last-checked">
            <span className="label">最後檢查：</span>
            <Space size="small">
              <ClockCircleOutlined />
              <span className="value">
                {formatTime(proxy.lastChecked)}
              </span>
            </Space>
          </div>

          {/* 標籤 */}
          {proxy.tags && proxy.tags.length > 0 && (
            <div className="proxy-tags">
              <span className="label">標籤：</span>
              <div className="tags-container">
                {proxy.tags.map((tag, index) => (
                  <Tag key={index}>
                    {tag}
                  </Tag>
                ))}
              </div>
            </div>
          )}

          {/* 匿名級別 */}
          {proxy.anonymity && (
            <div className="proxy-anonymity">
              <span className="label">匿名級別：</span>
              <Tag
                color={
                  proxy.anonymity === 'elite' ? 'red' :
                  proxy.anonymity === 'anonymous' ? 'orange' : 'green'
                }
              >
                {proxy.anonymity === 'elite' ? '高匿名' :
                 proxy.anonymity === 'anonymous' ? '匿名' : '透明'}
              </Tag>
            </div>
          )}
        </Space>
      </div>

      {/* 卡片底部 */}
      <div className="proxy-card-footer">
        <div className="proxy-id">
          ID: {proxy.id}
        </div>
        <div className="proxy-actions">
          <Space size="small">
            {proxy.isActive && (
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
            )}
            {proxy.isRotating && (
              <span className="rotating-indicator">輪換中</span>
            )}
          </Space>
        </div>
      </div>
    </Card>
  );
};

export default ProxyCard;