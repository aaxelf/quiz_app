from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
import subprocess
import json
import os
from typing import List
from datetime import datetime

from app.database import get_db
from app.models import Quiz, Question, AnswerOption
from app.schemas import QuizCreate, QuizResponse, QuizListItem


router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.post("/create", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(quiz_data: QuizCreate, db: Session = Depends(get_db)):
    """Создание нового квиза с вопросами и вариантами ответов"""
    
    new_quiz = Quiz(
        organizer_id=quiz_data.organizer_id,
        title=quiz_data.title,
        description=quiz_data.description,
        category=quiz_data.category,
        time_per_question_sec=quiz_data.time_per_question_sec,
    )
    
    db.add(new_quiz)
    db.flush()
    
    for q in quiz_data.questions:
        new_question = Question(
            quiz_id=new_quiz.id,
            order_index=q.order_index,
            question_text=q.question_text,
            image_url=q.image_url,
            answer_mode=q.answer_mode.value,
            points=q.points,
            time_limit_sec=q.time_limit_sec
        )
        db.add(new_question)
        db.flush()
        
        for opt in q.options:
            new_option = AnswerOption(
                question_id=new_question.id,
                option_text=opt.option_text,
                is_correct=opt.is_correct,
                order_index=opt.order_index
            )
            db.add(new_option)
    
    db.commit()
    db.refresh(new_quiz)
    
    return new_quiz


@router.get("/export-all")
def export_all_quizzes(organizer_id: int, db: Session = Depends(get_db)):
    """Экспорт всех квизов организатора в JSON"""
    
    # Запускаем твой скрипт
    result = subprocess.run(['python', 'export.py'], capture_output=True, text=True)
    
    if os.path.exists('quizzes_backup.json'):
        # Читаем файл и возвращаем с отступами
        with open('quizzes_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return Response(
            content=json.dumps(data, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=quizzes_export.json"}
        )
    else:
        raise HTTPException(status_code=500, detail="Ошибка экспорта")


@router.get("/my/{organizer_id}", response_model=List[QuizListItem])
def get_my_quizzes(organizer_id: int, db: Session = Depends(get_db)):
    """Получить все квизы организатора"""
    
    quizzes = db.query(Quiz).filter(Quiz.organizer_id == organizer_id).all()
    return quizzes


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """Получить полную информацию о квизе (с вопросами и ответами)"""
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Квиз не найден"
        )
    
    return quiz


@router.put("/{quiz_id}")
def update_quiz_full(quiz_id: int, quiz_data: QuizCreate, db: Session = Depends(get_db)):
    """Полностью заменяет квиз новыми данными (вопросы и ответы)"""
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Квиз не найден")
    
    if quiz.organizer_id != quiz_data.organizer_id:
        raise HTTPException(status_code=403, detail="Нет прав на редактирование")
    
    quiz.title = quiz_data.title
    quiz.description = quiz_data.description
    quiz.category = quiz_data.category
    quiz.time_per_question_sec = quiz_data.time_per_question_sec
    quiz.max_players = quiz_data.max_players
    quiz.updated_at = datetime.utcnow()
    
    db.query(Question).filter(Question.quiz_id == quiz_id).delete()
    
    for q in quiz_data.questions:
        new_question = Question(
            quiz_id=quiz_id,
            order_index=q.order_index,
            question_text=q.question_text,
            image_url=q.image_url,
            answer_mode=q.answer_mode.value,
            points=q.points,
            time_limit_sec=q.time_limit_sec
        )
        db.add(new_question)
        db.flush()
        
        for opt in q.options:
            new_option = AnswerOption(
                question_id=new_question.id,
                option_text=opt.option_text,
                is_correct=opt.is_correct,
                order_index=opt.order_index
            )
            db.add(new_option)
    
    db.commit()
    db.refresh(quiz)
    
    return {"message": "Квиз полностью обновлён", "quiz_id": quiz_id}


@router.patch("/{quiz_id}/publish")
def publish_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """Опубликовать квиз (сделать доступным для игр)"""
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Квиз не найден")
    
    db.commit()
    
    return {"message": "Квиз опубликован", "quiz_id": str(quiz_id)}


@router.delete("/{quiz_id}")
def delete_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """Удалить квиз (вместе с вопросами и ответами)"""
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Квиз не найден")
    
    db.delete(quiz)
    db.commit()
    
    return {"message": "Квиз удалён", "quiz_id": str(quiz_id)}


@router.post("/import")
def import_quiz(
    organizer_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):    
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Только JSON файлы")
    
    content = file.file.read()
    data = json.loads(content)
    
    if isinstance(data, list):
        imported_count = 0
        for quiz_data in data:
            imported_count += import_single_quiz(organizer_id, quiz_data, db)
        return {"message": f"Импортировано {imported_count} квизов"}
    else:
        import_single_quiz(organizer_id, data, db)
        return {"message": "Квиз импортирован"}


def import_single_quiz(organizer_id: int, data: dict, db: Session):
    if "info" in data:
        title = data["info"]["title"]
        description = data["info"].get("description")
        category = data["info"].get("category")
        time_per_question_sec = data["info"].get("time_per_question_sec", 30)
        max_players = data["info"].get("max_players", 10)
        questions_data = data["questions"]
    else:
        title = data.get("title", "Импортированный квиз")
        description = data.get("description")
        category = data.get("category")
        time_per_question_sec = data.get("time_per_question_sec", 30)
        max_players = data.get("max_players", 10)
        questions_data = data.get("questions", [])
    
    new_quiz = Quiz(
        organizer_id=organizer_id,
        title=title,
        description=description,
        category=category,
        time_per_question_sec=time_per_question_sec,
        max_players=max_players,
    )
    db.add(new_quiz)
    db.flush()
    
    for q_data in questions_data:
        new_question = Question(
            quiz_id=new_quiz.id,
            order_index=q_data.get("order_index", 0),
            question_text=q_data["question_text"],
            image_url=q_data.get("image_url"),
            answer_mode=q_data.get("answer_mode", "single"),
            points=q_data.get("points", 100),
            time_limit_sec=q_data.get("time_limit_sec")
        )
        db.add(new_question)
        db.flush()
        
        for opt_data in q_data.get("options", []):
            new_option = AnswerOption(
                question_id=new_question.id,
                option_text=opt_data["option_text"],
                is_correct=opt_data["is_correct"],
                order_index=opt_data.get("order_index", 0)
            )
            db.add(new_option)
    
    db.commit()
    return new_quiz.id
