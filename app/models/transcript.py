"""
Модуль модели `Transcript`.

Содержит ORM-модель транскрипта, которая привязана к записи в таблице
`audio_files` через внешний ключ. Модель хранит текст транскрипта,
статус обработки, метрики производительности и временные метки.

Используется совместно с моделями `Translation` и `AudioFile`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.types import Enum as SQLEnum
from .database import Base
from app.models.enums import TranscriptStatus


class Transcript(Base):
    """ORM-модель транскрипта аудиофайла.

    Атрибуты класса соответствуют столбцам таблицы `transcripts`.
    """
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    audio_file_id: Mapped[int] = mapped_column(Integer, ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False, unique=True)
    status: Mapped[TranscriptStatus] = mapped_column(SQLEnum(TranscriptStatus), nullable=False, default=TranscriptStatus.PROCESSING)
    text: Mapped[str] = mapped_column(String, nullable=True)
    processing_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    text_chars: Mapped[int] = mapped_column(Integer, nullable=True)
    real_time_factor: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

    audio_file: Mapped["AudioFile"] = relationship("AudioFile", back_populates="transcript")
    translation: Mapped["Translation"] = relationship("Translation", back_populates="transcript", uselist=False, cascade="all, delete-orphan")

if TYPE_CHECKING:
    from app.models.audio_file import AudioFile
    from app.models.translation import Translation