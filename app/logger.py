import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os

# Создаем папку для логов
LOG_DIR = Path("/app/log") 
LOG_DIR.mkdir(exist_ok=True)

# Конфигурация логирования
def setup_logging():
    # Форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
    )
    
    # Обработчик для файла с ротацией
    file_handler = RotatingFileHandler(
        LOG_DIR / 'app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    
    # Корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Логгер для SQLAlchemy
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_logger.setLevel(logging.WARNING)
    
    # Логгер для нашего приложения
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.DEBUG)

# Получение логгера для модуля
def get_logger(name):
    return logging.getLogger(f'app.{name}')