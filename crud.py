from sqlalchemy.orm import Session
from models import User
from schemas import UserCreate, UserUpdate
from werkzeug.security import generate_password_hash

def create_user(db: Session, user: UserCreate):
    db_user = User(
        email=user.email,
        role_id=user.role_id,
        password_hash=generate_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.user_id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, user_data: UserUpdate):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None
    if user_data.email:
        user.email = user_data.email
    if user_data.password:
        user.password_hash = generate_password_hash(user_data.password)
    if user_data.role_id:
        user.role_id = user_data.role_id
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user
