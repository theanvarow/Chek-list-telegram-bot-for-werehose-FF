import os
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
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
        'welcome': "Salom, bu chek list bot. Botdan foydalanish uchun tugmalarni bosing.",
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
        'select_date_prompt': "📅 *Statistika ko'rish uchun sanani tanlang:*",
        'no_reports_zone': "📍 Zona: *{zone}*\n\n🔒 Bugun bu zona hali tekshirilmadi.",
        'latest_report_header': "📋 *Zonaning bugungi oxirgi hisoboti: {zone}*\n\n",
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
        'welcome': "Привет, *{fio}*! Это чек-лист бот. Для использования бота нажмите кнопки.",
        'btn_new_check': "📝 Новая проверка",
        'btn_check_zone': "🔍 Проверить зону",
        'btn_stats': "📊 Статистика",
        'btn_change_fio': "⚙️ Изменить ФИО",
        'btn_finish': "🏁 Завершить обход",
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
        'select_date_prompt': "📅 *Выберите дату для просмотра статистики:*",
        'no_reports_zone': "📍 Зона: *{zone}*\n\n🔒 Сегодня эта зона ещё не проверялась.",
        'latest_report_header': "📋 *Сегодняшний отчет по зоне: {zone}*\n\n",
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
    waiting_for_fio = State()
    main_menu = State()
    selecting_zone = State()
    selecting_status = State()
    filling_checklist = State()
    uploading_photos = State()
    writing_comment = State()
    querying_zone = State()

def get_main_menu_keyboard(lang: str = "ru"):
    keyboard = [
        [KeyboardButton(text=LOCALIZATION['ru']['btn_new_check']), KeyboardButton(text=LOCALIZATION['ru']['btn_stats'])]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_date_selection_keyboard(lang: str = "ru"):
    now = datetime.now()
    d0 = now.date()
    
    keyboard = []
    row = []
    for i in range(7):
        dt = d0 - timedelta(days=i)
        dt_str = dt.strftime('%Y-%m-%d')
        if i == 0:
            lbl = f"📅 Сегодня ({dt.strftime('%d.%m')})"
        elif i == 1:
            lbl = f"📅 Вчера ({dt.strftime('%d.%m')})"
        else:
            lbl = f"📅 {dt.strftime('%d.%m.%Y')}"
        
        row.append(InlineKeyboardButton(text=lbl, callback_data=f"sdate:day:{dt_str}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_stats_actions_keyboard(lang: str = "ru", date_key: str = "today"):
    date_info = statistics.get_date_info(date_key, "ru")
    btn_excel = f"📥 Скачать Excel ({date_info['title']})"
    btn_change_date = "📅 Выбрать другую дату"
        
    keyboard = [
        [InlineKeyboardButton(text=btn_excel, callback_data=f"sexcel:{date_key}")],
        [InlineKeyboardButton(text=btn_change_date, callback_data="sdate_select")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_zone_keyboard(zone_statuses: dict = None, prefix: str = "szone:"):
    if zone_statuses is None:
        zone_statuses = {}
    keyboard = []
    # Display in 2 columns
    for i in range(0, len(config.ZONES), 2):
        row = []
        
        zone1 = config.ZONES[i]
        status1 = zone_statuses.get(zone1)
        prefix1 = "✅ " if status1 == "Чисто" else ("⚠️ " if status1 == "Есть замечания" else "🔒 ")
        row.append(InlineKeyboardButton(text=f"{prefix1}{zone1}", callback_data=f"{prefix}{i}"))
        
        if i + 1 < len(config.ZONES):
            zone2 = config.ZONES[i+1]
            status2 = zone_statuses.get(zone2)
            prefix2 = "✅ " if status2 == "Чисто" else ("⚠️ " if status2 == "Есть замечания" else "🔒 ")
            row.append(InlineKeyboardButton(text=f"{prefix2}{zone2}", callback_data=f"{prefix}{i+1}"))
            
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_status_keyboard(lang: str = "ru"):
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
        done_text = f"➡️ Готово ({photo_count} фото)" if lang == 'ru' else f"➡️ Tayyor ({photo_count} rasm)"
    else:
        done_text = "➡️ Готово" if lang == 'ru' else "➡️ Tayyor"
    
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


# USER REGISTRATION HELPER (AUTO FROM TELEGRAM ACCOUNT)
def ensure_user_registered(telegram_user: types.User) -> dict:
    account_fio = telegram_user.full_name.strip() if telegram_user.full_name else (telegram_user.username or "Пользователь")
    user = database.get_user(telegram_user.id)
    if not user:
        database.register_user(telegram_user.id, account_fio, telegram_user.username, 'ru')
        user = database.get_user(telegram_user.id)
    else:
        if user.get('fio') != account_fio or user.get('username') != telegram_user.username:
            database.register_user(telegram_user.id, account_fio, telegram_user.username, 'ru')
            user['fio'] = account_fio
            user['username'] = telegram_user.username
    return user


# RESTRICT ALL BOT COMMANDS/INTERACTIONS TO PRIVATE CHATS ONLY & WIPE GROUP KEYBOARDS
async def delete_after_delay(msg: types.Message, delay: int):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

@dp.message.outer_middleware()
async def private_chat_only_message_middleware(handler, event: types.Message, data: dict):
    if event.chat.type in ["group", "supergroup"]:
        if event.text and (event.text.startswith("/") or any(kw in event.text.lower() for kw in ["проверка", "завершить", "статистика", "зона", "fio", "фио", "обход"])):
            try:
                msg = await event.answer(
                    "⚠️ *Бот работает только в личных сообщениях с ботом.*",
                    parse_mode="Markdown",
                    reply_markup=ReplyKeyboardRemove()
                )
                asyncio.create_task(delete_after_delay(msg, 4))
            except Exception:
                pass
        return
    return await handler(event, data)

@dp.callback_query.outer_middleware()
async def private_chat_only_callback_middleware(handler, event: types.CallbackQuery, data: dict):
    if event.message and event.message.chat.type in ["group", "supergroup"]:
        return
    return await handler(event, data)


# START COMMAND
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user = ensure_user_registered(message.from_user)
    lang = 'ru'
    await state.update_data(lang=lang)
    await state.set_state(CheckStates.main_menu)
    fio_esc = statistics.escape_markdown(user['fio'])
    await message.answer(
        LOCALIZATION[lang]['welcome'].format(fio=fio_esc),
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(lang)
    )


# MAIN MENU COMMAND HANDLING
@dp.message(StateFilter("*"), F.text & (F.text.contains("Новая проверка") | F.text.contains("Yangi tekshiruv")))
async def start_check(message: types.Message, state: FSMContext):
    ensure_user_registered(message.from_user)
    lang = 'ru'
    await state.update_data(lang=lang)
    await state.set_state(CheckStates.selecting_zone)
    zone_statuses = database.get_zone_statuses_for_user(message.from_user.id, hours=3)
    await message.answer(LOCALIZATION[lang]['prompt_zone'], reply_markup=get_zone_keyboard(zone_statuses, prefix="szone:"))

@dp.message(StateFilter("*"), F.text & (F.text.contains("Проверить зону") | F.text.contains("Zonani tekshirish") | F.text.contains("проверка зона")))
async def start_query_zone(message: types.Message, state: FSMContext):
    ensure_user_registered(message.from_user)
    lang = 'ru'
    await state.update_data(lang=lang)
    await state.set_state(CheckStates.querying_zone)
    zone_statuses = database.get_zone_statuses_today()
    await message.answer(LOCALIZATION[lang]['prompt_query_zone'], reply_markup=get_zone_keyboard(zone_statuses, prefix="qzone:"))


@dp.message(F.text.in_(["📊 Статистика", "📊 Statistika"]))
async def show_stats_menu(message: types.Message, state: FSMContext):
    lang = 'ru'
    await state.update_data(lang=lang)
    await message.answer(
        LOCALIZATION[lang]['select_date_prompt'],
        parse_mode="Markdown",
        reply_markup=get_date_selection_keyboard(lang)
    )




# CHECKLIST STEP-BY-STEP FLOW
@dp.callback_query(StateFilter("*"), F.data.startswith("szone:"))
async def process_szone_select(callback: types.CallbackQuery, state: FSMContext):
    await process_zone_select(callback, state)

@dp.callback_query(StateFilter("*"), F.data.startswith("qzone:"))
async def process_qzone_select(callback: types.CallbackQuery, state: FSMContext):
    await process_query_zone_select(callback, state)

@dp.callback_query(StateFilter("*"), F.data.startswith("zone:"))
async def process_legacy_zone_select(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == CheckStates.querying_zone.state:
        await process_query_zone_select(callback, state)
    else:
        await process_zone_select(callback, state)

async def process_query_zone_select(callback: types.CallbackQuery, state: FSMContext):
    zone_index = int(callback.data.split(":")[1])
    zone_name = config.ZONES[zone_index]
    
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
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
    zone_esc = statistics.escape_markdown(zone_name)
    summary = LOCALIZATION[lang]['latest_report_header'].format(zone=zone_esc)
    raw_date = str(report['created_at'])
    if " " in raw_date:
        d_part, t_part = raw_date.split(" ", 1)
        formatted_date = f"{d_part} - {t_part}"
    else:
        formatted_date = raw_date
    summary += LOCALIZATION[lang]['report_date'].format(date=formatted_date)
    
    inspector_esc = statistics.escape_markdown(report['inspector'])
    username_esc = statistics.escape_markdown(report['telegram_username'])
    inspector_display = f"{inspector_esc} (@{username_esc})" if report['telegram_username'] else inspector_esc
    summary += LOCALIZATION[lang]['report_by'].format(fio=inspector_display)
    
    status_text = LOCALIZATION[lang]['status_clean'] if report['status'] == 'Чисто' else LOCALIZATION[lang]['status_issues']
    summary += f"📊 *Состояние:* {status_text}\n"
    
    if report['status'] != "Чисто":
        issues_items = []
        if report['has_empty_boxes']: issues_items.append(LOCALIZATION[lang]['item_boxes'])
        if report['has_goods_on_floor']: issues_items.append(LOCALIZATION[lang]['item_floor'])
        if report['has_mess']:  issues_items.append(LOCALIZATION[lang]['item_mess'])
        summary += f"🔍 *Замечания:* {', '.join(issues_items)}\n"
        
    if report['comment']:
        comment_esc = statistics.escape_markdown(report['comment'])
        summary += LOCALIZATION[lang]['report_comment_header'].format(comment=comment_esc)
        
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

async def process_zone_select(callback: types.CallbackQuery, state: FSMContext):
    zone_index = int(callback.data.split(":")[1])
    zone_name = config.ZONES[zone_index]
    
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    await state.update_data(zone=zone_name)
    await state.set_state(CheckStates.selecting_status)
    
    try:
        await callback.message.edit_text(
            LOCALIZATION[lang]['prompt_status'].format(zone=zone_name),
            parse_mode="Markdown",
            reply_markup=get_status_keyboard(lang)
        )
    except Exception:
        await callback.message.answer(
            LOCALIZATION[lang]['prompt_status'].format(zone=zone_name),
            parse_mode="Markdown",
            reply_markup=get_status_keyboard(lang)
        )
    await callback.answer()

@dp.callback_query(StateFilter("*"), F.data.startswith("status:"))
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
        
        try:
            await callback.message.delete()
        except Exception:
            pass
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
        try:
            await callback.message.edit_text(
                LOCALIZATION[lang]['prompt_checklist'],
                reply_markup=get_checklist_keyboard(lang, False, False, False)
            )
        except Exception:
            await callback.message.answer(
                LOCALIZATION[lang]['prompt_checklist'],
                reply_markup=get_checklist_keyboard(lang, False, False, False)
            )
    await callback.answer()

@dp.callback_query(StateFilter("*"), F.data.startswith("toggle:"))
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
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_checklist_keyboard(lang, boxes, floor, mess)
        )
    except Exception:
        pass
    await callback.answer()

@dp.callback_query(StateFilter("*"), F.data == "checklist_done")
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
    
    try:
        await callback.message.delete()
    except Exception:
        pass
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

@dp.message(CheckStates.uploading_photos, F.text & (F.text.contains("Готово") | F.text.contains("Tayyor") | F.text.icontains("готово") | F.text.icontains("tayyor")))
async def process_photos_done(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    await state.set_state(CheckStates.writing_comment)
    await message.answer(
        LOCALIZATION[lang]['prompt_comment'],
        reply_markup=get_comment_keyboard(lang)
    )

@dp.message(CheckStates.uploading_photos, F.text & (F.text.contains("Пропустить") | F.text.contains("Rasm yubormaslik") | F.text.icontains("пропустить")))
async def process_photos_skip(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    await state.update_data(photos=[])
    await state.set_state(CheckStates.writing_comment)
    await message.answer(
        LOCALIZATION[lang]['prompt_comment'],
        reply_markup=get_comment_keyboard(lang)
    )

@dp.message(CheckStates.uploading_photos, F.text)
async def process_photos_unknown_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    uploaded_photos = data.get("photos", [])
    prompt_msg = "📸 Пожалуйста, отправьте фото и нажмите *'Готово'*, либо нажмите *'Пропустить фото'*."
    await message.answer(prompt_msg, parse_mode="Markdown", reply_markup=get_photo_keyboard(lang, len(uploaded_photos)))

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
    fio_esc = statistics.escape_markdown(fio)
    if user and user.get("username"):
        username_esc = statistics.escape_markdown(user['username'])
        fio_esc = f"{fio_esc} (@{username_esc})"
    
    # Construct summary message
    status_text = LOCALIZATION[lang]['status_clean'] if status == 'Чисто' else LOCALIZATION[lang]['status_issues']
    zone_esc = statistics.escape_markdown(zone)
    summary = LOCALIZATION[lang]['report_saved'].format(report_id=report_id, zone=zone_esc, fio=fio_esc, status=status_text)
    
    if status != "Чисто":
        issues_items = []
        if boxes: issues_items.append(LOCALIZATION[lang]['item_boxes'])
        if floor: issues_items.append(LOCALIZATION[lang]['item_floor'])
        if mess:  issues_items.append(LOCALIZATION[lang]['item_mess'])
        summary += f"🔍 *Замечания:* {', '.join(issues_items)}\n"
        
    if comment:
        comment_esc = statistics.escape_markdown(comment)
        summary += LOCALIZATION[lang]['report_comment_header'].format(comment=comment_esc)
    if photos:
        summary += LOCALIZATION[lang]['report_photos_header'].format(count=len(photos))
        
    # Send report notification to group asynchronously in background
    asyncio.create_task(send_single_report_to_group(
        bot=bot,
        group_id=config.REPORT_GROUP_ID,
        zone=zone,
        status=status,
        fio=user['fio'] if user else "Неизвестный",
        username=user.get('username') if user else None,
        boxes=boxes,
        floor=floor,
        mess=mess,
        comment=comment,
        photos=photos,
        report_id=report_id
    ))

    await state.set_state(CheckStates.main_menu)
    await message.answer(
        summary,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(lang)
    )


# GROUP REPORT HELPERS & HANDLERS
async def send_single_report_to_group(bot: Bot, group_id: int, zone: str, status: str, fio: str, username: str, boxes: bool, floor: bool, mess: bool, comment: str, photos: list, report_id: int):
    import html
    fio_esc = html.escape(fio)
    if username:
        username_esc = html.escape(username)
        fio_display = f"{fio_esc} (@{username_esc})"
    else:
        fio_display = fio_esc
        
    zone_esc = html.escape(zone)
    status_text = "Чисто ✅" if status == 'Чисто' else "Есть замечания ⚠️"
    now_str = datetime.now().strftime("%Y-%m-%d - %H:%M:%S")
    
    msg = f"📋 <b>НОВЫЙ ОТЧЕТ ПРОВЕРКИ ЗОНЫ #{report_id}</b>\n\n"
    msg += f"📍 <b>Зона / Этаж:</b> {zone_esc}\n"
    msg += f"📊 <b>Состояние:</b> {status_text}\n"
    msg += f"👤 <b>Проверяющий:</b> {fio_display}\n"
    msg += f"📅 <b>Дата проверки:</b> {now_str}\n"
    
    if status != "Чисто":
        issues_items = []
        if boxes: issues_items.append("Пустые коробки под стеллажом")
        if floor: issues_items.append("Товары на полу")
        if mess:  issues_items.append("Общий беспорядок")
        msg += f"🔍 <b>Замечания:</b> {', '.join(issues_items)}\n"
        
    if comment:
        comment_esc = html.escape(comment)
        msg += f"\n💬 <b>Комментарий:</b> <i>{comment_esc}</i>\n"
        
    target_chats = [group_id]
    raw_str = str(abs(group_id))
    if not str(group_id).startswith("-100"):
        target_chats.extend([int(f"-100{raw_str}"), int(f"-{raw_str}"), abs(group_id)])
    
    for chat_id in target_chats:
        try:
            if photos:
                from aiogram.types import InputMediaPhoto
                media_group = []
                for idx, item in enumerate(photos):
                    file_id = item[1] if isinstance(item, tuple) else item
                    if idx == 0:
                        media_group.append(InputMediaPhoto(media=file_id, caption=msg, parse_mode="HTML"))
                    else:
                        media_group.append(InputMediaPhoto(media=file_id))
                await bot.send_media_group(chat_id=chat_id, media=media_group)
            else:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")
            break
        except Exception as e:
            logger.error(f"Failed sending single report to group chat_id {chat_id}: {e}")


async def send_consolidated_summary_to_group(bot: Bot, group_id: int, date_key: str = "today"):
    import html
    date_info = statistics.get_date_info(date_key, "ru")
    reports = database.get_reports_for_summary(date_info['date_from'], date_info['date_to'])
    
    if not reports:
        return False, "За выбранный период нет отчетов для отправки."
        
    clean_count = sum(1 for r in reports if r['status'] == 'Чисто')
    issues_count = len(reports) - clean_count
    
    header = f"📊 <b>СВОДНЫЙ ОБЩИЙ ОТЧЕТ ПРОВЕРКИ ЗОН СКЛАДА</b>\n"
    header += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    header += f"🗓 <b>Период:</b> {html.escape(date_info['title'])}\n"
    header += f"📋 <b>Всего проверок:</b> {len(reports)}\n"
    header += f"  ├ ✅ <b>Чисто:</b> {clean_count}\n"
    header += f"  └ ⚠️ <b>С замечаниями:</b> {issues_count}\n"
    header += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    entries = []
    all_photos = []
    
    for idx, r in enumerate(reports, 1):
        zone_esc = html.escape(r['zone'])
        status_icon = "✅" if r['status'] == 'Чисто' else "⚠️"
        inspector_esc = html.escape(r['inspector'])
        if r['telegram_username']:
            un_esc = html.escape(r['telegram_username'])
            inspector_display = f"{inspector_esc} (@{un_esc})"
        else:
            inspector_display = inspector_esc
            
        entry = f"📍 <b>{idx}. {zone_esc}</b>\n"
        entry += f"└ 👤 {inspector_display} | 📅 {r['created_at'][5:16]}\n"
        entry += f"└ Состояние: <b>{html.escape(r['status'])}</b> {status_icon}\n"
        
        if r['status'] != 'Чисто':
            issues = []
            if r['has_empty_boxes']: issues.append("Пустые коробки")
            if r['has_goods_on_floor']: issues.append("Товары на полу")
            if r['has_mess']: issues.append("Беспорядок")
            if issues:
                entry += f"   └ 🔍 <b>Замечания:</b> <i>{', '.join(issues)}</i>\n"
                
        if r['comment']:
            comm_esc = html.escape(r['comment'])
            entry += f"   └ Комментарий: <i>{comm_esc}</i>\n"
            
        if r['photos']:
            all_photos.extend(r['photos'])
            
        entry += "\n"
        entries.append(entry)
        
    chunks = []
    current_chunk = header
    for entry in entries:
        if len(current_chunk) + len(entry) > 3800:
            chunks.append(current_chunk)
            current_chunk = entry
        else:
            current_chunk += entry
    if current_chunk:
        chunks.append(current_chunk)
        
    raw_id = abs(group_id)
    target_chats = [int(f"-100{raw_id}"), int(f"-{raw_id}"), raw_id, group_id]
    
    for chat_id in target_chats:
        try:
            for chunk in chunks:
                await bot.send_message(chat_id=chat_id, text=chunk, parse_mode="HTML")
                
            if all_photos:
                from aiogram.types import InputMediaPhoto
                for i in range(0, len(all_photos), 10):
                    p_chunk = all_photos[i:i+10]
                    media = [InputMediaPhoto(media=pid) for pid in p_chunk]
                    await bot.send_media_group(chat_id=chat_id, media=media)
                    
            return True, f"✅ Сводный отчет за {date_info['title']} с фото ({len(all_photos)} шт.) успешно отправлен в группу!"
        except Exception as e:
            logger.error(f"Failed sending summary to group chat_id {chat_id}: {e}")
            
    return False, "⚠️ Не удалось отправить сводный отчет в группу. Проверьте добавление бота в группу ID: 4908690020."


@dp.callback_query(F.data.startswith("sdate:"))
async def process_date_select(callback: types.CallbackQuery, state: FSMContext):
    date_key = callback.data.split(":", 1)[1]
    data = await state.get_data()
    lang = data.get("lang") or database.get_user_lang(callback.from_user.id)
    
    date_info = statistics.get_date_info(date_key, lang)
    stats_text = statistics.generate_text_stats(
        lang=lang, 
        date_from=date_info["date_from"], 
        date_to=date_info["date_to"], 
        date_title=date_info["title"]
    )
    
    await callback.message.edit_text(
        stats_text, 
        parse_mode="Markdown", 
        reply_markup=get_stats_actions_keyboard(lang, date_key)
    )
    
    # Send photos associated with the selected date range
    photos = database.get_photos_for_date_range(date_info["date_from"], date_info["date_to"])
    if photos:
        from aiogram.types import InputMediaPhoto
        all_file_ids = [p["file_id"] for p in photos]
        for i in range(0, len(all_file_ids), 10):
            chunk = all_file_ids[i:i+10]
            media_group = []
            for idx, fid in enumerate(chunk):
                if i == 0 and idx == 0:
                    caption_txt = f"📸 Фотографии проверок за {date_info['title']} ({len(all_file_ids)} шт.)"
                    media_group.append(InputMediaPhoto(media=fid, caption=caption_txt))
                else:
                    media_group.append(InputMediaPhoto(media=fid))
            try:
                await callback.message.answer_media_group(media=media_group)
            except Exception as e:
                logger.error(f"Error sending stats photos media group: {e}")

    await callback.answer()



@dp.callback_query(F.data == "sdate_select")
async def process_back_to_date_select(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang") or database.get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        LOCALIZATION[lang]['select_date_prompt'],
        parse_mode="Markdown",
        reply_markup=get_date_selection_keyboard(lang)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("sexcel:"))
async def process_excel_date_stats(callback: types.CallbackQuery, state: FSMContext):
    date_key = callback.data.split(":", 1)[1]
    data = await state.get_data()
    lang = data.get("lang") or database.get_user_lang(callback.from_user.id)
    
    date_info = statistics.get_date_info(date_key, lang)
    await callback.message.answer(LOCALIZATION[lang]['excel_loading'])
    try:
        excel_path = statistics.generate_excel_report(
            date_from=date_info["date_from"], 
            date_to=date_info["date_to"]
        )
        file = types.FSInputFile(excel_path)
        caption_text = LOCALIZATION[lang]['excel_caption'].format(date=date_info["title"])
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


# FALLBACK HANDLER TO ALWAYS KEEP KEYBOARD UPDATED WITH 🏁 Завершить
@dp.message(StateFilter("*"))
async def fallback_any_message(message: types.Message, state: FSMContext):
    user = database.get_user(message.from_user.id)
    lang = user.get('lang', 'ru') if user else 'ru'
    await state.set_state(CheckStates.main_menu)
    await message.answer(
        "📍 Выберите действие в меню:",
        reply_markup=get_main_menu_keyboard(lang)
    )


# ==========================================
# FLASK WEBHOOK SETUP FOR DEPLOYMENT (PaaS/PythonAnywhere)
# ==========================================
from flask import Flask, request, jsonify
import asyncio

app = Flask(__name__)

# Initialize database on startup
try:
    database.init_db()
except Exception as e:
    logger.error(f"Error initializing database: {e}")

@app.route("/", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        try:
            json_string = request.get_data().decode("utf-8")
            update = types.Update.model_validate_json(json_string)
            asyncio.run(dp.feed_webhook_update(bot, update))
            return "OK", 200
        except Exception as e:
            logger.error(f"Webhook update processing failed: {e}")
            return "Internal Server Error", 500
    else:
        return "Forbidden", 403

@app.route("/set_webhook", methods=["GET"])
def set_webhook_route():
    host = request.headers.get("Host", "")
    if not host:
        return "Host header missing", 400
    
    webhook_url = f"https://{host}/"
    
    async def set_hook():
        return await bot.set_webhook(webhook_url)
    
    try:
        success = asyncio.run(set_hook())
        if success:
            return f"Webhook successfully set to: {webhook_url}", 200
        else:
            return "Telegram rejected webhook setting", 500
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        return f"Error setting webhook: {e}", 500

@app.route("/clear_webhook", methods=["GET"])
def clear_webhook_route():
    async def clear_hook():
        return await bot.delete_webhook()
    
    try:
        success = asyncio.run(clear_hook())
        if success:
            return "Webhook successfully cleared!", 200
        else:
            return "Telegram rejected webhook deletion", 500
    except Exception as e:
        logger.error(f"Failed to clear webhook: {e}")
        return f"Error clearing webhook: {e}", 500


# BACKGROUND 3-HOUR REMINDER SCHEDULER
async def schedule_3_hour_reminders():
    INTERVAL = 3 * 3600  # 3 hours = 10800 seconds
    while True:
        try:
            await asyncio.sleep(INTERVAL)
            
            # Send notification to group
            target_chats = [config.REPORT_GROUP_ID]
            raw_str = str(abs(config.REPORT_GROUP_ID))
            if not str(config.REPORT_GROUP_ID).startswith("-100"):
                target_chats.extend([int(f"-100{raw_str}"), int(f"-{raw_str}"), abs(config.REPORT_GROUP_ID)])
            group_msg = (
                "🔔 <b>ВНИМАНИЕ! ПРИШЛО ВРЕМЯ ОБХОДА СКЛАДА!</b>\n\n"
                "📋 Прошло 3 часа. Пожалуйста, начните новую проверку зон склада в боте."
            )
            for chat_id in target_chats:
                try:
                    await bot.send_message(chat_id=chat_id, text=group_msg, parse_mode="HTML")
                    break
                except Exception as e:
                    logger.error(f"Failed sending 3-hour reminder to group {chat_id}: {e}")

            # Send notification to all registered users
            users = database.get_all_users()
            user_msg = (
                "🔔 *Внимание! Пришло время обхода склада!*\n\n"
                "🔒 Прошло 3 часа. Все зоны обновлены. Пожалуйста, нажмите *'📝 Новая проверка'*, чтобы провести новый обход зон склада."
            )
            for u in users:
                user_id = u['user_id']
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=user_msg,
                        parse_mode="Markdown",
                        reply_markup=get_main_menu_keyboard('ru')
                    )
                    await asyncio.sleep(0.05)
                except Exception as e:
                    logger.warning(f"Could not send 3-hour reminder to user {user_id}: {e}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in schedule_3_hour_reminders loop: {e}")
            await asyncio.sleep(60)


# MAIN RUNNER FOR LOCAL POLLING
async def main():
    database.init_db()
    # Delete webhook to allow polling locally if it was set
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(schedule_3_hour_reminders())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
