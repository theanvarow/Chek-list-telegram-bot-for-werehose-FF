import os
import pandas as pd
from datetime import datetime
import database

def generate_text_stats(lang: str = "ru") -> str:
    user_stats = database.get_stats_by_user()
    recent_checks = database.get_recent_reports(10)
    
    if lang == "uz":
        text = "📊 *Tozalik tekshiruvlari statistikasi*\n\n"
        
        text += "📋 *Oxirgi 10 ta tekshiruv logi:*\n"
        if not recent_checks:
            text += "_Tekshiruvlar topilmadi_\n"
        else:
            for item in recent_checks:
                time_formatted = item['created_at'][5:16] # e.g. "07-05 13:45"
                user_display = f"{item['inspector']} (@{item['telegram_username']})" if item['telegram_username'] else item['inspector']
                status_icon = "✅" if item['status'] == "Чисто" else "⚠️"
                
                text += f"📍 *{item['zone']}*\n"
                text += f"└ 👤 {user_display} | 📅 {time_formatted}\n"
                
                status_lbl = "Toza" if item['status'] == "Чисто" else "Kamchiliklar bor"
                text += f"└ Holat: *{status_lbl}* {status_icon}\n"
                
                if item['status'] != "Чисто":
                    issues = []
                    if item['has_empty_boxes']: issues.append("Bo'sh qutilar")
                    if item['has_goods_on_floor']: issues.append("Polda tovarlar")
                    if item['has_mess']: issues.append("Tartibsizlik")
                    text += f"   └ Kamchiliklar: _{', '.join(issues)}_\n"
                    
                if item['comment']:
                    text += f"   └ Izoh: _{item['comment']}_\n"
                text += "\n"
                
        text += "👤 *TOP xodimlar (tekshiruvlar soni):*\n"
        if not user_stats:
            text += "Ma'lumotlar yo'q\n"
        else:
            for idx, (fio, username, total, issues) in enumerate(user_stats[:5], 1):
                user_display = f"{fio} (@{username})" if username else fio
                text += f"{idx}. {user_display}: *{total}* ta (kamchiliklar: {issues})\n"
                
    else:
        text = "📊 *Статистика проверок чистоты*\n\n"
        
        text += "📋 *Журнал последних 10 проверок:*\n"
        if not recent_checks:
            text += "_Проверки не найдены_\n"
        else:
            for item in recent_checks:
                time_formatted = item['created_at'][5:16] # e.g. "07-05 13:45"
                user_display = f"{item['inspector']} (@{item['telegram_username']})" if item['telegram_username'] else item['inspector']
                status_icon = "✅" if item['status'] == "Чисто" else "⚠️"
                
                text += f"📍 *{item['zone']}*\n"
                text += f"└ 👤 {user_display} | 📅 {time_formatted}\n"
                
                status_lbl = "Чисто" if item['status'] == "Чисто" else "Есть замечания"
                text += f"└ Состояние: *{status_lbl}* {status_icon}\n"
                
                if item['status'] != "Чисто":
                    issues = []
                    if item['has_empty_boxes']: issues.append("Пустые коробки")
                    if item['has_goods_on_floor']: issues.append("Товары на полу")
                    if item['has_mess']: issues.append("Беспорядок")
                    text += f"   └ Замечания: _{', '.join(issues)}_\n"
                    
                if item['comment']:
                    text += f"   └ Коммент: _{item['comment']}_\n"
                text += "\n"
                
        text += "👤 *ТОП сотрудников по проверкам:*\n"
        if not user_stats:
            text += "Нет данных\n"
        else:
            for idx, (fio, username, total, issues) in enumerate(user_stats[:5], 1):
                user_display = f"{fio} (@{username})" if username else fio
                text += f"{idx}. {user_display}: *{total}* (с замечаниями: {issues})\n"
                
    return text




def generate_excel_report() -> str:
    rows, columns = database.get_all_reports_for_export()
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=columns)
    
    # Generate temporary file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"checklist_report_{timestamp}.xlsx"
    
    # Save using pandas/openpyxl
    # We can adjust column widths to make it beautiful
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
