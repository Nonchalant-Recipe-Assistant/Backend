from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import settings
from werkzeug.security import generate_password_hash, check_password_hash

# Убираем bcrypt и используем werkzeug
def hash_password(password: str):
    return generate_password_hash(password)

def verify_password(plain_password, hashed_password):
    return check_password_hash(hashed_password, plain_password)

def create_access_token(data: dict, expires_delta_minutes: int = None):
    if expires_delta_minutes is None:
        expires_delta_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)