from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, UserLogin
from app.auth import get_password_hash, verify_password

from app.routers import quizzes
from app.routers import users
from app.routers import websocket
from app.routers import history
from app.routers import images
from app.routers import password_reset
from app.routers import sessions

# Создаём экземпляр приложения
app = FastAPI(
    title="Quiz App",
    description="Платформа для интерактивных квизов",
    version="1.0.0"
)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для разработки разрешаем всё
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем шаблоны Jinja2
templates = Jinja2Templates(directory="app/templates")


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        display_name=user_data.display_name,
        password_hash=hashed_password,
        role=user_data.role.value
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/auth/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Вход в систему, возвращает user_id и role"""
    
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    return {
        "user_id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role
    }

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        return f.read()
    
@app.get("/organizer", response_class=HTMLResponse)
async def organizer():
    with open("app/templates/organizer.html", "r", encoding="utf-8") as f:
        return f.read()
    
@app.get("/quiz/create", response_class=HTMLResponse)
async def quiz_create():
    with open("app/templates/quiz_create.html", "r", encoding="utf-8") as f:
        return f.read()
    
@app.get("/quiz/{quiz_id}/edit", response_class=HTMLResponse)
async def quiz_edit(quiz_id: int):
    with open("app/templates/quiz_edit.html", "r", encoding="utf-8") as f:
        return f.read()
    
@app.get("/profile", response_class=HTMLResponse)
async def profile():
    with open("app/templates/profile.html", "r", encoding="utf-8") as f:
        return f.read()
    
@app.get("/recover", response_class=HTMLResponse)
async def recover():
    with open("app/templates/recover.html", "r", encoding="utf-8") as f:
        return f.read()
    
@app.get("/lobby", response_class=HTMLResponse)
async def lobby():
    with open("app/templates/lobby.html", "r", encoding="utf-8") as f:
        return f.read()
    
@app.get("/game", response_class=HTMLResponse)
async def game():
    with open("app/templates/game.html", "r", encoding="utf-8") as f:
        return f.read()
    
@app.get("/history", response_class=HTMLResponse)
async def history_page():
    with open("app/templates/history.html", "r", encoding="utf-8") as f:
        return f.read()
    
@app.get("/history/{session_id}", response_class=HTMLResponse)
async def history_detail(session_id: int):
    with open("app/templates/history_detail.html", "r", encoding="utf-8") as f:
        return f.read()

app.include_router(quizzes.router)
app.include_router(users.router)
app.include_router(websocket.router)
app.include_router(history.router)
app.include_router(images.router)
app.include_router(password_reset.router)
app.include_router(sessions.router)
