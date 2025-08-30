"""
Простой роутер healthcheck.

Назначение:
    - Предоставляет эндпоинт `/ping` для проверки доступности сервиса.

Пример:
    GET /ping -> {"message": "pong"}
"""

from fastapi import APIRouter

router = APIRouter()


@router.get('/ping')
def ping():
    """Возвращает простой ответ для проверки работоспособности сервиса."""
    return {"message": "pong"}
