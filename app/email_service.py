import os
import resend
from app.logger import get_logger
from app.config import settings

logger = get_logger(__name__)

# Инициализируем Resend
resend.api_key = settings.RESEND_API_KEY

class EmailService:
    def __init__(self):
        self.from_email = settings.FROM_EMAIL
        self.base_url = settings.BASE_URL
    
    async def send_verification_email(self, email: str, token: str, email_type: str = "verification"):
        """Отправляет email для верификации"""
        try:
            if email_type == "verification":
                subject = "Verify Your Email - Nonchalant Recipe"
                verification_url = f"{self.base_url}/verify-email?token={token}"
                
                html_content = self._create_verification_template(
                    title="Verify Your Email",
                    message="Welcome to Nonchalant Recipe! Please verify your email address to start using your account.",
                    button_text="Verify Email",
                    verification_url=verification_url
                )
            else:  # email change
                subject = "Confirm Email Change - Nonchalant Recipe"
                verification_url = f"{self.base_url}/verify-email-change?token={token}"
                
                html_content = self._create_verification_template(
                    title="Confirm Email Change",
                    message="You have requested to change your email address. Please confirm this change.",
                    button_text="Confirm Change",
                    verification_url=verification_url
                )
            
            # Отправляем email через Resend
            params = {
                "from": self.from_email,
                "to": [email],
                "subject": subject,
                "html": html_content,
            }
            
            result = resend.Emails.send(params)
            logger.info(f"✅ Verification email sent to {email}, id: {result['id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send verification email to {email}: {str(e)}")
            return False
    
    def _create_verification_template(self, title: str, message: str, button_text: str, verification_url: str) -> str:
        """Создает HTML шаблон для email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10B981, #059669); padding: 30px; text-align: center; color: white; }}
                .content {{ background: #f9fafb; padding: 30px; }}
                .button {{ background: #10B981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #6B7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍳 Nonchalant Recipe</h1>
                    <p>Your AI-powered cooking companion</p>
                </div>
                <div class="content">
                    <h2>{title}</h2>
                    <p>{message}</p>
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">{button_text}</a>
                    </div>
                    <p><strong>This link will expire in 24 hours.</strong></p>
                    <p>If you didn't request this, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 Nonchalant Recipe. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    async def send_welcome_email(self, email: str, username: str):
        """Отправляет приветственное письмо после подтверждения email"""
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #10B981, #059669); padding: 30px; text-align: center; color: white; }}
                    .content {{ background: #f9fafb; padding: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Welcome to Nonchalant Recipe!</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {username}!</h2>
                        <p>Your email has been successfully verified and your account is now active.</p>
                        <p>Start exploring amazing recipes with our AI assistant!</p>
                        <ul>
                            <li>💡 Get personalized recipe suggestions</li>
                            <li>⭐ Save your favorite recipes</li>
                            <li>👥 Share recipes with friends</li>
                            <li>🍳 Discover new cooking techniques</li>
                        </ul>
                        <p>Ready to start cooking? <a href="{self.base_url}">Launch the app</a></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            params = {
                "from": self.from_email,
                "to": [email],
                "subject": "Welcome to Nonchalant Recipe!",
                "html": html_content,
            }
            
            result = resend.Emails.send(params)
            logger.info(f"✅ Welcome email sent to {email}, id: {result['id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send welcome email to {email}: {str(e)}")
            return False

# Создаем глобальный экземпляр сервиса
email_service = EmailService()