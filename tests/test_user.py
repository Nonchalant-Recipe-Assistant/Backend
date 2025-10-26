import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import check_password_hash

from database import Base
from models import Role
from schemas import UserCreate, UserUpdate
import crud.users as crud

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.add(Role(name="user"))
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_create_user(db_session):
    new_user = crud.create_user(db_session, UserCreate(email="test@example.com", password="123", role_id=1))
    assert new_user.email == "test@example.com"
    assert check_password_hash(new_user.password_hash, "123")

def test_get_user(db_session):
    u = crud.create_user(db_session, UserCreate(email="get@example.com", password="1", role_id=1))
    found = crud.get_user(db_session, u.user_id)
    assert found.email == "get@example.com"

def test_update_user(db_session):
    u = crud.create_user(db_session, UserCreate(email="old@mail.com", password="1", role_id=1))
    updated = crud.update_user(db_session, u.user_id, UserUpdate(email="new@mail.com"))
    assert updated.email == "new@mail.com"

def test_delete_user(db_session):
    u = crud.create_user(db_session, UserCreate(email="del@mail.com", password="1", role_id=1))
    crud.delete_user(db_session, u.user_id)
    assert crud.get_user(db_session, u.user_id) is None
