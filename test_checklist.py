import os
import shutil
import database
import statistics

def test_database_and_stats():
    print("Initializing Database...")
    database.init_db()
    
    print("Registering mock user...")
    user_id = 999999
    fio = "Тестовый Пользователь Отдела Контроля"
    database.register_user(user_id, fio, "test_username")
    
    user = database.get_user(user_id)
    assert user is not None, "Failed to get registered user!"
    assert user["fio"] == fio, f"FIO mismatch! Expected '{fio}', got '{user['fio']}'"
    assert user["username"] == "test_username", f"Username mismatch! Expected 'test_username', got '{user['username']}'"
    print(f"User retrieved successfully: {user}")
    
    print("Saving test report with issues...")
    photos = [("photos/test_photo1.jpg", "file_id_12345"), ("photos/test_photo2.jpg", "file_id_67890")]
    report_id = database.save_report(
        user_id=user_id,
        zone="1. Мезонин 1 этаж",
        status="Есть замечания",
        has_empty_boxes=True,
        has_goods_on_floor=False,
        has_mess=True,
        comment="Обнаружены пустые коробки под стеллажом и общий беспорядок",
        photos=photos
    )
    print(f"Report saved. Generated Report ID: {report_id}")
    
    print("Saving test report without issues...")
    report_id2 = database.save_report(
        user_id=user_id,
        zone="6. Ворота приёмки 1 - 8",
        status="Чисто",
        has_empty_boxes=False,
        has_goods_on_floor=False,
        has_mess=False,
        comment="Чисто, замечаний нет",
        photos=[]
    )
    print(f"Report saved. Generated Report ID: {report_id2}")
    
    print("\nRetrieving textual statistics:")
    text_stats = statistics.generate_text_stats()
    print("-" * 40)
    print(text_stats)
    print("-" * 40)
    
    print("\nTesting 3-day date info helper...")
    info_today = statistics.get_date_info("today", "uz")
    info_yesterday = statistics.get_date_info("yesterday", "uz")
    info_day_before = statistics.get_date_info("day_before", "uz")
    info_3days = statistics.get_date_info("3days", "uz")
    print(f"Today info: {info_today}")
    print(f"3-days info: {info_3days}")
    assert info_3days["key"] == "3days"
    
    stats_3days = statistics.generate_text_stats(lang="uz", date_from=info_3days["date_from"], date_to=info_3days["date_to"], date_title=info_3days["title"])
    assert "Tozalik tekshiruvlari statistikasi" in stats_3days
    print(f"3-day statistics output:\n{stats_3days}")

    print("\nGenerating Excel report for 3 days...")
    excel_path = statistics.generate_excel_report(date_from=info_3days["date_from"], date_to=info_3days["date_to"])
    print(f"Excel report created at: {excel_path}")
    assert os.path.exists(excel_path), "Excel report file was not created!"
    
    # Clean up test excel
    os.remove(excel_path)
    print("Test Excel report cleaned up successfully.")
    
    print("\nTesting retrieval of latest report by zone...")
    latest_report = database.get_latest_report_for_zone("1. Мезонин 1 этаж")
    assert latest_report is not None, "Failed to get latest report for zone!"
    assert latest_report["status"] == "Есть замечания"
    assert len(latest_report["photos"]) == 2
    assert latest_report["photos"][0] == "file_id_12345"
    print(f"Latest report for zone retrieved successfully: {latest_report}")
    
    print("\nAll database and statistics tests passed successfully! 🎉")


if __name__ == "__main__":
    test_database_and_stats()
