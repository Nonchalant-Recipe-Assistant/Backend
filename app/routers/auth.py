from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app.crud import UserRepository
from app.utils import verify_password, create_access_token
from jose import JWTError, jwt
from app.config import settings
from pydantic import BaseModel
from app.logger import get_logger  # Добавляем импорт

logger = get_logger(__name__)

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Registration attempt for email: {user.email}")
    user_repo = UserRepository(db)
    
    try:
        db_user = user_repo.get_user_by_email(email=user.email)
        if db_user:
            logger.warning(f"Registration failed - email already registered: {user.email}")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        new_user = user_repo.create_user(user=user)
        logger.info(f"User registered successfully: {user.email}")
        return new_user
        
    except Exception as e:
        logger.error(f"Registration error for {user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login", response_model=schemas.Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    logger.info(f"Login attempt for email: {login_data.email}")
    user_repo = UserRepository(db)
    
    try:
        db_user = user_repo.get_user_by_email(email=login_data.email)
        if not db_user:
            logger.warning(f"Login failed - user not found: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        
        if not verify_password(login_data.password, db_user.password_hash):
            logger.warning(f"Login failed - invalid password for: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        
        access_token = create_access_token(data={"sub": db_user.email})
        logger.info(f"Login successful for: {login_data.email}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {login_data.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    logger.debug("Token validation started")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token validation failed - no email in payload")
            raise credentials_exception
        logger.debug(f"Token validated for email: {email}")
    except JWTError as e:
        logger.warning(f"Token validation failed - JWT error: {str(e)}")
        raise credentials_exception
    
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_email(email=email)
    if user is None:
        logger.warning(f"Token validation failed - user not found: {email}")
        raise credentials_exception
        
    logger.debug(f"User authenticated: {email}")
    return user

@router.get("/me", response_model=schemas.UserOut)
def read_users_me(current_user: schemas.UserOut = Depends(get_current_user)):
    logger.debug(f"Profile accessed for: {current_user.email}")
    return current_user