from app.crud import UserRepository
from app import schemas
from sqlalchemy.orm import Session

class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def get_users(self):
        return self.repo.get_users()

    def get_user(self, user_id: int):
        return self.repo.get_user(user_id)

    def create_user(self, user: schemas.UserCreate):
        return self.repo.create_user(user)

    def delete_user(self, user_id: int):
        return self.repo.delete_user(user_id)