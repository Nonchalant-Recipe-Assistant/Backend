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
    return check_password_hash(hashed_password, plain_password)

def create_access_token(data: dict, expires_delta_minutes: int = None):
    if expires_delta_minutes is None:
        expires_delta_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str):
    """
    Verify JWT token or allow demo tokens in development mode
    """
    logger.info(f"🔍 Verifying token: {token}")
    
    # Allow demo tokens in development
    environment = os.getenv("ENVIRONMENT", "development")
    logger.info(f"🏗️ Environment: {environment}")
    
    if environment == "development":
        logger.info("🔧 Development mode - checking demo tokens")
        if token and (token.startswith("demo-") or "demo-jwt-token" in token):
            logger.info("✅ Demo token accepted")
            # Extract email from demo token if possible, or use default
            if "demo-jwt-token" in token:
                return {"email": "demo@example.com", "username": "demo_user"}
            elif "demo-google-token" in token:
                return {"email": "google-user@example.com", "username": "google_user"}
            else:
                return {"email": "demo@example.com", "username": "demo_user"}
        else:
            logger.warning(f"❌ Not a demo token: {token}")
    
    # If not development or not a demo token, try JWT verification
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("❌ No email in token payload")
            return None
        logger.info(f"✅ Valid JWT token for: {email}")
        return {"email": email, "username": email.split("@")[0]}
    except JWTError as e:
        logger.error(f"❌ JWT Error: {e}")
        return None