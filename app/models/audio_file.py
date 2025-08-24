from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from .database import Base

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import Enum as SQLEnum
from app.models.enums import AudioFileStatus, WhisperModel


from app.models.transcript import Transcript

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

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename: str = Column(String, unique=True, nullable=False)
    original_name: str = Column(String, nullable=False)
    content_type: str = Column(String, nullable=False)
    size: int = Column(Integer, nullable=False)
    upload_time: DateTime = Column(DateTime, nullable=False)
    whisper_model: WhisperModel = Column(SQLEnum(WhisperModel), nullable=False, default=WhisperModel.BASE)
    status: AudioFileStatus = Column(SQLEnum(AudioFileStatus), nullable=False, default=AudioFileStatus.UPLOADED)
    storage_path: str = Column(String, nullable=False)
    audio_duration_seconds: float = Column(Float, nullable=False)

    transcript = relationship("Transcript", back_populates="audio_file", uselist=False, cascade="all, delete-orphan")
    user = relationship("User")

from app.models.user import User
