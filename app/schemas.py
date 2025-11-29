from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional
import re

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

    @validator('email')
    def email_domain(cls, v):
        # Простая проверка формата email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

class UserOut(BaseModel):
    user_id: int
    email: EmailStr
    role_id: int
    created_at: datetime
    email_verified: bool
    avatar_url: Optional[str] = None

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
    message_type: str = "text"

class ChatMessageOut(BaseModel):
    id: int
    text: str
    sender_email: str
    sender_username: str
    timestamp: datetime
    message_type: str = "text"
    
    class Config:
        from_attributes = True

# Схемы для email верификации
class EmailVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationConfirm(BaseModel):
    token: str

class UpdateEmailRequest(BaseModel):
    new_email: EmailStr

class AvatarUpdateResponse(BaseModel):
    avatar_url: str
    message: str

class UserProfile(BaseModel):
    user_id: int
    email: EmailStr
    email_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True