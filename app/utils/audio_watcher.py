import os
"""
Модуль наблюдателя файловой системы (watcher).

Назначение и принципы работы:
    - Наблюдает за директорией, указанной в `settings.STORAGE_DIR`, на предмет
        появления и удаления аудиофайлов (например, `storage/base/*.mp3`).
    - Не выполняет прямых мутаций в базе данных из процесса FastAPI/Watcher. Вместо этого
        он ставит задачи в Celery (enqueue_add_file / enqueue_delete_file). Это обеспечивае
        т централизацию всех изменений БД в worker'ах и избежание смешивания async/sync сессий.

Основные компоненты:
    - AudioFileHandler(FileSystemEventHandler): обрабатывает события create/delete и
        откладывает enqueue задач (с debounce для уменьшения дубликатов).
    - start_watching(): конфигурирует Observer или PollingObserver (на Windows/WSL
        PollingObserver рекомендован), стартует наблюдение и ставит первоначальную задачу
        full-sync в Celery через `sync_storage_with_db.delay()`.

Надёжность и мотивация:
    - В Docker/WSL/Windows filesystem events могут теряться; поэтому предусмотрен
        периодический full-sync, который сверяет содержимое `storage` с БД и исправляет
        рассинхронизацию.
    - Debounce в обработчике уменьшает вероятность мульти-вызывов enqueue при атомарных
        операциях копирования/обновления файлов (копирование через временный файл -> переименование).

Конфигурация через окружение:
    - WATCHER_USE_POLLING - включает PollingObserver (true/1/yes).
    - WATCHER_DEBOUNCE_SECONDS - интервал дебаунса в секундах (по умолчанию 1.5).
    - ENABLE_IN_PROCESS_WATCHER_SYNC - поддержка старого поведения периодического
        in-process sync (по безопасности отключена по умолчанию).

Примечание: все изменения БД выполняются воркером Celery; watcher только ставит задачи.
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
from typing import Dict, Tuple

# Глобальный lock для сериализации доступа к БД из watcher (периодический sync + обработчики событий)
sync_lock = threading.Lock()

# Debounce buffers: map (model, filename) -> Timer
# Purpose: prevent rapid duplicate enqueue_add_file calls for the same file
_debounce_timers: Dict[Tuple[str, str], threading.Timer] = {}
# Debounce interval in seconds
_DEBOUNCE_SECONDS = float(os.getenv('WATCHER_DEBOUNCE_SECONDS', '1.5'))


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
        # Use debounce to avoid multiple rapid enqueues for the same file
        key = (whisper_model, filename)

        def _enqueue():
            try:
                from app.tasks.core import enqueue_add_file
                enqueue_add_file.delay(filename, whisper_model, rel_path, os.path.getsize(filepath), filename, 1)
            except Exception as e:
                print(f"[Watcher] Failed to enqueue add task: {e}")
            finally:
                # remove timer reference
                try:
                    _debounce_timers.pop(key, None)
                except Exception:
                    pass

        # Cancel existing timer if present
        existing = _debounce_timers.get(key)
        if existing:
            try:
                existing.cancel()
            except Exception:
                pass

        t = threading.Timer(_DEBOUNCE_SECONDS, _enqueue)
        _debounce_timers[key] = t
        t.daemon = True
        t.start()


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
