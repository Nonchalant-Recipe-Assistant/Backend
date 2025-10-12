from sqlalchemy.orm import Session
from app.models import User
from app.schemas import UserCreate
from werkzeug.security import generate_password_hash

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_users(self):
        return self.db.query(User).all()

    def get_user(self, user_id: int):
        return self.db.query(User).filter(User.user_id == user_id).first()

    def create_user(self, user: UserCreate):
        db_user = User(
            email=user.email,
            role_id=user.role_id,
            password_hash=generate_password_hash(user.password)
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def delete_user(self, user_id: int):
        db_user = self.db.query(User).filter(User.user_id == user_id).first()
        if db_user:
            self.db.delete(db_user)
            self.db.commit()
        return db_user
