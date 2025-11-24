"""
================================================================================
Farm Management System - WebSocket Connection Manager
================================================================================
Version: 1.0.0
Last Updated: 2025-11-22

Description:
  Manages WebSocket connections, user presence, and message broadcasting.
  Supports user-specific messages, room-based messaging, and global broadcasts.

================================================================================
"""
import asyncio
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
