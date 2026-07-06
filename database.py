import sqlite3
from datetime import datetime
from config import DB_NAME

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            fio TEXT NOT NULL,
            username TEXT,
            lang TEXT DEFAULT 'ru',
            created_at TIMESTAMP NOT NULL
        )
    """)
    
    # Ensure lang column exists if database was created earlier
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT 'ru'")
        conn.commit()
    except sqlite3.OperationalError:
        pass
        
    # Ensure username column exists if database was created earlier
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    # Create reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            zone TEXT NOT NULL,
            status TEXT NOT NULL,
            has_empty_boxes INTEGER NOT NULL DEFAULT 0,
            has_goods_on_floor INTEGER NOT NULL DEFAULT 0,
            has_mess INTEGER NOT NULL DEFAULT 0,
            comment TEXT,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # Create report_photos table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            photo_path TEXT NOT NULL,
            telegram_file_id TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (report_id) REFERENCES reports (id)
        )
    """)
    
    conn.commit()
    conn.close()

def register_user(user_id: int, fio: str, username: str = None, lang: str = "ru"):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, fio, username, lang, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, fio, username, lang, now)
    )
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, fio, username, lang, created_at FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"user_id": row[0], "fio": row[1], "username": row[2], "lang": row[3], "created_at": row[4]}
    return None


def update_user_lang(user_id: int, lang: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

def update_user_username(user_id: int, username: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
    conn.commit()
    conn.close()


def get_user_lang(user_id: int) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return row[0]
    return "ru"


def save_report(
    user_id: int,
    zone: str,
    status: str,
    has_empty_boxes: bool,
    has_goods_on_floor: bool,
    has_mess: bool,
    comment: str,
    photos: list # list of tuples: (photo_path, telegram_file_id)
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        """
        INSERT INTO reports (
            user_id, zone, status, has_empty_boxes, has_goods_on_floor, has_mess, comment, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            zone,
            status,
            1 if has_empty_boxes else 0,
            1 if has_goods_on_floor else 0,
            1 if has_mess else 0,
            comment,
            now
        )
    )
    report_id = cursor.lastrowid
    
    for photo_path, file_id in photos:
        cursor.execute(
            """
            INSERT INTO report_photos (report_id, photo_path, telegram_file_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (report_id, photo_path, file_id, now)
        )
        
    conn.commit()
    conn.close()
    return report_id

def get_stats_by_user():
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
    cursor.execute("""
        SELECT u.fio, u.username, COUNT(r.id) as total_checks,
               SUM(CASE WHEN r.status = 'Есть замечания' THEN 1 ELSE 0 END) as with_issues
        FROM users u
        LEFT JOIN reports r ON u.user_id = r.user_id AND r.created_at >= ?
        GROUP BY u.user_id, u.fio, u.username
        HAVING total_checks > 0
        ORDER BY total_checks DESC
    """, (today_str,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_stats_by_zone():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT zone, COUNT(id) as total_checks,
               SUM(CASE WHEN status = 'Чисто' THEN 1 ELSE 0 END) as clean_checks,
               SUM(CASE WHEN status = 'Есть замечания' THEN 1 ELSE 0 END) as issue_checks
        FROM reports
        GROUP BY zone
        ORDER BY total_checks DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_reports_for_export():
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
    cursor.execute("""
        SELECT 
            r.id,
            r.created_at,
            u.fio as inspector,
            u.username as telegram_username,
            r.zone,
            r.status,
            CASE WHEN r.has_empty_boxes = 1 THEN 'Да' ELSE 'Нет' END as empty_boxes,
            CASE WHEN r.has_goods_on_floor = 1 THEN 'Да' ELSE 'Нет' END as goods_on_floor,
            CASE WHEN r.has_mess = 1 THEN 'Да' ELSE 'Нет' END as mess,
            r.comment,
            (SELECT GROUP_CONCAT(photo_path, '; ') FROM report_photos WHERE report_id = r.id) as photo_paths
        FROM reports r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.created_at >= ?
        ORDER BY r.created_at DESC
    """, (today_str,))
    rows = cursor.fetchall()
    columns = [
        "ID отчета", "Дата и время", "Проверяющий (ФИО)", "Telegram username", "Зона / Этаж", 
        "Статус", "Пустые коробки", "Товары на полу", "Беспорядок", 
        "Комментарий", "Пути к фото"
    ]
    conn.close()
    return rows, columns


def get_latest_report_for_zone(zone_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
    cursor.execute("""
        SELECT 
            r.id,
            r.created_at,
            u.fio as inspector,
            u.username as telegram_username,
            r.status,
            r.has_empty_boxes,
            r.has_goods_on_floor,
            r.has_mess,
            r.comment
        FROM reports r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.zone = ? AND r.created_at >= ?
        ORDER BY r.created_at DESC
        LIMIT 1
    """, (zone_name, today_str))
    report_row = cursor.fetchone()
    
    if not report_row:
        conn.close()
        return None
        
    report_id = report_row[0]
    
    # Get photos
    cursor.execute("""
        SELECT telegram_file_id FROM report_photos
        WHERE report_id = ?
    """, (report_id,))
    photo_rows = cursor.fetchall()
    photos = [row[0] for row in photo_rows]
    
    conn.close()
    
    return {
        "id": report_id,
        "created_at": report_row[1],
        "inspector": report_row[2],
        "telegram_username": report_row[3],
        "status": report_row[4],
        "has_empty_boxes": bool(report_row[5]),
        "has_goods_on_floor": bool(report_row[6]),
        "has_mess": bool(report_row[7]),
        "comment": report_row[8],
        "photos": photos
    }


def get_checked_zones_today() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
    cursor.execute("SELECT DISTINCT zone FROM reports WHERE created_at >= ?", (today_str,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_recent_reports(limit: int = 10) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
    cursor.execute("""
        SELECT 
            r.id,
            r.created_at,
            u.fio as inspector,
            u.username as telegram_username,
            r.zone,
            r.status,
            r.has_empty_boxes,
            r.has_goods_on_floor,
            r.has_mess,
            r.comment
        FROM reports r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.created_at >= ?
        ORDER BY r.created_at DESC
        LIMIT ?
    """, (today_str, limit))
    rows = cursor.fetchall()
    conn.close()
    
    reports = []
    for row in rows:
        reports.append({
            "id": row[0],
            "created_at": row[1],
            "inspector": row[2],
            "telegram_username": row[3],
            "zone": row[4],
            "status": row[5],
            "has_empty_boxes": bool(row[6]),
            "has_goods_on_floor": bool(row[7]),
            "has_mess": bool(row[8]),
            "comment": row[9]
        })
    return reports



