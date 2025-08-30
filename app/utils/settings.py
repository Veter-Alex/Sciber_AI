
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
"""
Модуль настроек приложения.

Назначение:
    - Загружает переменные окружения из файла `.env`.
    - Предоставляет централизованный объект `settings` с удобными свойствами
      для получения синхронной и асинхронной строк подключения к БД и других
      конфигурационных значений.

Основные функции:
    - `Settings.sync_db_url` - возвращает синхронную DSN для SQLAlchemy/Alembic.
    - `Settings.async_db_url` - возвращает асинхронную DSN для asyncpg.

Зависимости:
    - dotenv (load_dotenv)
    - os

Пример использования:
    from app.utils.settings import settings
    engine = create_engine(settings.sync_db_url)
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class Settings:
    """
    Класс-обёртка над переменными окружения приложения.

    Атрибуты:
        STORAGE_DIR: str - путь к директории хранения аудиофайлов.
        DB_*: str - параметры подключения к базе данных.
    """

    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "storage")  # Директория для хранения файлов

    DB_HOST: str = os.getenv("DB_HOST", "localhost")  # Хост базы данных
    DB_PORT: str = os.getenv("DB_PORT", "5432")  # Порт базы данных
    DB_USER: str = os.getenv("DB_USER", "postgres")  # Имя пользователя
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")  # Пароль пользователя
    DB_NAME: str = os.getenv("DB_NAME", "postgres")  # Имя базы данных

    @property
    def sync_db_url(self) -> str:
        """
        Возвращает синхронную строку подключения для SQLAlchemy/Alembic.

        Returns:
            str: DSN в формате postgresql://user:pass@host:port/dbname
        """
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def async_db_url(self) -> str:
        """
        Возвращает асинхронную строку подключения для SQLAlchemy/asyncpg.

        Returns:
            str: DSN в формате postgresql+asyncpg://user:pass@host:port/dbname
        """
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


# Экземпляр настроек для использования в приложении
settings: Settings = Settings()
