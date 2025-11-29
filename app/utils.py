from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import settings
from werkzeug.security import generate_password_hash, check_password_hash
from app.logger import get_logger
import os

logger = get_logger(__name__)

def hash_password(password: str):
    return generate_password_hash(password)

def verify_password(plain_password, hashed_password):
    # ИСПРАВЛЕНО: правильный порядок аргументов
    return check_password_hash(hashed_password, plain_password)

def create_access_token(data: dict, expires_delta_minutes: int = None):
    if expires_delta_minutes is None:
        expires_delta_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str):
    """Упрощенная проверка токена"""
    logger.info(f"🔍 Verifying token: {token[:30]}...")
    
    # В development режиме принимаем любой JWT токен
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "development":
        logger.info("🔧 Development mode - accepting JWT tokens")
        try:
            # Декодируем без проверки подписи чтобы получить email
            payload = jwt.decode(token, options={"verify_signature": False})
            email = payload.get("sub", "unknown@example.com")
            username = email.split('@')[0]
            logger.info(f"✅ Development token accepted for: {email}")
            return {"email": email, "username": username}
        except Exception as e:
            logger.error(f"❌ Token decoding failed: {e}")
            return None
    
    # Для production оставляем строгую проверку
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return {"email": email, "username": email.split("@")[0]}
    except JWTError as e:
        logger.error(f"❌ JWT verification failed: {e}")
        return None