from sqlalchemy.orm import Session
from models import User
from schemas import UserCreate, UserUpdate
from werkzeug.security import generate_password_hash
from logger import logger

def create_user(db: Session, user: UserCreate):
    db_user = User(
        email=user.email,
        role_id=user.role_id,
        password_hash=generate_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created: id={db_user.user_id}, email={db_user.email}")
    return db_user

def get_user(db: Session, user_id: int):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        logger.info(f"User retrieved: id={user.user_id}, email={user.email}")
    else:
        logger.warning(f"User not found: id={user_id}")
    return user

def update_user(db: Session, user_id: int, user_data: UserUpdate):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        logger.warning(f"User update failed, not found: id={user_id}")
        return None
    if user_data.email:
        user.email = user_data.email
    if user_data.password:
        user.password_hash = generate_password_hash(user_data.password)
    if user_data.role_id:
        user.role_id = user_data.role_id
    db.commit()
    db.refresh(user)
    logger.info(f"User updated: id={user.user_id}, email={user.email}")
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        logger.warning(f"User delete failed, not found: id={user_id}")
        return None
    db.delete(user)
    db.commit()
    logger.info(f"User deleted: id={user_id}")
    return user
