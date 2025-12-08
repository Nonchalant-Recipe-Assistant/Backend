from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app.crud import UserRepository
from app.utils import verify_password, create_access_token
from jose import JWTError, jwt
from app.config import settings
from pydantic import BaseModel
from app.logger import get_logger 
from fastapi import Response


# Make sure this import matches where your send_verification_email function is located.
# Based on your pastes, it seems to be in app.services.email_service or app.email_utils
from app.email_service import send_verification_email 

logger = get_logger(__name__)

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/register", response_model=schemas.UserOut)
async def register(
    user_data: RegisterRequest, 
    background_tasks: BackgroundTasks,  # <--- Added BackgroundTasks
    db: Session = Depends(get_db)
):
    logger.info(f"Registration attempt for email: {user_data.email}")
    user_repo = UserRepository(db)
    
    try:
        # Check if user exists
        db_user = user_repo.get_user_by_email(email=user_data.email)
        if db_user:
            logger.warning(f"Registration failed - email already registered: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user with verification logic
        user_create = schemas.UserCreate(
            email=user_data.email,
            password=user_data.password
        )
        new_user = user_repo.create_user_with_verification(user=user_create)
        
        # --- FIX: Trigger the email sending task ---
        if new_user.email_verification_token:
            background_tasks.add_task(
                send_verification_email,
                new_user.email,
                new_user.email_verification_token,
                "verification"
            )
            logger.info(f"Queued verification email for: {user_data.email}")
        # -------------------------------------------
        
        logger.info(f"User registered successfully with email verification: {user_data.email}")
        return new_user
        
    except ValueError as e:
        logger.warning(f"Registration validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error for {user_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )

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
        
        # Optional: block login if not verified
        # if not db_user.email_verified:
        #    logger.warning(f"Login failed - email not verified: {login_data.email}")
        #    raise HTTPException(
        #        status_code=status.HTTP_403_FORBIDDEN,
        #       detail="Email not verified. Please check your email for verification link.",
        #    )
        
        access_token = create_access_token(data={"sub": db_user.email})
        logger.info(f"Login successful for: {login_data.email}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {login_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

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

@router.post("/set-language")
def set_language_preference(lang: str, response: Response):
    """
    Устанавливает cookie с предпочтительным языком.
    """
    if lang not in ["ru", "en"]:
        # Можно добавить валидацию, но пока просто вернем ошибку или default
        raise HTTPException(status_code=400, detail="Unsupported language")
    
    # Устанавливаем куку 'lang'
    # max_age = 1 год (в секундах)
    response.set_cookie(
        key="lang", 
        value=lang, 
        max_age=31536000, 
        httponly=False, # False, чтобы JS (i18next детектор) мог её прочитать, если нужно, хотя мы читаем её сервером
        samesite="lax"
    )
    return {"message": f"Language set to {lang}"}