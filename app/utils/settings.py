
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class Settings:
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "storage")  # Директория для хранения файлов
    """
    Класс для хранения и генерации настроек подключения к базе данных.
    Все значения берутся из переменных окружения.
    """
    DB_HOST: str = os.getenv("DB_HOST", "localhost")  # Хост базы данных
    DB_PORT: str = os.getenv("DB_PORT", "5432")       # Порт базы данных
    DB_USER: str = os.getenv("DB_USER", "postgres")   # Имя пользователя
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")   # Пароль пользователя
    DB_NAME: str = os.getenv("DB_NAME", "postgres")   # Имя базы данных

    @property
    def sync_db_url(self) -> str:
        """
        Синхронная строка подключения для Alembic и других sync-инструментов.
        """
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def async_db_url(self) -> str:
        """
        Асинхронная строка подключения для SQLAlchemy/asyncpg.
        """
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

# Экземпляр настроек для использования в приложении
settings: Settings = Settings()
