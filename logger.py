import logging
from logging.handlers import RotatingFileHandler

# Создаём логгер
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)

# Формат сообщений
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

# Логи в файл (макс. 5 MB, хранить 5 файлов)
file_handler = RotatingFileHandler(
    "app.log", maxBytes=5*1024*1024, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(formatter)

# Логи в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Добавляем хендлеры
logger.addHandler(file_handler)
logger.addHandler(console_handler)
