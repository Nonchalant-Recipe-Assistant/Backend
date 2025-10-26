from sqlalchemy.orm import Session
from models import Role
from schemas import RoleCreate, RoleUpdate

def create_role(db: Session, role: RoleCreate):
    new_role = Role(name=role.name)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role

def get_roles(db: Session):
    return db.query(Role).all()

def get_role(db: Session, role_id: int):
    return db.query(Role).filter(Role.role_id == role_id).first()

def update_role(db: Session, role_id: int, role: RoleUpdate):
    db_role = db.query(Role).filter(Role.role_id == role_id).first()
    if not db_role:
        return None
    db_role.name = role.name or db_role.name
    db.commit()
    db.refresh(db_role)
    return db_role

def delete_role(db: Session, role_id: int):
    db_role = db.query(Role).filter(Role.role_id == role_id).first()
    if not db_role:
        return None
    db.delete(db_role)
    db.commit()
    return db_role
