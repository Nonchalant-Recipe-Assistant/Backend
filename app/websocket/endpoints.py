from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from datetime import datetime
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        self.active_connections.append(websocket)
        logger.info(f"✅ New connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"🔌 Connection closed. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"❌ Failed to send: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Упрощенный рабочий WebSocket чат"""
    logger.info("🎯 WebSocket /ws/chat CALLED")
    
    # Принимаем соединение СРАЗУ
    await websocket.accept()
    logger.info("✅ WebSocket connection accepted")
    
    # Временно используем тестового пользователя
    user_email = "test@example.com"
    user = {"email": user_email, "username": user_email.split('@')[0]}
    
    await manager.connect(websocket)
    
    # Отправляем приветственное сообщение
    welcome_msg = {
        "id": 1,
        "text": f"Welcome to chat, {user['email']}!",
        "sender_email": "system",
        "sender_username": "System",
        "timestamp": datetime.now().isoformat(),
        "message_type": "system"
    }
    await websocket.send_text(json.dumps(welcome_msg))
    
    try:
        while True:
            # Ждем сообщения от клиента
            data = await websocket.receive_text()
            logger.info(f"📨 Received: {data}")
            
            try:
                message_data = json.loads(data)
                text = message_data.get("text", "").strip()
                
                if text:
                    # Создаем сообщение для отправки
                    chat_message = {
                        "id": int(datetime.now().timestamp()),
                        "text": text,
                        "sender_email": user["email"],
                        "sender_username": user["username"],
                        "timestamp": datetime.now().isoformat(),
                        "message_type": message_data.get("message_type", "text")
                    }
                    
                    # Отправляем всем
                    await manager.broadcast(chat_message)
                    logger.info(f"📢 Message broadcast: {text}")
                    
            except json.JSONDecodeError:
                error_msg = {
                    "id": 2,
                    "text": "Error: Invalid message format",
                    "sender_email": "system",
                    "sender_username": "System",
                    "timestamp": datetime.now().isoformat(),
                    "message_type": "error"
                }
                await websocket.send_text(json.dumps(error_msg))
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"💥 WebSocket error: {e}")
        manager.disconnect(websocket)

@router.get("/messages")
async def get_message_history():
    """Заглушка для истории сообщений"""
    return [
        {
            "id": 1,
            "text": "Welcome to the chat!",
            "sender_email": "system",
            "sender_username": "System",
            "timestamp": datetime.now().isoformat(),
            "message_type": "system"
        }
    ]