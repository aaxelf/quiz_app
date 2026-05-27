from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
from datetime import datetime
from pathlib import Path

router = APIRouter(prefix="/images", tags=["images"])

# Папка для хранения картинок
UPLOAD_DIR = Path("app/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):

    # Проверяем тип файла
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Можно загружать только изображения")
    
    # Генерируем уникальное имя
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_name
    
    # Сохраняем
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"url": f"/static/uploads/{safe_name}"}

@router.delete("/{filename}")
def delete_image(filename: str):
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        file_path.unlink()
        return {"message": "Изображение удалено"}
    raise HTTPException(404, "Изображение не найдено")