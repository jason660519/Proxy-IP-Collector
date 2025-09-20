import React from 'react';
import './Button.css';

export interface ButtonProps {
  /**
   * 按鈕類型
   */
  type?: 'primary' | 'secondary' | 'danger' | 'ghost';
  /**
   * 按鈕大小
   */
  size?: 'small' | 'medium' | 'large';
  /**
   * 是否禁用
   */
  disabled?: boolean;
  /**
   * 是否加載中
   */
  loading?: boolean;
  /**
   * 點擊事件處理函數
   */
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  /**
   * 子元素
   */
  children: React.ReactNode;
  /**
   * 自定義類名
   */
  className?: string;
  /**
   * 自定義樣式
   */
  style?: React.CSSProperties;
  /**
   * HTML按鈕類型
   */
  htmlType?: 'button' | 'submit' | 'reset';
  /**
   * 圖標
   */
  icon?: React.ReactNode;
}

/**
 * 通用按鈕組件
 * 提供一致的按鈕樣式和行為
 */
export const Button: React.FC<ButtonProps> = ({
  type = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  onClick,
  children,
  className = '',
  style,
  htmlType = 'button',
  icon,
}) => {
  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled || loading) {
      event.preventDefault();
      return;
    }
    onClick?.(event);
  };

  const classes = [
    'btn',
    `btn-${type}`,
    `btn-${size}`,
    className,
    loading ? 'btn-loading' : '',
  ].filter(Boolean).join(' ');

  return (
    <button
      type={htmlType}
      className={classes}
      style={style}
      disabled={disabled || loading}
      onClick={handleClick}
    >
      {loading && <span className="btn-spinner" />}
      {icon && <span className="btn-icon">{icon}</span>}
      <span className="btn-content">{children}</span>
    </button>
  );
};

export default Button;