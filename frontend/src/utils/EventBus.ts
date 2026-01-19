/**
 * TerraSim Event Bus
 * Centralized event management system
 */

type EventCallback = (...args: any[]) => void;

export class EventBus {
  private events: Map<string, EventCallback[]>;

  constructor() {
    this.events = new Map();
  }

  /**
   * Subscribe to an event
   * @param event - Event name
   * @param callback - Callback function
   */
  public on(event: string, callback: EventCallback): void {
    if (!this.events.has(event)) {
      this.events.set(event, []);
    }
    this.events.get(event)!.push(callback);
  }

  /**
   * Subscribe to an event (once)
   * @param event - Event name
   * @param callback - Callback function
   */
  public once(event: string, callback: EventCallback): void {
    const onceCallback = (...args: any[]) => {
      callback(...args);
      this.off(event, onceCallback);
    };
    this.on(event, onceCallback);
  }

  /**
   * Unsubscribe from an event
   * @param event - Event name
   * @param callback - Callback function (optional)
   */
  public off(event: string, callback?: EventCallback): void {
    if (!this.events.has(event)) {
      return;
    }

    if (!callback) {
      // Remove all listeners for this event
      this.events.delete(event);
      return;
    }

    const callbacks = this.events.get(event)!;
    const index = callbacks.indexOf(callback);
    if (index > -1) {
      callbacks.splice(index, 1);
    }

    if (callbacks.length === 0) {
      this.events.delete(event);
    }
  }

  /**
   * Emit an event
   * @param event - Event name
   * @param args - Arguments to pass to callbacks
   */
  public emit(event: string, ...args: any[]): void {
    if (!this.events.has(event)) {
      return;
    }

    const callbacks = this.events.get(event)!;
    callbacks.forEach(callback => {
      try {
        callback(...args);
      } catch (error) {
        console.error(`Error in event callback for "${event}":`, error);
      }
    });
  }

  /**
   * Get all event names
   */
  public getEventNames(): string[] {
    return Array.from(this.events.keys());
  }

  /**
   * Get number of listeners for an event
   * @param event - Event name
   */
  public getListenerCount(event: string): number {
    return this.events.get(event)?.length || 0;
  }

  /**
   * Clear all events
   */
  public clear(): void {
    this.events.clear();
  }

  /**
   * Check if event has listeners
   * @param event - Event name
   */
  public hasListeners(event: string): boolean {
    return this.events.has(event) && this.events.get(event)!.length > 0;
  }
}
