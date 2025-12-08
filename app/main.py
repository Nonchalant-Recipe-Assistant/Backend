from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.database import SessionLocal, engine
from app.routers import auth, chat, verification, search
from app import models
from app.crud.role import get_roles, create_role
from app.logger import setup_logging, get_logger
from app.websocket import endpoints as ws_endpoints
from app.utils import verify_token
from datetime import datetime
from app.migrations import migrate_database
from app.config import settings
import os
import json
import time
import random


# Настройка логирования
setup_logging()
logger = get_logger(__name__)

# Создаём таблицы, если их нет
models.Base.metadata.create_all(bind=engine)

# Выполняем миграцию базы данных
try:
    migrate_database()
    logger.info("✅ Database migration completed")
except Exception as e:
    logger.error(f"❌ Database migration failed: {e}")

# Инициализируем роли при запуске
def init_roles():
    db = SessionLocal()
    try:
        existing_roles = get_roles(db)
        if not existing_roles:
            create_role(db, "user")
            create_role(db, "admin")
            create_role(db, "moderator")
            logger.info("✅ Initial roles created successfully")
        else:
            role_names = [role.name for role in existing_roles]
            logger.info(f"✅ Roles already exist: {role_names}")
    except Exception as e:
        logger.error(f"❌ Error initializing roles: {e}")
    finally:
        db.close()

# Вызываем инициализацию ролей
init_roles()

app = FastAPI(title="Recipe Assistant API")

# CORS middleware - разрешаем всё для разработки
env_origins = os.getenv("BACKEND_CORS_ORIGINS")
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://25.29.64.173:3000",
    "http://25.29.64.173:5173",
    "http://25.25.240.5:3000",
    "http://25.25.240.5:5173"
]

# Если переменная из Docker есть, добавляем её значения в список
if env_origins:
    try:
        # Парсим JSON строку из docker-compose
        docker_origins = json.loads(env_origins)
        origins.extend(docker_origins)
    except json.JSONDecodeError:
        logger.error("Could not parse BACKEND_CORS_ORIGINS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем маршруты API
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(verification.router, prefix="/auth", tags=["auth"])  
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(ws_endpoints.router, prefix="/api/chat", tags=["chat"])
# ВАЖНО: Подключаем роутер поиска
app.include_router(search.router, prefix="/search", tags=["search"])


# Health check endpoint
@app.get("/")
def root():
    return {"message": "Recipe Assistant API is running", "status": "healthy"}

# Debug endpoints
@app.get("/debug/token")
def debug_token(token: str):
    result = verify_token(token)
    return {
        "token": token,
        "verification_result": result,
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

@app.get("/debug/routes")
def debug_routes():
    routes = []
    for route in app.routes:
        route_info = {
            "path": getattr(route, "path", None),
            "name": getattr(route, "name", None),
            "methods": getattr(route, "methods", None),
        }
        routes.append(route_info)
    return {"routes": routes}

# Email debug endpoints
@app.get("/debug/email")
async def debug_email():
    """Endpoint для отладки email настроек"""
    from app.email_debug import debug_email_config  # Импортируем внутри функции
    config_ok = debug_email_config()
    return {
        "email_config_ok": config_ok,
        "resend_api_key_set": bool(settings.RESEND_API_KEY),
        "from_email": settings.FROM_EMAIL,
        "base_url": settings.BASE_URL,
        "environment": settings.ENVIRONMENT
    }

@app.post("/debug/send-test-email")
async def send_test_email_endpoint(email: str):
    """Отправляет тестовое email"""
    from app.email_debug import send_test_email
    success = await send_test_email(email)
    return {
        "success": success,
        "message": "Test email sent" if success else "Failed to send test email"
    }

# WebSocket endpoints
@app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    """Простой тестовый WebSocket без проверок"""
    logger.info("🎯 TEST WebSocket endpoint CALLED")
    
    try:
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


@app.websocket("/ws/debug")
async def websocket_debug(websocket: WebSocket):
    """Простой debug WebSocket без проверок"""
    logger.info("🐛 DEBUG WebSocket endpoint CALLED")
    
    await websocket.accept()
    logger.info("✅ DEBUG WebSocket accepted")
    
    await websocket.send_text(json.dumps({
        "message": "Debug connection successful!", 
        "status": "connected"
    }))
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"🐛 DEBUG received: {data}")
            
            # Echo response
            await websocket.send_text(json.dumps({
                "echo": data,
                "timestamp": datetime.now().isoformat()
            }))
    except Exception as e:
        logger.error(f"🐛 DEBUG error: {e}")

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")

@app.websocket("/ws/simple")
async def websocket_simple(websocket: WebSocket):
    """Простой WebSocket без проверок для тестирования"""
    await websocket.accept()
    
    # Отправляем приветственное сообщение
    await websocket.send_text(json.dumps({
        "message": "Simple WebSocket connected!",
        "status": "success"
    }))
    
    try:
        while True:
            data = await websocket.receive_text()
            # Эхо-ответ
            await websocket.send_text(json.dumps({
                "echo": data,
                "timestamp": datetime.now().isoformat()
            }))
    except WebSocketDisconnect:
        print("Client disconnected")


@app.get("/debug/websocket-routes")
def debug_websocket_routes():
    """Показывает все зарегистрированные WebSocket маршруты"""
    routes = []
    for route in app.routes:
        route_info = {
            "path": getattr(route, "path", None),
            "name": getattr(route, "name", None),
            "type": type(route).__name__
        }
        # WebSocket routes имеют тип 'WebSocketRoute' или подобный
        if route_info["path"] and ("ws" in route_info["path"] or "websocket" in str(route_info["type"]).lower()):
            routes.append(route_info)
    return {"websocket_routes": routes}

# Добавьте этот класс ConnectionManager в main.py
class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        self.active_connections.append(websocket)
        print(f"✅ New WebSocket connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"🔌 WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"❌ Failed to send: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

# Добавьте этот WebSocket endpoint в main.py
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Основной WebSocket чат с правильной аутентификацией"""
    print("🎯 MAIN WebSocket /ws/chat CALLED")
    
    # Получаем токен из query параметров
    token = websocket.query_params.get("token")
    print(f"🔑 Token from query: {token}")
    
    # Аутентификация пользователя
    user_email = "anonymous@example.com"
    user_username = "Anonymous"
    
    if token:
        try:
            user_data = verify_token(token)
            if user_data:
                user_email = user_data["email"]
                user_username = user_data["username"]
                print(f"✅ Authenticated user: {user_email}")
            else:
                print("❌ Token verification failed")
        except Exception as e:
            print(f"❌ Token verification error: {e}")
    
    # Принимаем соединение
    await websocket.accept()
    print("✅ WebSocket connection accepted")
    
    # Подключаем к менеджеру
    await manager.connect(websocket)
    
    # Генерируем уникальный ID для приветственного сообщения
    welcome_id = int(time.time() * 1000) + random.randint(1, 999)
    welcome_msg = {
        "id": welcome_id,
        "text": f"Welcome to Recipe Chat, {user_username}!",
        "sender_email": "system",
        "sender_username": "System",
        "timestamp": datetime.now().isoformat(),
        "message_type": "system"
    }
    await websocket.send_text(json.dumps(welcome_msg))
    
    try:
        while True:
            # Ждем сообщения от клиента
            data = await websocket.receive_text()
            print(f"📨 Received from {user_email}: {data}")
            
            try:
                message_data = json.loads(data)
                text = message_data.get("text", "").strip()
                
                if text:
                    # Генерируем уникальный ID для каждого сообщения
                    message_id = int(time.time() * 1000) + random.randint(1, 999)
                    
                    # Проверяем, это приватное сообщение?
                    if message_data.get("message_type") == "private" and message_data.get("target_user"):
                        target_user = message_data["target_user"]
                        
                        # Создаем приватное сообщение
                        private_msg = {
                            "id": message_id,
                            "text": text,
                            "sender_email": user_email,
                            "sender_username": user_username,
                            "timestamp": datetime.now().isoformat(),
                            "message_type": "private",
                            "target_user": target_user
                        }
                        
                        await manager.broadcast(private_msg)
                        print(f"🔒 Private message from {user_email} to {target_user}: {text}")
                        
                    else:
                        # Обычное сообщение
                        response_msg = {
                            "id": message_id,
                            "text": text,
                            "sender_email": user_email,
                            "sender_username": user_username,
                            "timestamp": datetime.now().isoformat(),
                            "message_type": message_data.get("message_type", "text")
                        }
                        
                        await manager.broadcast(response_msg)
                        print(f"📢 Public message from {user_email}: {text}")
                        
            except json.JSONDecodeError:
                # Генерируем уникальный ID для сообщения об ошибке
                error_id = int(time.time() * 1000) + random.randint(1, 999)
                error_msg = {
                    "id": error_id,
                    "text": "Error: Invalid message format",
                    "sender_email": "system",
                    "sender_username": "System",
                    "timestamp": datetime.now().isoformat(),
                    "message_type": "error"
                }
                await websocket.send_text(json.dumps(error_msg))
                
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected: {user_email}")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"💥 WebSocket error: {e}")
        manager.disconnect(websocket)