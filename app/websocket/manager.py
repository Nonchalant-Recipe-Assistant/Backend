from fastapi import WebSocket
from typing import List, Dict
import json
from app.logger import get_logger

logger = get_logger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[Dict] = []
    
    async def connect(self, websocket: WebSocket, user: dict):
        """Добавляем новое соединение - ВСЕГДА вызывается после accept"""
        connection_data = {
            "websocket": websocket,
            "user": user
        }
        self.active_connections.append(connection_data)
        logger.info(f"✅ User {user['email']} connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Удаляем соединение"""
        initial_count = len(self.active_connections)
        self.active_connections = [conn for conn in self.active_connections if conn["websocket"] != websocket]
        logger.info(f"🔌 User disconnected. Was: {initial_count}, Now: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Отправляем сообщение всем подключенным клиентам"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection["websocket"].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"❌ Failed to send to {connection['user']['email']}: {e}")
                disconnected.append(connection["websocket"])
        
        # Удаляем отключившихся клиентов
        for ws in disconnected:
            self.disconnect(ws)

manager = ConnectionManager()