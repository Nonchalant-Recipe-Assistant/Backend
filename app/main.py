from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import SessionLocal, engine
from app.routers import auth  # Пока уберем users, если он вызывает ошибки
from app import models
from app.crud import get_roles, create_role  # Импортируем из папки crud
from app.schemas import RoleCreate

# Создаём таблицы, если их нет
models.Base.metadata.create_all(bind=engine)

# Инициализируем роли при запуске
def init_roles():
    db = SessionLocal()
    try:
        existing_roles = get_roles(db)
        if not existing_roles:
            roles_to_create = [
                RoleCreate(name="user"),
                RoleCreate(name="admin"),
                RoleCreate(name="moderator"),
            ]
            for role_data in roles_to_create:
                create_role(db, role_data)
            print("✅ Initial roles created successfully")
        else:
            print(f"✅ Roles already exist: {[r.role_name for r in existing_roles]}")
    except Exception as e:
        print(f"❌ Error initializing roles: {e}")
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

# Подключаем маршруты (пока только auth)
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
def root():
    return {"message": "API is working locally!"}