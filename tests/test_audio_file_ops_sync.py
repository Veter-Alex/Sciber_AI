"""
Юнит-тесты синхронных операций с AudioFile (sync_impl).

Используют временную sqlite базу для проверки CRUD операций.
"""

import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest

from app.models.audio_file import AudioFile


def setup_temp_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    url = f'sqlite:///{path}'
    engine = create_engine(url, future=True)
    # create tables using models metadata
    # import dependent models so their tables/classes are registered
    from app.models import user  # noqa: F401
    from app.models import audio_file  # noqa: F401
    from app.models import transcript  # noqa: F401
    from app.models import translation  # noqa: F401
    from app.models import summary  # noqa: F401
    from app.models.database import Base
    Base.metadata.create_all(engine)
    return path, url, engine


def teardown_temp_db(path):
    try:
        os.unlink(path)
    except Exception:
        pass


def test_add_get_delete_audio_file_sync(monkeypatch):
    path, url, engine = setup_temp_db()
    try:
        # monkeypatch the sync DB engine in the module under test
        import importlib
        # module that provides the public API (canonical impl)
        public_mod = importlib.import_module('app.db.ops.sync_impl')
        # actual implementation module — patch this so internal _Session/_engine are used
        impl_mod = importlib.import_module('app.db.ops.sync_impl')

        # replace engine and session factory in the implementation module
        impl_mod._engine = engine
        impl_mod._Session = sessionmaker(bind=engine, expire_on_commit=False)

        # Add an audio file via the public re-export module
        af_id = public_mod.add_audio_file_sync(
            user_id=1,
            filename='test.mp3',
            original_name='test_original.mp3',
            content_type='audio/mpeg',
            size=12345,
            whisper_model='BASE',
            storage_path='/tmp/test.mp3',
            audio_duration_seconds=3.3,
        )
        assert isinstance(af_id, int)

        # Get by filename
        af = public_mod.get_audio_file_sync('test.mp3', 'BASE')
        assert af is not None
        assert af.filename == 'test.mp3'

        # Update status
        ok = public_mod.update_audio_file_status_sync(af_id, 'processing')
        assert ok
        af2 = public_mod.get_audio_file_by_id_sync(af_id)
        assert af2.status == 'processing'

        # Delete
        deleted = public_mod.delete_audio_file_sync('test.mp3', 'BASE')
        assert deleted is True
        af3 = public_mod.get_audio_file_sync('test.mp3', 'BASE')
        assert af3 is None

    finally:
        teardown_temp_db(path)
