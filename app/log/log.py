# log.py — единый логгер приложения
# короткие комментарии

import logging
import os
from datetime import datetime

# директория логов
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# имя файла вида app_2025-11-13.log
log_file = os.path.join(
    LOG_DIR,
    f"app_{datetime.now().strftime('%Y-%m-%d')}.log"
)

# основной логгер
app_logger = logging.getLogger("app")
app_logger.setLevel(logging.INFO)

# формат логов
fmt = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# вывод в файл
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(fmt)
file_handler.setLevel(logging.INFO)

# вывод в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(fmt)
console_handler.setLevel(logging.INFO)

# подключение хендлеров
if not app_logger.handlers:
    app_logger.addHandler(file_handler)
    app_logger.addHandler(console_handler)

# короткая функция для внешних модулей
def log_info(msg: str):
    app_logger.info(msg)

def log_error(msg: str):
    app_logger.error(msg)
