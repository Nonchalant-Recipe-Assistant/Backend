from fastapi import FastAPI
from app.database import Base, engine
from app.routers import users

# Создаём таблицы, если их нет
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Local Recipe Assistant API")

# Подключаем маршруты
app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "API is working locally!"}
