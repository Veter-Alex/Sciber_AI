from celery import Celery
from app.models.audio_file import AudioFile
from app.models.enums import AudioFileStatus
from app.utils.audio_watcher import SessionLocal

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
    from app.utils.audio_watcher import SessionLocal
    with SessionLocal() as session:
        audio_file = session.query(AudioFile).get(audio_file_id)
        if not audio_file:
            return f"AudioFile {audio_file_id} not found"
        # Пример: меняем статус на PROCESSING
        audio_file.status = AudioFileStatus.PROCESSING
        session.commit()
        # TODO: добавить реальную обработку файла
        print(f"Started processing: {audio_file.filename}")
        return audio_file.filename

