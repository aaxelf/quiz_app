from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import PlayerAnswer, GameSession, User

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/user/{user_id}")
def get_user_history(user_id: int, db: Session = Depends(get_db)):
    # Получаем все уникальные сессии пользователя
    session_ids = db.query(PlayerAnswer.game_session_id).filter(PlayerAnswer.user_id == user_id).distinct().all()
    session_ids = [s[0] for s in session_ids]
    
    result = []
    for session_id in session_ids:
        game_session = db.query(GameSession).filter(GameSession.id == session_id).first()
        if not game_session:
            continue
        
        # Получаем ответы пользователя на эту сессию
        answers = db.query(PlayerAnswer).filter(
            PlayerAnswer.game_session_id == session_id,
            PlayerAnswer.user_id == user_id
        ).all()
        
        total_score = sum(a.points_awarded for a in answers)
        correct_count = sum(1 for a in answers if a.is_correct)
        answered_count = len(answers)
        total_questions = game_session.total_questions or answered_count
        
        # Вычисляем место пользователя
        all_answers = db.query(PlayerAnswer).filter(PlayerAnswer.game_session_id == session_id).all()
        user_scores = {}
        user_times = {}
        for a in all_answers:
            if a.user_id not in user_scores:
                user_scores[a.user_id] = 0
                user_times[a.user_id] = 0
            user_scores[a.user_id] += a.points_awarded
            user_times[a.user_id] += a.response_time_ms or 0
        
        sorted_users = sorted(user_scores.items(), key=lambda x: (-x[1], user_times[x[0]]))
        position = 1
        for idx, (uid, score) in enumerate(sorted_users):
            if uid == user_id:
                position = idx + 1
                break
        
        result.append({
            "game_session_id": session_id,
            "quiz_title": game_session.quiz_title or "Неизвестный квиз",
            "date": game_session.finished_at or game_session.created_at,
            "total_score": total_score,
            "answered_questions": answered_count,
            "total_questions": total_questions,
            "correct_count": correct_count,
            "position": position
        })
    
    result.sort(key=lambda x: x["date"], reverse=True)
    return result


@router.get("/session/{session_id}")
def get_session_results(session_id: int, db: Session = Depends(get_db)):
    
    answers = db.query(PlayerAnswer).filter(PlayerAnswer.game_session_id == session_id).all()
    
    # Группируем по пользователям
    users_scores = {}
    for answer in answers:
        if answer.user_id not in users_scores:
            users_scores[answer.user_id] = 0
        users_scores[answer.user_id] += answer.points_awarded
    
    result = []
    for user_id, score in users_scores.items():
        user = db.query(User).filter(User.id == user_id).first()
        result.append({
            "user_id": user_id,
            "name": user.display_name if user else "Неизвестно",
            "score": score
        })
    
    # Сортируем по очкам
    result.sort(key=lambda x: x["score"], reverse=True)
    
    return result

@router.get("/session/{session_id}/answers")
def get_session_answers(session_id: int, user_id: int, db: Session = Depends(get_db)):
    answers = db.query(PlayerAnswer).filter(
        PlayerAnswer.game_session_id == session_id,
        PlayerAnswer.user_id == user_id
    ).order_by(PlayerAnswer.id).all()
    
    result = []
    for idx, answer in enumerate(answers):
        result.append({
            "question_number": idx + 1,
            "question_text": answer.question_text,
            "is_correct": answer.is_correct,
            "points_awarded": answer.points_awarded,
            "user_answer": answer.user_answer_text,
            "correct_answer": answer.correct_answer_text
        })
    
    return result