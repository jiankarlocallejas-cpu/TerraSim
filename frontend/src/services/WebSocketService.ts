/**
 * TerraSim WebSocket Service
 * Real-time communication with backend
 */

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;
  private isConnecting: boolean = false;
  private eventListeners: Map<string, Function[]> = new Map();

  constructor(url: string = 'ws://localhost:8000/ws') {
    this.url = url;
  }

  /**
   * Connect to WebSocket server
   */
  public connect(): void {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.isConnecting = true;

    try {
      this.ws = new WebSocket(this.url);
      this.setupWebSocket();
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.reconnectAttempts = 0;
    this.isConnecting = false;
  }

  /**
   * Send message to server
   * @param message - Message to send
   */
  public send(message: string | object): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      this.ws.send(data);
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }

  /**
   * Add event listener
   * @param event - Event name
   * @param callback - Callback function
   */
  public on(event: string, callback: Function): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event)!.push(callback);
  }

  /**
   * Remove event listener
   * @param event - Event name
   * @param callback - Callback function
   */
  public off(event: string, callback?: Function): void {
    if (!this.eventListeners.has(event)) {
      return;
    }

    if (!callback) {
      this.eventListeners.delete(event);
      return;
    }

    const callbacks = this.eventListeners.get(event)!;
    const index = callbacks.indexOf(callback);
    if (index > -1) {
      callbacks.splice(index, 1);
    }

    if (callbacks.length === 0) {
      this.eventListeners.delete(event);
    }
  }

  /**
   * Get connection status
   */
  public getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  /**
   * Check if connected
   */
  public isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupWebSocket(): void {
    if (!this.ws) return;

    this.ws.onopen = (event) => {
      console.log('WebSocket connected');
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.emit('connected', event);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.emit('message', data);
        this.emit(data.type || 'data', data);
      } catch (error) {
        // If not JSON, emit as raw message
        this.emit('message', event.data);
        this.emit('data', { type: 'raw', data: event.data });
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.isConnecting = false;
      this.ws = null;
      this.emit('disconnected', event);

      // Attempt to reconnect if not a normal closure
      if (event.code !== 1000) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      this.isConnecting = false;
      this.emit('error', event);
    };
  }

  /**
   * Emit event to listeners
   * @param event - Event name
   * @param data - Event data
   */
  private emit(event: string, data?: any): void {
    const callbacks = this.eventListeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket event callback for "${event}":`, error);
        }
      });
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached');
      this.emit('reconnect-failed');
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    console.log(`Scheduling reconnection attempt ${this.reconnectAttempts + 1} in ${delay}ms`);

    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  /**
   * Send ping to server
   */
  public ping(): void {
    this.send({ type: 'ping', timestamp: Date.now() });
  }

  /**
   * Send pong to server
   */
  public pong(): void {
    this.send({ type: 'pong', timestamp: Date.now() });
  }

  /**
   * Join room/channel
   * @param room - Room name
   */
  public join(room: string): void {
    this.send({ type: 'join', room });
  }

  /**
   * Leave room/channel
   * @param room - Room name
   */
  public leave(room: string): void {
    this.send({ type: 'leave', room });
  }

  /**
   * Subscribe to data updates
   * @param dataType - Type of data to subscribe to
   */
  public subscribe(dataType: string): void {
    this.send({ type: 'subscribe', dataType });
  }

  /**
   * Unsubscribe from data updates
   * @param dataType - Type of data to unsubscribe from
   */
  public unsubscribe(dataType: string): void {
    this.send({ type: 'unsubscribe', dataType });
  }

  /**
   * Get connection statistics
   */
  public getStats(): {
    connected: boolean;
    readyState: number;
    reconnectAttempts: number;
    url: string;
  } {
    return {
      connected: this.isConnected(),
      readyState: this.getReadyState(),
      reconnectAttempts: this.reconnectAttempts,
      url: this.url
    };
  }
}
