"""
Совместимый shim для устаревших импортов.

Этот модуль реэкспортирует асинхронные помощники из
`app.db.audio_file_ops_async`, чтобы существующие места в коде,
ссылающиеся на `app.db.audio_file_ops` продолжали работать без изменений.

Важно: фактическая реализация — асинхронная и находится в
`audio_file_ops_async.py`.
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
