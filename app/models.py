from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {'extend_existing': True}

    role_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}  # Добавьте это

    user_id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Новые поля для подтверждения email
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime, nullable=True)
    
    # Поле для аватарки
    avatar_url = Column(String(500), nullable=True)
    
    # Поля для временного email при смене
    pending_email = Column(String(100), nullable=True)
    pending_email_token = Column(String(255), nullable=True)
    pending_email_expires = Column(DateTime, nullable=True)

    role = relationship("Role", back_populates="users")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = {'extend_existing': True}  # Добавьте это
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    sender_email = Column(String(255), nullable=False)
    sender_username = Column(String(100), nullable=False)
    message_type = Column(String(50), default="text")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(Text, nullable=True) # Для полнотекстового поиска
    instructions = Column(Text, nullable=True)
    
    # Поля для фильтрации
    category = Column(String(100), nullable=True) # Например: "Italian", "Vegan"
    cooking_time = Column(Integer, nullable=True) # В минутах
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с автором (если нужно по заданию)
    author_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)