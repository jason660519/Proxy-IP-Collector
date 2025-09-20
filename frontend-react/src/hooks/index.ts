/**
 * 自定義 Hooks
 * @description 提供類型化的 Redux hooks 和其他自定義邏輯
 */

import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import { useState, useEffect, useCallback, useRef } from 'react';
import type { RootState, AppDispatch } from '../store';

/**
 * 類型化的 Redux hooks
 */
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

/**
 * 防抖 Hook
 * @param value 要防抖的值
 * @param delay 延遲時間（毫秒）
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * 節流 Hook
 * @param callback 要節流的回調函數
 * @param delay 節流時間（毫秒）
 */
export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const lastCall = useRef(0);
  const lastCallTime = useRef(Date.now());
  const lastArgs = useRef<Parameters<T>>();

  return useCallback((...args: Parameters<T>) => {
    const now = Date.now();
    lastArgs.current = args;

    if (now - lastCallTime.current >= delay) {
      lastCall.current++;
      lastCallTime.current = now;
      return callback(...args);
    }
  }, [callback, delay]) as T;
}

/**
 * 本地存儲 Hook
 * @param key 存儲鍵名
 * @param initialValue 初始值
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((val: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  };

  return [storedValue, setValue];
}

/**
 * 定時器 Hook
 * @param callback 定時執行的回調函數
 * @param delay 延遲時間（毫秒），null 表示停止定時器
 */
export function useInterval(callback: () => void, delay: number | null) {
  const savedCallback = useRef<() => void>();

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    function tick() {
      if (savedCallback.current) {
        savedCallback.current();
      }
    }

    if (delay !== null) {
      const id = setInterval(tick, delay);
      return () => clearInterval(id);
    }
  }, [delay]);
}

/**
 * 頁面標題 Hook
 * @param title 頁面標題
 */
export function useDocumentTitle(title: string) {
  useEffect(() => {
    const originalTitle = document.title;
    document.title = title ? `${title} - Proxy IP Pool Collector` : 'Proxy IP Pool Collector';

    return () => {
      document.title = originalTitle;
    };
  }, [title]);
}

/**
 * 網絡狀態 Hook
 */
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

/**
 * 複製到剪貼板 Hook
 */
export function useCopyToClipboard() {
  const [copiedText, setCopiedText] = useState<string | null>(null);

  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedText(text);
      setTimeout(() => setCopiedText(null), 2000);
      return true;
    } catch (error) {
      console.error('Failed to copy text:', error);
      return false;
    }
  };

  return [copiedText, copy] as const;
}