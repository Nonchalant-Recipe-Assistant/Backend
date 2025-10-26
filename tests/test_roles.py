import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import Role
import crud.roles as crud
from schemas import RoleCreate, RoleUpdate

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_create_role(db):
    role = crud.create_role(db, RoleCreate(name="admin"))
    assert role.name == "admin"

def test_update_role(db):
    role = crud.create_role(db, RoleCreate(name="user"))
    updated = crud.update_role(db, role.role_id, RoleUpdate(name="superuser"))
    assert updated.name == "superuser"
