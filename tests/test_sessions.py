import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import Session
import crud.sessions as crud
from schemas import SessionCreate, SessionUpdate

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    s = SessionLocal()
    yield s
    s.close()
    Base.metadata.drop_all(bind=engine)

def test_create_session(db):
    new_session = crud.create_session(db, SessionCreate(user_id=1, token="abc123"))
    assert new_session.token == "abc123"

def test_update_session(db):
    s = crud.create_session(db, SessionCreate(user_id=1, token="old"))
    updated = crud.update_session(db, s.session_id, SessionUpdate(token="new"))
    assert updated.token == "new"
