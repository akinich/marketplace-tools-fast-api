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
 *
 * Features:
 *   - Automatic reconnection with exponential backoff
 *   - Event listener system
 *   - Keep-alive ping/pong mechanism
 *   - Room-based messaging support
 *
 * Usage:
 *   import websocketService from './services/websocket';
 *
 *   // Connect (typically on login)
 *   websocketService.connect(token);
 *
 *   // Listen for events
 *   websocketService.on('ticket.created', (data) => {
 *     console.log('New ticket:', data);
 *   });
 *
 *   // Disconnect (typically on logout)
 *   websocketService.disconnect();
 * ============================================================================
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectTimeout = null;
    this.listeners = {};
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.pingInterval = null;
  }

  /**
   * Connect to WebSocket server
   * @param {string} token - JWT access token for authentication
   */
  connect(token) {
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

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
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

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.isConnecting = false;
    };
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
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
   * @param {object} data - Message data
   */
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }

  /**
   * Register event listener
   * @param {string} eventType - Event type to listen for
   * @param {function} callback - Callback function to execute
   */
  on(eventType, callback) {
    if (!this.listeners[eventType]) {
      this.listeners[eventType] = [];
    }
    this.listeners[eventType].push(callback);
  }

  /**
   * Unregister event listener
   * @param {string} eventType - Event type
   * @param {function} callback - Callback function to remove (optional)
   */
  off(eventType, callback) {
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
   * @param {object} message - Parsed message object
   */
  handleMessage(message) {
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
  joinRoom(room) {
    this.send({ type: 'join_room', room });
  }

  /**
   * Leave a room
   * @param {string} room - Room name
   */
  leaveRoom(room) {
    this.send({ type: 'leave_room', room });
  }
}

// Global instance
const websocketService = new WebSocketService();

export default websocketService;
