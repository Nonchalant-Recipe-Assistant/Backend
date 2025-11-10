from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    role_id: int

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = None

class RoleOut(RoleBase):
    role_id: int
    
    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    text: str
    message_type: str = "text"  # text, system, etc.

class ChatMessageOut(BaseModel):
    id: int
    text: str
    sender_email: str
    sender_username: str
    timestamp: datetime
    message_type: str = "text"
    
    class Config:
        from_attributes = True