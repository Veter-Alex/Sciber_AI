
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
