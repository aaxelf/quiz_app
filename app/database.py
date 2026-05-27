from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# параметры подключения к postgresql
DB_USER = "postgres"
DB_PASSWORD = ""
DB_HOST = "localhost" 
DB_PORT = "5432"
DB_NAME = "data"

# формирование url бд (по нему sqlalchemy находит бд)
if DB_PASSWORD:
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# создаём движок (управляет подключениями к бд)
engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # сколько соединений держать открытыми
    max_overflow=20,  # сколько дополнительных соединений при нагрузке
    echo=False
)

# фабрика сессий (через сессии делаем запросы к бд)
SessionLocal = sessionmaker(
    autocommit=False,  # изменения фиксируются только явным commit()
    autoflush=False,  # не отправляем запросы до явного flush() (для большего контроля)
    bind=engine
)

# базовый класс для моделей
Base = declarative_base()

# ф-ия для получения сессии (создаёт сессию и сама закрывает после завершения запроса)
def get_db():
    db = SessionLocal()  # открывает соединение
    try:
        yield db  # передаём его в эндпоинт
    finally:
        db.close()