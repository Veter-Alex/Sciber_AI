"""
Синхронные операции с таблицей AudioFile для использования в Celery worker'ах.

Назначение:
    - Предоставить безопасные синхронные хелперы для создания/чтения/удаления записей AudioFile.
    - Эти функции используются исключительно внутри Celery workers, чтобы избежать смешивания
      async/sync сессий SQLAlchemy в одном процессе.

Основные функции:
    - get_audio_file_sync(filename, whisper_model)
    - get_audio_file_by_id_sync(audio_file_id)
    - add_audio_file_sync(...)
    - delete_audio_file_sync(filename, whisper_model)
    - get_all_audio_files_sync()
    - update_audio_file_status_sync(audio_file_id, status)

Зависимости:
    - sqlalchemy (create_engine, sessionmaker)
    - app.models.audio_file.AudioFile
    - app.utils.settings.settings

Примечание:
    - commit/rollback обрабатываются здесь локально; IntegrityError при дубликате обрабатывается
      и возвращает существующий id.
"""

from typing import Optional, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.audio_file import AudioFile
from app.utils.settings import settings


_engine = create_engine(settings.sync_db_url, future=True)
_Session = sessionmaker(bind=_engine, expire_on_commit=False)


def get_audio_file_sync(filename: str, whisper_model: str) -> Optional[AudioFile]:
    """
    Получить запись AudioFile по имени и модели.

    Args:
        filename (str): имя файла.
        whisper_model (str): модель (подпапка в storage).

    Returns:
        Optional[AudioFile]: объект AudioFile или None.
    """
    with _Session() as s:
        return s.query(AudioFile).filter_by(filename=filename, whisper_model=whisper_model).first()


def get_audio_file_by_id_sync(audio_file_id: int) -> Optional[AudioFile]:
    """
    Получить запись AudioFile по id.

    Args:
        audio_file_id (int): PK записи.

    Returns:
        Optional[AudioFile]: объект AudioFile или None.
    """
    with _Session() as s:
        return s.get(AudioFile, audio_file_id)


def add_audio_file_sync(user_id: int, filename: str, original_name: str, content_type: str,
                        size: int, whisper_model: str, storage_path: str, audio_duration_seconds: float) -> Optional[int]:
    """
    Создать новую запись AudioFile и вернуть её id.

    Args:
        user_id (int): id пользователя-владельца.
        filename (str): имя файла.
        original_name (str): оригинальное имя файла.
        content_type (str): MIME-type.
        size (int): размер файла в байтах.
        whisper_model (str): модель/папка.
        storage_path (str): относительный путь в storage.
        audio_duration_seconds (float): длительность в секундах.

    Returns:
        Optional[int]: id созданной записи или id существующей записи при конфликте.
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
    """
    Удалить запись AudioFile по имени и модели.

    Args:
        filename (str): имя файла.
        whisper_model (str): модель.

    Returns:
        bool: True если запись удалена, False если не найдена.
    """
    with _Session() as s:
        af = s.query(AudioFile).filter_by(filename=filename, whisper_model=whisper_model).first()
        if af:
            s.delete(af)
            s.commit()
            return True
        return False


def get_all_audio_files_sync() -> List[AudioFile]:
    """
    Получить все записи AudioFile.

    Returns:
        List[AudioFile]: список всех записей.
    """
    with _Session() as s:
        return s.query(AudioFile).all()


def update_audio_file_status_sync(audio_file_id: int, status):
    """
    Обновить поле status у записи AudioFile.

    Args:
        audio_file_id (int): id записи.
        status: новое значение статуса (enum/строка).

    Returns:
        bool: True если успешено, False если запись не найдена.
    """
    with _Session() as s:
        af = s.get(AudioFile, audio_file_id)
        if not af:
            return False
        af.status = status
        s.commit()
        return True
