"""
Асинхронные операции с таблицей AudioFile для использования внутри FastAPI.

Назначение:
    - Предоставить async-версии CRUD для AudioFile, используемые в HTTP-эндпоинтах.
    - Использует `AsyncSessionLocal` из `app.models.database`.

Основные функции:
    - get_audio_file(filename, whisper_model)
    - add_audio_file(**kwargs)
    - delete_audio_file(filename, whisper_model)
    - get_all_audio_files()

Зависимости:
    - sqlalchemy (async)
    - app.models.audio_file.AudioFile

Примечание:
    - Эти функции не должны использоваться в Celery workers — для них существуют sync-хелперы.
"""

from app.models.audio_file import AudioFile
from app.models.database import AsyncSessionLocal
from sqlalchemy.future import select
from typing import Optional, List, Sequence, cast


async def get_audio_file(filename: str, whisper_model: str) -> Optional[AudioFile]:
    """
    Получить аудиофайл по имени и модели.

    Args:
        filename (str): имя файла.
        whisper_model (str): модель/подпапка.

    Returns:
        Optional[AudioFile]: объект AudioFile или None.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AudioFile).filter_by(filename=filename, whisper_model=whisper_model)
        )
        return result.scalars().first()


async def add_audio_file(**kwargs) -> AudioFile:
    """
    Добавить новую запись AudioFile (асинхронно).

    Args:
        kwargs: поля AudioFile как именованные аргументы.

    Returns:
        AudioFile: созданный объект (с заполненным id).
    """
    async with AsyncSessionLocal() as session:
        audio_file = AudioFile(**kwargs)
        session.add(audio_file)
        await session.commit()
        return audio_file


async def delete_audio_file(filename: str, whisper_model: str) -> bool:
    """
    Удалить запись AudioFile по имени и модели (асинхронно).

    Args:
        filename (str): имя файла.
        whisper_model (str): модель/подпапка.

    Returns:
        bool: True если удалено, False если не найдено.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AudioFile).filter_by(filename=filename, whisper_model=whisper_model)
        )
        audio_file = result.scalars().first()
        if audio_file:
            await session.delete(audio_file)
            await session.commit()
            return True
        return False


async def get_all_audio_files() -> List[AudioFile]:
    """
    Получить все записи AudioFile (асинхронно).

    Returns:
        List[AudioFile]: список всех записей.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(AudioFile))
        # result.scalars().all() returns a Sequence[AudioFile]; mypy expects List
        return cast(List[AudioFile], list(result.scalars().all()))
