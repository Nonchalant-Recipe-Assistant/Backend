from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import UserRepository
from app.schemas import EmailVerificationConfirm, UpdateEmailRequest, AvatarUpdateResponse, UserProfile
from .auth import get_current_user
import os
import uuid
from pathlib import Path
from app.logger import get_logger
from app.email_service import send_verification_email # Ensure this import is correct

logger = get_logger(__name__)

router = APIRouter()

# Directory for storing avatars
AVATAR_UPLOAD_DIR = "uploads/avatars"
os.makedirs(AVATAR_UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024

@router.post("/verify-email")
async def verify_email(verification_data: EmailVerificationConfirm, db: Session = Depends(get_db)):
    """Confirms user email"""
    logger.info(f"Email verification attempt with token")
    
    user_repo = UserRepository(db)
    user = user_repo.verify_email(verification_data.token)
    
    if not user:
        logger.warning("Email verification failed - invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    logger.info(f"Email verified successfully for: {user.email}")
    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Resends verification email"""
    logger.info(f"Resending verification email for: {current_user.email}")
    
    if current_user.email_verified:
        logger.warning(f"Email already verified: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    user_repo = UserRepository(db)
    user = user_repo.resend_verification_email(current_user.user_id)
    
    if not user:
        logger.error(f"Failed to resend verification for: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to resend verification email"
        )
    
    # --- FIX: Trigger the email task ---
    if user.email_verification_token:
        background_tasks.add_task(
            send_verification_email,
            user.email,
            user.email_verification_token,
            "verification"
        )
    # -----------------------------------
    
    logger.info(f"Verification email resent for: {user.email}")
    return {"message": "Verification email sent"}

@router.post("/update-email")
async def update_email(
    email_data: UpdateEmailRequest, 
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Initiates email change"""
    logger.info(f"Email change request for user {current_user.user_id} to {email_data.new_email}")
    
    user_repo = UserRepository(db)
    result = user_repo.initiate_email_change(current_user.user_id, email_data.new_email)
    
    if not result:
        logger.warning(f"Email change failed for user {current_user.user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email change failed. Email may already be in use."
        )
    
    logger.info(f"Email change initiated for user {current_user.user_id}")
    return {"message": "Verification email sent to new address"}

@router.post("/upload-avatar", response_model=AvatarUpdateResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Загружает аватар пользователя"""
    logger.info(f"Avatar upload attempt for user: {current_user.user_id}")
    
    # Проверяем тип файла
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        logger.warning(f"Invalid file type for avatar: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a JPEG, PNG, GIF, or WebP image"
        )
    
    # Проверяем размер файла
    file.file.seek(0, 2)  # Перемещаемся в конец файла
    file_size = file.file.tell()
    file.file.seek(0)  # Возвращаемся в начало
    
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file_size} bytes")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size must be less than {MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    
    # Генерируем уникальное имя файла
    file_extension = Path(file.filename).suffix.lower()
    if not file_extension:
        file_extension = ".jpg"
    
    filename = f"{current_user.user_id}_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(AVATAR_UPLOAD_DIR, filename)
    
    # Сохраняем файл
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        logger.error(f"Failed to save avatar file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )
    
    # Обновляем аватар в базе данных
    user_repo = UserRepository(db)
    # Сохраняем относительный путь к файлу
    avatar_url = f"/auth/avatar/{filename}"
    
    user = user_repo.update_avatar(current_user.user_id, avatar_url)
    
    if not user:
        logger.error(f"Failed to update avatar in database for user: {current_user.user_id}")
        # Удаляем загруженный файл, если не удалось обновить БД
        try:
            os.remove(file_path)
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update avatar"
        )
    
    logger.info(f"Avatar uploaded successfully for user: {current_user.user_id}")
    return AvatarUpdateResponse(
        avatar_url=avatar_url,
        message="Avatar updated successfully"
    )

@router.get("/avatar/{filename}")
async def get_avatar(filename: str):
    """Отдает файл аватара"""
    logger.info(f"Avatar file request: {filename}")
    
    # Безопасная проверка имени файла
    if not filename or '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = os.path.join(AVATAR_UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    # Определяем Content-Type по расширению файла
    extension = Path(filename).suffix.lower()
    content_type = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }.get(extension, 'application/octet-stream')
    
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        
        return Response(content=content, media_type=content_type)
    except Exception as e:
        logger.error(f"Failed to read avatar file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to read avatar file")

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user = Depends(get_current_user)):
    """Получает профиль пользователя"""
    return UserProfile(
        user_id=current_user.user_id,
        email=current_user.email,
        email_verified=current_user.email_verified,
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at
    )

@router.delete("/avatar")
async def delete_avatar(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаляет аватар пользователя"""
    logger.info(f"Deleting avatar for user: {current_user.user_id}")
    
    user_repo = UserRepository(db)
    user = user_repo.get_user(current_user.user_id)
    
    if not user or not user.avatar_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    # Извлекаем имя файла из URL
    if user.avatar_url.startswith("/auth/avatar/"):
        avatar_filename = user.avatar_url.split("/")[-1]
        avatar_path = os.path.join(AVATAR_UPLOAD_DIR, avatar_filename)
        
        # Удаляем файл
        try:
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
                logger.info(f"Avatar file deleted: {avatar_path}")
        except Exception as e:
            logger.warning(f"Failed to delete avatar file: {str(e)}")
    
    # Обновляем базу данных
    user.avatar_url = None
    db.commit()
    
    logger.info(f"Avatar deleted for user: {current_user.user_id}")
    return {"message": "Avatar deleted successfully"}

@router.post("/debug/verify-email-manually")
async def verify_email_manually(
    email: str,
    db: Session = Depends(get_db)
):
    """Ручное подтверждение email для тестирования"""
    logger.info(f"Manual email verification for: {email}")
    
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_email(email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Подтверждаем email вручную
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    db.commit()
    
    logger.info(f"Email manually verified for: {email}")
    return {"message": "Email verified manually"}