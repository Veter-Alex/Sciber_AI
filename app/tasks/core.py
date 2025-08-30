import os
import psutil
from app.utils.settings import settings
from datetime import datetime
from celery import Celery
from app.models.audio_file import AudioFile
from app.models.enums import AudioFileStatus
from app.db.session import SessionLocal
import redis
import time

"""
Модуль Celery задач приложения.

Содержит задачи для обработки аудиофайлов, а также задачу периодической
синхронизации содержимого storage с БД. Код ориентирован на запуск в
контейнере Celery worker — задачи, выполняющие мутации БД, используют
синхронные helper'ы из `app.db.ops.sync_impl`.
"""

celery_app = Celery(
    'sciber_ai',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

# Configure a simple beat schedule to run the full storage->DB sync on interval set by env
try:
    _sync_interval = int(os.getenv("WATCHER_SYNC_INTERVAL_SECONDS", "30"))
except Exception:
    _sync_interval = 30

celery_app.conf.beat_schedule = {
    'sync_storage_with_db': {
        'task': 'app.tasks.core.sync_storage_with_db',
        'schedule': _sync_interval,
    }
}
celery_app.conf.timezone = os.getenv('TZ', 'UTC')

# Redis client for lightweight coordination if needed
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, db=0)

@celery_app.task
def process_audio_file(audio_file_id):
    """
    Задача Celery: обработка одного аудиофайла по его id.

    Логика:
        - Проверяет наличие свободной оперативной памяти и при необходимости делает retry.
        - Помечает запись в БД как PROCESSING (через синхронный helper) перед началом работы.
        - Выполняет обработку (здесь место для реальной работы: транскрибция/транслейшн/и т.п.).
        - По завершении помечает запись как DONE.

    Важно: все изменения в БД делаются через синхронные helper'ы из
    `app.db.ops.sync_impl`, чтобы не смешивать async и sync сессии.
    """
    from app.models.audio_file import AudioFile
    from app.models.enums import AudioFileStatus
    from app.db.session import SessionLocal
    min_free_ram_mb = int(os.getenv("MIN_FREE_RAM_MB", "1024"))
    free_ram_mb = psutil.virtual_memory().available // (1024 * 1024)
    if free_ram_mb < min_free_ram_mb:
        raise process_audio_file.retry(countdown=30)
    from app.db.ops.sync_impl import get_audio_file_by_id_sync, update_audio_file_status_sync
    audio_file = get_audio_file_by_id_sync(audio_file_id)
    if not audio_file:
        return f"AudioFile {audio_file_id} not found"
    # Меняем статус на PROCESSING только при реальном старте обработки
    update_audio_file_status_sync(audio_file_id, AudioFileStatus.PROCESSING)
    # TODO: добавить реальную обработку файла
    print(f"Started processing: {audio_file.filename}")
    # ... обработка файла ...
    # После успешной обработки: обновим статус через sync-хелпер
    update_audio_file_status_sync(audio_file_id, AudioFileStatus.DONE)
    return audio_file.filename


@celery_app.task
def enqueue_add_file(filename, whisper_model, storage_path, size, original_name, user_id=1):
    """
    Синхронно добавить запись в БД (в Celery worker) и поставить задачу обработки.
    """
    from app.models.audio_file import AudioFile
    from app.models.enums import AudioFileStatus
    from app.db.session import SessionLocal

    from app.db.ops.sync_impl import add_audio_file_sync, get_audio_file_sync
    exists = get_audio_file_sync(filename, whisper_model)
    if exists:
        return exists.id
    new_id = add_audio_file_sync(
        user_id=user_id,
        filename=filename,
        original_name=original_name,
        content_type="audio/unknown",
        size=size,
        whisper_model=whisper_model,
        storage_path=storage_path,
        audio_duration_seconds=0.0,
    )
    if new_id:
        process_audio_file.delay(new_id)
    return new_id


@celery_app.task
def enqueue_delete_file(filename, whisper_model):
    """
    Синхронно удалить запись аудиофайла (и каскадно связанные сущности).
    """
    from app.models.audio_file import AudioFile
    from app.db.session import SessionLocal

    from app.db.ops.sync_impl import delete_audio_file_sync
    return delete_audio_file_sync(filename, whisper_model)


# Full sync task for Celery beat: scans storage and enqueues per-file add/delete tasks
@celery_app.task
def sync_storage_with_db():
    storage_dir = os.getenv('STORAGE_DIR', '/app/storage')
    from pathlib import Path
    from app.tasks.core import enqueue_add_file, enqueue_delete_file
    from app.db.ops.sync_impl import get_all_audio_files_sync, get_audio_file_sync
    from app.models.enums import WhisperModel
    storage_path = Path(storage_dir)
    if not storage_path.exists():
        print(f"[beat] storage_dir {storage_dir} does not exist, skipping sync")
        return

    disk_files = []
    for model_dir in storage_path.iterdir():
        if not model_dir.is_dir():
            continue
        # Skip directories that are not valid whisper model names to avoid
        # passing invalid enum values into DB queries (causes DataError)
        model_name = model_dir.name
        if model_name not in [m.value for m in WhisperModel]:
            print(f"[beat] skipping unknown model directory: {model_name}")
            continue
        for f in model_dir.iterdir():
            if f.is_file() and f.suffix.lower() in ('.mp3', '.wav'):
                disk_files.append((f.name, model_dir.name, str(f)))

    # Enqueue add tasks for files missing in DB
    for filename, model_name, abs_path in disk_files:
        exists = get_audio_file_sync(filename, model_name)
        if not exists:
            try:
                enqueue_add_file.delay(filename, model_name, os.path.relpath(abs_path, storage_dir), Path(abs_path).stat().st_size, filename, 1)
            except Exception as e:
                print(f"[beat] Failed to enqueue add for {filename}: {e}")

    # Enqueue delete tasks for DB entries without files on disk
    db_files = get_all_audio_files_sync()
    for af in db_files:
        expected_path = storage_path / af.whisper_model.value / af.filename
        if not expected_path.exists():
            try:
                enqueue_delete_file.delay(af.filename, af.whisper_model.value)
            except Exception as e:
                print(f"[beat] Failed to enqueue delete for {af.filename}: {e}")

