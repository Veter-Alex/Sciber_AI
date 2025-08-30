"""
Модуль саммаризации — skeleton.

Контракт:
- process(text: str, **opts) -> dict
  - возвращает: {"summary": str, "highlights": Optional[list]}
  - может бросать SummaryError
"""
from typing import Dict, Optional


class SummaryError(Exception):
    """Ошибка суммаризации."""
    pass


def process(text: str, **opts) -> Dict:
    """Сделать краткое содержание текста.

    На входе — транскрипт или перевод. Возвращаем словарь с кратким summary.
    """
    try:
        # TODO: реальная логика суммаризации (ML/Prompt и т.п.)
        return {"summary": "", "highlights": []}
    except Exception as e:
        raise SummaryError(str(e))
