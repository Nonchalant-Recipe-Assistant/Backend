from sqlalchemy.orm import Session
from models import Role
from schemas import RoleCreate, RoleUpdate
from logger import logger

def create_role(db: Session, role: RoleCreate):
    new_role = Role(name=role.name)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    logger.info(f"Role created: id={new_role.role_id}, name={new_role.name}")
    return new_role

def get_roles(db: Session):
    roles = db.query(Role).all()
    logger.info(f"Fetched {len(roles)} roles")
    return roles

def get_role(db: Session, role_id: int):
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if role:
        logger.info(f"Role fetched: id={role.role_id}")
    else:
        logger.warning(f"Role not found: id={role_id}")
    return role

def update_role(db: Session, role_id: int, role: RoleUpdate):
    db_role = db.query(Role).filter(Role.role_id == role_id).first()
    if not db_role:
        logger.warning(f"Role update failed, not found id={role_id}")
        return None
    db_role.name = role.name or db_role.name
    db.commit()
    db.refresh(db_role)
    logger.info(f"Role updated: id={db_role.role_id}, name={db_role.name}")
    return db_role

def delete_role(db: Session, role_id: int):
    db_role = db.query(Role).filter(Role.role_id == role_id).first()
    if not db_role:
        logger.warning(f"Role delete failed, not found id={role_id}")
        return None
    db.delete(db_role)
    db.commit()
    logger.info(f"Role deleted: id={role_id}")
    return db_role
