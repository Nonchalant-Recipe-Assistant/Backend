from fastapi import WebSocket
from typing import List, Dict
import json
from app.logger import get_logger

logger = get_logger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[Dict] = []
    
    async def connect(self, websocket: WebSocket, user: dict):
        connection_data = {
            "websocket": websocket,
            "user": user
        }
        self.active_connections.append(connection_data)
        logger.info(f"User {user['email']} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections = [conn for conn in self.active_connections if conn["websocket"] != websocket]
        logger.info(f"User disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection["websocket"].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {connection['user']['email']}: {e}")
                disconnected.append(connection["websocket"])
        
        # Remove disconnected clients
        for ws in disconnected:
            self.disconnect(ws)

manager = ConnectionManager()