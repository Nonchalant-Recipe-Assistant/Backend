from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import SessionLocal, engine
from app.routers import auth, chat
from app import models
from app.crud.role import get_roles, create_role
from app.logger import setup_logging, get_logger
from app.websocket import endpoints as ws_endpoints
from app.utils import verify_token
import os
from fastapi import FastAPI, WebSocket  
import json

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
            create_role(db, "user")
            create_role(db, "admin")
            create_role(db, "moderator")
            print("✅ Initial roles created successfully")
        else:
            role_names = [role.name for role in existing_roles]
            print(f"✅ Roles already exist: {role_names}")
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

# Подключаем маршруты
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

@app.get("/")
def root():
    logger.debug("Root endpoint accessed")
    return {"message": "API is working locally!"}

@app.get("/debug/token")
def debug_token(token: str):
    """Temporary endpoint to debug token verification"""
    result = verify_token(token)
    return {
        "token": token,
        "verification_result": result,
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")

app.include_router(ws_endpoints.router)

@app.get("/debug/websocket-routes")
def debug_websocket_routes():
    """Check if WebSocket routes are registered"""
    routes = []
    for route in app.routes:
        route_info = {
            "path": getattr(route, "path", None),
            "name": getattr(route, "name", None),
            "methods": getattr(route, "methods", None),
            "type": type(route).__name__
        }
        routes.append(route_info)
    return {"routes": routes}

# Тестовый WebSocket endpoint - добавляется прямо в main.py
@app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    """Простой тестовый WebSocket без проверок"""
    logger.info("🎯 TEST WebSocket endpoint CALLED")
    
    try:
        # Принимаем соединение
        await websocket.accept()
        logger.info("✅ TEST WebSocket connection accepted")
        
        # Отправляем приветственное сообщение
        await websocket.send_text(json.dumps({
            "id": 1,
            "text": "Test connection successful! WebSocket is working.",
            "sender_email": "system",
            "sender_username": "System",
            "timestamp": "2024-01-01T00:00:00",
            "message_type": "system"
        }))
        
        logger.info("✅ TEST Welcome message sent")
        
        # Ждем сообщения от клиента
        while True:
            data = await websocket.receive_text()
            logger.info(f"📨 TEST Received: {data}")
            
            # Отправляем эхо-ответ
            response = {
                "id": 2,
                "text": f"Echo: {data}",
                "sender_email": "system", 
                "sender_username": "System",
                "timestamp": "2024-01-01T00:00:00",
                "message_type": "echo"
            }
            await websocket.send_text(json.dumps(response))
            logger.info("✅ TEST Echo response sent")
            
    except Exception as e:
        logger.error(f"💥 TEST WebSocket error: {e}")
        import traceback
        logger.error(f"💥 TEST Traceback: {traceback.format_exc()}")

@app.get("/debug/routes")
def debug_routes():
    routes = []
    for route in app.routes:
        route_info = {
            "path": getattr(route, "path", None),
            "name": getattr(route, "name", None),
            "methods": getattr(route, "methods", None),
        }
        if route_info["path"] and ("ws" in route_info["path"] or "chat" in route_info["path"]):
            routes.append(route_info)
    return {"routes": routes}