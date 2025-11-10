from sqlalchemy.orm import Session
from models import Session as UserSession
from schemas import SessionCreate, SessionUpdate

def create_session(db: Session, session_data: SessionCreate):
    session = UserSession(**session_data.dict())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_sessions(db: Session, user_id: int = None):
    query = db.query(UserSession)
    if user_id:
        query = query.filter(UserSession.user_id == user_id)
    return query.all()

def update_session(db: Session, session_id: int, session_data: SessionUpdate):
    session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
    if not session:
        return None
    for field, value in session_data.dict(exclude_unset=True).items():
        setattr(session, field, value)
    db.commit()
    db.refresh(session)
    return session

def delete_session(db: Session, session_id: int):
    session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
    if not session:
        return None
    db.delete(session)
    db.commit()
    return session

