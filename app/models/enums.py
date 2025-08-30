
"""
Модуль перечислений (Enum), используемых в моделях.

Назначение:
    - Содержит наборы возможных значений для полей статусов и выбора модели Whisper.

Основные перечисления:
    - AudioFileStatus, TranscriptStatus, TranslationStatus, SummaryStatus, WhisperModel

Примечание:
    - Значения строковые и используются как в базе данных (SQLEnum), так и в коде приложения.
"""

from enum import Enum
from sqlalchemy import Enum as SQLEnum

class AudioFileStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class TranscriptStatus(str, Enum):
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class TranslationStatus(str, Enum):
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class SummaryStatus(str, Enum):
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class WhisperModel(str, Enum):
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
