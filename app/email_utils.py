import secrets
import string
from datetime import datetime, timedelta
from app.logger import get_logger
from app.config import settings

logger = get_logger(__name__)

def generate_verification_token(length=32):
    """Генерирует случайный токен для верификации"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def calculate_expiration_time(hours=24):
    """Рассчитывает время истечения токена"""
    return datetime.utcnow() + timedelta(hours=hours)

async def send_verification_email(email: str, token: str, email_type: str = "verification"):
    """Отправляет email с ссылкой для верификации"""
    # В development используем мок-сервис
    if settings.ENVIRONMENT == "development":
        logger.info(f"📧 [MOCK] Sending {email_type} email to: {email}")
        logger.info(f"📧 [MOCK] Verification token: {token}")
        logger.info(f"📧 [MOCK] Verification URL: {settings.BASE_URL}/verify-email?token={token}")
        return True
    else:
        # В продакшене используем реальный сервис
        try:
            from app.email_service import email_service
            return await email_service.send_verification_email(email, token, email_type)
        except Exception as e:
            logger.error(f"❌ Failed to send verification email: {str(e)}")
            return False

async def send_welcome_email(email: str, username: str):
    """Отправляет приветственное письмо после подтверждения"""
    if settings.ENVIRONMENT == "development":
        logger.info(f"📧 [MOCK] Sending welcome email to: {email}")
        logger.info(f"📧 [MOCK] Welcome username: {username}")
        return True
    else:
        try:
            from app.email_service import email_service
            return await email_service.send_welcome_email(email, username)
        except Exception as e:
            logger.error(f"❌ Failed to send welcome email: {str(e)}")
            return False