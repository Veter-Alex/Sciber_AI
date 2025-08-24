from app.models.audio_file import AudioFile
from app.models.database import AsyncSessionLocal
from sqlalchemy.future import select
from typing import Optional

import asyncio

async def get_audio_file(filename: str, whisper_model: str) -> Optional[AudioFile]:
    """
    Получить аудиофайл по имени и модели.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AudioFile).filter_by(filename=filename, whisper_model=whisper_model)
        )
        return result.scalars().first()


async def add_audio_file(**kwargs) -> AudioFile:
    """
    Добавить новый аудиофайл. kwargs должны содержать все необходимые поля.
    """
    async with AsyncSessionLocal() as session:
        audio_file = AudioFile(**kwargs)
        session.add(audio_file)
        await session.commit()
        return audio_file


async def delete_audio_file(filename: str, whisper_model: str) -> bool:
    """
    Удалить аудиофайл по имени и модели.
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
