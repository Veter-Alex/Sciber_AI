from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import Enum as SQLEnum
from app.models.enums import TranslationStatus

from .database import Base

class Translation(Base):
    """
    Модель для хранения переводов транскриптов.
    """
    __tablename__ = "translations"

    id: int = Column(Integer, primary_key=True, index=True)
    transcript_id: int = Column(Integer, ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False, unique=True)
    source_language: str = Column(String, nullable=False)
    text_en: str = Column(String, nullable=True)
    text_ru: str = Column(String, nullable=True)
    status: TranslationStatus = Column(SQLEnum(TranslationStatus), nullable=False, default=TranslationStatus.PROCESSING)
    processing_seconds: float = Column(Float, nullable=True)
    text_chars: int = Column(Integer, nullable=True)
    created_at: DateTime = Column(DateTime, nullable=False)
    updated_at: DateTime = Column(DateTime, nullable=False)

    transcript = relationship("Transcript", back_populates="translation")
    summary = relationship("Summary", back_populates="translation", uselist=False, cascade="all, delete-orphan")

from app.models.summary import Summary