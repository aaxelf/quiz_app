from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Index, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="player")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    quizzes_created = relationship("Quiz", back_populates="organizer", cascade="all, delete-orphan")
    game_sessions = relationship("SessionPlayer", back_populates="user")
    answers = relationship("PlayerAnswer", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("idx_sessions_user_id", "user_id"),
        Index("idx_sessions_expires_at", "expires_at"),
    )


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    organizer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    max_players = Column(Integer, default=10)
    time_per_question_sec = Column(Integer, nullable=False, default=30)
    play_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    organizer = relationship("User", back_populates="quizzes_created")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_quizzes_category", "category"),
    )


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    image_url = Column(String)
    answer_mode = Column(String, nullable=False)   # single, multiple
    points = Column(Integer, nullable=False, default=100)
    time_limit_sec = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    quiz = relationship("Quiz", back_populates="questions")
    options = relationship("AnswerOption", back_populates="question", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_questions_order", "quiz_id", "order_index"),
    )


class AnswerOption(Base):
    __tablename__ = "answer_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    option_text = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False, default=False)
    order_index = Column(Integer, nullable=False)

    question = relationship("Question", back_populates="options")


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, nullable=True)
    quiz_title = Column(String, nullable=True)
    total_questions = Column(Integer, default=0)
    room_code = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, default="waiting")
    current_question_index = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    players = relationship("SessionPlayer", back_populates="game_session", cascade="all, delete-orphan")
    answers = relationship("PlayerAnswer", back_populates="game_session")

    __table_args__ = (
        Index("idx_game_sessions_status", "status"),
    )


class SessionPlayer(Base):
    __tablename__ = "session_players"

    id = Column(Integer, primary_key=True, index=True)
    game_session_id = Column(Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=False, default=0)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    game_session = relationship("GameSession", back_populates="players")
    user = relationship("User", back_populates="game_sessions")

    __table_args__ = (
        Index("idx_session_players_score", "game_session_id", "score"),
    )


class PlayerAnswer(Base):
    __tablename__ = "player_answers"

    id = Column(Integer, primary_key=True, index=True)
    game_session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    question_text = Column(Text, nullable=False)
    user_answer_text = Column(Text, nullable=True)
    correct_answer_text = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=False)
    points_awarded = Column(Integer, default=0)
    response_time_ms = Column(Integer)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    game_session = relationship("GameSession", back_populates="answers")
    user = relationship("User", back_populates="answers")