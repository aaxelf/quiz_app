from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.room_manager import room_manager
from app.database import SessionLocal
from app.models import Question, AnswerOption, GameSession, PlayerAnswer, Quiz, User
import json
import asyncio
from datetime import datetime
import time

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/{user_type}/{identifier}")
async def websocket_endpoint(websocket: WebSocket, user_type: str, identifier: str):
    await websocket.accept()
    print(f"✅ Подключился: {user_type}/{identifier}")
    
    try:
        data = await websocket.receive_text()
        message = json.loads(data)
        
        if message["action"] == "create_room":
            quiz_id = message["quiz_id"]
            code = room_manager.generate_code()
            
            db = SessionLocal()
            try:
                total_questions = db.query(Question).filter(Question.quiz_id == quiz_id).count()
                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
                max_players_value = quiz.max_players if quiz else 10
                
                # Создаём запись в GameSession
                game_session = GameSession(
                    quiz_id=quiz_id,
                    room_code=code,
                    status="waiting"
                )
                db.add(game_session)
                db.commit()
                db.refresh(game_session)
                game_session_id = game_session.id
                
            finally:
                db.close()
            
            room_manager.rooms[code] = {
                "quiz_id": quiz_id,
                "organizer": websocket,
                "players": {},
                "status": "waiting",
                "current_question_index": 0,
                "total_questions": total_questions,
                "max_players": max_players_value,
                "game_session_id": game_session_id
            }
            
            await websocket.send_text(json.dumps({
                "type": "room_created",
                "code": code,
                "message": f"Комната {code} создана",
                "total_questions": total_questions
            }))
            print(f"🎯 Создана комната: {code}, вопросов: {total_questions}, макс игроков: {max_players_value}, session_id: {game_session_id}")
            
            await handle_organizer(websocket, code)
        
        elif message["action"] == "join_room":
            code = message["code"]
            user_id = message.get("user_id")
            user_name = message.get("user_name")
            
            print(f"🔍 Попытка подключения: code={code}, user_id={user_id}, user_name={user_name}")
            
            room = room_manager.rooms.get(code)
            if not room:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Комната не найдена"
                }))
                await websocket.close()
                return
            
            print(f"Комната найдена. Статус: {room['status']}, игроков: {len(room['players'])}")
            
            if room["status"] != "waiting":
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Квиз уже начался"
                }))
                await websocket.close()
                return
            
            max_players = room.get("max_players", 10)
            if len(room["players"]) >= max_players:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Комната заполнена (максимум {max_players} игроков)"
                }))
                await websocket.close()
                return
            
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    print(f"❌ Пользователь с ID {user_id} не найден")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Пользователь с ID {user_id} не найден"
                    }))
                    return
                
                player_name = user_name if user_name else user.display_name
                print(f"✅ Пользователь найден: {player_name}")
                
                room["players"][websocket] = {
                    "user_id": user.id,
                    "name": player_name,
                    "score": 0,
                    "answers": []
                }
                
                print(f"👤 Игрок {player_name} добавлен, всего игроков: {len(room['players'])}")
                
            except Exception as e:
                print(f"⚠️ Ошибка БД: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Ошибка БД: {e}"
                }))
                return
            finally:
                db.close()
            
            await websocket.send_text(json.dumps({
                "type": "joined",
                "code": code,
                "message": f"Вы присоединились как {player_name}"
            }))
            
            await send_leaderboard(code)
            
            if room["organizer"]:
                await room["organizer"].send_text(json.dumps({
                    "type": "player_joined",
                    "players_count": len(room["players"]),
                    "player_name": player_name
                }))
            
            await handle_player(websocket, code)
        
        elif message["action"] == "check_room":
            code = message["code"]
            room = room_manager.rooms.get(code)
            
            if not room:
                await websocket.send_text(json.dumps({
                    "type": "room_not_found",
                    "message": "Комната не найдена"
                }))
            elif room["status"] != "waiting":
                await websocket.send_text(json.dumps({
                    "type": "game_started",
                    "message": "Игра уже началась"
                }))
            else:
                max_players = room.get("max_players", 10)
                if len(room["players"]) >= max_players:
                    await websocket.send_text(json.dumps({
                        "type": "room_full",
                        "message": f"Комната заполнена (максимум {max_players} игроков)"
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "room_ok",
                        "message": "Можно входить"
                    }))
            
            await websocket.close()
        
    except WebSocketDisconnect:
        print(f"❌ Отключился: {user_type}/{identifier}")
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")

async def handle_organizer(websocket: WebSocket, code: str):
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            print(f"📨 Команда от организатора: {message}")
            
            room = room_manager.rooms.get(code)
            if not room:
                break
            
            elif message["action"] == "start_session":
                room_code = message["room_code"]
                room = room_manager.rooms.get(room_code)
                if room:
                    room["status"] = "active"
                    room["current_question_index"] = 0
                    # Отправляем первый вопрос
                    await send_current_question(room_code)
                    print(f"🚀 Сессия {room_code} запущена!")
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Комната не найдена"
                    }))
            
            elif message["action"] == "next_question":
                await send_current_question(code)
    
    except WebSocketDisconnect:
        if code in room_manager.rooms:
            del room_manager.rooms[code]
            print(f"🗑️ Комната {code} удалена")

async def send_current_question(code: str):
    room = room_manager.rooms.get(code)
    if not room or room["status"] != "active":
        return
    
    index = room["current_question_index"]
    quiz_id = room["quiz_id"]
    total = room["total_questions"]
    
    print(f"📤 send_current_question: комната {code}, индекс {index}, всего {total}")
    
    if index >= total:
        await finish_quiz(code)
        return
    
    db = SessionLocal()
    question = db.query(Question).filter(
        Question.quiz_id == quiz_id,
        Question.order_index == index
    ).first()
    
    if not question:
        print(f"❌ Вопрос {index} не найден")
        await finish_quiz(code)
        db.close()
        return
    
    # Время из вопроса или из квиза
    time_limit = question.time_limit_sec
    if not time_limit:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        time_limit = quiz.time_per_question_sec if quiz else 30
    
    options = db.query(AnswerOption).filter(
        AnswerOption.question_id == question.id
    ).order_by(AnswerOption.order_index).all()
    db.close()
    
    print(f"📤 Вопрос {index}: time_limit={time_limit}, options={len(options)}")
    
    question_data = {
        "type": "new_question",
        "question_id": question.id,
        "text": question.question_text,
        "image_url": question.image_url,
        "answer_mode": question.answer_mode,
        "points": question.points,
        "options": [
            {"id": opt.id, "text": opt.option_text}
            for opt in options
        ],
        "question_number": index + 1,
        "total_questions": total,
        "time_limit": time_limit,
        "timestamp": int(time.time() * 1000)
    }
    
    # Отправляем всем игрокам
    for player_ws in room["players"].keys():
        try:
            await player_ws.send_text(json.dumps(question_data))
        except Exception as e:
            print(f"❌ Ошибка отправки игроку: {e}")
    
    room["current_question_index"] += 1
    
    # Запускаем таймер на следующий вопрос (передаём ID вопроса)
    asyncio.create_task(wait_for_answers(code, time_limit, question.id))

async def wait_for_answers(code: str, delay: int, question_id: int):
    """Ждём ответы, потом сохраняем пропуски и переходим к следующему вопросу"""
    print(f"⏱️ wait_for_answers: комната {code}, вопрос {question_id}, задержка {delay} сек")
    await asyncio.sleep(delay)
    
    room = room_manager.rooms.get(code)
    if not room:
        print(f"❌ wait_for_answers: комната {code} не найдена после задержки")
        return
    
    if room["status"] != "active":
        print(f"❌ wait_for_answers: комната {code} уже не активна (статус {room['status']})")
        return
    
    print(f"📝 wait_for_answers: сохраняем пустые ответы для вопроса {question_id}")
    
    # Сохраняем пустые ответы для тех, кто не ответил
    for player_ws, player_data in room["players"].items():
        answered = any(a["question_id"] == question_id for a in player_data.get("answers", []))
        print(f"   Игрок {player_data['name']}: ответил на вопрос {question_id}? {answered}")
        
        if not answered:
            if "answers" not in player_data:
                player_data["answers"] = []
            
            player_data["answers"].append({
                "question_id": question_id,
                "selected_ids": [],
                "is_correct": False,
                "points": 0,
                "no_answer": True
            })
            print(f"   ⏰ {player_data['name']} не ответил на вопрос {question_id}, добавлен пустой ответ (теперь ответов={len(player_data['answers'])})")
    
    # Переходим к следующему вопросу
    print(f"📤 wait_for_answers: переходим к следующему вопросу в комнате {code}")
    await send_current_question(code)

async def send_leaderboard(code: str):
    room = room_manager.rooms.get(code)
    if not room:
        return
    
    # Сортировка: сначала по очкам (больше лучше), потом по времени (меньше лучше)
    leaderboard = sorted(
        [{
            "name": p["name"], 
            "score": p["score"],
            "total_time": p.get("total_time_ms", 0)
        } for p in room["players"].values()],
        key=lambda x: (-x["score"], x["total_time"])
    )

    debug_leaderboard = [
        {"name": p["name"], "score": p["score"], "time_ms": p["total_time"]} 
        for p in leaderboard
    ]
    
    leaderboard_data = {
        "type": "leaderboard_update",
        "leaderboard": debug_leaderboard
    }
    
    for player_ws in room["players"].keys():
        try:
            await player_ws.send_text(json.dumps(leaderboard_data))
        except:
            pass

async def finish_quiz(code: str):
    room = room_manager.rooms.get(code)
    if not room:
        print(f"❌ finish_quiz: комната {code} не найдена")
        return
    
    print(f"🏁 finish_quiz: комната {code}")
    print(f"   quiz_id: {room.get('quiz_id')}")
    print(f"   game_session_id: {room.get('game_session_id')}")
    print(f"   игроков: {len(room['players'])}")
    
    # Увеличиваем счётчик игр для квиза
    db = SessionLocal()
    try:
        quiz_id = room.get("quiz_id")
        if not quiz_id:
            print(f"   ❌ Нет quiz_id в комнате!")
        else:
            quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
            if quiz:
                old_count = quiz.play_count or 0
                quiz.play_count = old_count + 1
                db.commit()
                print(f"   ✅ Увеличен счётчик игр для квиза '{quiz.title}': {old_count} → {quiz.play_count}")
            else:
                print(f"   ❌ Квиз с id={quiz_id} не найден в БД!")
    except Exception as e:
        print(f"   ⚠️ Ошибка обновления счётчика: {e}")
        db.rollback()
    finally:
        db.close()
    
    leaderboard = sorted(
        [{
            "name": p["name"],
            "score": p["score"],
            "total_time": p.get("total_time_ms", 0)
        } for p in room["players"].values()],
        key=lambda x: (-x["score"], x["total_time"])
    )

    clean_leaderboard = [{"name": p["name"], "score": p["score"]} for p in leaderboard]
    
    result_data = {
        "type": "quiz_finished",
        "leaderboard": clean_leaderboard
    }
    
    # Отправляем результаты
    for player_ws in room["players"].keys():
        try:
            await player_ws.send_text(json.dumps(result_data))
        except Exception as e:
            print(f"   ⚠️ Ошибка отправки игроку: {e}")
    
    if room["organizer"]:
        try:
            await room["organizer"].send_text(json.dumps(result_data))
        except Exception as e:
            print(f"   ⚠️ Ошибка отправки организатору: {e}")
    
    # Сохраняем историю в БД
    db = SessionLocal()
    try:
        game_session_id = room.get("game_session_id")
        if not game_session_id:
            print(f"   ❌ Нет game_session_id в комнате!")
            db.close()
            room["status"] = "finished"
            return
        
        game_session = db.query(GameSession).filter(GameSession.id == game_session_id).first()
        if game_session:
            game_session.status = "finished"
            game_session.finished_at = datetime.utcnow()
            room["status"] = "finished"
            db.commit()
            print(f"   ✅ Обновлена сессия {game_session_id}")
        else:
            print(f"   ❌ Сессия {game_session_id} не найдена в БД")
        
        # Сохраняем ответы игроков
        answers_saved = 0
        for player_ws, player_data in room["players"].items():
            answers_list = player_data.get("answers", [])
            print(f"   Игрок {player_data['name']}: {len(answers_list)} ответов в памяти")
            
            for answer in answers_list:
                # Получаем текст вопроса
                db_temp = SessionLocal()
                question = db_temp.query(Question).filter(Question.id == answer["question_id"]).first()
                question_text = question.question_text if question else "Неизвестный вопрос"
                
                # Получаем текст ответа пользователя
                user_answer_text = ""
                if answer["selected_ids"]:
                    user_options = db_temp.query(AnswerOption).filter(AnswerOption.id.in_(answer["selected_ids"])).all()
                    user_answer_text = ", ".join([opt.option_text for opt in user_options])
                
                # Получаем текст правильного ответа
                correct_options = db_temp.query(AnswerOption).filter(
                    AnswerOption.question_id == answer["question_id"],
                    AnswerOption.is_correct == True
                ).all()
                correct_answer_text = ", ".join([opt.option_text for opt in correct_options])
                db_temp.close()
                
                player_answer = PlayerAnswer(
                    game_session_id=game_session_id,
                    user_id=player_data["user_id"],
                    question_text=question_text,
                    user_answer_text=user_answer_text,
                    correct_answer_text=correct_answer_text,
                    is_correct=answer["is_correct"],
                    points_awarded=answer["points"],
                    response_time_ms=answer.get("response_time_ms", 0)
                )
                db.add(player_answer)
                answers_saved += 1
        
        room["status"] = "finished"
        db.commit()
        print(f"   ✅ Статус сессии {game_session_id} изменён на finished в БД")
        print(f"   ✅ Сохранено ответов в БД: {answers_saved}")
        
    except Exception as e:
        print(f"   ❌ Ошибка сохранения: {e}")
        db.rollback()
    finally:
        db.close()
    
    room["status"] = "finished"
    print(f"🏁 Квиз в комнате {code} завершён!")

async def handle_player(websocket: WebSocket, code: str):
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["action"] == "answer":
                question_id = message["question_id"]
                selected_ids = message["selected_option_ids"]
                start_time = message.get("start_time")
                
                room = room_manager.rooms.get(code)
                if not room or websocket not in room["players"]:
                    continue
                
                # Инициализируем answered_questions если нет
                if "answered_questions" not in room["players"][websocket]:
                    room["players"][websocket]["answered_questions"] = []
                
                if question_id in room["players"][websocket]["answered_questions"]:
                    continue  # Пропускаем повторный ответ
                
                # Проверяем правильность
                db = SessionLocal()
                question = db.query(Question).filter(Question.id == question_id).first()
                correct_options = db.query(AnswerOption).filter(
                    AnswerOption.question_id == question_id,
                    AnswerOption.is_correct == True
                ).all()
                correct_ids = [opt.id for opt in correct_options]
                db.close()
                
                is_correct = set(selected_ids) == set(correct_ids)
                points = question.points if is_correct else 0
                
                # Вычисляем время ответа
                if start_time:
                    response_time_ms = int((time.time() * 1000) - start_time)
                else:
                    response_time_ms = 0
                
                # Начисляем баллы
                room["players"][websocket]["score"] += points
                
                # Запоминаем, что ответил на этот вопрос
                room["players"][websocket]["answered_questions"].append(question_id)
                
                # Сохраняем для истории
                if "answers" not in room["players"][websocket]:
                    room["players"][websocket]["answers"] = []
                room["players"][websocket]["answers"].append({
                    "question_id": question_id,
                    "selected_ids": selected_ids,
                    "is_correct": is_correct,
                    "points": points,
                    "response_time_ms": response_time_ms
                })
                
                # Обновляем общее время
                if "total_time_ms" not in room["players"][websocket]:
                    room["players"][websocket]["total_time_ms"] = 0
                room["players"][websocket]["total_time_ms"] += response_time_ms
                
                print(f"📊 {room['players'][websocket]['name']}: +{points} очков, всего: {room['players'][websocket]['score']}, время ответа: {response_time_ms} мс")
                
                await websocket.send_text(json.dumps({
                    "type": "answer_result",
                    "is_correct": is_correct,
                    "points_awarded": points,
                    "your_score": room["players"][websocket]["score"]
                }))
                
                await send_leaderboard(code)
                
    except WebSocketDisconnect:
        pass

async def save_missing_answers(code: str, question_id: int):
    """Сохраняет пустые ответы для игроков, которые не ответили на вопрос"""
    room = room_manager.rooms.get(code)
    if not room:
        print(f"❌ save_missing_answers: комната {code} не найдена")
        return
    
    print(f"📝 save_missing_answers: комната {code}, вопрос {question_id}, игроков: {len(room['players'])}")
    
    for player_ws, player_data in room["players"].items():
        answered = any(a["question_id"] == question_id for a in player_data.get("answers", []))
        print(f"   Игрок {player_data['name']}: answered={answered}, текущих ответов={len(player_data.get('answers', []))}")
        
        if not answered:
            if "answers" not in player_data:
                player_data["answers"] = []
            
            player_data["answers"].append({
                "question_id": question_id,
                "selected_ids": [],
                "is_correct": False,
                "points": 0,
                "no_answer": True
            })
            print(f"   ⏰ {player_data['name']} не ответил на вопрос {question_id}, добавлен пустой ответ (теперь ответов={len(player_data['answers'])})")