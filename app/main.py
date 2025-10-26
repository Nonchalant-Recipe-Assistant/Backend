from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import SessionLocal, engine
from app.routers import auth
from app import models
from app.crud import get_roles, create_role
from app.logger import setup_logging, get_logger  # Добавляем импорт

# Настройка логирования
setup_logging()
logger = get_logger(__name__)

# Создаём таблицы, если их нет
models.Base.metadata.create_all(bind=engine)

# Инициализируем роли при запуске
def init_roles():
    db = SessionLocal()
    try:
        existing_roles = get_roles(db)
        if not existing_roles:
            # Создаем базовые роли
            create_role(db, "user")
            create_role(db, "admin")
            create_role(db, "moderator")
            logger.info("✅ Initial roles created successfully")
        else:
            logger.info(f"✅ Roles already exist: {[r.name for r in existing_roles]}")
    except Exception as e:
        logger.error(f"❌ Error initializing roles: {e}")
    finally:
        db.close()

# Вызываем инициализацию ролей
init_roles()

app = FastAPI(title="Local Recipe Assistant API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://25.29.64.173:3000", "http://25.29.64.173:5173", "http://25.25.240.5:3000", "http://25.25.240.5:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем маршруты
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
def root():
    logger.debug("Root endpoint accessed")
    return {"message": "API is working locally!"}

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")