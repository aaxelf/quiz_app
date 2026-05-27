from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres@localhost:5432/data"
    
    class Config:
        env_file = ".env"

settings = Settings()