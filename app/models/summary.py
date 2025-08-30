"""
Модуль модели `Summary`.

Сохраняет итоговое краткое содержание (summary) для переведённого транскрипта.
Содержит статус выполнения и временные метки.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.types import Enum as SQLEnum

from .database import Base
from app.models.enums import SummaryStatus


class Summary(Base):
    """ORM-модель для хранения саммари перевода.

    Поля:
        - translation_id: FK на `translations`
        - base_language/target_language: языки саммари
        - status: статус обработки
        - text: итоговый текст саммари
        - created_at/updated_at: метки времени
    """
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    translation_id: Mapped[int] = mapped_column(Integer, ForeignKey("translations.id", ondelete="CASCADE"), nullable=False, unique=True)
    base_language: Mapped[str] = mapped_column(String, nullable=False)
    target_language: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[SummaryStatus] = mapped_column(SQLEnum(SummaryStatus), nullable=False, default=SummaryStatus.PROCESSING)
    text: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

    translation: Mapped["Translation"] = relationship("Translation", back_populates="summary")


if TYPE_CHECKING:
    from app.models.translation import Translation