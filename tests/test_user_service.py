import pytest
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base
from app.crud.user import UserRepository
from app.schemas import UserCreate
from app.utils import verify_password
from app.models import Role

DB_USER = os.getenv("DB_USER", "devuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "devpass")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "nra")

def get_test_db_url():
    """Получаем URL для тестовой базы данных"""
    return f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Движок для тестовой базы
test_engine = create_engine(get_test_db_url(), echo=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session():
    """Создаем сессию для тестов и очищаем таблицы после каждого теста"""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    
    # Создаем необходимые роли для тестов
    roles = session.query(Role).all()
    if not roles:
        # Если ролей нет, создаем базовые
        session.add(Role(name="user"))
        session.add(Role(name="admin")) 
        session.add(Role(name="moderator"))
        session.commit()
    
    yield session
    
    # Очищаем таблицы после теста (только пользователей)
    session.rollback()
    
    # Удаляем только пользователей, роли не трогаем
    from app.models import User
    session.query(User).delete()
    
    session.commit()
    session.close()

class TestUserRepository:
    def test_create_user_success(self, db_session):
        """Тест успешного создания пользователя"""
        user_repo = UserRepository(db_session)
        
        # Получаем первую роль
        role = db_session.query(Role).first()
        user_data = UserCreate(email="test@example.com", password="testpassword123", role_id=role.role_id)
        
        user = user_repo.create_user(user=user_data)
        
        assert user.email == "test@example.com"
        assert user.role_id == role.role_id
        assert user.password_hash != "testpassword123"
        assert verify_password("testpassword123", user.password_hash)

    def test_create_user_duplicate_email(self, db_session):
        """Тест создания пользователя с существующим email"""
        user_repo = UserRepository(db_session)
        role = db_session.query(Role).first()
        user_data = UserCreate(email="duplicate@example.com", password="password123", role_id=role.role_id)
        
        # Первое создание - должно быть успешно
        user_repo.create_user(user=user_data)
        
        # Второе создание с тем же email - должно вызвать исключение
        with pytest.raises(Exception):
            user_repo.create_user(user=user_data)

    def test_get_user_by_email_exists(self, db_session):
        """Тест поиска существующего пользователя по email"""
        user_repo = UserRepository(db_session)
        role = db_session.query(Role).first()
        user_data = UserCreate(email="find@example.com", password="password123", role_id=role.role_id)
        created_user = user_repo.create_user(user=user_data)
        
        found_user = user_repo.get_user_by_email("find@example.com")
        
        assert found_user is not None
        assert found_user.email == created_user.email
        assert found_user.user_id == created_user.user_id

    def test_get_user_by_email_not_exists(self, db_session):
        """Тест поиска несуществующего пользователя по email"""
        user_repo = UserRepository(db_session)
        
        user = user_repo.get_user_by_email("nonexistent@example.com")
        
        assert user is None

    def test_get_user_by_id_exists(self, db_session):
        """Тест поиска пользователя по ID"""
        user_repo = UserRepository(db_session)
        role = db_session.query(Role).first()
        user_data = UserCreate(email="idtest@example.com", password="password123", role_id=role.role_id)
        created_user = user_repo.create_user(user=user_data)
        
        found_user = user_repo.get_user(created_user.user_id)
        
        assert found_user is not None
        assert found_user.user_id == created_user.user_id
        assert found_user.email == created_user.email

    def test_get_user_by_id_not_exists(self, db_session):
        """Тест поиска несуществующего пользователя по ID"""
        user_repo = UserRepository(db_session)
        
        user = user_repo.get_user(999)
        
        assert user is None

    def test_user_password_hashing(self, db_session):
        """Тест корректного хэширования пароля"""
        user_repo = UserRepository(db_session)
        role = db_session.query(Role).first()
        user_data = UserCreate(email="hash@example.com", password="my_secure_password", role_id=role.role_id)
        
        user = user_repo.create_user(user=user_data)
        
        assert user.password_hash != "my_secure_password"
        assert verify_password("my_secure_password", user.password_hash)
        assert not verify_password("wrong_password", user.password_hash)

    def test_create_user_with_custom_role(self, db_session):
        """Тест создания пользователя с кастомной ролью"""
        user_repo = UserRepository(db_session)
        # Берем вторую роль
        roles = db_session.query(Role).all()
        if len(roles) > 1:
            admin_role = roles[1]
            user_data = UserCreate(email="admin@example.com", password="password123", role_id=admin_role.role_id)
            
            user = user_repo.create_user(user=user_data)
            
            assert user.role_id == admin_role.role_id
            assert user.email == "admin@example.com"

    def test_get_all_users(self, db_session):
        """Тест получения всех пользователей"""
        user_repo = UserRepository(db_session)
        role = db_session.query(Role).first()
        
        # Создаем нескольких пользователей
        user1_data = UserCreate(email="user1@example.com", password="pass1", role_id=role.role_id)
        user2_data = UserCreate(email="user2@example.com", password="pass2", role_id=role.role_id)
        
        user_repo.create_user(user=user1_data)
        user_repo.create_user(user=user2_data)
        
        all_users = user_repo.get_users()
        
        assert len(all_users) >= 2
        emails = [user.email for user in all_users]
        assert "user1@example.com" in emails
        assert "user2@example.com" in emails