/**
 * WebSocket服務
 * @description 管理WebSocket連接和即時通信
 */

import { store } from '@/store';
import { addNotification } from '@/store/slices/notificationSlice';
import { 
  addProxy, 
  updateProxy, 
  removeProxy 
} from '@/store/slices/proxySlice';
import { 
  setStats, 
  updateSystemStatus 
} from '@/store/slices/dashboardSlice';
import { 
  updateTaskProgress,
  completeTask,
  failTask 
} from '@/store/slices/taskSlice';

/**
 * WebSocket消息類型
 */
export enum WebSocketMessageType {
  // 代理相關
  PROXY_ADDED = 'proxy_added',
  PROXY_UPDATED = 'proxy_updated',
  PROXY_REMOVED = 'proxy_removed',
  PROXY_VALIDATED = 'proxy_validated',
  PROXY_BATCH_UPDATED = 'proxy_batch_updated',
  
  // 統計數據
  STATS_UPDATED = 'stats_updated',
  SYSTEM_STATUS_UPDATED = 'system_status_updated',
  
  // 任務相關
  TASK_CREATED = 'task_created',
  TASK_PROGRESS = 'task_progress',
  TASK_COMPLETED = 'task_completed',
  TASK_FAILED = 'task_failed',
  
  // 通知相關
  NOTIFICATION = 'notification',
  
  // 連接相關
  CONNECTION_ESTABLISHED = 'connection_established',
  CONNECTION_LOST = 'connection_lost',
  CONNECTION_RESTORED = 'connection_restored',
  
  // 錯誤
  ERROR = 'error',
}

/**
 * WebSocket消息接口
 */
interface WebSocketMessage {
  type: WebSocketMessageType;
  data: any;
  timestamp: string;
  id: string;
}

/**
 * WebSocket服務類
 */
class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectInterval: number;
  private maxReconnectAttempts: number;
  private reconnectAttempts: number = 0;
  private shouldReconnect: boolean = true;
  private messageHandlers: Map<WebSocketMessageType, Function[]> = new Map();
  private connectionState: 'connecting' | 'connected' | 'disconnected' | 'error' = 'disconnected';

  constructor(url: string = 'ws://localhost:8080/ws', 
              reconnectInterval: number = 5000, 
              maxReconnectAttempts: number = 5) {
    this.url = url;
    this.reconnectInterval = reconnectInterval;
    this.maxReconnectAttempts = maxReconnectAttempts;
    this.initializeMessageHandlers();
  }

  /**
   * 初始化消息處理器
   */
  private initializeMessageHandlers() {
    // 代理相關消息處理
    this.registerHandler(WebSocketMessageType.PROXY_ADDED, (data: { proxy: any }) => {
      store.dispatch(addProxy(data.proxy));
      store.dispatch(addNotification({
        type: 'info',
        title: '新增代理',
        message: `發現新的代理IP: ${data.proxy.ip}:${data.proxy.port}`,
        level: 'medium',
      }));
    });

    this.registerHandler(WebSocketMessageType.PROXY_UPDATED, (data: { proxy: any; notify?: boolean }) => {
      store.dispatch(updateProxy(data.proxy));
      if (data.notify) {
        store.dispatch(addNotification({
          type: 'info',
          title: '代理更新',
          message: `代理 ${data.proxy.ip}:${data.proxy.port} 已更新`,
          level: 'low',
        }));
      }
    });

    this.registerHandler(WebSocketMessageType.PROXY_REMOVED, (data: { proxyId: string }) => {
      store.dispatch(removeProxy(data.proxyId));
      store.dispatch(addNotification({
        type: 'warning',
        title: '代理移除',
        message: `代理已被移除`,
        level: 'medium',
      }));
    });

    // 統計數據消息處理
    this.registerHandler(WebSocketMessageType.STATS_UPDATED, (data: { stats: any }) => {
      store.dispatch(setStats(data.stats));
    });

    this.registerHandler(WebSocketMessageType.SYSTEM_STATUS_UPDATED, (data: { status: any }) => {
      store.dispatch(updateSystemStatus(data.status));
    });

    // 任務相關消息處理
    this.registerHandler(WebSocketMessageType.TASK_CREATED, (data: { task: { name: string } }) => {
      store.dispatch(addNotification({
        type: 'info',
        title: '新任務',
        message: `任務 "${data.task.name}" 已創建`,
        level: 'low',
      }));
    });

    this.registerHandler(WebSocketMessageType.TASK_PROGRESS, (data: any) => {
      store.dispatch(updateTaskProgress({
        taskId: data.taskId,
        progress: data.progress,
        message: data.message,
      }));
    });

    this.registerHandler(WebSocketMessageType.TASK_COMPLETED, (data: { taskId: string; result: any; message: string; taskName: string }) => {
      store.dispatch(completeTask({
        taskId: data.taskId,
        result: data.result,
        message: data.message,
      }));
      store.dispatch(addNotification({
        type: 'success',
        title: '任務完成',
        message: `任務 "${data.taskName}" 已完成`,
        level: 'low',
      }));
    });

    this.registerHandler(WebSocketMessageType.TASK_FAILED, (data: { taskId: string; error: string; retry: boolean; taskName: string }) => {
      store.dispatch(failTask({
        taskId: data.taskId,
        error: data.error,
        retry: data.retry,
      }));
      store.dispatch(addNotification({
        type: 'error',
        title: '任務失敗',
        message: `任務 "${data.taskName}" 失敗: ${data.error}`,
        level: 'medium',
      }));
    });

    // 通知消息處理
    this.registerHandler(WebSocketMessageType.NOTIFICATION, (data: { notification: any }) => {
      store.dispatch(addNotification(data.notification));
    });

    // 連接狀態消息處理
    this.registerHandler(WebSocketMessageType.CONNECTION_ESTABLISHED, () => {
      this.connectionState = 'connected';
      this.reconnectAttempts = 0;
      store.dispatch(addNotification({
        type: 'success',
        title: '連接成功',
        message: 'WebSocket連接已建立',
        level: 'low',
      }));
    });

    this.registerHandler(WebSocketMessageType.CONNECTION_LOST, () => {
      this.connectionState = 'disconnected';
      store.dispatch(addNotification({
        type: 'warning',
        title: '連接斷開',
        message: 'WebSocket連接已斷開',
        level: 'medium',
      }));
    });

    this.registerHandler(WebSocketMessageType.CONNECTION_RESTORED, () => {
      this.connectionState = 'connected';
      store.dispatch(addNotification({
        type: 'success',
        title: '連接恢復',
        message: 'WebSocket連接已恢復',
        level: 'low',
      }));
    });

    // 錯誤消息處理
    this.registerHandler(WebSocketMessageType.ERROR, (data: { message?: string }) => {
      store.dispatch(addNotification({
        type: 'error',
        title: '錯誤',
        message: data.message || '發生未知錯誤',
        level: 'medium',
      }));
    });
  }

  /**
   * 註冊消息處理器
   */
  public registerHandler<T = any>(messageType: WebSocketMessageType, handler: (data: T) => void) {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }

  /**
   * 取消註冊消息處理器
   */
  public unregisterHandler(messageType: WebSocketMessageType, handler: Function) {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * 連接到WebSocket服務器
   */
  public connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket已連接');
      return;
    }

    try {
      this.connectionState = 'connecting';
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket連接已建立');
        this.connectionState = 'connected';
        this.reconnectAttempts = 0;
        
        // 發送連接確認消息
        this.send({
          type: WebSocketMessageType.CONNECTION_ESTABLISHED,
          data: { client: 'proxy-collector-frontend' },
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('解析WebSocket消息失敗:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket連接已關閉');
        this.connectionState = 'disconnected';
        this.ws = null;
        
        if (this.shouldReconnect) {
          this.attemptReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket錯誤:', error);
        this.connectionState = 'error';
      };

    } catch (error) {
      console.error('創建WebSocket連接失敗:', error);
      this.connectionState = 'error';
      if (this.shouldReconnect) {
        this.attemptReconnect();
      }
    }
  }

  /**
   * 處理接收到的消息
   */
  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers && handlers.length > 0) {
      handlers.forEach(handler => {
        try {
          handler(message.data);
        } catch (error) {
          console.error(`處理消息類型 ${message.type} 失敗:`, error);
        }
      });
    } else {
      console.warn(`未找到消息類型 ${message.type} 的處理器`);
    }
  }

  /**
   * 發送消息
   */
  public send(message: Omit<WebSocketMessage, 'id' | 'timestamp'>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const fullMessage: WebSocketMessage = {
        ...message,
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
      };
      this.ws.send(JSON.stringify(fullMessage));
    } else {
      console.warn('WebSocket未連接，無法發送消息');
    }
  }

  /**
   * 嘗試重新連接
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('達到最大重連嘗試次數');
      store.dispatch(addNotification({
        type: 'error',
        title: '連接失敗',
        message: '無法連接到服務器，請檢查網絡連接',
      } as any));
      return;
    }

    this.reconnectAttempts++;
    console.log(`第 ${this.reconnectAttempts} 次重連嘗試，${this.reconnectInterval}ms 後重試`);
    
    setTimeout(() => {
      if (this.shouldReconnect) {
        this.connect();
      }
    }, this.reconnectInterval);
  }

  /**
   * 斷開連接
   */
  public disconnect(): void {
    this.shouldReconnect = false;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 獲取連接狀態
   */
  public getConnectionState(): string {
    return this.connectionState;
  }

  /**
   * 是否已連接
   */
  public isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// 創建WebSocket服務實例
const wsService = new WebSocketService();

export default wsService;
export type { WebSocketMessage };