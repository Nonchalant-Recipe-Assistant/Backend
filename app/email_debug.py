import os
import resend
from app.logger import get_logger
from app.config import settings

logger = get_logger(__name__)

def debug_email_config():
    """Проверяет конфигурацию email"""
    logger.info("🔧 Debugging email configuration...")
    
    logger.info(f"RESEND_API_KEY: {'Set' if settings.RESEND_API_KEY and settings.RESEND_API_KEY != 'your-resend-api-key-here' else 'Not set or default'}")
    logger.info(f"FROM_EMAIL: {settings.FROM_EMAIL}")
    logger.info(f"BASE_URL: {settings.BASE_URL}")
    logger.info(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    
    # Проверяем, доступен ли Resend API
    try:
        if settings.ENVIRONMENT == "development":
            logger.info("✅ Development mode - using mock email service")
            return True
            
        if not settings.RESEND_API_KEY:
            logger.error("❌ RESEND_API_KEY is not set")
            return False
            
        if settings.RESEND_API_KEY == "your-resend-api-key-here":
            logger.error("❌ RESEND_API_KEY is still the default value")
            return False
            
        # Инициализируем Resend только если не в development
        resend.api_key = settings.RESEND_API_KEY
        logger.info("✅ Resend configuration looks good")
        return True
        
    except Exception as e:
        logger.error(f"❌ Resend configuration error: {e}")
        return False

async def send_test_email(email: str):
    """Отправляет тестовое email для проверки работы"""
    try:
        logger.info(f"📧 Attempting to send test email to: {email}")
        
        # В development режиме просто логируем
        if settings.ENVIRONMENT == "development":
            logger.info(f"✅ [MOCK] Test email would be sent to: {email}")
            logger.info(f"✅ [MOCK] Environment: {settings.ENVIRONMENT}")
            return True
        
        # В production используем реальный Resend
        if not settings.RESEND_API_KEY or settings.RESEND_API_KEY == "your-resend-api-key-here":
            logger.error("❌ Cannot send test email - RESEND_API_KEY not configured")
            return False
            
        # Инициализируем Resend
        resend.api_key = settings.RESEND_API_KEY
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #10B981; padding: 20px; text-align: center; color: white; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Test Email Successful!</h1>
                </div>
                <div>
                    <h2>Hello!</h2>
                    <p>This is a test email from Nonchalant Recipe Assistant.</p>
                    <p>If you received this, email sending is working correctly!</p>
                    <p><strong>Environment:</strong> {settings.ENVIRONMENT}</p>
                </div>
            </div>
        </body>
        </html>
        """.format(settings=settings)
        
        params = {
            "from": settings.FROM_EMAIL,
            "to": [email],
            "subject": "Test Email from Nonchalant Recipe",
            "html": html_content,
        }
        
        result = resend.Emails.send(params)
        logger.info(f"✅ Test email sent successfully! ID: {result['id']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send test email: {str(e)}")
        return False    