"""
================================================================================
Farm Management System - WebSocket Routes
================================================================================
Version: 1.0.0
Last Updated: 2025-11-22

Description:
  WebSocket endpoint for real-time bidirectional communication.
  Requires JWT authentication via query parameter.

Endpoints:
  WS /ws?token=<jwt_token> - WebSocket connection endpoint

Client Message Types:
  - ping: Keep-alive ping
  - join_room: Join a room for group messaging
  - leave_room: Leave a room

Server Message Types:
  - pong: Response to ping
  - joined_room: Confirmation of room join
  - user.online: User came online
  - user.offline: User went offline
  - ticket.created: New ticket created
  - ticket.updated: Ticket updated
  - dashboard.update: Dashboard stats updated
  - notification: User-specific notification

================================================================================
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.websocket.connection_manager import manager
from app.auth.jwt import verify_access_token
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
        payload = verify_access_token(token)
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
