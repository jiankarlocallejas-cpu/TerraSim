/**
 * TerraSim Status Bar Component
 * Application status and information display
 */

import { EventBus } from '../utils/EventBus';

interface StatusItem {
  id: string;
  type: 'coordinates' | 'scale' | 'connection' | 'progress' | 'message';
  content: string;
  priority: number;
  timestamp: number;
}

export class StatusBar {
  private container!: HTMLElement;
  private eventBus: EventBus;
  private statusItems: Map<string, StatusItem>;
  private coordinates: { lat: number; lng: number };
  private scale: string;
  private connectionStatus: 'connected' | 'disconnected' | 'connecting';

  constructor(eventBus: EventBus) {
    this.eventBus = eventBus;
    this.statusItems = new Map();
    this.coordinates = { lat: 0, lng: 0 };
    this.scale = '1:50000';
    this.connectionStatus = 'disconnected';
  }

  public mount(selector: string): void {
    const container = document.querySelector(selector) as HTMLElement;
    if (!container) {
      throw new Error(`Status bar container ${selector} not found`);
    }

    this.container = container;
    this.render();
    this.setupEventListeners();
  }

  private render(): void {
    this.container.innerHTML = `
      <div class="status-bar">
        <div class="status-section status-left">
          <div class="status-item" id="coordinates-status">
            <span class="status-label">Coordinates:</span>
            <span class="status-value" id="coordinates-value">0.000000°, 0.000000°</span>
          </div>
          <div class="status-item" id="scale-status">
            <span class="status-label">Scale:</span>
            <span class="status-value" id="scale-value">1:50000</span>
          </div>
        </div>
        
        <div class="status-section status-center">
          <div class="status-item" id="message-status">
            <span class="status-value" id="message-value">Ready</span>
          </div>
          <div class="status-item hidden" id="progress-status">
            <div class="progress-bar">
              <div class="progress-fill" id="progress-fill"></div>
            </div>
            <span class="progress-text" id="progress-text">0%</span>
          </div>
        </div>
        
        <div class="status-section status-right">
          <div class="status-item" id="connection-status">
            <span class="connection-indicator" id="connection-indicator">
              <span class="connection-dot disconnected"></span>
              <span class="connection-text" id="connection-text">Disconnected</span>
            </span>
          </div>
          <div class="status-item" id="crs-status">
            <span class="status-label">CRS:</span>
            <span class="status-value">WGS84</span>
          </div>
          <div class="status-item" id="units-status">
            <span class="status-label">Units:</span>
            <span class="status-value">Metric</span>
          </div>
        </div>
      </div>
    `;
  }

  private setupEventListeners(): void {
    // Listen for coordinate updates
    this.eventBus.on('coordinates:changed', (coords: { lat: number; lng: number }) => {
      this.updateCoordinates(coords);
    });

    this.eventBus.on('map:mousemove', (coords: { lat: number; lng: number }) => {
      this.updateCoordinates(coords);
    });

    // Listen for scale updates
    this.eventBus.on('map:scale:changed', (scale: string) => {
      this.updateScale(scale);
    });

    // Listen for connection status
    this.eventBus.on('connection:changed', (connected: boolean) => {
      this.updateConnectionStatus(connected);
    });

    // Listen for progress updates
    this.eventBus.on('progress:updated', (progress: { value: number; message?: string }) => {
      this.updateProgress(progress.value, progress.message);
    });

    // Listen for messages
    this.eventBus.on('status:message', (message: string) => {
      this.showMessage(message);
    });

    // Listen for tool changes
    this.eventBus.on('tool:changed', (tool: any) => {
      this.showMessage(`Tool: ${tool.name}`);
    });

    // Listen for layer operations
    this.eventBus.on('layer:added', (layer: any) => {
      this.showMessage(`Layer added: ${layer.name}`);
    });

    this.eventBus.on('layer:removed', (layerId: string) => {
      this.showMessage(`Layer removed`);
    });

    // Listen for analysis operations
    this.eventBus.on('erosion:calculated', (result: any) => {
      this.showMessage(`Erosion analysis complete: ${result.risk_category} risk`);
    });

    // Listen for notifications
    this.eventBus.on('notification:show', (notification: any) => {
      this.showMessage(notification.message, notification.type);
    });
  }

  private updateCoordinates(coords: { lat: number; lng: number }): void {
    this.coordinates = coords;
    const coordsValue = this.container.querySelector('#coordinates-value') as HTMLElement;
    
    if (coordsValue) {
      const latStr = coords.lat.toFixed(6) + '°';
      const lngStr = coords.lng.toFixed(6) + '°';
      coordsValue.textContent = `${latStr}, ${lngStr}`;
    }
  }

  private updateScale(scale: string): void {
    this.scale = scale;
    const scaleValue = this.container.querySelector('#scale-value') as HTMLElement;
    
    if (scaleValue) {
      scaleValue.textContent = scale;
    }
  }

  private updateConnectionStatus(connected: boolean): void {
    this.connectionStatus = connected ? 'connected' : 'disconnected';
    const indicator = this.container.querySelector('#connection-indicator') as HTMLElement;
    const connectionText = this.container.querySelector('#connection-text') as HTMLElement;
    const connectionDot = this.container.querySelector('.connection-dot') as HTMLElement;
    
    if (indicator && connectionText && connectionDot) {
      connectionText.textContent = connected ? 'Connected' : 'Disconnected';
      
      // Update dot class
      connectionDot.className = `connection-dot ${connected ? 'connected' : 'disconnected'}`;
      
      // Update indicator class
      indicator.className = `connection-indicator ${connected ? 'connected' : 'disconnected'}`;
    }
  }

  private updateProgress(value: number, message?: string): void {
    const progressStatus = this.container.querySelector('#progress-status') as HTMLElement;
    const progressFill = this.container.querySelector('#progress-fill') as HTMLElement;
    const progressText = this.container.querySelector('#progress-text') as HTMLElement;
    const messageStatus = this.container.querySelector('#message-status') as HTMLElement;
    
    if (progressStatus && progressFill && progressText) {
      // Show progress bar
      progressStatus.classList.remove('hidden');
      
      // Update progress fill
      progressFill.style.width = `${value}%`;
      
      // Update progress text
      progressText.textContent = `${Math.round(value)}%`;
      
      // Hide message if showing progress
      if (messageStatus) {
        messageStatus.classList.add('hidden');
      }
      
      // Hide progress when complete
      if (value >= 100) {
        setTimeout(() => {
          progressStatus.classList.add('hidden');
          if (messageStatus) {
            messageStatus.classList.remove('hidden');
          }
        }, 1000);
      }
    }
    
    if (message) {
      this.showMessage(message);
    }
  }

  private showMessage(message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info'): void {
    const messageValue = this.container.querySelector('#message-value') as HTMLElement;
    const messageStatus = this.container.querySelector('#message-status') as HTMLElement;
    
    if (messageValue && messageStatus) {
      messageValue.textContent = message;
      messageValue.className = `status-value message-${type}`;
      messageStatus.classList.remove('hidden');
      
      // Auto-hide message after 5 seconds
      setTimeout(() => {
        if (messageValue.textContent === message) {
          messageValue.textContent = 'Ready';
          messageValue.className = 'status-value';
        }
      }, 5000);
    }
  }

  public setCRS(crs: string): void {
    const crsValue = this.container.querySelector('.status-section.status-right .status-value') as HTMLElement;
    if (crsValue) {
      crsValue.textContent = crs;
    }
  }

  public setUnits(units: 'metric' | 'imperial'): void {
    const unitsValue = this.container.querySelector('#units-status .status-value') as HTMLElement;
    if (unitsValue) {
      unitsValue.textContent = units === 'metric' ? 'Metric' : 'Imperial';
    }
  }

  public showTemporaryMessage(message: string, duration: number = 3000): void {
    this.showMessage(message);
    setTimeout(() => {
      const messageValue = this.container.querySelector('#message-value') as HTMLElement;
      if (messageValue && messageValue.textContent === message) {
        messageValue.textContent = 'Ready';
      }
    }, duration);
  }

  public getCoordinates(): { lat: number; lng: number } {
    return { ...this.coordinates };
  }

  public getScale(): string {
    return this.scale;
  }

  public getConnectionStatus(): 'connected' | 'disconnected' | 'connecting' {
    return this.connectionStatus;
  }

  public destroy(): void {
    if (this.container) {
      this.container.innerHTML = '';
    }
  }
}
