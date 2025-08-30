"""
Асинхронная реализация операций с таблицей audio_files.

Этот модуль предоставляет неблокирующие (async) обёртки вокруг SQLAlchemy
для использования в FastAPI и других асинхронных контекстах.

Важно: для синхронных воркеров Celery используй соответствующий модуль
`app.db.ops.sync_impl` — там реализованы те же операции в синхронном виде.
"""

from typing import Optional, List, Any, cast
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import datetime

from app.models.audio_file import AudioFile
from app.utils.settings import settings


_engine = create_async_engine(settings.async_db_url, future=True)
# Use SQLAlchemy's async_sessionmaker which is the proper factory for AsyncSession
AsyncSessionLocal = async_sessionmaker(_engine, expire_on_commit=False)


async def get_audio_file(filename: str, whisper_model: str) -> Optional[AudioFile]:
    """Найти одну запись AudioFile по `filename` и `whisper_model`.

    Возвращает объект модели или None.
    """
    async with AsyncSessionLocal() as s:
        q = await s.execute(
            select(AudioFile).where(
                (AudioFile.filename == filename) & (AudioFile.whisper_model == whisper_model)
            )
        )
        af = q.scalars().first()
        return af


async def add_audio_file(user_id: int, filename: str, original_name: str, content_type: str,
                         size: int, whisper_model: str, storage_path: str, audio_duration_seconds: float) -> Optional[int]:
    """Добавить новую запись AudioFile и вернуть её id.

    Аргументы совпадают с полями модели. Устанавливает `upload_time` в текущее время
    и статус по умолчанию 'uploaded'.
    """
    async with AsyncSessionLocal() as s:
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
        await s.commit()
        await s.refresh(af)
        return af.id


async def delete_audio_file(filename: str, whisper_model: str) -> bool:
    """Удалить запись AudioFile по `filename` и `whisper_model`.

    Возвращает True, если запись была найдена и удалена, иначе False.
    """
    async with AsyncSessionLocal() as s:
        q = await s.execute(
            select(AudioFile).where(
                (AudioFile.filename == filename) & (AudioFile.whisper_model == whisper_model)
            )
        )
        af = q.scalars().first()
        if not af:
            return False
        await s.delete(af)
        await s.commit()
        return True


async def get_all_audio_files() -> List[AudioFile]:
    """Вернуть все записи AudioFile (список моделей)."""
    async with AsyncSessionLocal() as s:
        q = await s.execute(select(AudioFile))
        return list(q.scalars().all())


async def update_audio_file_status(audio_file_id: int, status):
    """Обновить статус записи по её id. Возвращает True/False по успеху."""
    async with AsyncSessionLocal() as s:
        af = await s.get(AudioFile, audio_file_id)
        if not af:
            return False
        af.status = status
        await s.commit()
        return True
