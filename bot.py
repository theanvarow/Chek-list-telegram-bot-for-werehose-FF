import os
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
import config
import database
import statistics

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
if not config.BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables or .env file!")

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Localization Dictionary
LOCALIZATION = {
    'uz': {
        'select_lang': "Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
        'enter_fio': "Tizimdan ro'yxatdan o'tish uchun *F.I.Sh. (Familiya Ism Sharifingizni)* kiriting:",
        'invalid_fio': "Iltimos, F.I.Sh.ni to'g'ri kiriting (kamida ism va familiya):",
        'reg_success': "Ro'yxatdan muvaffaqiyatli o'tdingiz! Sizning ma'lumotlaringiz: *{fio}*\n\nEndi tekshiruv boshlashingiz yoki statistikani ko'rishingiz mumkin.",
        'welcome': "Xush kelibsiz, *{fio}*!\n\nBot bilan ishlash uchun quyidagi menyudan foydalaning.",
        'btn_new_check': "📝 Yangi tekshiruv",
        'btn_check_zone': "🔍 Zonani tekshirish",
        'btn_stats': "📊 Statistika",
        'btn_change_fio': "⚙️ F.I.Sh. o'zgartirish",
        'btn_change_lang': "🌐 Tilni o'zgartirish",
        'prompt_zone': "📍 Tekshirish uchun zona/qavatni tanlang:",
        'prompt_query_zone': "📍 Qaysi zona bo'yicha oxirgi hisobotni ko'rmoqchisiz?",
        'prompt_status': "📍 Tanlangan zona: *{zone}*\n\nUshbu zonada tozalik holati qanday?",
        'btn_clean': "✅ Toza (kamchiliklarsiz)",
        'btn_issues': "⚠️ Kamchiliklar bor",
        'prompt_checklist': "⚠️ Aniqlangan kamchiliklarni belgilang:",
        'item_boxes': "Bo'sh qutilar",
        'item_floor': "Polda tovarlar bor",
        'item_mess': "Tartibsizlik",
        'btn_done': "➡️ Tayyor (Tasdiqlash)",
        'prompt_photos': "📸 Iltimos, kamchiliklarni tasdiqlovchi rasmlarni yuboring (bir yoki bir nechta).\nRasmlarni yuborgach, *'Tayyor'* tugmasini bosing yoki rasm bo'lmasa *'Rasm yubormaslik'* tugmasini bosing.",
        'prompt_photos_clean': "📸 Iltimos, tasdiqlovchi rasmlarni yuboring (bir yoki bir nechta).\nRasmlarni yuborgach, *'Tayyor'* tugmasini bosing yoki rasm bo'lmasa *'Rasm yubormaslik'* tugmasini bosing.",
        'btn_photo_done': "➡️ Tayyor ({count} rasm)",
        'btn_photo_skip': "⏭️ Rasm yubormaslik",
        'prompt_comment': "💬 Ushbu tekshiruv yuzasidan izoh qoldiring, yoki quyidagi tugmani bosib o'tkazib yuboring:",
        'btn_comment_skip': "⏭️ Izohni o'tkazib yuborish",
        'report_saved': "📋 *Hisobot #{report_id} muvaffaqiyatli saqlandi!*\n\n📍 *Zona:* {zone}\n👤 *Tekshirdi:* {fio}\n📊 *Holat:* {status}\n",
        'status_clean': "Toza ✅",
        'status_issues': "Kamchiliklar bor ⚠️",
        'report_issues_header': "🔍 *Kamchiliklar:*\n",
        'report_comment_header': "💬 *Izoh:* {comment}\n",
        'report_photos_header': "📸 *Yuklangan rasmlar soni:* {count}\n",
        'stats_menu_title': "Statistika hisoboti turini tanlang:",
        'btn_stats_text': "📝 Matn ko'rinishida",
        'btn_stats_excel': "📥 Excel yuklab olish",
        'no_reports_zone': "📍 Zona: *{zone}*\n\nUshbu zona bo'yicha hali tekshiruv hisoboti saqlanmagan.",
        'latest_report_header': "📋 *Zonaning oxirgi hisoboti: {zone}*\n\n",
        'report_date': "📅 *Tekshiruv sanasi:* {date}\n",
        'report_by': "👤 *Tekshirdi:* {fio}\n",
        'loading_photos': "Hisobot rasmlari yuklanmoqda...",
        'back_to_menu': "Bosh menyuga qaytish.",
        'excel_loading': "⏳ Excel hisoboti tayyorlanmoqda, iltimos kuting...",
        'excel_caption': "📊 Tekshiruvlar ro'yxati: {date}",
        'excel_error': "⚠️ Excel hisobotini tayyorlashda xatolik yuz berdi. Balki ma'lumotlar yo'qdir.",
    },
    'ru': {
        'select_lang': "Пожалуйста, выберите язык / Iltimos, tilni tanlang:",
        'enter_fio': "Пожалуйста, введите ваше *ФИО (Фамилия Имя Отчество)* для регистрации:",
        'invalid_fio': "Пожалуйста, введите корректное ФИО (минимум имя и фамилия):",
        'reg_success': "Регистрация прошла успешно! Ваши данные: *{fio}*\n\nТеперь вы можете начать проверку или просмотреть статистику.",
        'welcome': "Приветствуем, *{fio}*!\n\nИспользуйте меню ниже для работы с ботом.",
        'btn_new_check': "📝 Новая проверка",
        'btn_check_zone': "🔍 Проверить зону",
        'btn_stats': "📊 Статистика",
        'btn_change_fio': "⚙️ Изменить ФИО",
        'btn_change_lang': "🌐 Изменить язык",
        'prompt_zone': "📍 Выберите зону / этаж для проверки:",
        'prompt_query_zone': "📍 Выберите зону / этаж для просмотра последнего отчета:",
        'prompt_status': "📍 Выбранная зона: *{zone}*\n\nКаково состояние чистоты в этой зоне?",
        'btn_clean': "✅ Чисто без замечаний",
        'btn_issues': "⚠️ Есть замечания",
        'prompt_checklist': "⚠️ Выберите обнаруженные замечания:",
        'item_boxes': "Пустые коробки",
        'item_floor': "Товары на полу",
        'item_mess': "Беспорядок",
        'btn_done': "➡️ Готово (Подтвердить)",
        'prompt_photos': "📸 Пожалуйста, отправьте фотографии нарушений (одну или несколько).\nПосле отправки нажмите *'Готово'*, либо *'Пропустить фото'*.",
        'prompt_photos_clean': "📸 Пожалуйста, отправьте подтверждающие фотографии (одно или несколько).\nПосле отправки всех фото нажмите кнопку *'Готово'*, либо нажмите *'Пропустить фото'*, если фото нет.",
        'btn_photo_done': "➡️ Готово ({count} фото)",
        'btn_photo_skip': "⏭️ Пропустить фото",
        'prompt_comment': "💬 Напишите комментарий к этой проверке, либо нажмите кнопку ниже, чтобы пропустить:",
        'btn_comment_skip': "⏭️ Пропустить комментарий",
        'report_saved': "📋 *Отчет #{report_id} успешно сохранен!*\n\n📍 *Зона:* {zone}\n👤 *Проверил:* {fio}\n📊 *Состояние:* {status}\n",
        'status_clean': "Чисто ✅",
        'status_issues': "Замечания ⚠️",
        'report_issues_header': "🔍 *Замечания:*\n",
        'report_comment_header': "💬 *Комментарий:* {comment}\n",
        'report_photos_header': "📸 *Загружено фотографий:* {count}\n",
        'stats_menu_title': "Выберите тип отчета по статистике:",
        'btn_stats_text': "📝 Текстовый отчет",
        'btn_stats_excel': "📥 Скачать Excel",
        'no_reports_zone': "📍 Зона: *{zone}*\n\nПо этой зоне пока нет сохраненных отчетов проверок.",
        'latest_report_header': "📋 *Последний отчет по зоне: {zone}*\n\n",
        'report_date': "📅 *Дата проверки:* {date}\n",
        'report_by': "👤 *Проверил:* {fio}\n",
        'loading_photos': "Загружаю фотографии отчета...",
        'back_to_menu': "Возврат в главное меню.",
        'excel_loading': "⏳ Создаю Excel отчет, пожалуйста подождите...",
        'excel_caption': "📊 Выгрузка отчетов на {date}",
        'excel_error': "⚠️ Не удалось сформировать Excel отчет. Возможно, нет данных.",
    }
}

# Define conversation states
class CheckStates(StatesGroup):
    selecting_lang = State()
    waiting_for_fio = State()
    main_menu = State()
    selecting_zone = State()
    selecting_status = State()
    filling_checklist = State()
    uploading_photos = State()
    writing_comment = State()
    querying_zone = State()

# Keyboard Generators
def get_lang_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_main_menu_keyboard(lang: str):
    keyboard = [
        [KeyboardButton(text=LOCALIZATION[lang]['btn_new_check']), KeyboardButton(text=LOCALIZATION[lang]['btn_check_zone'])],
        [KeyboardButton(text=LOCALIZATION[lang]['btn_stats']), KeyboardButton(text=LOCALIZATION[lang]['btn_change_fio'])],
        [KeyboardButton(text=LOCALIZATION[lang]['btn_change_lang'])]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_zone_keyboard(checked_zones: list = None):
    if checked_zones is None:
        checked_zones = []
    keyboard = []
    # Display in 2 columns
    for i in range(0, len(config.ZONES), 2):
        row = []
        
        zone1 = config.ZONES[i]
        prefix1 = "✅ " if zone1 in checked_zones else ""
        row.append(InlineKeyboardButton(text=f"{prefix1}{zone1}", callback_data=f"zone:{i}"))
        
        if i + 1 < len(config.ZONES):
            zone2 = config.ZONES[i+1]
            prefix2 = "✅ " if zone2 in checked_zones else ""
            row.append(InlineKeyboardButton(text=f"{prefix2}{zone2}", callback_data=f"zone:{i+1}"))
            
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_status_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=LOCALIZATION[lang]['btn_clean'], callback_data="status:clean")],
        [InlineKeyboardButton(text=LOCALIZATION[lang]['btn_issues'], callback_data="status:issues")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_checklist_keyboard(lang: str, boxes: bool, floor: bool, mess: bool):
    box_icon = "✅" if boxes else "⬜️"
    floor_icon = "✅" if floor else "⬜️"
    mess_icon = "✅" if mess else "⬜️"
    
    keyboard = [
        [InlineKeyboardButton(text=f"{box_icon} {LOCALIZATION[lang]['item_boxes']}", callback_data="toggle:boxes")],
        [InlineKeyboardButton(text=f"{floor_icon} {LOCALIZATION[lang]['item_floor']}", callback_data="toggle:floor")],
        [InlineKeyboardButton(text=f"{mess_icon} {LOCALIZATION[lang]['item_mess']}", callback_data="toggle:mess")],
        [InlineKeyboardButton(text=LOCALIZATION[lang]['btn_done'], callback_data="checklist_done")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_photo_keyboard(lang: str, photo_count: int):
    if photo_count > 0:
        done_text = LOCALIZATION[lang]['btn_photo_done'].format(count=photo_count)
    else:
        done_text = LOCALIZATION[lang]['btn_photo_done'].format(count="").replace(" ()", "").replace(" (0)", "")
    
    keyboard = [
        [KeyboardButton(text=done_text)],
        [KeyboardButton(text=LOCALIZATION[lang]['btn_photo_skip'])]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_comment_keyboard(lang: str):
    keyboard = [
        [KeyboardButton(text=LOCALIZATION[lang]['btn_comment_skip'])]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_stats_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=LOCALIZATION[lang]['btn_stats_text'], callback_data="stats:text")],
        [InlineKeyboardButton(text=LOCALIZATION[lang]['btn_stats_excel'], callback_data="stats:excel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# START COMMAND & LANGUAGE FLOW
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user = database.get_user(message.from_user.id)
    if user:
        # Dynamic self-healing for username updates
        if message.from_user.username != user.get('username'):
            database.update_user_username(message.from_user.id, message.from_user.username)
            user['username'] = message.from_user.username
            
        lang = user['lang'] or 'ru'
        await state.update_data(lang=lang)
        await state.set_state(CheckStates.main_menu)
        await message.answer(
            LOCALIZATION[lang]['welcome'].format(fio=user['fio']),
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(lang)
        )
    else:
        await state.set_state(CheckStates.selecting_lang)
        await message.answer(
            "Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
            reply_markup=get_lang_keyboard()
        )

@dp.callback_query(CheckStates.selecting_lang, F.data.startswith("lang:"))
async def process_lang_select(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data.split(":")[1]
    await state.update_data(lang=lang)
    
    user = database.get_user(callback.from_user.id)
    if user:
        # Update existing user language and username
        database.update_user_lang(callback.from_user.id, lang)
        if callback.from_user.username != user.get('username'):
            database.update_user_username(callback.from_user.id, callback.from_user.username)
            user['username'] = callback.from_user.username
            
        await state.set_state(CheckStates.main_menu)
        await callback.message.delete()
        await callback.message.answer(
            LOCALIZATION[lang]['welcome'].format(fio=user['fio']),
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(lang)
        )
    else:
        # New registration: go to FIO state
        await state.set_state(CheckStates.waiting_for_fio)
        await callback.message.delete()
        await callback.message.answer(
            LOCALIZATION[lang]['enter_fio'],
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
    await callback.answer()


# REGISTRATION FLOW
@dp.message(CheckStates.waiting_for_fio)
async def process_fio(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    fio = message.text.strip()
    if len(fio) < 5 or " " not in fio:
        await message.answer(LOCALIZATION[lang]['invalid_fio'])
        return
        
    database.register_user(message.from_user.id, fio, message.from_user.username, lang)
    await state.set_state(CheckStates.main_menu)
    await message.answer(
        LOCALIZATION[lang]['reg_success'].format(fio=fio),
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(lang)
    )


# MAIN MENU COMMAND HANDLING
@dp.message(lambda msg: msg.text in ["📝 Новая проверка", "📝 Yangi tekshiruv"])
async def start_check(message: types.Message, state: FSMContext):
    user = database.get_user(message.from_user.id)
    if not user:
        await state.set_state(CheckStates.selecting_lang)
        await message.answer("Пожалуйста, выберите язык / Iltimos, tilni tanlang:", reply_markup=get_lang_keyboard())
        return

    # Update username if it changed
    if message.from_user.username != user.get('username'):
        database.update_user_username(message.from_user.id, message.from_user.username)

    lang = user['lang'] or 'ru'
    await state.update_data(lang=lang)
    await state.set_state(CheckStates.selecting_zone)
    checked_today = database.get_checked_zones_today()
    await message.answer(LOCALIZATION[lang]['prompt_zone'], reply_markup=get_zone_keyboard(checked_today))

@dp.message(lambda msg: msg.text in ["🔍 Проверить зону", "🔍 Zonani tekshirish"])
async def start_query_zone(message: types.Message, state: FSMContext):
    user = database.get_user(message.from_user.id)
    if not user:
        await state.set_state(CheckStates.selecting_lang)
        await message.answer("Пожалуйста, выберите язык / Iltimos, tilni tanlang:", reply_markup=get_lang_keyboard())
        return

    # Update username if it changed
    if message.from_user.username != user.get('username'):
        database.update_user_username(message.from_user.id, message.from_user.username)

    lang = user['lang'] or 'ru'
    await state.update_data(lang=lang)
    await state.set_state(CheckStates.querying_zone)
    checked_today = database.get_checked_zones_today()
    await message.answer(LOCALIZATION[lang]['prompt_query_zone'], reply_markup=get_zone_keyboard(checked_today))



@dp.message(lambda msg: msg.text in ["📊 Статистика", "📊 Statistika"])
async def show_stats_menu(message: types.Message, state: FSMContext):
    lang = database.get_user_lang(message.from_user.id)
    await state.update_data(lang=lang)
    await message.answer(
        LOCALIZATION[lang]['stats_menu_title'],
        reply_markup=get_stats_keyboard(lang)
    )

@dp.message(lambda msg: msg.text in ["⚙️ Изменить ФИО", "⚙️ F.I.Sh. o'zgartirish"])
async def change_fio(message: types.Message, state: FSMContext):
    lang = database.get_user_lang(message.from_user.id)
    await state.update_data(lang=lang)
    await state.set_state(CheckStates.waiting_for_fio)
    await message.answer(
        LOCALIZATION[lang]['enter_fio'],
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(lambda msg: msg.text in ["🌐 Изменить язык", "🌐 Tilni o'zgartirish"])
async def change_lang(message: types.Message, state: FSMContext):
    await state.set_state(CheckStates.selecting_lang)
    await message.answer(
        "Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
        reply_markup=get_lang_keyboard()
    )


# CHECKLIST STEP-BY-STEP FLOW
@dp.callback_query(CheckStates.querying_zone, F.data.startswith("zone:"))
async def process_query_zone_select(callback: types.CallbackQuery, state: FSMContext):
    zone_index = int(callback.data.split(":")[1])
    zone_name = config.ZONES[zone_index]
    
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    await callback.message.delete()
    await state.set_state(CheckStates.main_menu)
    
    report = database.get_latest_report_for_zone(zone_name)
    
    if not report:
        await callback.message.answer(
            LOCALIZATION[lang]['no_reports_zone'].format(zone=zone_name),
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(lang)
        )
        await callback.answer()
        return
        
    # Construct summary message
    summary = LOCALIZATION[lang]['latest_report_header'].format(zone=zone_name)
    summary += LOCALIZATION[lang]['report_date'].format(date=report['created_at'])
    inspector_display = f"{report['inspector']} (@{report['telegram_username']})" if report['telegram_username'] else report['inspector']
    summary += LOCALIZATION[lang]['report_by'].format(fio=inspector_display)
    
    status_text = LOCALIZATION[lang]['status_clean'] if report['status'] == 'Чисто' else LOCALIZATION[lang]['status_issues']
    summary += f"📊 *Holat / Состояние:* {status_text}\n"
    
    if report['status'] != "Чисто":
        summary += LOCALIZATION[lang]['report_issues_header']
        if report['has_empty_boxes']: summary += f"  - {LOCALIZATION[lang]['item_boxes']}\n"
        if report['has_goods_on_floor']: summary += f"  - {LOCALIZATION[lang]['item_floor']}\n"
        if report['has_mess']:  summary += f"  - {LOCALIZATION[lang]['item_mess']}\n"
        
    if report['comment']:
        summary += LOCALIZATION[lang]['report_comment_header'].format(comment=report['comment'])
        
    photos = report['photos']
    if photos:
        summary += LOCALIZATION[lang]['report_photos_header'].format(count=len(photos))
        await callback.message.answer(LOCALIZATION[lang]['loading_photos'])
        
        # Send photos as media group
        from aiogram.types import InputMediaPhoto
        media_group = []
        for idx, file_id in enumerate(photos):
            if idx == 0:
                media_group.append(InputMediaPhoto(media=file_id, caption=summary, parse_mode="Markdown"))
            else:
                media_group.append(InputMediaPhoto(media=file_id))
        
        try:
            await callback.message.answer_media_group(media=media_group)
        except Exception as e:
            logger.error(f"Error sending media group: {e}")
            # Fallback to sending photos individually
            for file_id in photos:
                try:
                    await callback.message.answer_photo(photo=file_id)
                except Exception:
                    pass
            await callback.message.answer(summary, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(lang))
            await callback.answer()
            return
            
        # Send main menu
        await callback.message.answer(LOCALIZATION[lang]['back_to_menu'], reply_markup=get_main_menu_keyboard(lang))
    else:
        # No photos, just send text
        await callback.message.answer(summary, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(lang))
        
    await callback.answer()

@dp.callback_query(CheckStates.selecting_zone, F.data.startswith("zone:"))
async def process_zone_select(callback: types.CallbackQuery, state: FSMContext):
    zone_index = int(callback.data.split(":")[1])
    zone_name = config.ZONES[zone_index]
    
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    await state.update_data(zone=zone_name)
    await state.set_state(CheckStates.selecting_status)
    
    await callback.message.edit_text(
        LOCALIZATION[lang]['prompt_status'].format(zone=zone_name),
        parse_mode="Markdown",
        reply_markup=get_status_keyboard(lang)
    )
    await callback.answer()

@dp.callback_query(CheckStates.selecting_status, F.data.startswith("status:"))
async def process_status_select(callback: types.CallbackQuery, state: FSMContext):
    status_type = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    if status_type == "clean":
        await state.update_data(
            status="Чисто",
            has_empty_boxes=False,
            has_goods_on_floor=False,
            has_mess=False
        )
        # Directly move to photo upload state
        await state.update_data(photos=[])
        await state.set_state(CheckStates.uploading_photos)
        
        await callback.message.delete()
        await callback.message.answer(
            LOCALIZATION[lang]['prompt_photos_clean'],
            parse_mode="Markdown",
            reply_markup=get_photo_keyboard(lang, 0)
        )
    else:
        # User clicked "Есть замечания / Kamchiliklar bor"
        await state.update_data(
            status="Есть замечания",
            has_empty_boxes=False,
            has_goods_on_floor=False,
            has_mess=False
        )
        await state.set_state(CheckStates.filling_checklist)
        await callback.message.edit_text(
            LOCALIZATION[lang]['prompt_checklist'],
            reply_markup=get_checklist_keyboard(lang, False, False, False)
        )
    await callback.answer()

@dp.callback_query(CheckStates.filling_checklist, F.data.startswith("toggle:"))
async def process_checklist_toggle(callback: types.CallbackQuery, state: FSMContext):
    toggle_item = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    # Toggle individual values
    boxes = data.get("has_empty_boxes", False)
    floor = data.get("has_goods_on_floor", False)
    mess = data.get("has_mess", False)
    
    if toggle_item == "boxes":
        boxes = not boxes
    elif toggle_item == "floor":
        floor = not floor
    elif toggle_item == "mess":
        mess = not mess
        
    await state.update_data(
        has_empty_boxes=boxes,
        has_goods_on_floor=floor,
        has_mess=mess
    )
    
    # Update UI to reflect selected items
    await callback.message.edit_reply_markup(
        reply_markup=get_checklist_keyboard(lang, boxes, floor, mess)
    )
    await callback.answer()

@dp.callback_query(CheckStates.filling_checklist, F.data == "checklist_done")
async def process_checklist_done(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    boxes = data.get("has_empty_boxes", False)
    floor = data.get("has_goods_on_floor", False)
    mess = data.get("has_mess", False)
    
    if not (boxes or floor or mess):
        alert_msg = "⚠️ Kamchiliklarni belgilang!" if lang == "uz" else "⚠️ Выберите хотя бы одно замечание!"
        await callback.answer(alert_msg, show_alert=True)
        return
        
    await state.update_data(photos=[])
    await state.set_state(CheckStates.uploading_photos)
    
    await callback.message.delete()
    await callback.message.answer(
        LOCALIZATION[lang]['prompt_photos'],
        parse_mode="Markdown",
        reply_markup=get_photo_keyboard(lang, 0)
    )
    await callback.answer()


# PHOTO & COMMENT FLOW
@dp.message(CheckStates.uploading_photos, F.photo)
async def process_photo_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    uploaded_photos = data.get("photos", [])
    
    # Extract largest photo
    photo_file = message.photo[-1]
    file_id = photo_file.file_id
    
    # Download file locally
    try:
        file_info = await bot.get_file(file_id)
        filename = f"photo_{message.from_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
        dest_path = os.path.join(config.PHOTOS_DIR, filename)
        
        await bot.download_file(file_info.file_path, dest_path)
        
        uploaded_photos.append((dest_path, file_id))
        await state.update_data(photos=uploaded_photos)
        
        success_msg = f"✅ Rasm yuklandi! (Jami: {len(uploaded_photos)})" if lang == "uz" else f"✅ Фото успешно загружено! (Всего: {len(uploaded_photos)})"
        await message.answer(
            success_msg,
            reply_markup=get_photo_keyboard(lang, len(uploaded_photos))
        )
    except Exception as e:
        logger.error(f"Error downloading photo: {e}")
        err_msg = "⚠️ Rasmni yuklab bo'lmadi, qaytadan yuboring." if lang == "uz" else "⚠️ Не удалось загрузить фото. Пожалуйста, попробуйте еще раз."
        await message.answer(err_msg)

@dp.message(CheckStates.uploading_photos, lambda msg: "➡️ Готово" in msg.text or "➡️ Tayyor" in msg.text)
async def process_photos_done(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    await state.set_state(CheckStates.writing_comment)
    await message.answer(
        LOCALIZATION[lang]['prompt_comment'],
        reply_markup=get_comment_keyboard(lang)
    )

@dp.message(CheckStates.uploading_photos, lambda msg: msg.text in ["⏭️ Пропустить фото", "⏭️ Rasm yubormaslik"])
async def process_photos_skip(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    await state.update_data(photos=[])
    await state.set_state(CheckStates.writing_comment)
    await message.answer(
        LOCALIZATION[lang]['prompt_comment'],
        reply_markup=get_comment_keyboard(lang)
    )

@dp.message(CheckStates.writing_comment)
async def process_comment(message: types.Message, state: FSMContext):
    comment = message.text.strip()
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    if comment in ["⏭️ Пропустить комментарий", "⏭️ Izohni o'tkazib yuborish"]:
        comment = ""
        
    zone = data.get("zone")
    status = data.get("status")
    boxes = data.get("has_empty_boxes", False)
    floor = data.get("has_goods_on_floor", False)
    mess = data.get("has_mess", False)
    photos = data.get("photos", [])
    
    # Save to SQLite database
    report_id = database.save_report(
        user_id=message.from_user.id,
        zone=zone,
        status=status,
        has_empty_boxes=boxes,
        has_goods_on_floor=floor,
        has_mess=mess,
        comment=comment,
        photos=photos
    )
    
    # Get user FIO
    user = database.get_user(message.from_user.id)
    fio = user["fio"] if user else "Неизвестный"
    if user and user.get("username"):
        fio = f"{fio} (@{user['username']})"
    
    # Construct summary message
    status_text = LOCALIZATION[lang]['status_clean'] if status == 'Чисто' else LOCALIZATION[lang]['status_issues']
    summary = LOCALIZATION[lang]['report_saved'].format(report_id=report_id, zone=zone, fio=fio, status=status_text)
    
    if status != "Чисто":
        summary += LOCALIZATION[lang]['report_issues_header']
        if boxes: summary += f"  - {LOCALIZATION[lang]['item_boxes']}\n"
        if floor: summary += f"  - {LOCALIZATION[lang]['item_floor']}\n"
        if mess:  summary += f"  - {LOCALIZATION[lang]['item_mess']}\n"
        
    if comment:
        summary += LOCALIZATION[lang]['report_comment_header'].format(comment=comment)
    if photos:
        summary += LOCALIZATION[lang]['report_photos_header'].format(count=len(photos))
        
    await state.set_state(CheckStates.main_menu)
    await message.answer(
        summary,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(lang)
    )


# STATISTICS CALLBACK HANDLERS
@dp.callback_query(F.data == "stats:text")
async def process_text_stats(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    stats_text = statistics.generate_text_stats(lang)
    await callback.message.answer(stats_text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "stats:excel")
async def process_excel_stats(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    await callback.message.answer(LOCALIZATION[lang]['excel_loading'])
    try:
        excel_path = statistics.generate_excel_report()
        file = types.FSInputFile(excel_path)
        caption_text = LOCALIZATION[lang]['excel_caption'].format(date=datetime.now().strftime('%d.%m.%Y %H:%M'))
        await callback.message.answer_document(
            file,
            caption=caption_text
        )
        if os.path.exists(excel_path):
            os.remove(excel_path)
    except Exception as e:
        logger.error(f"Error sending Excel report: {e}")
        await callback.message.answer(LOCALIZATION[lang]['excel_error'])
    await callback.answer()


# MAIN RUNNER
async def main():
    database.init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
