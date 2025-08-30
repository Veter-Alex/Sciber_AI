# (removed async in-process sync helper — in-process sync now uses Celery task)

import os
""" 
Модуль наблюдателя файловой системы. 
 
Назначение: 
    - Слушает директорию `settings.STORAGE_DIR` на предмет появления и удаления аудиофайлов. 
    - Не выполняет прямых записей в БД; вместо этого ставит задачи в Celery (enqueue_add_file / enqueue_delete_file). 
 
Основные классы/функции: 
    - class AudioFileHandler(FileSystemEventHandler): обрабатывает события create/delete и ставит задачи в Celery. 
    - start_watching(): стартует Observer/PollingObserver и при необходимости периодически ставит full-sync задачу. 
 
Зависимости: 
    - watchdog (Observer, PollingObserver, FileSystemEventHandler) 
    - app.utils.settings.settings 
    - app.models.enums.WhisperModel 
    - app.tasks.core.enqueue_add_file / enqueue_delete_file / sync_storage_with_db 
 
Примечания: 
    - По соображениям безопасности и консистентности БД все мутации делаются в Celery worker'е. 
    - В Docker/WSL файловые события иногда теряются; для этого предусмотрен PollingObserver и периодический full-sync. 
""" 

from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from app.utils.settings import settings
from app.models.enums import WhisperModel
from app.models.database import Base
from app.models.audio_file import AudioFile
# async DB helpers intentionally not imported here — DB mutations are handled by Celery workers
import time
from datetime import datetime
import threading

# Глобальный lock для сериализации доступа к БД из watcher (периодический sync + обработчики событий)
sync_lock = threading.Lock()


class AudioFileHandler(FileSystemEventHandler):
    def on_deleted(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        print(f"[Watcher] on_deleted event: {filepath}")
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
        # Удаляем файл: ставим задачу в Celery, воркер выполнит удаление синхронно
        try:
            from app.tasks.core import enqueue_delete_file
            enqueue_delete_file.delay(filename, whisper_model)
        except Exception as e:
            print(f"[Watcher] Failed to enqueue delete task: {e}")

    def on_created(self, event):
        if event.is_directory:
            return
        print(f"[Watcher] on_created event: {event.src_path}")
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
        # Добавляем файл: ставим задачу в Celery, воркер выполнит вставку и поставит задачу обработки
        try:
            from app.tasks.core import enqueue_add_file
            enqueue_add_file.delay(filename, whisper_model, rel_path, os.path.getsize(filepath), filename, 1)
        except Exception as e:
            print(f"[Watcher] Failed to enqueue add task: {e}")


def start_watching():
    storage_dir = settings.STORAGE_DIR
    # Синхронизация файлов и БД при запуске
    # Используем модульный sync_lock, чтобы не запускать несколько sync одновременно (asyncpg InterfaceError)
    try:
        # Enqueue initial full sync as a Celery task so FastAPI process does not perform DB writes
        from app.tasks.core import sync_storage_with_db as sync_task
        sync_task.delay()
        print("[Watcher] Enqueued initial full sync task to Celery")
    except Exception as e:
        print(f"[Watcher] Failed to enqueue initial sync task: {e}")
    event_handler = AudioFileHandler()
    # Allow switching to PollingObserver when filesystem events are unreliable (Docker on Windows/WSL)
    use_polling = os.getenv("WATCHER_USE_POLLING", "false").lower() in ("1", "true", "yes")
    observer = PollingObserver() if use_polling else Observer()
    print(f"[Watcher] Using {'PollingObserver' if use_polling else 'Observer'}")
    observer.schedule(event_handler, storage_dir, recursive=True)
    observer.start()
    print(f"[Watcher] Monitoring {storage_dir} for new audio files...")

    # Периодическая синхронизация на случай, если watchdog не получает события
    # Periodic in-process sync is disabled by default to ensure FastAPI process does not
    # perform DB mutations. Use ENABLE_IN_PROCESS_WATCHER_SYNC=true to enable temporarily.
    enable_in_process_sync = os.getenv("ENABLE_IN_PROCESS_WATCHER_SYNC", "false").lower() in ("1", "true", "yes")
    if not enable_in_process_sync:
        print("[Watcher] In-process periodic sync is disabled (use ENABLE_IN_PROCESS_WATCHER_SYNC=true to enable)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    # If enabled, retain the previous periodic sync behavior (kept for backward compatibility)
    try:
        sync_interval = int(os.getenv("WATCHER_SYNC_INTERVAL_SECONDS", "30"))
    except Exception:
        sync_interval = 30

    last_sync = time.time()
    try:
        while True:
            time.sleep(1)
            # По таймеру вызываем полную синхронизацию — ставим задачу в Celery
            if time.time() - last_sync >= sync_interval:
                # Попытка получить lock без блокировки — если предыдущий enqueue ещё выполняется, пропускаем запуск
                if not sync_lock.acquire(blocking=False):
                    print("[Watcher] Previous sync still running, skipping this periodic sync")
                    last_sync = time.time()
                    continue
                try:
                    print(f"[Watcher] Enqueuing periodic full sync task to Celery (every {sync_interval}s)")
                    from app.tasks.core import sync_storage_with_db as sync_task
                    try:
                        sync_task.delay()
                    except Exception as e:
                        print(f"[Watcher] Failed to enqueue periodic sync task: {e}")
                finally:
                    try:
                        sync_lock.release()
                    except RuntimeError:
                        pass
                last_sync = time.time()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
