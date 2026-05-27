from typing import Dict, Set, Optional
import random
import string

class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, dict] = {}
    
    def generate_code(self) -> str:
        """Генерирует 6-значный код комнаты"""
        return ''.join(random.choices(string.digits, k=6))

room_manager = RoomManager()