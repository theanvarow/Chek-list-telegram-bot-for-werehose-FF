import os
import pandas as pd
from datetime import datetime, timedelta
import database

def escape_markdown(text: str) -> str:
    if not text:
        return ""
    escaped = str(text)
    escaped = escaped.replace("\\", "\\\\")
    for char in ['_', '*', '[', '`']:
        escaped = escaped.replace(char, f"\\{char}")
    return escaped

def get_date_info(date_key: str, lang: str = "ru"):
    now = datetime.now()
    d0 = now.date()
    d1 = d0 - timedelta(days=1)
    d2 = d0 - timedelta(days=2)
    d6 = d0 - timedelta(days=6)
    
    if date_key in ["all", "all_time"]:
        label = "📁 ВСЕ отчеты (В одном файле)"
        title = "За всё время"
        return {
            "key": "all",
            "date_from": None,
            "date_to": None,
            "all_time": True,
            "label": label,
            "title": title
        }
    
    if date_key.startswith("day:"):
        date_str = date_key.split("day:")[1]
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            date_from = f"{target_date.strftime('%Y-%m-%d')} 00:00:00"
            date_to = f"{target_date.strftime('%Y-%m-%d')} 23:59:59"
            label = f"{target_date.strftime('%d.%m.%Y')}"
            title = f"{target_date.strftime('%d.%m.%Y')}"
            return {
                "key": date_key,
                "date_from": date_from,
                "date_to": date_to,
                "label": label,
                "title": title
            }
        except Exception:
            pass

    if date_key == "yesterday":
        date_from = f"{d1.strftime('%Y-%m-%d')} 00:00:00"
        date_to = f"{d1.strftime('%Y-%m-%d')} 23:59:59"
        label = f"Вчера ({d1.strftime('%d.%m')})"
        title = f"{d1.strftime('%d.%m.%Y')}"
    elif date_key == "day_before":
        date_from = f"{d2.strftime('%Y-%m-%d')} 00:00:00"
        date_to = f"{d2.strftime('%Y-%m-%d')} 23:59:59"
        label = f"{d2.strftime('%d.%m')}"
        title = f"{d2.strftime('%d.%m.%Y')}"
    elif date_key == "3days":
        date_from = f"{d2.strftime('%Y-%m-%d')} 00:00:00"
        date_to = f"{d0.strftime('%Y-%m-%d')} 23:59:59"
        label = f"За последние 3 дня ({d2.strftime('%d.%m')}-{d0.strftime('%d.%m')})"
        title = f"{d2.strftime('%d.%m.%Y')} - {d0.strftime('%d.%m.%Y')}"
    elif date_key == "7days":
        date_from = f"{d6.strftime('%Y-%m-%d')} 00:00:00"
        date_to = f"{d0.strftime('%Y-%m-%d')} 23:59:59"
        label = f"За последние 7 дней ({d6.strftime('%d.%m')}-{d0.strftime('%d.%m')})"
        title = f"{d6.strftime('%d.%m.%Y')} - {d0.strftime('%d.%m.%Y')}"
    else:
        date_key = "today"
        date_from = f"{d0.strftime('%Y-%m-%d')} 00:00:00"
        date_to = f"{d0.strftime('%Y-%m-%d')} 23:59:59"
        label = f"Сегодня ({d0.strftime('%d.%m')})"
        title = f"{d0.strftime('%d.%m.%Y')}"
        
    return {
        "key": date_key,
        "date_from": date_from,
        "date_to": date_to,
        "label": label,
        "title": title
    }

def generate_text_stats(lang: str = "ru", date_from: str = None, date_to: str = None, date_title: str = None, all_time: bool = False) -> str:
    user_stats = database.get_stats_by_user(date_from, date_to, all_time=all_time)
    recent_checks = database.get_recent_reports(10, date_from, date_to, all_time=all_time)
    
    date_header = f" ({date_title})" if date_title else ""
    
    if not recent_checks and not user_stats:
        return f"📊 *Статистика проверок чистоты*{date_header}\n\n⚠️ *Нет данных об обходах.*"

    text = f"📊 *Статистика проверок чистоты*{date_header}\n\n"
    text += "📋 *Журнал проверок:*\n"
    if not recent_checks:
        text += "_Нет данных об обходах_\n\n"
    else:
        for item in recent_checks:
            time_formatted = item['created_at'][5:16] # e.g. "07-05 13:45"
            inspector_esc = escape_markdown(item['inspector'])
            username_esc = escape_markdown(item['telegram_username'])
            user_display = f"{inspector_esc} (@{username_esc})" if item['telegram_username'] else inspector_esc
            status_icon = "✅" if item['status'] == "Чисто" else "⚠️"
            
            zone_esc = escape_markdown(item['zone'])
            text += f"📍 *{zone_esc}*\n"
            text += f"└ 👤 {user_display} | 📅 {time_formatted}\n"
            
            status_lbl = "Чисто" if item['status'] == "Чисто" else "Есть замечания"
            text += f"└ Состояние: *{status_lbl}* {status_icon}\n"
            
            if item['status'] != "Чисто":
                issues = []
                if item.get('has_empty_boxes'): issues.append("Пустые коробки")
                if item.get('has_empty_pallets'): issues.append("Пустые поддоны")
                if item.get('has_goods_on_floor'): issues.append("Товары на полу")
                if item.get('has_damaged_goods'): issues.append("Брак товар")
                if item.get('has_empty_bags'): issues.append("Пустой пакет")
                if item.get('has_mess'): issues.append("Беспорядок")
                if issues:
                    text += f"   └ Замечания: _{', '.join(issues)}_\n"
                
            if item['comment']:
                comment_esc = escape_markdown(item['comment'])
                text += f"   └ Коммент: _{comment_esc}_\n"
            text += "\n"
            
    # Department Statistics Breakdown (First)
    otdel_stats = database.get_stats_by_otdel(date_from, date_to, all_time=all_time)
    if otdel_stats:
        text += "🏢 *Статистика обходов по отделам:*\n"
        for idx, (otdel_name, total, issues, active_users) in enumerate(otdel_stats, 1):
            medal = "🥇 " if idx == 1 else ("🥈 " if idx == 2 else ("🥉 " if idx == 3 else "▫️ "))
            otdel_esc = escape_markdown(otdel_name or "ОКЗ")
            text += f"{medal}*{otdel_esc}*: *{total}* обходов\n"
            
    return text


def generate_3hour_summary_stats() -> str:
    """
    Generates a concise cumulative department checklist ranking for today.
    """
    now = datetime.now()
    today_start = now.strftime("%Y-%m-%d 00:00:00")
    otdel_stats_today = database.get_stats_by_otdel(date_from=today_start)
    
    time_header = f"{now.strftime('%H:%M')} ({now.strftime('%d.%m.%Y')})"
    
    text = f"📊 <b>СВОДКА ОБХОДОВ ПО ОТДЕЛАМ ЗА СЕГОДНЯ</b>\n"
    text += f"🕒 <i>Время фиксации: {time_header}</i>\n\n"
    
    if not otdel_stats_today:
        text += "▫️ <i>За сегодня обходов пока не зафиксировано</i>\n"
    else:
        for idx, (otdel_name, total, issues, active_users) in enumerate(otdel_stats_today, 1):
            medal = "🥇 " if idx == 1 else ("🥈 " if idx == 2 else ("🥉 " if idx == 3 else "▫️ "))
            otdel_clean = otdel_name or "ОКЗ"
            text += f"{medal}<b>{otdel_clean}</b> — <b>{total}</b> обходов\n"
            
    return text



def generate_excel_report(date_from: str = None, date_to: str = None, all_time: bool = False) -> str:
    rows, columns = database.get_all_reports_for_export(date_from, date_to, all_time=all_time)
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=columns)
    
    # Generate temporary file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = "all_reports" if all_time else "checklist_report"
    filepath = f"{prefix}_{timestamp}.xlsx"
    
    # Save using pandas/openpyxl
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Отчеты по чистоте")
        
        # Access openpyxl workbook and worksheet to style it
        workbook = writer.book
        worksheet = writer.sheets["Отчеты по чистоте"]
        
        # Adjust columns width
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 10)
            
    return filepath

