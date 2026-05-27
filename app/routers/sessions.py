from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import random
import string
import asyncio
from app.database import get_db
from app.models import Quiz, GameSession, Question
from app.room_manager import room_manager
from app.routers.websocket import send_current_question

router = APIRouter(prefix="/sessions", tags=["sessions"])

def generate_room_code():
    return ''.join(random.choices(string.digits, k=6))

@router.post("/create")
def create_session(session_data: dict, db: Session = Depends(get_db)):
    quiz_id = session_data.get("quiz_id")
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Квиз не найден")
    
    total_questions = db.query(Question).filter(Question.quiz_id == quiz_id).count()

    code = generate_room_code()
    while db.query(GameSession).filter(GameSession.room_code == code).first():
        code = generate_room_code()
    
    new_session = GameSession(
        quiz_id=quiz_id,
        quiz_title=quiz.title,
        total_questions=total_questions,
        room_code=code,
        status="waiting"
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    room_manager.rooms[code] = {
        "quiz_id": quiz_id,
        "organizer": None,
        "players": {},
        "status": "waiting",
        "current_question_index": 0,
        "total_questions": total_questions,
        "max_players": quiz.max_players if hasattr(quiz, 'max_players') else 10,
        "game_session_id": new_session.id
    }
    
    return {
        "id": new_session.id,
        "room_code": new_session.room_code,
        "status": new_session.status,
        "created_at": new_session.created_at,
        "quiz_title": quiz.title
    }

@router.get("/my")
def get_my_sessions(db: Session = Depends(get_db)):
    sessions = db.query(GameSession).filter(
        GameSession.status.in_(['waiting', 'active'])
    ).order_by(GameSession.created_at.desc()).all()
    
    result = []
    for s in sessions:
        quiz = db.query(Quiz).filter(Quiz.id == s.quiz_id).first()
        result.append({
            "id": s.id,
            "room_code": s.room_code,
            "status": s.status,
            "quiz_title": quiz.title if quiz else "Неизвестный квиз",
            "players_count": len(room_manager.rooms.get(s.room_code, {}).get("players", {})),
            "created_at": s.created_at
        })
    
    return result

@router.delete("/{room_code}")
def delete_session(room_code: str, db: Session = Depends(get_db)):
    session = db.query(GameSession).filter(GameSession.room_code == room_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    # Удаляем из room_manager
    if room_code in room_manager.rooms:
        del room_manager.rooms[room_code]
    
    db.delete(session)
    db.commit()
    
    return {"message": "Сессия удалена"}

@router.post("/{room_code}/start")
async def start_session(room_code: str, db: Session = Depends(get_db)):
    session = db.query(GameSession).filter(GameSession.room_code == room_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    session.status = "active"
    session.started_at = datetime.utcnow()
    db.commit()
    
    if room_code in room_manager.rooms:
        room_manager.rooms[room_code]["status"] = "active"
        room_manager.rooms[room_code]["current_question_index"] = 0
        
        asyncio.create_task(send_current_question(room_code))
    
    return {"message": "Квиз начат"}

@router.get("/check/{room_code}")
def check_room(room_code: str, db: Session = Depends(get_db)):
    session = db.query(GameSession).filter(GameSession.room_code == room_code).first()
    if not session:
        return {"exists": False, "status": None, "is_active": False, "is_full": False}
    
    from app.room_manager import room_manager
    room = room_manager.rooms.get(room_code)
    is_full = False
    players_count = 0
    if room:
        max_players = room.get("max_players", 10)
        players_count = len(room["players"])
        is_full = players_count >= max_players
    
    return {
        "exists": True,
        "status": session.status,
        "is_active": session.status == "active",
        "is_full": is_full,
        "players_count": players_count
    }