"""
Модуль транскрипции — легковесный skeleton.

Контракт:
- process(audio_path: str, model: str = 'base', **opts) -> dict
  - возвращает: {"text": str, "segments": Optional[list], "duration": float}
  - может бросать TranscriptionError при ошибках

Реализация здесь минимальна и служит точкой расширения для реальной интеграции
(Whisper, сервисы ASR и т.п.).
"""
from typing import Optional, Dict


class TranscriptionError(Exception):
    """Ошибка транскрипции."""
    pass


def process(audio_path: str, model: str = "base", **opts) -> Dict:
    """Выполнить транскрипцию аудиофайла.

    Параметры:
        audio_path: путь к файлу на диске
        model: имя/версия модели (строка)
        opts: доп. параметры (chunking, timeout и т.п.)

    Возвращает словарь с ключами:
        text: полный транскрипт (str)
        segments: опциональный список сегментов/таймкодов
        duration: длительность в секундах (float)
    """
    # Заглушка: на проде здесь будет интеграция с моделью ASR
    try:
        # TODO: реальная логика транскрипции
        return {"text": "", "segments": [], "duration": 0.0}
    except Exception as e:
        raise TranscriptionError(str(e))
