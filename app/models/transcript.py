from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import Enum as SQLEnum
from app.models.enums import TranscriptStatus

from .database import Base

class Transcript(Base):
    """
    Модель для хранения транскриптов аудиофайлов.
    """
    __tablename__ = "transcripts"

    id: int = Column(Integer, primary_key=True, index=True)
    audio_file_id: int = Column(Integer, ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False, unique=True)
    status: TranscriptStatus = Column(SQLEnum(TranscriptStatus), nullable=False, default=TranscriptStatus.PROCESSING)
    text: str = Column(String, nullable=True)
    processing_seconds: float = Column(Float, nullable=True)
    text_chars: int = Column(Integer, nullable=True)
    real_time_factor: float = Column(Float, nullable=True)
    created_at: DateTime = Column(DateTime, nullable=False)
    updated_at: DateTime = Column(DateTime, nullable=False)

    audio_file = relationship("AudioFile", back_populates="transcript")
    translation = relationship("Translation", back_populates="transcript", uselist=False, cascade="all, delete-orphan")

from app.models.translation import Translation