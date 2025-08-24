from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
import sqlalchemy

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
    __table_args__ = (
        sqlalchemy.UniqueConstraint('filename', 'whisper_model', name='uix_filename_whisper_model'),
        {'sqlite_autoincrement': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    upload_time = Column(DateTime, nullable=False)
    whisper_model = Column(SQLEnum(WhisperModel), nullable=False, default=WhisperModel.BASE)  # type: ignore
    status = Column(SQLEnum(AudioFileStatus), nullable=False, default=AudioFileStatus.UPLOADED)  # type: ignore
    storage_path = Column(String, nullable=False)
    audio_duration_seconds = Column(Float, nullable=False)

    transcript = relationship("Transcript", back_populates="audio_file", uselist=False, cascade="all, delete-orphan")
    user = relationship("User")

from app.models.user import User
