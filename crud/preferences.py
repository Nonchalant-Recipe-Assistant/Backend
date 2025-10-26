from sqlalchemy.orm import Session
from models import UserPreference
from schemas import UserPreferenceCreate, UserPreferenceUpdate
from logger import logger

def create_preference(db: Session, pref: UserPreferenceCreate):
    new_pref = UserPreference(**pref.dict())
    db.add(new_pref)
    db.commit()
    db.refresh(new_pref)
    logger.info(f"Preferences created for user_id={new_pref.user_id}")
    return new_pref

def get_preference(db: Session, user_id: int):
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if pref:
        logger.info(f"Preferences fetched for user_id={user_id}")
    else:
        logger.warning(f"Preferences not found for user_id={user_id}")
    return pref

def update_preference(db: Session, user_id: int, pref_data: UserPreferenceUpdate):
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        logger.warning(f"Preference update failed: user_id={user_id}")
        return None
    for field, value in pref_data.dict(exclude_unset=True).items():
        setattr(pref, field, value)
    db.commit()
    db.refresh(pref)
    logger.info(f"Preferences updated for user_id={user_id}")
    return pref

def delete_preference(db: Session, user_id: int):
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        logger.warning(f"Preference delete failed: user_id={user_id}")
        return None
    db.delete(pref)
    db.commit()
    logger.info(f"Preferences deleted for user_id={user_id}")
    return pref
