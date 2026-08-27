import sqlite3
from datetime import datetime
from config import DB_NAME

def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=15)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA cache_size=-64000;")  # 64MB memory cache
    return conn

def backup_db():
    """Creates a safe hot backup of the database into backups/ directory"""
    try:
        import os
        backups_dir = os.path.join(os.path.dirname(__file__), "backups")
        os.makedirs(backups_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        backup_file = os.path.join(backups_dir, f"checklist_bot_backup_{timestamp}.db")
        
        # Use sqlite3 online backup API for safe hot backup while WAL is active
        src = get_connection()
        dst = sqlite3.connect(backup_file)
        with dst:
            src.backup(dst)
        dst.close()
        src.close()
    except Exception as e:
        import logging
        logging.error(f"Failed to create database backup: {e}")

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

    # Ensure otdel column exists if database was created earlier
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN otdel TEXT DEFAULT 'ОКЗ'")
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
            otdel TEXT DEFAULT 'ОКЗ',
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)

    # Ensure otdel column in reports exists if table was created earlier
    try:
        cursor.execute("ALTER TABLE reports ADD COLUMN otdel TEXT DEFAULT 'ОКЗ'")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # New fields for issue responsible notification and fix status
    for col_def in [
        ("notified_user", "TEXT"),
        ("is_fixed", "INTEGER DEFAULT 0"),
        ("fixed_by", "TEXT"),
        ("fixed_at", "TIMESTAMP"),
        ("fix_photo_path", "TEXT"),
        ("fix_telegram_file_id", "TEXT"),
        ("fix_comment", "TEXT"),
        ("has_empty_pallets", "INTEGER DEFAULT 0"),
        ("has_damaged_goods", "INTEGER DEFAULT 0"),
        ("has_empty_bags", "INTEGER DEFAULT 0"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE reports ADD COLUMN {col_def[0]} {col_def[1]}")
            conn.commit()
        except sqlite3.OperationalError:
            pass
    
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
    
    # Create performance indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_zone_created ON reports(zone, created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_photos_report_id ON report_photos(report_id)")
    
    conn.commit()
    conn.close()
    
    # Perform initial backup
    backup_db()


def register_user(user_id: int, fio: str, username: str = None, lang: str = "ru", otdel: str = "ОКЗ"):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, fio, username, lang, otdel, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, fio, username, lang, otdel, now)
    )
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, fio, username, lang, created_at, otdel FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"user_id": row[0], "fio": row[1], "username": row[2], "lang": row[3], "created_at": row[4], "otdel": row[5] or "ОКЗ"}
    return None

def get_all_users() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, fio, username, lang, created_at, otdel FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [{"user_id": r[0], "fio": r[1], "username": r[2], "lang": r[3], "created_at": r[4], "otdel": r[5] or "ОКЗ"} for r in rows]


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

def update_user_otdel(user_id: int, otdel: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET otdel = ? WHERE user_id = ?", (otdel, user_id))
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
    has_empty_boxes: bool = False,
    has_goods_on_floor: bool = False,
    has_mess: bool = False,
    comment: str = "",
    photos: list = None,
    otdel: str = None,
    notified_user: str = None,
    has_empty_pallets: bool = False,
    has_damaged_goods: bool = False,
    has_empty_bags: bool = False,
) -> int:
    if photos is None:
        photos = []
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        """
        INSERT INTO reports (
            user_id, zone, status, has_empty_boxes, has_goods_on_floor, has_mess, comment, otdel, created_at, notified_user,
            has_empty_pallets, has_damaged_goods, has_empty_bags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            zone,
            status,
            1 if has_empty_boxes else 0,
            1 if has_goods_on_floor else 0,
            1 if has_mess else 0,
            comment,
            otdel,
            now,
            notified_user,
            1 if has_empty_pallets else 0,
            1 if has_damaged_goods else 0,
            1 if has_empty_bags else 0
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
    
    # Auto-backup db on new report
    try:
        backup_db()
    except Exception:
        pass
        
    return report_id


def mark_report_fixed(
    report_id: int,
    fixed_by: str,
    fix_photo_path: str = None,
    fix_telegram_file_id: str = None,
    fix_comment: str = ""
) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        """
        UPDATE reports
        SET is_fixed = 1,
            fixed_by = ?,
            fixed_at = ?,
            fix_photo_path = ?,
            fix_telegram_file_id = ?,
            fix_comment = ?
        WHERE id = ?
        """,
        (fixed_by, now, fix_photo_path, fix_telegram_file_id, fix_comment, report_id)
    )
    conn.commit()
    conn.close()
    return True


def get_report_by_id(report_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT r.id, r.user_id, r.zone, r.status, r.has_empty_boxes, r.has_goods_on_floor, r.has_mess,
               r.comment, r.otdel, r.created_at, r.notified_user, r.is_fixed, r.fixed_by, r.fixed_at,
               r.fix_photo_path, r.fix_telegram_file_id, r.fix_comment, u.fio, u.username,
               r.has_empty_pallets, r.has_damaged_goods, r.has_empty_bags
        FROM reports r
        LEFT JOIN users u ON r.user_id = u.user_id
        WHERE r.id = ?
        """,
        (report_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "user_id": row[1],
            "zone": row[2],
            "status": row[3],
            "has_empty_boxes": bool(row[4]),
            "has_goods_on_floor": bool(row[5]),
            "has_mess": bool(row[6]),
            "comment": row[7],
            "otdel": row[8],
            "created_at": row[9],
            "notified_user": row[10],
            "is_fixed": bool(row[11]),
            "fixed_by": row[12],
            "fixed_at": row[13],
            "fix_photo_path": row[14],
            "fix_telegram_file_id": row[15],
            "fix_comment": row[16],
            "inspector": row[17] or "Неизвестный",
            "telegram_username": row[18],
            "has_empty_pallets": bool(row[19] if len(row) > 19 else 0),
            "has_damaged_goods": bool(row[20] if len(row) > 20 else 0),
            "has_empty_bags": bool(row[21] if len(row) > 21 else 0)
        }
    return None



def get_stats_by_user(date_from: str = None, date_to: str = None, all_time: bool = False):
    conn = get_connection()
    cursor = conn.cursor()
    if all_time:
        cursor.execute("""
            SELECT u.fio, u.username, COUNT(r.id) as total_checks,
                   SUM(CASE WHEN r.status = 'Есть замечания' THEN 1 ELSE 0 END) as with_issues
            FROM users u
            JOIN reports r ON u.user_id = r.user_id
            GROUP BY u.user_id, u.fio, u.username
            HAVING total_checks > 0
            ORDER BY total_checks DESC
        """)
    elif date_from and date_to:
        cursor.execute("""
            SELECT u.fio, u.username, COUNT(r.id) as total_checks,
                   SUM(CASE WHEN r.status = 'Есть замечания' THEN 1 ELSE 0 END) as with_issues
            FROM users u
            LEFT JOIN reports r ON u.user_id = r.user_id AND r.created_at >= ? AND r.created_at <= ?
            GROUP BY u.user_id, u.fio, u.username
            HAVING total_checks > 0
            ORDER BY total_checks DESC
        """, (date_from, date_to))
    else:
        if not date_from:
            date_from = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
        cursor.execute("""
            SELECT u.fio, u.username, COUNT(r.id) as total_checks,
                   SUM(CASE WHEN r.status = 'Есть замечания' THEN 1 ELSE 0 END) as with_issues
            FROM users u
            LEFT JOIN reports r ON u.user_id = r.user_id AND r.created_at >= ?
            GROUP BY u.user_id, u.fio, u.username
            HAVING total_checks > 0
            ORDER BY total_checks DESC
        """, (date_from,))
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

def get_all_reports_for_export(date_from: str = None, date_to: str = None, all_time: bool = False):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            r.id,
            r.created_at,
            u.fio as inspector,
            u.username as telegram_username,
            r.otdel as otdel,
            r.zone,
            r.status,
            CASE WHEN r.has_empty_boxes = 1 THEN 'Да' ELSE 'Нет' END as empty_boxes,
            CASE WHEN r.has_empty_pallets = 1 THEN 'Да' ELSE 'Нет' END as empty_pallets,
            CASE WHEN r.has_goods_on_floor = 1 THEN 'Да' ELSE 'Нет' END as goods_on_floor,
            CASE WHEN r.has_damaged_goods = 1 THEN 'Да' ELSE 'Нет' END as damaged_goods,
            CASE WHEN r.has_empty_bags = 1 THEN 'Да' ELSE 'Нет' END as empty_bags,
            CASE WHEN r.has_mess = 1 THEN 'Да' ELSE 'Нет' END as mess,
            r.comment,
            (SELECT GROUP_CONCAT(photo_path, '; ') FROM report_photos WHERE report_id = r.id) as photo_paths
        FROM reports r
        JOIN users u ON r.user_id = u.user_id
    """
    params = []
    where_clauses = []
    
    if not all_time:
        if date_from:
            where_clauses.append("r.created_at >= ?")
            params.append(date_from)
        else:
            default_date_from = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
            where_clauses.append("r.created_at >= ?")
            params.append(default_date_from)
            
        if date_to:
            where_clauses.append("r.created_at <= ?")
            params.append(date_to)
            
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
        
    query += " ORDER BY r.created_at DESC"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    columns = [
        "ID отчета", "Дата и время", "Проверяющий (ФИО)", "Telegram username", "Отдел", "Зона / Этаж", 
        "Статус", "Пустые коробки", "Пустые поддоны", "Товары на полу", "Брак товар", "Пустой пакет", "Беспорядок", 
        "Комментарий", "Пути к фото"
    ]
    conn.close()
    return rows, columns




def get_latest_report_for_zone(zone_name: str, today_only: bool = True):
    conn = get_connection()
    cursor = conn.cursor()
    if today_only:
        today_start = datetime.now().strftime("%Y-%m-%d 00:00:00")
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
        """, (zone_name, today_start))
    else:
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
            WHERE r.zone = ?
            ORDER BY r.created_at DESC
            LIMIT 1
        """, (zone_name,))
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
        "photos": photos,
        "has_empty_pallets": bool(report_row[9] if len(report_row) > 9 else 0),
        "has_damaged_goods": bool(report_row[10] if len(report_row) > 10 else 0),
        "has_empty_bags": bool(report_row[11] if len(report_row) > 11 else 0)
    }


def get_checked_zones_today() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
    cursor.execute("SELECT DISTINCT zone FROM reports WHERE created_at >= ?", (today_str,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_zone_statuses_today() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
    cursor.execute("""
        SELECT zone, status
        FROM reports
        WHERE created_at >= ?
        ORDER BY created_at ASC
    """, (today_str,))
    rows = cursor.fetchall()
    conn.close()
    
    zone_statuses = {}
    for zone, status in rows:
        zone_statuses[zone] = status
    return zone_statuses

def get_zone_statuses_for_user(user_id: int, hours: int = 3) -> dict:
    from datetime import timedelta
    conn = get_connection()
    cursor = conn.cursor()
    cutoff_str = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        SELECT zone, status
        FROM reports
        WHERE user_id = ? AND created_at >= ?
        ORDER BY created_at ASC
    """, (user_id, cutoff_str))
    rows = cursor.fetchall()
    conn.close()
    
    zone_statuses = {}
    for zone, status in rows:
        zone_statuses[zone] = status
    return zone_statuses

def get_photos_for_date_range(date_from: str = None, date_to: str = None, all_time: bool = False) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    if all_time:
        cursor.execute("""
            SELECT rp.telegram_file_id, r.zone, r.status
            FROM report_photos rp
            JOIN reports r ON rp.report_id = r.id
            ORDER BY r.created_at ASC
        """)
    elif date_from and date_to:
        cursor.execute("""
            SELECT rp.telegram_file_id, r.zone, r.status
            FROM report_photos rp
            JOIN reports r ON rp.report_id = r.id
            WHERE r.created_at >= ? AND r.created_at <= ?
            ORDER BY r.created_at ASC
        """, (date_from, date_to))
    elif date_from:
        cursor.execute("""
            SELECT rp.telegram_file_id, r.zone, r.status
            FROM report_photos rp
            JOIN reports r ON rp.report_id = r.id
            WHERE r.created_at >= ?
            ORDER BY r.created_at ASC
        """, (date_from,))
    else:
        conn.close()
        return []
    rows = cursor.fetchall()
    conn.close()
    return [{"file_id": r[0], "zone": r[1], "status": r[2]} for r in rows]

def get_recent_reports(limit: int = 10, date_from: str = None, date_to: str = None, all_time: bool = False) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
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
            r.comment,
            r.has_empty_pallets,
            r.has_damaged_goods,
            r.has_empty_bags
        FROM reports r
        JOIN users u ON r.user_id = u.user_id
    """
    params = []
    where_clauses = []
    
    if not all_time:
        if not date_from:
            date_from = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
        where_clauses.append("r.created_at >= ?")
        params.append(date_from)
        
        if date_to:
            where_clauses.append("r.created_at <= ?")
            params.append(date_to)
            
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
        
    query += " ORDER BY r.created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, tuple(params))
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
            "comment": row[9],
            "has_empty_pallets": bool(row[10] if len(row) > 10 else 0),
            "has_damaged_goods": bool(row[11] if len(row) > 11 else 0),
            "has_empty_bags": bool(row[12] if len(row) > 12 else 0)
        })
    return reports


def get_reports_for_summary(date_from: str = None, date_to: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    if not date_from:
        date_from = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
        
    query = """
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
            r.comment,
            r.has_empty_pallets,
            r.has_damaged_goods,
            r.has_empty_bags
        FROM reports r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.created_at >= ?
    """
    params = [date_from]
    if date_to:
        query += " AND r.created_at <= ?"
        params.append(date_to)
        
    query += " ORDER BY r.created_at ASC"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    
    reports = []
    for row in rows:
        report_id = row[0]
        cursor.execute("SELECT telegram_file_id FROM report_photos WHERE report_id = ?", (report_id,))
        p_rows = cursor.fetchall()
        photos = [pr[0] for pr in p_rows if pr[0]]
        
        reports.append({
            'id': row[0],
            'created_at': row[1],
            'inspector': row[2],
            'telegram_username': row[3],
            'zone': row[4],
            'status': row[5],
            'has_empty_boxes': bool(row[6]),
            'has_goods_on_floor': bool(row[7]),
            'has_mess': bool(row[8]),
            'comment': row[9],
            'photos': photos,
            'has_empty_pallets': bool(row[10] if len(row) > 10 else 0),
            'has_damaged_goods': bool(row[11] if len(row) > 11 else 0),
            'has_empty_bags': bool(row[12] if len(row) > 12 else 0)
        })
        
    conn.close()
    return reports



