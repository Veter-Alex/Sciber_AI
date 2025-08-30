"""
Модуль модели `Translation`.

Хранит переводы для транскрипта: тексты на целевых языках, статус обработки
и метрики. Связан с `Transcript` и может иметь связанный `Summary`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.types import Enum as SQLEnum

from .database import Base
from app.models.enums import TranslationStatus


class Translation(Base):
    """ORM-модель перевода транскрипта.

    Поля включают исходный язык, переводы (англ/рус), статус и временные метки.
    """
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transcript_id: Mapped[int] = mapped_column(Integer, ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False, unique=True)
    source_language: Mapped[str] = mapped_column(String, nullable=False)
    text_en: Mapped[str] = mapped_column(String, nullable=True)
    text_ru: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[TranslationStatus] = mapped_column(SQLEnum(TranslationStatus), nullable=False, default=TranslationStatus.PROCESSING)
    processing_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    text_chars: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

    transcript: Mapped["Transcript"] = relationship("Transcript", back_populates="translation")
    summary: Mapped["Summary"] = relationship("Summary", back_populates="translation", uselist=False, cascade="all, delete-orphan")

if TYPE_CHECKING:
    from app.models.transcript import Transcript
    from app.models.summary import Summary