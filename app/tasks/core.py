import os
import psutil
from app.utils.settings import settings
from celery import Celery
from app.models.audio_file import AudioFile
from app.models.enums import AudioFileStatus
from app.db.session import SessionLocal

celery_app = Celery(
    'sciber_ai',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

@celery_app.task
def process_audio_file(audio_file_id):
    """
    Задача Celery: обработка одного аудиофайла по id.
    """
    from app.models.audio_file import AudioFile
    from app.models.enums import AudioFileStatus
    from app.db.session import SessionLocal
    min_free_ram_mb = int(os.getenv("MIN_FREE_RAM_MB", "1024"))
    free_ram_mb = psutil.virtual_memory().available // (1024 * 1024)
    if free_ram_mb < min_free_ram_mb:
        raise process_audio_file.retry(countdown=30)
    with SessionLocal() as session:
        audio_file = session.query(AudioFile).get(audio_file_id)
        if not audio_file:
            return f"AudioFile {audio_file_id} not found"
        # Меняем статус на PROCESSING только при реальном старте обработки
        audio_file.status = AudioFileStatus.PROCESSING
        session.commit()
        # TODO: добавить реальную обработку файла
        print(f"Started processing: {audio_file.filename}")
        # ... обработка файла ...
        # После успешной обработки:
        audio_file.status = AudioFileStatus.DONE
        session.commit()
        return audio_file.filename

