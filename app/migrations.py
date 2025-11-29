from app.database import SessionLocal, engine
from app.models import Base, User
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def migrate_database():
    """Добавляет отсутствующие колонки в таблицу users"""
    db = SessionLocal()
    try:
        # Проверяем существующие колонки
        result = db.execute(text("SHOW COLUMNS FROM users"))
        existing_columns = [row[0] for row in result]
        
        logger.info(f"Existing columns: {existing_columns}")
        
        # Добавляем отсутствующие колонки
        if 'email_verified' not in existing_columns:
            logger.info("Adding email_verified column")
            db.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE"))
        
        if 'email_verification_token' not in existing_columns:
            logger.info("Adding email_verification_token column")
            db.execute(text("ALTER TABLE users ADD COLUMN email_verification_token VARCHAR(255)"))
        
        if 'email_verification_expires' not in existing_columns:
            logger.info("Adding email_verification_expires column")
            db.execute(text("ALTER TABLE users ADD COLUMN email_verification_expires DATETIME"))
        
        if 'avatar_url' not in existing_columns:
            logger.info("Adding avatar_url column")
            db.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)"))
        
        if 'pending_email' not in existing_columns:
            logger.info("Adding pending_email column")
            db.execute(text("ALTER TABLE users ADD COLUMN pending_email VARCHAR(100)"))
        
        if 'pending_email_token' not in existing_columns:
            logger.info("Adding pending_email_token column")
            db.execute(text("ALTER TABLE users ADD COLUMN pending_email_token VARCHAR(255)"))
        
        if 'pending_email_expires' not in existing_columns:
            logger.info("Adding pending_email_expires column")
            db.execute(text("ALTER TABLE users ADD COLUMN pending_email_expires DATETIME"))
        
        db.commit()
        logger.info("Database migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_database()