"""
Модуль модели AudioFile.

Назначение:
    - Описывает ORM-модель `AudioFile`, которая хранит метаинформацию об аудиофайлах
      (имя файла, владелец, путь в storage, статус обработки и т.д.).

Основные сущности:
    - class AudioFile(Base): SQLAlchemy модель таблицы `audio_files`.

Зависимости:
    - SQLAlchemy ORM, типы колонок.

Примечания:
    - Модель использует типы Enum для полей статуса и выбора модели Whisper.
    - В таблице присутствует уникальный индекс на (filename, whisper_model).
"""

from __future__ import annotations

import sqlalchemy
from sqlalchemy import Integer, String, DateTime, ForeignKey, Float
from sqlalchemy import sql as sqlalchemy_sql
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.types import Enum as SQLEnum
from datetime import datetime

from .database import Base
from app.models.enums import AudioFileStatus, WhisperModel


class AudioFile(Base):
    """
    Модель для хранения информации об аудиофайлах, загруженных пользователями.
    Атрибуты:
        id (int): Уникальный идентификатор аудиофайла.
        user_id (int): Владелец файла (пользователь).
        filename (str): Имя файла на сервере (уникальное или с UUID).
        original_name (str): Оригинальное имя файла при загрузке.
        content_type (str): MIME-тип файла (например, audio/mpeg).
        size (int): Размер файла в байтах.
        upload_time (datetime): Время загрузки файла.
        whisper_model (str): Название модели Whisper, выбранной для транскрибации.
        status (str): Статус обработки: uploaded, processing, done, failed.
        storage_path (str): Относительный путь (model/user/filename).
    """
    __tablename__ = "audio_files"
    __table_args__ = (
        sqlalchemy.UniqueConstraint('filename', 'whisper_model', name='uix_filename_whisper_model'),
        {'sqlite_autoincrement': True}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    original_name: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    upload_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    whisper_model: Mapped[WhisperModel] = mapped_column(SQLEnum(WhisperModel), nullable=False, default=WhisperModel.BASE)
    status: Mapped[AudioFileStatus] = mapped_column(SQLEnum(AudioFileStatus), nullable=False, default=AudioFileStatus.UPLOADED)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    audio_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)

    transcript: Mapped["Transcript"] = relationship("Transcript", back_populates="audio_file", uselist=False, cascade="all, delete-orphan")
    user: Mapped["User"] = relationship("User")

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.transcript import Transcript
