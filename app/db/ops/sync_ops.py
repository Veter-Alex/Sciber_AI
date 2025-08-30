"""
Шим для синхронных (blocking) операций с audio_files.

Реэкспортирует синхронные helper'ы из `app.db.audio_file_ops_sync` для
использования внутри Celery worker'ов и других блокирующих контекстов.
"""

from app.db.audio_file_ops_sync import (
    add_audio_file_sync,
    get_audio_file_sync,
    get_audio_file_by_id_sync,
    delete_audio_file_sync,
    get_all_audio_files_sync,
    update_audio_file_status_sync,
)

__all__ = [
    "add_audio_file_sync",
    "get_audio_file_sync",
    "get_audio_file_by_id_sync",
    "delete_audio_file_sync",
    "get_all_audio_files_sync",
    "update_audio_file_status_sync",
]
