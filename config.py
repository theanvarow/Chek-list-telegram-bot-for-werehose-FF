import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# SQLite Database filename
DB_NAME = os.getenv("DB_NAME", "checklist_bot.db")

# Directory to save uploaded photos
PHOTOS_DIR = os.getenv("PHOTOS_DIR", "photos")

# Target Telegram Group ID for reports
REPORT_GROUP_ID = int(os.getenv("REPORT_GROUP_ID", "-1003777301742"))

# Ensure photos directory exists
if not os.path.exists(PHOTOS_DIR):
    os.makedirs(PHOTOS_DIR)

# Checklist Zones
ZONES = [
    "1. Мезонин 1 этаж",
    "2. Мезонин 2 этаж",
    "3. Мезонин 3 этаж",
    "4. Мезонин 4 этаж",
    "5. Мезонин 5 этаж",
    "6. Ворота приёмки 1 - 8",
    "7. Зона буферов приёмки",
    "8. Столы пересчёта входящего потока",
    "9. Столы пересчёта возвратного потока",
    "10. Зона цпт",
    "11. Н , Ф зона",
    "12. Зона длиномеров",
    "13. Зона опт",
    "14. Зона опв",
    "15. Зона Сервис, ГОВП",
    "16. Сортировка 1,2",
    "17. Упаковка",
    "18. Потаварка",
    "19. Ромашка ( раскидка)",
    "20. Отгрузка",
    "21. Зона кошачки",
    "22. Зона палетного хранения"
]
