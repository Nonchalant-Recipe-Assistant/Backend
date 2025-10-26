import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("backend_logger")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

file_handler = RotatingFileHandler("backend.log", maxBytes=5*1024*1024, backupCount=3)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
