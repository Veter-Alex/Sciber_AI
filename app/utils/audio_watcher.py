import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.utils.settings import settings
from app.models.enums import WhisperModel
from app.models.database import Base
from app.models.audio_file import AudioFile
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import time
from datetime import datetime

# Синхронный движок для работы с БД
engine = create_engine(settings.sync_db_url)
SessionLocal = sessionmaker(bind=engine)

class AudioFileHandler(FileSystemEventHandler):
    def on_deleted(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        filename = os.path.basename(filepath)
        with SessionLocal() as session:
            audio_file = session.query(AudioFile).filter_by(filename=filename).first()
            if audio_file:
                session.delete(audio_file)
                session.commit()
    def on_created(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        # Проверяем, что это аудиофайл по расширению
        if not filepath.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.m4a')):
            return
        filename = os.path.basename(filepath)
        # Извлекаем имя модели из пути
        rel_path = os.path.relpath(filepath, settings.STORAGE_DIR)
        parts = rel_path.split(os.sep)
        if len(parts) < 2:
            return
        whisper_model = parts[0]
        # Проверяем, что модель допустима
        if whisper_model not in [m.value for m in WhisperModel]:
            return
        # Добавляем файл в базу данных
        with SessionLocal() as session:
            exists = session.query(AudioFile).filter_by(filename=filename).first()
            if exists:
                return
            audio_file = AudioFile(
                user_id=1,  # TODO: определить пользователя
                filename=filename,
                original_name=filename,
                content_type="audio/unknown",
                size=os.path.getsize(filepath),
                upload_time=datetime.now(),
                whisper_model=whisper_model,
                status="uploaded",
                storage_path=rel_path,
                audio_duration_seconds=0.0  # TODO: вычислить длительность
            )
            session.add(audio_file)
            session.commit()


def start_watching():
    storage_dir = settings.STORAGE_DIR
    event_handler = AudioFileHandler()
    observer = Observer()
    observer.schedule(event_handler, storage_dir, recursive=True)
    observer.start()
    print(f"[Watcher] Monitoring {storage_dir} for new audio files...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
