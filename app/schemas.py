from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    role_id: int

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
