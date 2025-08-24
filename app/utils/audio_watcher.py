import asyncio
async def sync_storage_with_db():
    """
    Синхронизирует STORAGE_DIR и записи в БД:
    - Добавляет записи для новых файлов
    - Удаляет записи для отсутствующих файлов
    """
    storage_dir = settings.STORAGE_DIR
    # 1. Собираем все файлы из STORAGE_DIR
    all_files = []
    for model_name in os.listdir(storage_dir):
        model_path = os.path.join(storage_dir, model_name)
        if not os.path.isdir(model_path):
            continue
        for filename in os.listdir(model_path):
            file_path = os.path.join(model_path, filename)
            if os.path.isfile(file_path) and filename.lower().endswith(('.mp3', '.wav')):
                all_files.append((filename, model_name, file_path))

    # 2. Добавляем отсутствующие записи в БД
    for filename, model_name, file_path in all_files:
        exists = await get_audio_file(filename, model_name)
        if not exists:
            await add_audio_file(
                user_id=1,  # TODO: определить пользователя
                filename=filename,
                original_name=filename,
                content_type="audio/unknown",
                size=os.path.getsize(file_path),
                upload_time=datetime.now(),
                whisper_model=model_name,
                status="uploaded",
                storage_path=os.path.relpath(file_path, storage_dir),
                audio_duration_seconds=0.0  # TODO: вычислить длительность
            )

    # 3. Удаляем записи, для которых нет файла
    # Получаем все записи из БД
    from app.models.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        from sqlalchemy.future import select
        result = await session.execute(select(AudioFile))
        db_files = result.scalars().all()
        for audio_file in db_files:
            abs_path = os.path.join(storage_dir, audio_file.whisper_model.value, audio_file.filename)
            if not os.path.isfile(abs_path):
                await delete_audio_file(audio_file.filename, audio_file.whisper_model.value)

import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.utils.settings import settings
from app.models.enums import WhisperModel
from app.models.database import Base
from app.models.audio_file import AudioFile
from app.db.audio_file_ops import get_audio_file, add_audio_file, delete_audio_file
import time
from datetime import datetime


class AudioFileHandler(FileSystemEventHandler):
    def on_deleted(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
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
        # Удаляем файл из базы данных
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(delete_audio_file(filename, whisper_model))

    def on_created(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        # Проверяем, что это аудиофайл по расширению
        if not filepath.lower().endswith(('.mp3', '.wav')):
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
        # Добавляем файл в базу данных через функцию
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        async def process_audio():
            exists = await get_audio_file(filename, whisper_model)
            if exists:
                return
            await add_audio_file(
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
        loop.run_until_complete(process_audio())


def start_watching():
    storage_dir = settings.STORAGE_DIR
    # Синхронизация файлов и БД при запуске
    asyncio.run(sync_storage_with_db())
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
