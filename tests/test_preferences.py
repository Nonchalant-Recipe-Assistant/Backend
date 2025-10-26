import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import crud.preferences as crud
from schemas import UserPreferenceCreate, UserPreferenceUpdate

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_create_preference(db):
    p = crud.create_preference(db, UserPreferenceCreate(user_id=1, cuisine="Italian", max_cooking_time=30, difficulty="easy"))
    assert p.cuisine == "Italian"

def test_update_preference(db):
    p = crud.create_preference(db, UserPreferenceCreate(user_id=2, cuisine="French", max_cooking_time=45, difficulty="medium"))
    upd = crud.update_preference(db, 2, UserPreferenceUpdate(cuisine="Asian"))
    assert upd.cuisine == "Asian"
