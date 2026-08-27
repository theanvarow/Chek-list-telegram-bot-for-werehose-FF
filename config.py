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

# Departments (Отделы)
OTDELY = [
    "ОТД Входящий поток",
    "ОТД Возвратный поток",
    "ОКЗ",
    "РАО",
    "ГОВП",
    "СЕРВИС",
    "ЦПТ"
]

# Senior Shift Supervisors grouped by Department (Старшие смены по отделам)
# Easily edit or add names and telegram usernames for each department here
STARSHIY_SMENA = {
    "ОКЗ": [
        {"name": "ОКЗ (1-смена)", "username": "Kahramonn"},
        {"name": "ОКЗ (2-смена)", "username": "GGWP0704"},
        {"name": "ОКЗ (3-смена)", "username": "abdullaev4335"},
        {"name": "ОКЗ (4-смена)", "username": "NaaaRiman4IK"},
    ],
    "ОТД Входящий поток": [
        {
            "name": "ОТД Входящий (1-смена)",
            "username": "karimov_9944 @d_talipbayev @Sardor5559 @Suxrob29 @rakhimov_877",
            "members": [
                {"role": "Старший смены", "username": "karimov_9944"},
                {"role": "Вед. специалист", "username": "d_talipbayev"},
                {"role": "Вед. специалист", "username": "Sardor5559"},
                {"role": "Вед. специалист", "username": "Suxrob29"},
                {"role": "Наставник", "username": "rakhimov_877"},
            ]
        },
        {
            "name": "ОТД Входящий (2-смена)",
            "username": "KRamil9206 @ibrokhim_05_95 @Mishanya1986 @islom_900000",
            "members": [
                {"role": "Старший смены", "username": "KRamil9206"},
                {"role": "Вед. специалист", "username": "ibrokhim_05_95"},
                {"role": "Вед. специалист", "username": "Mishanya1986"},
                {"role": "Наставник", "username": "islom_900000"},
            ]
        },
        {
            "name": "ОТД Входящий (3-смена)",
            "username": "nizomiddin_uz @Ahmadjon022 @djurabek3010 @gulamov94 @mvrodd",
            "members": [
                {"role": "Старший смены", "username": "nizomiddin_uz"},
                {"role": "Вед. специалист", "username": "Ahmadjon022"},
                {"role": "Вед. специалист", "username": "djurabek3010"},
                {"role": "Наставник", "username": "gulamov94"},
                {"role": "Наставник", "username": "mvrodd"},
            ]
        },
        {
            "name": "ОТД Входящий (4-смена)",
            "username": "SaidkarimovDavid @OmarovaRailya @radmir_kushtanov @MuhammadKarim_0408 @otabek_0821",
            "members": [
                {"role": "Старший смены", "username": "SaidkarimovDavid"},
                {"role": "Вед. специалист", "username": "OmarovaRailya"},
                {"role": "Вед. специалист", "username": "radmir_kushtanov"},
                {"role": "Вед. специалист", "username": "MuhammadKarim_0408"},
                {"role": "Наставник", "username": "otabek_0821"},
            ]
        },
        {
            "name": "ОТД Межсклад (1-смена)",
            "username": "usss09",
            "members": [
                {"role": "Старший смены", "username": "usss09"}
            ]
        },
        {
            "name": "ОТД Межсклад (2-смена)",
            "username": "SodiqovShovkaT",
            "members": [
                {"role": "Старший смены", "username": "SodiqovShovkaT"}
            ]
        },
    ],
    "ОТД Возвратный поток": [
        {
            "name": "ОТД Возвратный (1-смена)",
            "username": "Sardor_998 @Lobar1288 @Ergashev5551",
            "members": [
                {"role": "Старший смены", "username": "Sardor_998"},
                {"role": "Вед. специалист", "username": "Lobar1288"},
                {"role": "Вед. специалист", "username": "Ergashev5551"},
            ]
        },
        {
            "name": "ОТД Возвратный (2-смена)",
            "username": "Sardor_998 @ArturXarisov @Azizbek5898",
            "members": [
                {"role": "Старший смены", "username": "Sardor_998"},
                {"role": "Вед. специалист", "username": "ArturXarisov"},
                {"role": "Вед. специалист", "username": "Azizbek5898"},
            ]
        },
        {
            "name": "ОТД Возвратный (3-смена)",
            "username": "Sardor_998 @Jakhhon @kar1movsss",
            "members": [
                {"role": "Старший смены", "username": "Sardor_998"},
                {"role": "Вед. специалист", "username": "Jakhhon"},
                {"role": "Вед. специалист", "username": "kar1movsss"},
            ]
        },
        {
            "name": "ОТД Возвратный (4-смена)",
            "username": "Sardor_998 @Sarvar8808 @SaidAxror1987",
            "members": [
                {"role": "Старший смены", "username": "Sardor_998"},
                {"role": "Вед. специалист", "username": "Sarvar8808"},
                {"role": "Вед. специалист", "username": "SaidAxror1987"},
            ]
        },
    ],
    "РАО": [
        {"name": "РАО (1-смена)", "username": None},
        {"name": "РАО (2-смена)", "username": None},
        {"name": "РАО (3-смена)", "username": None},
        {"name": "РАО (4-смена)", "username": None},
    ],
    "ГОВП": [
        {"name": "ГОВП (1-смена)", "username": None},
        {"name": "ГОВП (2-смена)", "username": None},
        {"name": "ГОВП (3-смена)", "username": None},
        {"name": "ГОВП (4-смена)", "username": None},
    ],
    "СЕРВИС": [
        {"name": "СЕРВИС (1-смена)", "username": None},
        {"name": "СЕРВИС (2-смена)", "username": None},
        {"name": "СЕРВИС (3-смена)", "username": None},
        {"name": "СЕРВИС (4-смена)", "username": None},
    ],
    "ЦПТ": [
        {"name": "ЦПТ (1-смена)", "username": "Life_93Uzum"},
    ],
}

