import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os

# Создаем папку для логов
LOG_DIR = Path("/app/log")
LOG_DIR.mkdir(exist_ok=True)

# Временный логгер с маленьким размером для демонстрации
handler = RotatingFileHandler(
    LOG_DIR / 'app.log',
    maxBytes=1000,  # 1KB для быстрой ротации
    backupCount=3,
    encoding='utf-8'
)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger('demo')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Генерируем много логов чтобы вызвать ротацию
print("Generating logs for rotation demo...")
for i in range(500):
    logger.info(f"Test log message #{i} - This is a demo message to fill up the log file quickly for rotation demonstration purposes.")
    
print("Log generation complete!")