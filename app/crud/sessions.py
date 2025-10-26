from sqlalchemy.orm import Session
from models import Session as UserSession
from schemas import SessionCreate, SessionUpdate
from logger import logger

def create_session(db: Session, session_data: SessionCreate):
    session = UserSession(**session_data.dict())
    db.add(session)
    db.commit()
    db.refresh(session)
    logger.info(f"Session created: id={session.session_id}, user={session.user_id}")
    return session

def get_sessions(db: Session, user_id: int = None):
    query = db.query(UserSession)
    if user_id:
        query = query.filter(UserSession.user_id == user_id)
        logger.info(f"Fetched sessions for user_id={user_id}")
    sessions = query.all()
    return sessions

def update_session(db: Session, session_id: int, session_data: SessionUpdate):
    session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
    if not session:
        logger.warning(f"Session update failed: id={session_id} not found")
        return None
    for field, value in session_data.dict(exclude_unset=True).items():
        setattr(session, field, value)
    db.commit()
    db.refresh(session)
    logger.info(f"Session updated: id={session.session_id}")
    return session

def delete_session(db: Session, session_id: int):
    session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
    if not session:
        logger.warning(f"Session delete failed: id={session_id}")
        return None
    db.delete(session)
    db.commit()
    logger.info(f"Session deleted: id={session_id}")
    return session
