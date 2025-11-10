from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.websocket.manager import manager
from app.crud.message import MessageRepository
from app.database import get_db
from app.schemas import ChatMessage
from app.utils import verify_token
from sqlalchemy.orm import Session
import json
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, db: Session = Depends(get_db)):
    logger.info("🎯 MAIN WebSocket endpoint /ws/chat CALLED")
    
    try:
        # Принимаем соединение ДО проверки токена
        logger.info("🔌 MAIN Attempting to accept WebSocket connection...")
        await websocket.accept()
        logger.info("✅ MAIN WebSocket connection accepted")
        
        # Authenticate via query parameter
        token = websocket.query_params.get("token")
        logger.info(f"🔑 MAIN Token from query params: {token}")
        
        if not token:
            logger.warning("❌ MAIN No token provided")
            await websocket.close(code=1008)
            return
        
        logger.info("🔍 MAIN Starting token verification...")
        user = verify_token(token)
        logger.info(f"👤 MAIN Token verification result: {user}")
        
        if not user:
            logger.warning("❌ MAIN Token verification failed")
            await websocket.close(code=1008)
            return
        
        logger.info(f"✅ MAIN WebSocket authenticated for user: {user['email']}")
        await manager.connect(websocket, user)
        logger.info("✅ MAIN User added to connection manager")
        
        try:
            while True:
                logger.info("🔄 MAIN Waiting for messages...")
                data = await websocket.receive_text()
                logger.info(f"📨 MAIN Received: {data}")
                
                message_data = json.loads(data)
                
                # Validate message
                chat_message = ChatMessage(**message_data)
                
                # Save to database
                message_repo = MessageRepository(db)
                db_message = message_repo.create_message(
                    chat_message, 
                    user["email"], 
                    user.get("username", user["email"])
                )
                
                # Prepare broadcast message
                broadcast_msg = {
                    "id": db_message.id,
                    "text": db_message.text,
                    "sender_email": db_message.sender_email,
                    "sender_username": db_message.sender_username,
                    "timestamp": db_message.timestamp.isoformat(),
                    "message_type": db_message.message_type
                }
                
                # Broadcast to all connected clients
                await manager.broadcast(broadcast_msg)
                logger.info(f"📢 MAIN Message broadcast from {user['email']}")
                
        except WebSocketDisconnect:
            logger.info(f"🔌 MAIN WebSocket disconnected for user: {user['email']}")
            manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"❌ MAIN WebSocket error: {e}")
            manager.disconnect(websocket)
            
    except Exception as e:
        logger.error(f"💥 MAIN WebSocket connection error: {e}")
        import traceback
        logger.error(f"💥 MAIN Traceback: {traceback.format_exc()}")
        try:
            await websocket.close(code=1011)
        except:
            pass

@router.get("/messages")
async def get_message_history(db: Session = Depends(get_db)):
    try:
        message_repo = MessageRepository(db)
        messages = message_repo.get_recent_messages(limit=50)
        
        # Конвертируем в формат для фронтенда
        result = [
            {
                "id": msg.id,
                "text": msg.text,
                "sender_email": msg.sender_email,
                "sender_username": msg.sender_username,
                "timestamp": msg.timestamp.isoformat(),
                "message_type": msg.message_type
            }
            for msg in messages
        ]
        
        logger.info(f"📋 Loaded {len(result)} messages from history")
        return result
    except Exception as e:
        logger.error(f"❌ Error loading message history: {e}")
        return []