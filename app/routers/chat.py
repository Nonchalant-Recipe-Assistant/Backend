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
    try:
        # Authenticate via query parameter
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008)
            return
        
        user = verify_token(token)
        if not user:
            await websocket.close(code=1008)
            return
        
        await manager.connect(websocket, user)
        
        try:
            while True:
                data = await websocket.receive_text()
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
                logger.info(f"Message broadcast from {user['email']}")
                
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            manager.disconnect(websocket)
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=1011)