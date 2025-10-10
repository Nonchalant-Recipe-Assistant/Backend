from sqlalchemy.orm import Session
from models import UserPreference
from schemas import UserPreferenceCreate, UserPreferenceUpdate

def create_preference(db: Session, pref: UserPreferenceCreate):
    new_pref = UserPreference(**pref.dict())
    db.add(new_pref)
    db.commit()
    db.refresh(new_pref)
    return new_pref

def get_preference(db: Session, user_id: int):
    return db.query(UserPreference).filter(UserPreference.user_id == user_id).first()

def update_preference(db: Session, user_id: int, pref_data: UserPreferenceUpdate):
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        return None
    for field, value in pref_data.dict(exclude_unset=True).items():
        setattr(pref, field, value)
    db.commit()
    db.refresh(pref)
    return pref

def delete_preference(db: Session, user_id: int):
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        return None
    db.delete(pref)
    db.commit()
    return pref
