from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.database import engine

from sqlalchemy.ext.asyncio import async_sessionmaker

SessionLocal = async_sessionmaker(
	bind=engine,
	expire_on_commit=False
)
