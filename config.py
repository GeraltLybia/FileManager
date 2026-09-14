"""
Конфигурация приложения. Переменные читаются из окружения или .env.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Корень проекта
BASE_DIR = Path(__file__).resolve().parent

# Директория для загружаемых файлов (можно переопределить через UPLOAD_DIR)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "src")))

# CORS: разрешённые origins через запятую (например: http://localhost:5173,http://localhost:3000)
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "http://localhost:5173")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",") if origin.strip()]

# Сервер (для деплоя)
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Максимальный размер одного загружаемого файла, в МБ
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "500"))
MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024
