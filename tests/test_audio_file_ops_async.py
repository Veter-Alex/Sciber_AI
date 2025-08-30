"""
Юнит-тесты асинхронных операций с AudioFile (async_impl).

Запускают in-memory aiosqlite движок и проверяют добавление/получение/удаление.
"""

import asyncio
import tempfile
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

import pytest


@pytest.mark.asyncio
async def test_async_add_get_delete(monkeypatch):
    # Setup an in-memory aiosqlite engine
    url = 'sqlite+aiosqlite:///:memory:'
    engine = create_async_engine(url, future=True)
    async with engine.begin() as conn:
        # import models and create tables (import dependent models so their tables are registered)
        from app.models.database import Base
        from app.models import user  # noqa: F401
        from app.models import audio_file  # noqa: F401
        from app.models import transcript  # noqa: F401
        from app.models import translation  # noqa: F401
        from app.models import summary  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)

    # Patch the async_impl AsyncSessionLocal to use the test engine
    from importlib import import_module
    impl = import_module('app.db.ops.async_impl')
    impl._engine = engine
    impl.AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Use the public async apis
    public = import_module('app.db.ops.async_impl')
    af_id = await public.add_audio_file(
        user_id=1,
        filename='a.mp3',
        original_name='a.mp3',
        content_type='audio/mpeg',
        size=10,
        whisper_model='base',
        storage_path='/tmp/a.mp3',
        audio_duration_seconds=1.1,
    )
    assert isinstance(af_id, int)

    af = await public.get_audio_file('a.mp3', 'base')
    assert af is not None

    deleted = await public.delete_audio_file('a.mp3', 'BASE')
    assert deleted is True
