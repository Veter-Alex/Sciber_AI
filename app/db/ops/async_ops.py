"""
Шим для асинхронных операций с audio_files.

Реэкспортирует функции из `app.db.audio_file_ops_async` — служит для
сохранения обратной совместимости публичного API.
"""

from app.db.audio_file_ops_async import (
    get_audio_file,
    add_audio_file,
    delete_audio_file,
    get_all_audio_files,
)

__all__ = [
    "get_audio_file",
    "add_audio_file",
    "delete_audio_file",
    "get_all_audio_files",
]
