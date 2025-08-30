"""
Утилита для проверки записей в БД со статусом UPLOADED и наличия соответствующих файлов на диске.

Назначение:
    - Подключается к локальной БД и выбирает записи `audio_files` со статусом UPLOADED.
    - Формирует список кандидатных путей для каждого файла и проверяет, существуют ли они на диске.
    - Выводит JSON с результатами для удобного анализа.

Использование:
    - Локально (Windows PowerShell): python .\scripts\check_uploaded_files.py

Примечание:
    - Скрипт пытается определить storage_dir из `app.utils.settings` и из переменных окружения.
    - Скрипт не изменяет БД — только читает и проводит проверку файловой системы.
"""

import os
import json
import sys
from typing import List, Dict, Optional

try:
    import psycopg2
except Exception as e:
    print(json.dumps({"error": "psycopg2 is required to run this script", "details": str(e)}, ensure_ascii=False))
    sys.exit(1)

# Конфигурация через переменные окружения (совпадает с docker-compose по умолчанию)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_USER = os.getenv('DB_USER', 'sciber_user')
DB_PASS = os.getenv('DB_PASSWORD', 'sciber_pass')
DB_NAME = os.getenv('DB_NAME', 'sciber_db')
# Если STORAGE_DIR задан как относительный путь, он интерпретируется относительно корня репозитория
STORAGE_DIR_ENV = os.getenv('STORAGE_DIR', 'storage')


def _candidates_for_record(storage_root: str, filename: str, whisper_model: Optional[str], storage_path: Optional[str]) -> List[str]:
    """
    Собрать список кандидатов абсолютных путей для данной записи из БД.

    Порядок от самого специфичного к самому общему.
    """
    candidates: List[str] = []

    # Если в БД сохранён конкретный storage_path — используем его первым
    if storage_path:
        candidates.append(os.path.abspath(os.path.join(storage_root, storage_path)))

    # Если указана модель (подпапка) — пробуем несколько вариантов регистра
    if whisper_model:
        wm = whisper_model
        candidates.append(os.path.abspath(os.path.join(storage_root, wm.lower(), filename)))
        candidates.append(os.path.abspath(os.path.join(storage_root, wm.upper(), filename)))
        candidates.append(os.path.abspath(os.path.join(storage_root, wm, filename)))

    # Общие места: файл в корне storage
    candidates.append(os.path.abspath(os.path.join(storage_root, filename)))

    return candidates


def discover_storage_root() -> str:
    """Попытаться определить корень папки storage в репозитории.

    Логика:
        1. Если указано абсолютное значение в ENV STORAGE_DIR, используем его.
        2. Иначе считаем STORAGE_DIR относительным к корню репозитория (одна ступень выше scripts/).
    """
    # Путь к корню проекта (один уровень выше папки scripts)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # ENV может содержать либо абсолютный путь, либо относительный
    env_val = STORAGE_DIR_ENV
    if os.path.isabs(env_val):
        return env_val
    return os.path.abspath(os.path.join(repo_root, env_val))


def query_uploaded_rows(limit: int = 500) -> List[Dict]:
    """Запросить из БД последние строки со статусом UPLOADED.

    Возвращаем список словарей с полями: id, filename, whisper_model, storage_path, status
    """
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id, filename, whisper_model, storage_path, status FROM audio_files WHERE status='UPLOADED' ORDER BY id DESC LIMIT %s", (limit,))
        rows = cur.fetchall()
        result = []
        for r in rows:
            id_, filename, whisper_model, storage_path, status = r
            result.append({
                'id': id_,
                'filename': filename,
                'whisper_model': whisper_model,
                'storage_path': storage_path,
                'status': status,
            })
        return result
    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def build_report(rows: List[Dict], storage_root: str) -> List[Dict]:
    """Сформировать итоговый список с кандидатами и существующими путями на диске."""
    out: List[Dict] = []
    for row in rows:
        id_ = row.get('id')
        filename = row.get('filename') or ""
        whisper_model = row.get('whisper_model')
        storage_path = row.get('storage_path')

        candidates = _candidates_for_record(storage_root, filename, whisper_model, storage_path)
        existing = [p for p in candidates if os.path.exists(p)]

        out.append({
            'id': id_,
            'filename': filename,
            'whisper_model': whisper_model,
            'storage_path': storage_path,
            'candidates': candidates,
            'existing_paths': existing,
            'exists_on_disk': bool(existing),
        })
    return out


def main() -> None:
    rows = query_uploaded_rows(limit=500)
    storage_root = discover_storage_root()
    report = build_report(rows, storage_root)
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
