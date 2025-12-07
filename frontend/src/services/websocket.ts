/**
 * ============================================================================
 * WebSocket Service
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-22
 *
 * Description:
 *   Real-time WebSocket service for bidirectional communication with backend.
 *   Handles connection management, auto-reconnection, and event broadcasting.
 */

interface WebSocketMessage {
    type: string;
    data?: any;
    room?: string;
    [key: string]: any;
}

type WebSocketListener = (data: any) => void;

class WebSocketService {
    private ws: WebSocket | null = null;
    private reconnectTimeout: NodeJS.Timeout | null = null;
    private listeners: { [key: string]: WebSocketListener[] } = {};
    private isConnecting: boolean = false;
    private reconnectAttempts: number = 0;
    private readonly maxReconnectAttempts: number = 5;
    private pingInterval: NodeJS.Timeout | null = null;

    /**
     * Connect to WebSocket server
     * @param {string} token - JWT access token for authentication
     */
    connect(token: string): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }

        if (this.isConnecting) {
            console.log('WebSocket connection in progress');
            return;
        }

        this.isConnecting = true;

        const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
        const url = `${wsUrl}/ws?token=${token}`;

        console.log('Connecting to WebSocket...');

        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.isConnecting = false;
            this.reconnectAttempts = 0;

            // Send ping every 30 seconds to keep alive
            this.pingInterval = setInterval(() => {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.send({ type: 'ping' });
                }
            }, 30000);
        };

        this.ws.onmessage = (event: MessageEvent) => {
            try {
                const message: WebSocketMessage = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        this.ws.onclose = (event: CloseEvent) => {
            console.log('WebSocket disconnected', event.code, event.reason);
            this.isConnecting = false;

            if (this.pingInterval) {
                clearInterval(this.pingInterval);
            }

            // Auto-reconnect
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
                console.log(`Reconnecting in ${delay}ms...`);

                this.reconnectTimeout = setTimeout(() => {
                    this.reconnectAttempts++;
                    const token = localStorage.getItem('access_token');
                    if (token) {
                        this.connect(token);
                    }
                }, delay);
            }
        };

        this.ws.onerror = (event: Event) => {
            console.error('WebSocket error:', event);
            this.isConnecting = false;
        };
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect(): void {
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
        }

        if (this.pingInterval) {
            clearInterval(this.pingInterval);
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.listeners = {};
    }

    /**
     * Send message to server
     * @param {WebSocketMessage} data - Message data
     */
    send(data: WebSocketMessage): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected, cannot send message');
        }
    }

    /**
     * Register event listener
     * @param {string} eventType - Event type to listen for
     * @param {WebSocketListener} callback - Callback function to execute
     */
    on(eventType: string, callback: WebSocketListener): void {
        if (!this.listeners[eventType]) {
            this.listeners[eventType] = [];
        }
        this.listeners[eventType].push(callback);
    }

    /**
     * Unregister event listener
     * @param {string} eventType - Event type
     * @param {WebSocketListener} callback - Callback function to remove (optional)
     */
    off(eventType: string, callback?: WebSocketListener): void {
        if (!this.listeners[eventType]) return;

        if (callback) {
            this.listeners[eventType] = this.listeners[eventType].filter(
                cb => cb !== callback
            );
        } else {
            delete this.listeners[eventType];
        }
    }

    /**
     * Handle incoming message from server
     * @param {WebSocketMessage} message - Parsed message object
     */
    handleMessage(message: WebSocketMessage): void {
        const { type, data } = message;

        // Call all listeners for this event type
        if (this.listeners[type]) {
            this.listeners[type].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in WebSocket listener for ${type}:`, error);
                }
            });
        }

        // Call wildcard listeners
        if (this.listeners['*']) {
            this.listeners['*'].forEach(callback => {
                try {
                    callback(message);
                } catch (error) {
                    console.error('Error in WebSocket wildcard listener:', error);
                }
            });
        }
    }

    /**
     * Join a room for group messaging
     * @param {string} room - Room name
     */
    joinRoom(room: string): void {
        this.send({ type: 'join_room', room });
    }

    /**
     * Leave a room
     * @param {string} room - Room name
     */
    leaveRoom(room: string): void {
        this.send({ type: 'leave_room', room });
    }
}

// Global instance
const websocketService = new WebSocketService();

export default websocketService;
