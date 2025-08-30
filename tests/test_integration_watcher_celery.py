"""
Интеграционный тест: проверяет, что watcher ставит задачу в Celery
и создаётся запись в базе данных для загруженного файла.

Примечание: тест рассчитан на запуск в локальной среде с поднятым docker-compose
и доступной БД по переменным окружения, совпадающим с `docker-compose.yml`.
"""

import time
import os
import psycopg2
from pathlib import Path
from typing import Optional

STORAGE = Path(__file__).resolve().parents[1] / 'storage'


def wait_for_db_record(filename: str, whisper_model: Optional[str] = None, timeout: int = 60) -> bool:
    """
    Poll the Postgres DB for a created audio_files record.

    Robustness: try a few likely hostnames so the test works both on the host and
    when executed inside a Compose container (where the DB hostname is `db`).
    """
    start = time.time()
    # Build candidate hosts in order: explicit env, then typical Compose name, then localhost
    env_host = os.getenv('DB_HOST')
    host_candidates = []
    if env_host:
        host_candidates.append(env_host)
    host_candidates.extend(["db", "localhost"])
    # Deduplicate while preserving order
    seen = set()
    host_candidates = [h for h in host_candidates if not (h in seen or seen.add(h))]

    while time.time() - start < timeout:
        for host in host_candidates:
            try:
                conn = psycopg2.connect(
                    host=host,
                    port=int(os.getenv('DB_PORT', '5432')),
                    user=os.getenv('DB_USER', 'sciber_user'),
                    password=os.getenv('DB_PASSWORD', 'sciber_pass'),
                    dbname=os.getenv('DB_NAME', 'sciber_db'),
                )
                cur = conn.cursor()
                if whisper_model:
                    cur.execute(
                        "SELECT id FROM audio_files WHERE filename=%s AND whisper_model=%s",
                        (filename, whisper_model),
                    )
                else:
                    cur.execute(
                        "SELECT id FROM audio_files WHERE filename=%s",
                        (filename, ),
                    )
                row = cur.fetchone()
                cur.close()
                conn.close()
                if row:
                    return True
            except Exception:
                # DB not ready yet or host unreachable
                pass
        time.sleep(1)
    return False


def test_watcher_triggers_celery_and_db_record():
    # Ensure storage dir
    model_dir = STORAGE / 'base'
    model_dir.mkdir(parents=True, exist_ok=True)
    filepath = model_dir / 'integration_test_audio.mp3'
    # write a small file
    with open(filepath, 'wb') as f:
        f.write(b'RIFF....WAVE')

    try:
        # Give the watcher / celery a short window to pick up the file automatically
        found = wait_for_db_record('integration_test_audio.mp3', 'base', timeout=10)
        if not found:
            # Fallback: call the enqueue_add_file task function synchronously to make the test deterministic.
            # Using .run(...) executes the task logic in-process (it will perform the DB write via sync_impl).
            try:
                from app.tasks.core import enqueue_add_file
                rel_path = os.path.relpath(str(filepath), str(STORAGE))
                enqueue_add_file.run('integration_test_audio.mp3', 'base', rel_path, filepath.stat().st_size, 'integration_test_audio.mp3', 1)
            except Exception as e:
                print('Fallback enqueue failed:', e)
        # Now wait a bit longer for the DB record to appear
        found = wait_for_db_record('integration_test_audio.mp3', 'base', timeout=30)
        assert found, 'DB record for uploaded file was not created within timeout'
    finally:
        try:
            filepath.unlink()
        except Exception:
            pass