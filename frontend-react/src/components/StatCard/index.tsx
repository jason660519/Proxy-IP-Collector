/**
 * 統計卡片組件
 * @description 顯示統計數據的卡片組件
 */

import React from 'react';
import { Card, Progress, Statistic, Typography, Space } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { formatNumber } from '../../utils/format';
import './StatCard.css';

const { Text } = Typography;

interface StatCardProps {
  title: string;
  value: string | number;
  suffix?: string;
  icon: React.ReactNode;
  color: string;
  progress?: number;
  trend?: number;
  trendLabel?: string;
  loading?: boolean;
}

/**
 * 統計卡片組件
 */
const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  suffix,
  icon,
  color,
  progress,
  trend,
  trendLabel = '較昨日',
  loading = false,
}) => {
  const trendIcon = trend && trend > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />;
  const trendColor = trend && trend > 0 ? '#3f8600' : '#cf1322';
  const trendText = trend ? `${Math.abs(trend)}%` : '';

  return (
    <Card className="stat-card" loading={loading}>
      <div className="stat-card-content">
        <div className="stat-card-icon" style={{ backgroundColor: color }}>
          {icon}
        </div>
        
        <div className="stat-card-info">
          <Statistic
            title={title}
            value={typeof value === 'number' ? formatNumber(value) : value}
            suffix={suffix}
            valueStyle={{ color, fontSize: '24px', fontWeight: 'bold' }}
          />
          
          {progress !== undefined && (
            <Progress
              percent={progress}
              strokeColor={color}
              showInfo={false}
              size="small"
              style={{ marginTop: '8px' }}
            />
          )}
          
          {trend !== undefined && (
            <div className="stat-card-trend" style={{ color: trendColor }}>
              <Space size="small">
                {trendIcon}
                <Text style={{ color: trendColor, fontSize: '12px' }}>
                  {trendText} {trendLabel}
                </Text>
              </Space>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

export default StatCard;