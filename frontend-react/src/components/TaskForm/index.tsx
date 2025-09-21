import React, { useState, useEffect } from 'react';
import { Button, Input, Card } from '../index';

import { Task, TaskType } from '../../types/task.types';
import ProxySourceSelector from '../ProxySourceSelector';
import './TaskForm.css';

export interface TaskFormProps {
  /**
   * 任務數據（編輯模式）
   */
  task?: Task;
  /**
   * 是否顯示表單
   */
  visible?: boolean;
  /**
   * 提交按鈕文本
   */
  submitText?: string;
  /**
   * 表單提交事件
   */
  onSubmit?: (task: Partial<Task>) => void;
  /**
   * 取消事件
   */
  onCancel?: () => void;
  /**
   * 表單標題
   */
  title?: string;
  /**
   * 是否禁用
   */
  disabled?: boolean;
}

/**
 * 任務表單組件
 * 用於創建和編輯任務
 */
export const TaskForm: React.FC<TaskFormProps> = ({
  task,
  visible = true,
  submitText = '創建任務',
  onSubmit,
  onCancel,
  title = task ? '編輯任務' : '創建任務',
  disabled = false,
}) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'data_collection' as TaskType,
    config: '',
    schedule: '',
    priority: 1,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [useProxySourceSelector, setUseProxySourceSelector] = useState(false);
  const [selectedProxySource, setSelectedProxySource] = useState<string>('');

  useEffect(() => {
    if (task) {
      setFormData({
        name: task.name,
        description: task.description || '',
        type: task.type,
        config: task.config ? JSON.stringify(task.config, null, 2) : '',
        schedule: task.schedule || '',
        priority: task.priority || 1,
      });
      // 檢查是否包含代理來源配置
      if (task.config && task.config.source_type) {
        setUseProxySourceSelector(true);
        // 嘗試從配置中識別來源名稱
        const sourceName = task.config.source_name || 
                         (task.config.base_url && extractSourceName(task.config.base_url)) ||
                         (task.config.api_endpoint && extractSourceName(task.config.api_endpoint)) ||
                         '';
        setSelectedProxySource(sourceName);
      }
    } else {
      setFormData({
        name: '',
        description: '',
        type: 'data_collection',
        config: '',
        schedule: '',
        priority: 1,
      });
      setUseProxySourceSelector(false);
      setSelectedProxySource('');
    }
    setErrors({});
  }, [task]);

  const extractSourceName = (url: string) => {
    // 從URL中提取可能的來源名稱
    try {
      const urlObj = new URL(url);
      const hostname = urlObj.hostname;
      if (hostname.includes('89ip')) return '89ip.cn';
      if (hostname.includes('kuaidaili')) return 'kuaidaili-intr';
      if (hostname.includes('geonode')) return 'geonode-api-v2';
      if (hostname.includes('proxydb')) return 'proxydb-net';
      if (hostname.includes('proxynova')) return 'proxynova-com';
      if (hostname.includes('spys')) return 'spys-one';
      if (hostname.includes('free-proxy-list')) return 'free-proxy-list.net';
      if (hostname.includes('sslproxies')) return 'ssl-proxies';
      return '';
    } catch {
      return '';
    }
  };

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // 清除對應字段的錯誤
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleProxySourceChange = (sourceName: string, config: any) => {
    setSelectedProxySource(sourceName);
    setFormData(prev => ({ 
      ...prev, 
      config: JSON.stringify(config, null, 2),
      description: `使用代理來源: ${sourceName}`
    }));
  };

  const handleUseProxySelectorChange = (useSelector: boolean) => {
    setUseProxySourceSelector(useSelector);
    if (!useSelector) {
      setSelectedProxySource('');
      setFormData(prev => ({ ...prev, config: '' }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = '任務名稱不能為空';
    }

    if (!formData.type) {
      newErrors.type = '請選擇任務類型';
    }

    if (formData.config.trim()) {
      try {
        JSON.parse(formData.config);
      } catch (error) {
        newErrors.config = '配置格式錯誤，請輸入有效的JSON';
      }
    }

    if (formData.priority < 1 || formData.priority > 10) {
      newErrors.priority = '優先級必須在1-10之間';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm() || disabled) {
      return;
    }

    setLoading(true);
    
    try {
      let config = {};
      if (formData.config.trim()) {
        config = JSON.parse(formData.config);
      }

      const taskData: Partial<Task> = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        type: formData.type,
        config,
        schedule: formData.schedule.trim() || undefined,
        priority: formData.priority,
      };

      if (task) {
        taskData.id = task.id;
        taskData.status = task.status;
        taskData.createdAt = task.createdAt;
      }

      onSubmit?.(taskData);
      
      // 重置表單（如果不是編輯模式）
      if (!task) {
        setFormData({
          name: '',
          description: '',
          type: 'data_collection',
          config: '',
          schedule: '',
          priority: 1,
        });
      }
    } catch (error) {
      console.error('提交任務失敗:', error);
      setErrors({ submit: '提交失敗，請重試' });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    onCancel?.();
  };

  if (!visible) {
    return null;
  }

  return (
    <Card title={title} className="task-form-card">
      <form onSubmit={handleSubmit} className="task-form">
        <div className="form-group">
          <label className="form-label">
            任務名稱 <span className="required">*</span>
          </label>
          <Input
            value={formData.name}
            onChange={(value, _event) => handleInputChange('name', value)}
            placeholder="請輸入任務名稱"
            disabled={disabled}
            error={!!errors.name}
            errorMessage={errors.name}
            maxLength={100}
          />
        </div>

        <div className="form-group">
          <label className="form-label">任務描述</label>
          <Input
            value={formData.description}
            onChange={(value, _event) => handleInputChange('description', value)}
            placeholder="請輸入任務描述（可選）"
            disabled={disabled}
            maxLength={500}
          />
        </div>

        <div className="form-group">
          <label className="form-label">
            任務類型 <span className="required">*</span>
          </label>
          <select
            value={formData.type}
            onChange={(e) => handleInputChange('type', e.target.value)}
            className="form-select"
            disabled={disabled}
          >
            <option value="proxy_collection">代理收集</option>
            <option value="proxy_validation">代理驗證</option>
            <option value="data_export">數據導出</option>
            <option value="system_maintenance">系統維護</option>
          </select>
          {errors.type && <div className="error-message">{errors.type}</div>}
        </div>

        <div className="form-group">
          <label className="form-label">配置方式</label>
          <div style={{ marginBottom: 12 }}>
            <label style={{ marginRight: 16 }}>
              <input
                type="radio"
                checked={!useProxySourceSelector}
                onChange={() => handleUseProxySelectorChange(false)}
                disabled={disabled}
                style={{ marginRight: 8 }}
              />
              手動輸入JSON配置
            </label>
            <label>
              <input
                type="radio"
                checked={useProxySourceSelector}
                onChange={() => handleUseProxySelectorChange(true)}
                disabled={disabled}
                style={{ marginRight: 8 }}
              />
              使用代理來源選擇器
            </label>
          </div>
        </div>

        {useProxySourceSelector ? (
          <div className="form-group">
            <ProxySourceSelector
              value={selectedProxySource}
              onChange={handleProxySourceChange}
              disabled={disabled}
            />
          </div>
        ) : (
          <div className="form-group">
            <label className="form-label">配置（JSON格式）</label>
            <textarea
              value={formData.config}
              onChange={(e) => handleInputChange('config', e.target.value)}
              placeholder='例如：\n{\n  "timeout": 30,\n  "retry_count": 3\n}'
              className="form-textarea"
              disabled={disabled}
              rows={6}
            />
            {errors.config && <div className="error-message">{errors.config}</div>}
          </div>
        )}

        <div className="form-group">
          <label className="form-label">定時任務（Cron表達式）</label>
          <Input
            value={formData.schedule}
            onChange={(value, _event) => handleInputChange('schedule', value)}
            placeholder="例如：0 0 * * * （每天凌晨）"
            disabled={disabled}
          />
        </div>

        <div className="form-group">
          <label className="form-label">
            優先級 <span className="required">*</span>
          </label>
          <Input
            type="number"
            value={formData.priority.toString()}
            onChange={(value, _event) => handleInputChange('priority', parseInt(value.toString()) || 1)}
            placeholder="1-10，數字越大優先級越高"
            disabled={disabled}
            error={!!errors.priority}
            errorMessage={errors.priority}
          />
        </div>

        {errors.submit && (
          <div className="form-error-message">
            {errors.submit}
          </div>
        )}

        <div className="form-actions">
          <Button
            type="secondary"
            onClick={handleCancel}
            disabled={disabled || loading}
          >
            取消
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            disabled={disabled}
          >
            {submitText}
          </Button>
        </div>
      </form>
    </Card>
  );
};

export default TaskForm;