from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func, DateTime, Text
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
    user_id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    role = relationship("Role", back_populates="users")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    sender_email = Column(String(255), nullable=False)
    sender_username = Column(String(100), nullable=False)
    message_type = Column(String(50), default="text")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())