from sqlalchemy.orm import Session
from app.models import User, Role
from app.schemas import UserCreate
from app.utils import hash_password, verify_password
from app.email_utils import generate_verification_token, calculate_expiration_time, send_verification_email
from app.logger import get_logger  
from datetime import datetime

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
        """Создает пользователя без верификации (для обратной совместимости)"""
        logger.info(f"Creating user with email: {user.email}")
        try:
            user_role = self.db.query(Role).filter(Role.name == "user").first()
            if not user_role:
                logger.warning("Role 'user' not found, creating it...")
                user_role = Role(name="user")
                self.db.add(user_role)
                self.db.commit()
                self.db.refresh(user_role)
                logger.info(f"Created role 'user' with ID: {user_role.role_id}")

            db_user = User(
                email=user.email,
                role_id=user_role.role_id,
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

    def verify_user_password(self, email: str, password: str) -> bool:
        """Проверяет пароль пользователя"""
        user = self.get_user_by_email(email)
        if not user:
            return False
        return verify_password(password, user.password_hash)
    
    def get_user_by_verification_token(self, token: str):
        """Находит пользователя по токену верификации"""
        logger.debug(f"Looking for user with verification token: {token}")
        return self.db.query(User).filter(
            (User.email_verification_token == token) | 
            (User.pending_email_token == token)
        ).first()

    def create_user_with_verification(self, user: UserCreate):
        """Создает пользователя и отправляет email для верификации"""
        logger.info(f"Creating user with email verification: {user.email}")
        try:
            # Проверяем, не существует ли уже пользователь с таким email
            existing_user = self.get_user_by_email(user.email)
            if existing_user:
                logger.warning(f"User already exists: {user.email}")
                raise ValueError("User with this email already exists")

            # Находим или создаем роль "user"
            user_role = self.db.query(Role).filter(Role.name == "user").first()
            if not user_role:
                logger.warning("Role 'user' not found, creating it...")
                user_role = Role(name="user")
                self.db.add(user_role)
                self.db.commit()
                self.db.refresh(user_role)
                logger.info(f"Created role 'user' with ID: {user_role.role_id}")

            # Генерируем токен верификации
            verification_token = generate_verification_token()
            verification_expires = calculate_expiration_time()

            # Создаем пользователя
            db_user = User(
                email=user.email,
                role_id=user_role.role_id,
                password_hash=hash_password(user.password),
                email_verified=False,
                email_verification_token=verification_token,
                email_verification_expires=verification_expires
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            # Отправляем email для верификации
            send_verification_email(user.email, verification_token, "verification")
            
            logger.info(f"User created with verification: {user.email}")
            return db_user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user {user.email}: {str(e)}")
            raise

    def verify_email(self, token: str):
        """Подтверждает email пользователя по токену"""
        logger.info(f"Verifying email with token: {token}")
        user = self.get_user_by_verification_token(token)
        
        if not user:
            logger.warning(f"Verification failed: invalid token")
            return None
            
        if user.email_verification_token == token:
            # Верификация основного email
            if user.email_verification_expires and user.email_verification_expires < datetime.utcnow():
                logger.warning(f"Verification token expired for user: {user.email}")
                return None
                
            user.email_verified = True
            user.email_verification_token = None
            user.email_verification_expires = None
            self.db.commit()
            
            # Отправляем приветственное письмо
            from app.email_utils import send_welcome_email
            send_welcome_email(user.email, user.email.split('@')[0])
            
        elif user.pending_email_token == token:
            # Верификация смены email
            if user.pending_email_expires and user.pending_email_expires < datetime.utcnow():
                logger.warning(f"Email change token expired for user: {user.email}")
                return None
                
            user.email = user.pending_email
            user.email_verified = True
            user.pending_email = None
            user.pending_email_token = None
            user.pending_email_expires = None
            self.db.commit()
            
        logger.info(f"Email verified successfully for user: {user.email}")
        return user

    def initiate_email_change(self, user_id: int, new_email: str):
        """Инициирует смену email с отправкой подтверждения"""
        logger.info(f"Initiating email change for user {user_id} to {new_email}")
        
        user = self.get_user(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            return None
            
        # Проверяем, не используется ли новый email
        existing_user = self.get_user_by_email(new_email)
        if existing_user:
            logger.warning(f"Email already in use: {new_email}")
            return None
            
        # Генерируем токен для смены email
        change_token = generate_verification_token()
        change_expires = calculate_expiration_time()
        
        user.pending_email = new_email
        user.pending_email_token = change_token
        user.pending_email_expires = change_expires
        
        self.db.commit()
        
        # Отправляем email для подтверждения смены
        send_verification_email(new_email, change_token, "email_change")
        
        logger.info(f"Email change initiated for user {user_id}")
        return user

    def update_avatar(self, user_id: int, avatar_url: str):
        """Обновляет аватар пользователя"""
        logger.info(f"Updating avatar for user {user_id}")
        
        user = self.get_user(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            return None
            
        user.avatar_url = avatar_url
        self.db.commit()
        
        logger.info(f"Avatar updated for user {user_id}")
        return user

    def resend_verification_email(self, user_id: int):
        """Повторно отправляет email для верификации"""
        logger.info(f"Resending verification email for user: {user_id}")
        
        user = self.get_user(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            return None
            
        if user.email_verified:
            logger.warning(f"Email already verified: {user.email}")
            return None
            
        # Генерируем новый токен
        verification_token = generate_verification_token()
        verification_expires = calculate_expiration_time()
        
        user.email_verification_token = verification_token
        user.email_verification_expires = verification_expires
        self.db.commit()
        
        # Отправляем email
        send_verification_email(user.email, verification_token, "verification")
        
        logger.info(f"Verification email resent for: {user.email}")
        return user