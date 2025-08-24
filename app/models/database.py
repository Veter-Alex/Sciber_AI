from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.utils.settings import settings

# Формируем строку подключения к базе данных из настроек
DATABASE_URL: str = settings.async_db_url

# Создаем асинхронный движок SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=True)

# Создаем фабрику асинхронных сессий для работы с БД
AsyncSessionLocal = async_sessionmaker(
	bind=engine,
	expire_on_commit=False
)
# Базовый класс для всех моделей
Base = declarative_base()
# Пример использования:
# async with AsyncSessionLocal() as session:
#     ... # работа с сессией
