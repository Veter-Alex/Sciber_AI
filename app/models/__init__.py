"""
Пакет моделей приложения.

Здесь объявляются ORM-модели и служебные конструкции, используемые в
других частях приложения (app.db, маршруты, задачи).
"""

# Этот файл делает папку models Python-пакетом и импортирует все модули
# моделей в определённом порядке, чтобы SQLAlchemy успел зарегистрировать
# все классы до использования сессий/mapper'ов (предотвращает ошибки вида
# "expression 'Transcript' failed to locate a name").

# Импортируем перечисления и базу
from . import enums  # noqa: F401
from . import database  # noqa: F401

# Импортируем модели в безопасном порядке
from . import user  # noqa: F401
from . import audio_file  # noqa: F401
from . import transcript  # noqa: F401
from . import translation  # noqa: F401
from . import summary  # noqa: F401

# Экспортируем Base для внешних модулей
from .database import Base  # noqa: F401
