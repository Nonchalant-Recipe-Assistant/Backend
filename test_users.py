import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import check_password_hash

from database import Base
from models import User, Role
import crud
from schemas import UserCreate, UserUpdate

# Используем in-memory SQLite для тестов
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Фикстура для БД
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    # добавляем роль user по умолчанию
    role = Role(name="user")
    session.add(role)
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

# --- ТЕСТЫ ---

def test_create_user(db_session):
    user_data = UserCreate(email="test@example.com", password="secret123", role_id=1)
    user = crud.create_user(db_session, user_data)

    assert user.user_id is not None
    assert user.email == "test@example.com"
    assert check_password_hash(user.password_hash, "secret123")

def test_get_user(db_session):
    user_data = UserCreate(email="test@example.com", password="secret123", role_id=1)
    created = crud.create_user(db_session, user_data)

    fetched = crud.get_user(db_session, created.user_id)
    assert fetched is not None
    assert fetched.email == "test@example.com"

def test_update_user(db_session):
    user_data = UserCreate(email="old@example.com", password="12345", role_id=1)
    created = crud.create_user(db_session, user_data)

    update_data = UserUpdate(email="new@example.com", password="67890")
    updated = crud.update_user(db_session, created.user_id, update_data)

    assert updated.email == "new@example.com"
    assert check_password_hash(updated.password_hash, "67890")

def test_delete_user(db_session):
    user_data = UserCreate(email="delete@example.com", password="to_remove", role_id=1)
    created = crud.create_user(db_session, user_data)

    deleted = crud.delete_user(db_session, created.user_id)
    assert deleted is not None

    fetched = crud.get_user(db_session, created.user_id)
    assert fetched is None

def test_get_nonexistent_user(db_session):
    user = crud.get_user(db_session, 9999)
    assert user is None

def test_update_nonexistent_user(db_session):
    update_data = UserUpdate(email="ghost@example.com")
    updated = crud.update_user(db_session, 9999, update_data)
    assert updated is None

def test_delete_nonexistent_user(db_session):
    deleted = crud.delete_user(db_session, 9999)
    assert deleted is None
