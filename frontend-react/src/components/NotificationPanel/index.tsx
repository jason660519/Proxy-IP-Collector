/**
 * 通知面板組件
 * @description 顯示系統通知和消息
 */

import React, { useState } from 'react';
import { Drawer, List, Badge, Button, Empty, Typography, Space, Tag } from 'antd';
import { BellOutlined, CheckOutlined, DeleteOutlined } from '@ant-design/icons';
import { useAppSelector, useAppDispatch } from '../../hooks';
import { formatTime } from '../../utils/format';
import './NotificationPanel.css';

const { Text, Paragraph } = Typography;

interface NotificationPanelProps {
  visible: boolean;
  onClose: () => void;
}

/**
 * 通知面板組件
 */
const NotificationPanel: React.FC<NotificationPanelProps> = ({ visible, onClose }) => {
  const dispatch = useAppDispatch();
  const notifications = useAppSelector((state) => state.notification.notifications);
  
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  // 過濾通知
  const filteredNotifications = notifications.filter(notification => {
    if (filter === 'unread') {
      return !notification.read;
    }
    return true;
  });

  // 標記為已讀
  const markAsRead = (id: string) => {
    dispatch({ type: 'notification/markAsRead', payload: id });
  };

  // 標記全部為已讀
  const markAllAsRead = () => {
    dispatch({ type: 'notification/markAllAsRead' });
  };

  // 刪除通知
  const deleteNotification = (id: string) => {
    dispatch({ type: 'notification/deleteNotification', payload: id });
  };

  // 清除所有通知
  const clearAll = () => {
    dispatch({ type: 'notification/clearAll' });
  };

  // 獲取通知類型標籤顏色
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      case 'info':
      default:
        return 'processing';
    }
  };

  // 獲取通知圖標
  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success':
        return '🟢';
      case 'warning':
        return '🟡';
      case 'error':
        return '🔴';
      case 'info':
      default:
        return '🔵';
    }
  };

  return (
    <Drawer
      title={
        <Space>
          <BellOutlined />
          <span>通知中心</span>
          <Badge count={notifications.filter(n => !n.read).length} size="small" />
        </Space>
      }
      placement="right"
      width={400}
      onClose={onClose}
      open={visible}
      className="notification-panel"
      extra={
        <Space>
          <Button size="small" onClick={markAllAsRead} disabled={notifications.filter(n => !n.read).length === 0}>
            全部已讀
          </Button>
          <Button size="small" danger onClick={clearAll} disabled={notifications.length === 0}>
            清空
          </Button>
        </Space>
      }
    >
      <div className="notification-panel-header">
        <Space>
          <Button
            type={filter === 'all' ? 'primary' : 'default'}
            size="small"
            onClick={() => setFilter('all')}
          >
            全部 ({notifications.length})
          </Button>
          <Button
            type={filter === 'unread' ? 'primary' : 'default'}
            size="small"
            onClick={() => setFilter('unread')}
          >
            未讀 ({notifications.filter(n => !n.read).length})
          </Button>
        </Space>
      </div>

      {filteredNotifications.length === 0 ? (
        <Empty
          description="暫無通知"
          style={{ marginTop: '50px' }}
        />
      ) : (
        <List
          className="notification-list"
          dataSource={filteredNotifications}
          renderItem={(notification) => (
            <List.Item
              className={`notification-item ${!notification.read ? 'unread' : ''}`}
              actions={[
                <Button
                  key="read"
                  type="text"
                  size="small"
                  icon={<CheckOutlined />}
                  onClick={() => markAsRead(notification.id)}
                  disabled={notification.read}
                />,
                <Button
                  key="delete"
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => deleteNotification(notification.id)}
                />
              ]}
            >
              <List.Item.Meta
                avatar={
                  <span className="notification-icon">
                    {getNotificationIcon(notification.type)}
                  </span>
                }
                title={
                  <Space>
                    <Text strong>{notification.title}</Text>
                    <Tag color={getTypeColor(notification.type)}>
                      {notification.type}
                    </Tag>
                  </Space>
                }
                description={
                  <div>
                    <Paragraph ellipsis={{ rows: 2 }} style={{ margin: 0 }}>
                      {notification.message}
                    </Paragraph>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {formatTime(notification.createdAt)}
                    </Text>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Drawer>
  );
};

export default NotificationPanel;