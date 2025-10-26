from sqlalchemy.orm import Session
from app.models import User
from app.schemas import UserCreate
from app.utils import hash_password
from app.logger import get_logger  # Добавляем импорт

logger = get_logger(__name__)

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
        logger.debug("UserRepository initialized")

    def get_users(self):
        logger.debug("Fetching all users")
        return self.db.query(User).all()

    def get_user(self, user_id: int):
        logger.debug(f"Fetching user by ID: {user_id}")
        return self.db.query(User).filter(User.user_id == user_id).first()

    def get_user_by_email(self, email: str):
        logger.debug(f"Fetching user by email: {email}")
        user = self.db.query(User).filter(User.email == email).first()
        if user:
            logger.debug(f"User found: {email}")
        else:
            logger.debug(f"User not found: {email}")
        return user

    def create_user(self, user: UserCreate):
        logger.info(f"Creating user with email: {user.email}")
        try:
            db_user = User(
                email=user.email,
                role_id=user.role_id,
                password_hash=hash_password(user.password)
            )
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            logger.info(f"User created successfully: {user.email}")
            return db_user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user {user.email}: {str(e)}")
            raise

    def delete_user(self, user_id: int):
        logger.warning(f"Deleting user with ID: {user_id}")
        db_user = self.db.query(User).filter(User.user_id == user_id).first()
        if db_user:
            self.db.delete(db_user)
            self.db.commit()
            logger.warning(f"User deleted: {user_id}")
        return db_user