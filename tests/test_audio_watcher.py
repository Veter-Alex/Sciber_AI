"""
Тесты watcher'а файловой системы.

Проверяют, что при создании/удалении файлов handler вызывает задачи enqueue_add_file
и enqueue_delete_file (имитируем их через DummyQueue).
"""

import importlib
from unittest.mock import MagicMock, patch
import os

from app.utils import audio_watcher


def test_watcher_enqueues(monkeypatch, tmp_path):
    # Create a watcher instance pointed at tmp_path
    calls = []

    class DummyQueue:
        def delay(self, *args, **kwargs):
            calls.append((args, kwargs))

    dummy_add = DummyQueue()
    dummy_delete = DummyQueue()

    # Patch the celery task functions imported by the watcher (they are imported inside handlers)
    import app.tasks.core as tasks_core
    monkeypatch.setattr(tasks_core, 'enqueue_add_file', dummy_add)
    monkeypatch.setattr(tasks_core, 'enqueue_delete_file', dummy_delete)

    # Ensure storage dir matches tmp_path so relpath stays on same drive
    from app.utils import settings as settings_mod
    settings_mod.settings.STORAGE_DIR = str(tmp_path)

    # Simulate created event by calling the handler directly
    handler = audio_watcher.AudioFileHandler()
    class Event:
        def __init__(self, path):
            self.src_path = path
            self.is_directory = False

    # create a fake path with model dir
    model_dir = tmp_path / 'base'
    model_dir.mkdir()
    path = model_dir / 'x.mp3'
    path.write_text('dummy')

    handler.on_created(Event(str(path)))
    assert len(calls) == 1

    handler.on_deleted(Event(str(path)))
    assert len(calls) == 2
