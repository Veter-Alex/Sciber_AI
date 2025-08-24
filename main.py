from app.models.user import User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import hashlib
import threading
from app.utils.audio_watcher import start_watching

from fastapi import FastAPI
from app.routes.ping import router as ping_router
import os
from app.utils.settings import settings
from app.models.enums import WhisperModel

app = FastAPI()

# Создание структуры папок для моделей FastWhisper при старте приложения
def create_storage_structure():
	storage_dir = os.getenv("STORAGE_DIR", "storage")
	os.makedirs(storage_dir, exist_ok=True)
	for model in WhisperModel:
		model_dir = os.path.join(storage_dir, model.value)
		os.makedirs(model_dir, exist_ok=True)
    
create_storage_structure()

# Запуск отслеживания новых аудиофайлов в отдельном потоке
watcher_thread = threading.Thread(target=start_watching, daemon=True)
watcher_thread.start()

# Автоматическое добавление пользователя admin при запуске
def create_admin_user():
	engine = create_engine(settings.sync_db_url)
	SessionLocal = sessionmaker(bind=engine)
	with SessionLocal() as session:
		admin = session.query(User).filter_by(name="admin").first()
		if not admin:
			# Простой хэш пароля admin
			hashed_password = hashlib.sha256("admin".encode()).hexdigest()
			admin = User(
				id=1,
				name="admin",
				hashed_password=hashed_password,
				is_active=True,
				is_admin=True
			)
			session.add(admin)
			session.commit()

create_admin_user()

app.include_router(ping_router)
