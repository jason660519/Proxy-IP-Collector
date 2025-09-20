import React from 'react';
import './Card.css';

export interface CardProps {
  /**
   * 卡片標題
   */
  title?: React.ReactNode;
  /**
   * 卡片額外操作區域
   */
  extra?: React.ReactNode;
  /**
   * 卡片內容
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
   * 是否顯示邊框
   */
  bordered?: boolean;
  /**
   * 是否可懸停
   */
  hoverable?: boolean;
  /**
   * 卡片大小
   */
  size?: 'small' | 'medium' | 'large';
  /**
   * 點擊事件
   */
  onClick?: (event: React.MouseEvent<HTMLDivElement>) => void;
  /**
   * 自定義頭部
   */
  headStyle?: React.CSSProperties;
  /**
   * 自定義內容區域樣式
   */
  bodyStyle?: React.CSSProperties;
  /**
   * 是否顯示頭部
   */
  showHead?: boolean;
}

/**
 * 通用卡片組件
 * 提供一致的卡片樣式和行為
 */
export const Card: React.FC<CardProps> = ({
  title,
  extra,
  children,
  className = '',
  style,
  bordered = true,
  hoverable = false,
  size = 'medium',
  onClick,
  headStyle,
  bodyStyle,
  showHead = true,
}) => {
  const classes = [
    'card',
    `card-${size}`,
    bordered ? 'card-bordered' : '',
    hoverable ? 'card-hoverable' : '',
    onClick ? 'card-clickable' : '',
    className,
  ].filter(Boolean).join(' ');

  const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (onClick) {
      onClick(event);
    }
  };

  const shouldShowHead = showHead && (title || extra);

  return (
    <div className={classes} style={style} onClick={handleClick}>
      {shouldShowHead && (
        <div className="card-head" style={headStyle}>
          <div className="card-head-wrapper">
            {title && (
              <div className="card-head-title">
                {title}
              </div>
            )}
            {extra && (
              <div className="card-head-extra">
                {extra}
              </div>
            )}
          </div>
        </div>
      )}
      
      <div className="card-body" style={bodyStyle}>
        {children}
      </div>
    </div>
  );
};

export default Card;