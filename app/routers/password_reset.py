from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
from app.database import get_db
from app.models import User
from app.auth import get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["password"])

# Временное хранилище токенов сброса
reset_tokens = {}

@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    """Запрос на восстановление пароля"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь с таким email не найден")
    
    # Генерируем токен
    token = secrets.token_urlsafe(32)
    reset_tokens[token] = {
        "user_id": user.id,
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }
    
    return {
        "message": "Инструкция отправлена",
        "reset_url": f"http://localhost:8000/auth/reset-password?token={token}"
    }

@router.post("/reset-password")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    """Сброс пароля по токену"""
    token_data = reset_tokens.get(token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Неверный или просроченный токен")
    
    if token_data["expires_at"] < datetime.utcnow():
        del reset_tokens[token]
        raise HTTPException(status_code=400, detail="Токен просрочен")
    
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Пароль должен быть не менее 6 символов")
    
    user.password_hash = get_password_hash(new_password)
    db.commit()
    
    del reset_tokens[token]
    
    return {"message": "Пароль успешно изменён"}

@router.post("/change-password")
def change_password(
    user_id: int, 
    current_password: str, 
    new_password: str, 
    db: Session = Depends(get_db)
):
    """Смена пароля авторизованным пользователем (из профиля)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Пароль должен быть не менее 6 символов")
    
    user.password_hash = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Пароль успешно изменён"}