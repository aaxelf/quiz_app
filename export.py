import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

# Подключение к твоей БД (из твоего database.py)
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="data",
    user="postgres",
    password=""  # У тебя пустой пароль
)
cur = conn.cursor(cursor_factory=RealDictCursor)

# Получаем все квизы
cur.execute("SELECT * FROM quizzes;")
quizzes = cur.fetchall()

all_quizzes = []

for quiz in quizzes:
    print(f"Экспортируем: {quiz['title']}")
    
    # Вопросы
    cur.execute("SELECT * FROM questions WHERE quiz_id = %s ORDER BY order_index;", (quiz['id'],))
    questions = cur.fetchall()
    
    for q in questions:
        # Варианты ответов
        cur.execute("SELECT * FROM answer_options WHERE question_id = %s ORDER BY order_index;", (q['id'],))
        q['options'] = cur.fetchall()
    
    quiz['questions'] = questions
    all_quizzes.append(quiz)

# Сохраняем в JSON
with open("quizzes_backup.json", "w", encoding="utf-8") as f:
    json.dump(all_quizzes, f, ensure_ascii=False, indent=2, default=str)

print(f"\n✅ Экспортировано {len(all_quizzes)} квизов в файл quizzes_backup.json")
print(f"📁 Файл сохранён: {os.path.abspath('quizzes_backup.json')}")

cur.close()
conn.close()