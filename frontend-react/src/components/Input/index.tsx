import React, { useState, useRef, useEffect } from 'react';
import './Input.css';

export interface InputProps {
  /**
   * 輸入類型
   */
  type?: 'text' | 'password' | 'email' | 'number' | 'tel' | 'url' | 'search';
  /**
   * 輸入框大小
   */
  size?: 'small' | 'medium' | 'large';
  /**
   * 占位符文本
   */
  placeholder?: string;
  /**
   * 輸入框值
   */
  value?: string;
  /**
   * 默認值
   */
  defaultValue?: string;
  /**
   * 是否禁用
   */
  disabled?: boolean;
  /**
   * 是否只讀
   */
  readOnly?: boolean;
  /**
   * 是否顯示清除按鈕
   */
  allowClear?: boolean;
  /**
   * 是否顯示密碼切換按鈕（僅限密碼類型）
   */
  showPasswordToggle?: boolean;
  /**
   * 前綴圖標
   */
  prefix?: React.ReactNode;
  /**
   * 後綴圖標
   */
  suffix?: React.ReactNode;
  /**
   * 輸入框改變事件
   */
  onChange?: (value: string, event: React.ChangeEvent<HTMLInputElement>) => void;
  /**
   * 輸入框聚焦事件
   */
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  /**
   * 輸入框失焦事件
   */
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  /**
   * 按下Enter鍵事件
   */
  onPressEnter?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  /**
   * 清除事件
   */
  onClear?: () => void;
  /**
   * 自定義類名
   */
  className?: string;
  /**
   * 自定義樣式
   */
  style?: React.CSSProperties;
  /**
   * 最大長度
   */
  maxLength?: number;
  /**
   * 自動聚焦
   */
  autoFocus?: boolean;
  /**
   * 自動完成
   */
  autoComplete?: string;
  /**
   * 輸入框名稱
   */
  name?: string;
  /**
   * 輸入框ID
   */
  id?: string;
  /**
   * 錯誤狀態
   */
  error?: boolean;
  /**
   * 錯誤消息
   */
  errorMessage?: string;
}

/**
 * 通用輸入框組件
 * 提供一致的輸入框樣式和行為
 */
export const Input: React.FC<InputProps> = ({
  type = 'text',
  size = 'medium',
  placeholder,
  value,
  defaultValue,
  disabled = false,
  readOnly = false,
  allowClear = false,
  showPasswordToggle = false,
  prefix,
  suffix,
  onChange,
  onFocus,
  onBlur,
  onPressEnter,
  onClear,
  className = '',
  style,
  maxLength,
  autoFocus = false,
  autoComplete,
  name,
  id,
  error = false,
  errorMessage,
}) => {
  const [inputValue, setInputValue] = useState<string>(value ?? defaultValue ?? '');
  const [isPasswordVisible, setIsPasswordVisible] = useState<boolean>(false);
  const [isFocused, setIsFocused] = useState<boolean>(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const isControlled = value !== undefined;
  const displayValue = isControlled ? value : inputValue;

  useEffect(() => {
    if (!isControlled && defaultValue !== undefined) {
      setInputValue(defaultValue);
    }
  }, [defaultValue, isControlled]);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    
    if (!isControlled) {
      setInputValue(newValue);
    }
    
    onChange?.(newValue, event);
  };

  const handleFocus = (event: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(true);
    onFocus?.(event);
  };

  const handleBlur = (event: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(false);
    onBlur?.(event);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      onPressEnter?.(event);
    }
  };

  const handleClear = () => {
    if (!isControlled) {
      setInputValue('');
    }
    
    onClear?.();
    inputRef.current?.focus();
  };

  const togglePasswordVisibility = () => {
    setIsPasswordVisible(!isPasswordVisible);
  };

  const shouldShowClearButton = allowClear && !disabled && !readOnly && displayValue && displayValue.length > 0;
  const shouldShowPasswordToggle = showPasswordToggle && type === 'password' && !disabled && !readOnly;

  const classes = [
    'input-wrapper',
    `input-${size}`,
    isFocused ? 'input-focused' : '',
    disabled ? 'input-disabled' : '',
    readOnly ? 'input-readonly' : '',
    error ? 'input-error' : '',
    prefix ? 'input-has-prefix' : '',
    (suffix || shouldShowClearButton || shouldShowPasswordToggle) ? 'input-has-suffix' : '',
    className,
  ].filter(Boolean).join(' ');

  const inputType = type === 'password' && isPasswordVisible ? 'text' : type;

  return (
    <div className="input-container">
      <div className={classes} style={style}>
        {prefix && (
          <span className="input-prefix">
            {prefix}
          </span>
        )}
        
        <input
          ref={inputRef}
          type={inputType}
          className="input-element"
          placeholder={placeholder}
          value={displayValue}
          disabled={disabled}
          readOnly={readOnly}
          maxLength={maxLength}
          autoFocus={autoFocus}
          autoComplete={autoComplete}
          name={name}
          id={id}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
        />
        
        <div className="input-suffix-container">
          {shouldShowClearButton && (
            <button
              type="button"
              className="input-clear-btn"
              onClick={handleClear}
              aria-label="清除"
            >
              ✕
            </button>
          )}
          
          {shouldShowPasswordToggle && (
            <button
              type="button"
              className="input-password-toggle"
              onClick={togglePasswordVisibility}
              aria-label={isPasswordVisible ? "隱藏密碼" : "顯示密碼"}
            >
              {isPasswordVisible ? '👁️' : '👁️‍🗨️'}
            </button>
          )}
          
          {suffix && (
            <span className="input-suffix">
              {suffix}
            </span>
          )}
        </div>
      </div>
      
      {error && errorMessage && (
        <div className="input-error-message">
          {errorMessage}
        </div>
      )}
    </div>
  );
};

export default Input;