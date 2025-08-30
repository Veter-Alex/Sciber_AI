"""
Синхронная реализация операций с audio_files для использования в
синхронных воркерах Celery и других блокирующих контекстах.

Функции названы с постфиксом `_sync` чтобы явно различать их с асинхронными
аналогами в `app.db.ops.async_impl`.
"""

from typing import Optional, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.audio_file import AudioFile
# ensure related models are imported so SQLAlchemy can resolve relationships
from app.models import transcript  # noqa: F401
from app.models import translation  # noqa: F401
from app.models import summary  # noqa: F401
from app.models import user  # noqa: F401
from app.utils.settings import settings


_engine = create_engine(settings.sync_db_url, future=True)
_Session = sessionmaker(bind=_engine, expire_on_commit=False)


def get_audio_file_sync(filename: str, whisper_model: str) -> Optional[AudioFile]:
    """Найти запись по имени файла и модели. Возвращает AudioFile или None."""
    with _Session() as s:
        return s.query(AudioFile).filter_by(filename=filename, whisper_model=whisper_model).first()


def get_audio_file_by_id_sync(audio_file_id: int) -> Optional[AudioFile]:
    """Получить запись по её id."""
    with _Session() as s:
        return s.get(AudioFile, audio_file_id)


def add_audio_file_sync(user_id: int, filename: str, original_name: str, content_type: str,
                        size: int, whisper_model: str, storage_path: str, audio_duration_seconds: float) -> Optional[int]:
    """Добавить запись в таблицу и вернуть её id.

    Если вставка ломается из-за уникального ограничения, функция откатывает
    транзакцию и возвращает id существующей записи.
    """
    with _Session() as s:
        try:
            af = AudioFile(
                user_id=user_id,
                filename=filename,
                original_name=original_name,
                content_type=content_type,
                size=size,
                upload_time=datetime.now(),
                whisper_model=whisper_model,
                status='uploaded',
                storage_path=storage_path,
                audio_duration_seconds=audio_duration_seconds,
            )
            s.add(af)
            s.commit()
            return af.id
        except IntegrityError:
            s.rollback()
            existing = s.query(AudioFile).filter_by(filename=filename, whisper_model=whisper_model).first()
            return existing.id if existing else None


def delete_audio_file_sync(filename: str, whisper_model: str) -> bool:
    """Удалить запись по имени файла и модели. Возвращает True/False по успеху."""
    with _Session() as s:
        af = s.query(AudioFile).filter_by(filename=filename, whisper_model=whisper_model).first()
        if af:
            s.delete(af)
            s.commit()
            return True
        return False


def get_all_audio_files_sync() -> List[AudioFile]:
    """Вернуть все записи AudioFile как список моделей."""
    with _Session() as s:
        return s.query(AudioFile).all()


def update_audio_file_status_sync(audio_file_id: int, status):
    """Обновить статус записи по её id. Возвращает True/False по успеху."""
    with _Session() as s:
        af = s.get(AudioFile, audio_file_id)
        if not af:
            return False
        af.status = status
        s.commit()
        return True
