from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Quiz
from app.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    """Получить список всех пользователей"""
    users = db.query(User).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Получить информацию о пользователе по ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user


@router.get("/{user_id}/quizzes")
def get_user_quizzes(user_id: int, db: Session = Depends(get_db)):
    """Получить все квизы, созданные пользователем (как организатор)"""
    
    # Проверяем, существует ли пользователь
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Получаем все квизы этого пользователя
    quizzes = db.query(Quiz).filter(Quiz.organizer_id == user_id).all()
    
    return [
        {
            "id": q.id,
            "title": q.title,
            "description": q.description,
            "category": q.category,
            "is_published": q.is_published,
            "play_count": q.play_count,
            "created_at": q.created_at
        }
        for q in quizzes
    ]


@router.put("/{user_id}")
def update_user(
    user_id: int,
    display_name: str = None,
    email: str = None,
    db: Session = Depends(get_db)
):    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    if display_name:
        user.display_name = display_name
    if email:
        # Проверяем, не занят ли email другим пользователем
        existing = db.query(User).filter(User.email == email, User.id != user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже используется другим пользователем"
            )
        user.email = email
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Профиль обновлён",
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role
        }
    }


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Удалить пользователя (осторожно! удалятся все его квизы)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": f"Пользователь {user.display_name} удалён"}