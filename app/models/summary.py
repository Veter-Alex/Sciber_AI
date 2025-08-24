from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import Enum as SQLEnum
from app.models.enums import SummaryStatus

from .database import Base

class Summary(Base):
    """
    Модель для хранения саммари перевода.
    """
    __tablename__ = "summaries"

    id: int = Column(Integer, primary_key=True, index=True)
    translation_id: int = Column(Integer, ForeignKey("translations.id", ondelete="CASCADE"), nullable=False, unique=True)
    base_language: str = Column(String, nullable=False)
    target_language: str = Column(String, nullable=False)
    status: SummaryStatus = Column(SQLEnum(SummaryStatus), nullable=False, default=SummaryStatus.PROCESSING)
    text: str = Column(String, nullable=True)
    created_at: DateTime = Column(DateTime, nullable=False)
    updated_at: DateTime = Column(DateTime, nullable=False)

    translation = relationship("Translation", back_populates="summary")