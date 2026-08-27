import asyncio
import os
from datetime import datetime
import database
import config
from bot import bot, send_single_report_to_group

async def main():
    database.init_db()
    today_start = datetime.now().strftime("%Y-%m-%d 00:00:00")
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, zone, status, has_empty_boxes, has_goods_on_floor, has_mess, comment, otdel, created_at
        FROM reports
        WHERE created_at >= ?
        ORDER BY created_at ASC
    """, (today_start,))
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} reports for today ({today_start[:10]}).")
    
    for row in rows:
        report_id, user_id, zone, status, boxes, floor, mess, comment, otdel, created_at = row
        user = database.get_user(user_id)
        fio = user['fio'] if user else "Неизвестный"
        username = user.get('username') if user else None
        
        # Get photos for this report
        cursor.execute("SELECT photo_path, telegram_file_id FROM report_photos WHERE report_id = ?", (report_id,))
        photo_rows = cursor.fetchall()
        photos = [(r[0], r[1]) for r in photo_rows]
        
        print(f"Resending Report #{report_id} | Zone: {zone} | Photos: {len(photos)} | Otdel: {otdel or 'ОКЗ'}")
        
        try:
            await send_single_report_to_group(
                bot=bot,
                group_id=config.REPORT_GROUP_ID,
                zone=zone,
                status=status,
                fio=fio,
                username=username,
                boxes=bool(boxes),
                floor=bool(floor),
                mess=bool(mess),
                comment=comment or "",
                photos=photos,
                report_id=report_id,
                otdel=otdel or "ОКЗ"
            )
            await asyncio.sleep(1.5)  # Pause to avoid Telegram rate limits
        except Exception as e:
            print(f"Failed to resend Report #{report_id}: {e}")

    conn.close()
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
