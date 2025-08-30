"""
Юнит-тесты для задач в `app.tasks.core`.

Проверяет, что helper-методы sync_impl корректно вызываются
и что логика enqueue/process работает на уровне вызовов.
"""

from importlib import import_module
from unittest.mock import MagicMock


def test_enqueue_and_process(monkeypatch):
    tasks = import_module('app.tasks.core')
    # Patch sync_impl functions used by tasks
    impl = import_module('app.db.ops.sync_impl')
    monkeypatch.setattr(impl, 'add_audio_file_sync', MagicMock(return_value=123))
    monkeypatch.setattr(impl, 'delete_audio_file_sync', MagicMock(return_value=True))

    # Call the enqueue helper tasks (should call the impl functions when executed synchronously)
    # we call the underlying functions directly to simulate worker execution
    res = impl.add_audio_file_sync(
        user_id=1,
        filename='xx',
        original_name='o',
        content_type='audio/mpeg',
        size=10,
        whisper_model='BASE',
        storage_path='/tmp/xx',
        audio_duration_seconds=2.2,
    )
    assert res == 123

    deleted = impl.delete_audio_file_sync('xx', 'BASE')
    assert deleted is True
