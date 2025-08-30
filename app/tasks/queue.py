"""
Модуль очереди задач Celery — точка экспорта задач для остального приложения.

Этот файл не содержит логики сам по себе, но предоставляет удобные имена для
импорта в тестах и в коде, чтобы не ссылаться напрямую на `app.tasks.core`.
"""

from .core import enqueue_add_file, enqueue_delete_file, process_audio_file, sync_storage_with_db

__all__ = [
	"enqueue_add_file",
	"enqueue_delete_file",
	"process_audio_file",
	"sync_storage_with_db",
]
