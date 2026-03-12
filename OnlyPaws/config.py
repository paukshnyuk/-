import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "admin123")

# База данных
DB_NAME = os.getenv("DB_NAME", "OnlyPaws")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123")
DB_HOST = os.getenv("DB_HOST", "localhost")

# Списки
CATS_BREEDS = ["Мейн-кун", "Сфинкс", "Рэгдолл", "Персидская", "Сиамская", "Британская", "Дворняга", "Шотландская", "Бенгальская", "Абиссинская"]
CATS_COLORS = ["Чёрный", "Белый", "Серый", "Рыжий", "Коричневый", "Черепаховый", "Пятнистый", "Кремовый"]
CATS_EYES = ["Голубые", "Чёрные", "Карие", "Зелёные", "Жёлтые", "Гетерохромия"]
CATS_AGES = ["Котёнок (<1 года)", "Молодой (1-3 года)", "Взрослый (3-10 лет)", "Мудрый (10+ лет)"]
