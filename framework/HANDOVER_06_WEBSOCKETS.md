# HANDOVER MESSAGE #6: WebSocket Real-time System

## 📋 MISSION
Build **WebSocket real-time notification system** using FastAPI native WebSockets. Enable live dashboard updates, instant notifications, and real-time data synchronization.

## 🎯 FEATURES

1. **WebSocket Server:** FastAPI WebSocket endpoint with authentication
2. **Connection Manager:** Track active connections, user presence
3. **Event Broadcasting:** Emit events to specific users, rooms, or all users
4. **Auto-Reconnect:** Client-side reconnection logic
5. **Real-time Updates:** Dashboard stats, ticket notifications, user presence

---

## 🔧 PART 1: BACKEND IMPLEMENTATION

### File 1: `backend/app/websocket/connection_manager.py`

```python
"""
WebSocket Connection Manager
"""
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        # user_id -> list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

        # room_name -> set of user_ids
        self.rooms: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept connection and add to active connections"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

        logger.info(f"WebSocket connected: user_id={user_id}, total_connections={self.get_connection_count()}")

        # Broadcast user online
        await self.broadcast({
            "type": "user.online",
            "data": {"user_id": user_id}
        }, exclude_user=user_id)

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove connection"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

            # Remove user entry if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

                # Broadcast user offline
                asyncio.create_task(
                    self.broadcast({
                        "type": "user.offline",
                        "data": {"user_id": user_id}
                    })
                )

        logger.info(f"WebSocket disconnected: user_id={user_id}, total_connections={self.get_connection_count()}")

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user (all their connections)"""
        if user_id in self.active_connections:
            dead_connections = []

            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    dead_connections.append(connection)

            # Remove dead connections
            for conn in dead_connections:
                self.active_connections[user_id].remove(conn)

    async def send_to_users(self, user_ids: List[str], message: dict):
        """Send message to multiple users"""
        for user_id in user_ids:
            await self.send_to_user(user_id, message)

    async def broadcast(self, message: dict, exclude_user: str = None):
        """Send message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            if exclude_user and user_id == exclude_user:
                continue
            await self.send_to_user(user_id, message)

    async def broadcast_to_admins(self, message: dict):
        """Send message to all admin users (requires user role info)"""
        # This would need access to user roles from database
        # For now, broadcast to all - can be refined
        await self.broadcast(message)

    def join_room(self, user_id: str, room: str):
        """Add user to a room"""
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(user_id)

    def leave_room(self, user_id: str, room: str):
        """Remove user from a room"""
        if room in self.rooms:
            self.rooms[room].discard(user_id)
            if not self.rooms[room]:
                del self.rooms[room]

    async def broadcast_to_room(self, room: str, message: dict):
        """Send message to all users in a room"""
        if room in self.rooms:
            await self.send_to_users(list(self.rooms[room]), message)

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_online_users(self) -> List[str]:
        """Get list of online user IDs"""
        return list(self.active_connections.keys())


# Global instance
manager = ConnectionManager()
```

### File 2: `backend/app/websocket/events.py`

```python
"""
WebSocket Event Emitters
"""
from typing import Dict, Any
from .connection_manager import manager

async def emit_ticket_created(ticket: Dict[str, Any]):
    """Emit ticket created event"""
    await manager.broadcast({
        "type": "ticket.created",
        "data": ticket
    })

async def emit_ticket_updated(ticket: Dict[str, Any]):
    """Emit ticket updated event"""
    await manager.broadcast({
        "type": "ticket.updated",
        "data": ticket
    })

async def emit_dashboard_update(stats: Dict[str, Any]):
    """Emit dashboard stats update"""
    await manager.broadcast({
        "type": "dashboard.update",
        "data": stats
    })

async def emit_notification(user_id: str, notification: Dict[str, Any]):
    """Emit notification to specific user"""
    await manager.send_to_user(user_id, {
        "type": "notification",
        "data": notification
    })

async def emit_low_stock_alert(items: list):
    """Emit low stock alert to admins"""
    await manager.broadcast_to_admins({
        "type": "inventory.low_stock",
        "data": {"items": items}
    })
```

### File 3: `backend/app/routes/websocket.py`

```python
"""
WebSocket Routes
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.websocket.connection_manager import manager
from app.auth.jwt import decode_access_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint
    Authentication via token query parameter
    """
    user_id = None

    try:
        # Verify token
        payload = decode_access_token(token)
        if not payload or 'sub' not in payload:
            await websocket.close(code=1008, reason="Invalid token")
            return

        user_id = payload['sub']

        # Connect
        await manager.connect(websocket, user_id)

        try:
            # Keep connection alive and listen for messages
            while True:
                # Receive message from client
                data = await websocket.receive_json()

                # Handle client messages (ping/pong, join room, etc.)
                message_type = data.get('type')

                if message_type == 'ping':
                    await websocket.send_json({"type": "pong"})

                elif message_type == 'join_room':
                    room = data.get('room')
                    if room:
                        manager.join_room(user_id, room)
                        await websocket.send_json({
                            "type": "joined_room",
                            "data": {"room": room}
                        })

                elif message_type == 'leave_room':
                    room = data.get('room')
                    if room:
                        manager.leave_room(user_id, room)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {user_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket.client_state.name == 'CONNECTED':
            await websocket.close(code=1011, reason="Internal error")

    finally:
        if user_id:
            manager.disconnect(websocket, user_id)
```

### File 4: Update `backend/app/main.py`

```python
from app.routes import websocket

app.include_router(websocket.router)
```

### File 5: Integrate with existing routes

In `backend/app/routes/tickets.py`:

```python
from app.websocket import events as ws_events

@router.post("/api/v1/tickets")
async def create_ticket(...):
    ticket = await ticket_service.create(...)

    # Emit WebSocket event
    await ws_events.emit_ticket_created({
        "id": ticket['id'],
        "title": ticket['title'],
        "priority": ticket['priority']
    })

    return ticket
```

In `backend/app/routes/dashboard.py`:

```python
from app.websocket import events as ws_events

# Periodically emit dashboard updates
async def emit_dashboard_stats_job():
    """Background job to emit dashboard stats"""
    try:
        conn = await get_db_connection()
        stats = await get_dashboard_stats(conn)
        await ws_events.emit_dashboard_update(stats)
    except Exception as e:
        logger.error(f"Failed to emit dashboard stats: {e}")

# Add to scheduler (every 30 seconds)
scheduler.add_job(
    emit_dashboard_stats_job,
    'interval',
    seconds=30,
    id='emit_dashboard_stats'
)
```

---

## 🎨 PART 2: FRONTEND IMPLEMENTATION

### File 1: `frontend/src/services/websocket.js`

```javascript
/**
 * WebSocket Service
 */
class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectTimeout = null;
    this.listeners = {};
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

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

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }

  on(eventType, callback) {
    if (!this.listeners[eventType]) {
      this.listeners[eventType] = [];
    }
    this.listeners[eventType].push(callback);
  }

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
}

// Global instance
const websocketService = new WebSocketService();

export default websocketService;
```

### File 2: Update `frontend/src/App.jsx`

Initialize WebSocket on login:

```javascript
import websocketService from './services/websocket';
import { useEffect } from 'react';

function App() {
  const { user } = useAuthStore();

  useEffect(() => {
    // Connect WebSocket when user logs in
    if (user) {
      const token = localStorage.getItem('access_token');
      if (token) {
        websocketService.connect(token);
      }
    } else {
      // Disconnect when user logs out
      websocketService.disconnect();
    }

    // Cleanup on unmount
    return () => {
      websocketService.disconnect();
    };
  }, [user]);

  return (
    // ... your routes
  );
}
```

### File 3: Use in components

Example: Real-time dashboard updates

```javascript
// frontend/src/pages/DashboardHome.jsx
import { useEffect, useState } from 'react';
import websocketService from '../services/websocket';

function DashboardHome() {
  const [stats, setStats] = useState({});

  useEffect(() => {
    // Load initial stats
    loadStats();

    // Listen for real-time updates
    const handleDashboardUpdate = (data) => {
      setStats(data);
    };

    websocketService.on('dashboard.update', handleDashboardUpdate);

    // Cleanup
    return () => {
      websocketService.off('dashboard.update', handleDashboardUpdate);
    };
  }, []);

  // ... render stats
}
```

Example: Real-time ticket notifications

```javascript
// frontend/src/components/Layout.jsx
import { useSnackbar } from 'notistack';
import websocketService from '../services/websocket';

function Layout() {
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    websocketService.on('ticket.created', (ticket) => {
      enqueueSnackbar(`New ticket: ${ticket.title}`, {
        variant: 'info',
        autoHideDuration: 5000
      });
    });

    websocketService.on('notification', (notification) => {
      enqueueSnackbar(notification.message, {
        variant: notification.type || 'info'
      });
    });

    return () => {
      websocketService.off('ticket.created');
      websocketService.off('notification');
    };
  }, []);

  // ... render layout
}
```

### File 4: Update `.env` files

Add WebSocket URL:

```
# frontend/.env
VITE_WS_URL=ws://localhost:8000
```

For production:
```
VITE_WS_URL=wss://your-domain.com
```

---

## 🧪 TESTING

1. **Login to app**
2. **Open browser console** - should see "WebSocket connected"
3. **Open app in another tab** - should see user.online event
4. **Create a ticket** - should see real-time notification
5. **Watch dashboard** - should update every 30 seconds
6. **Close one tab** - should see user.offline event

---

## ✅ VERIFICATION CHECKLIST

- [ ] WebSocket connects on login
- [ ] Reconnects after disconnect
- [ ] Ticket creation shows real-time notification
- [ ] Dashboard updates automatically
- [ ] Multiple tabs work correctly
- [ ] Disconnects on logout

**READY FOR HANDOVER #7: Telegram Module Migration**
