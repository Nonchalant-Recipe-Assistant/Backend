from sqlalchemy.orm import Session
from app.models import ChatMessage
from app.schemas import ChatMessage as ChatMessageSchema
from app.logger import get_logger

logger = get_logger(__name__)

class MessageRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_message(self, message: ChatMessageSchema, user_email: str, username: str) -> ChatMessage:
        try:
            db_message = ChatMessage(
                text=message.text,
                sender_email=user_email,
                sender_username=username,
                message_type=message.message_type
            )
            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)
            logger.info(f"Message saved to DB from user {user_email}")
            return db_message
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving message to DB: {e}")
            raise
    
    def get_recent_messages(self, limit: int = 50):
        return self.db.query(ChatMessage).order_by(ChatMessage.timestamp.desc()).limit(limit).all()