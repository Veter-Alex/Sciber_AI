"""
Модель пользователя (ORM).

Определяет таблицу `users` и основные поля: имя, хэш пароля и флаги активности/админства.
"""

from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base

from .database import Base


class User(Base):
    """
    Модель пользователя системы.
    Атрибуты:
        id (int): Уникальный идентификатор пользователя.
        name (str): Имя пользователя (уникальное).
        hashed_password (str): Хэш пароля пользователя.
        is_active (bool): Активен ли пользователь.
        is_admin (bool): Является ли пользователь администратором.
    """
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("name", name="uq_user_name"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
