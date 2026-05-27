from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    PLAYER = "player"
    ORGANIZER = "organizer"

class AnswerMode(str, Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"

class GameSessionStatus(str, Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    FINISHED = "finished"

# ========== ПОЛЬЗОВАТЕЛИ ==========

class UserBase(BaseModel):
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.PLAYER

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=72)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 

class UserInDB(UserResponse):
    password_hash: str


# ========== ВАРИАНТЫ ОТВЕТОВ ==========

class AnswerOptionBase(BaseModel):
    option_text: str
    is_correct: bool = False
    order_index: int

class AnswerOptionCreate(AnswerOptionBase):
    id: Optional[int] = None

class AnswerOptionResponse(AnswerOptionBase):
    id: int
    question_id: int

    class Config:
        from_attributes = True


# ========== ВОПРОСЫ ==========

class QuestionBase(BaseModel):
    order_index: int
    question_text: str
    image_url: Optional[str] = None
    answer_mode: AnswerMode
    points: int = Field(default=100, ge=1)
    time_limit_sec: Optional[int] = Field(default=None, ge=5)
    max_players: int = Field(default=10, ge=1, le=100)

class QuestionCreate(QuestionBase):
    id: Optional[int] = None
    options: List[AnswerOptionCreate]  # варианты ответов при создании

class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    image_url: Optional[str] = None
    points: Optional[int] = Field(None, ge=1)
    time_limit_sec: Optional[int] = Field(None, ge=5)

class QuestionResponse(QuestionBase):
    id: int
    quiz_id: int
    created_at: datetime
    options: List[AnswerOptionResponse] = []

    class Config:
        from_attributes = True


# ========== КВИЗЫ ==========

class QuizBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    time_per_question_sec: int = Field(default=30, ge=5, le=300)
    max_players: int = Field(default=10, ge=1, le=100)

class QuizCreate(QuizBase):
    organizer_id: int
    max_players: int = Field(default=10, ge=1, le=100)
    questions: List[QuestionCreate]  # вопросы при создании

class QuizUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    time_per_question_sec: Optional[int] = Field(None, ge=5, le=300)

class QuizResponse(QuizBase):
    id: int
    organizer_id: int
    play_count: int
    created_at: datetime
    updated_at: datetime
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True

class QuizListItem(BaseModel):
    id: int
    title: str
    category: Optional[str]
    play_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ========== ИГРОВЫЕ СЕССИИ (КОМНАТЫ) ==========

class GameSessionCreate(BaseModel):
    quiz_id: int

class GameSessionResponse(BaseModel):
    id: int
    quiz_id: int
    room_code: str
    status: GameSessionStatus
    current_question_index: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class JoinGameRequest(BaseModel):
    room_code: str


# ========== УЧАСТНИКИ СЕССИИ ==========

class SessionPlayerResponse(BaseModel):
    id: int
    user_id: int
    display_name: str  # из users
    score: int
    joined_at: datetime

    class Config:
        from_attributes = True


# ========== ОТВЕТЫ УЧАСТНИКОВ ==========

class PlayerAnswerSubmit(BaseModel):
    question_id: int
    selected_option_ids: List[int]

class PlayerAnswerResponse(BaseModel):
    id: int
    user_id: int
    question_id: int
    selected_option_ids: List[int]
    is_correct: bool
    points_awarded: int
    response_time_ms: Optional[int]
    answered_at: datetime

    class Config:
        from_attributes = True


# ========== ЛИДЕРБОРД ==========

class LeaderboardEntry(BaseModel):
    user_id: int
    display_name: str
    score: int

class LeaderboardResponse(BaseModel):
    session_id: int
    leaderboard: List[LeaderboardEntry]


# ========== ВЕБСОКЕТ СООБЩЕНИЯ ==========

class WSMessage(BaseModel):
    type: str  # new_question, answer_result, leaderboard_update, quiz_ended
    data: dict