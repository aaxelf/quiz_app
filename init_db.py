from sqlalchemy import inspect

from app.database import engine, Base

def init_db():
    print("Удаляем старые таблицы...")
    Base.metadata.drop_all(bind=engine)
    
    print("Создаём новые таблицы...")
    Base.metadata.create_all(bind=engine)
    
    print("Таблицы успешно созданы!")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("\nСозданные таблицы:")
    for table in tables:
        print(f"   - {table}")

if __name__ == "__main__":
    init_db()