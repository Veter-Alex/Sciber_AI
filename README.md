# Sciber_AI Backend

Backend API built with FastAPI.

## Запуск

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Запустите сервер:
   ```bash
   uvicorn main:app --reload
   ```

## Эндпоинты

- `GET /ping` — проверка работоспособности API.

## Development / Tests

1. Создайте виртуальное окружение и установите dev-зависимости:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

1. Запустите тесты:

```powershell
.\.venv\Scripts\pytest -q
```

1. Запустите mypy статическую проверку:

```powershell
.\.venv\Scripts\python.exe -m mypy -p app
```

