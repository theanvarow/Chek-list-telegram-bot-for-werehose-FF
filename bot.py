import os
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter, CommandObject
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

import socket
import sys
from aiogram.client.session.aiohttp import AiohttpSession

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SINGLE_BOT_INSTANCE_PORT = 47830
_bot_lock_socket = None

def ensure_single_bot_instance():
    global _bot_lock_socket
    try:
        _bot_lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _bot_lock_socket.bind(('127.0.0.1', SINGLE_BOT_INSTANCE_PORT))
        _bot_lock_socket.listen(1)
        logger.info("Single bot instance lock acquired (port 47830).")
    except socket.error:
        logger.error("Another bot.py instance is already running! Exiting duplicate process.")
        sys.exit(0)

ensure_single_bot_instance()

# Initialize bot and dispatcher
if not config.BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables or .env file!")

session = AiohttpSession(timeout=30.0)
bot = Bot(token=config.BOT_TOKEN, session=session)
dp = Dispatcher(storage=MemoryStorage())

# Localization Dictionary (Russian only)
LOCALIZATION = {
    'ru': {
        'select_lang': "Пожалуйста, выберите язык:",
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
        'item_pallets': "Пустые поддоны",
        'item_floor': "Товары на полу",
        'item_damaged': "Брак товар",
        'item_bags': "Пустой пакет",
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
        'btn_all_excel': "📁 ВСЕ отчеты (В одном файле)",
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
    selecting_otdel = State()
    main_menu = State()
    selecting_zone = State()
    selecting_status = State()
    filling_checklist = State()
    selecting_notified_user = State()
    uploading_photos = State()
    writing_comment = State()
    querying_zone = State()
    uploading_fix_photo = State()

def get_otdel_keyboard(prefix: str = "set_otdel:"):
    keyboard = []
    otdely = getattr(config, "OTDELY", ["ОТД Входящий поток", "ОТД Возвратный поток", "ОКЗ", "РАО", "ГОВП", "СЕРВИС", "ЦПТ"])
    row = []
    for i, otdel in enumerate(otdely):
        row.append(InlineKeyboardButton(text=f"🏢 {otdel}", callback_data=f"{prefix}{otdel}"))
        if len(row) == 2 or i == len(otdely) - 1:
            keyboard.append(row)
            row = []
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_starshiy_smena_keyboard(otdel: str = None, lang: str = "ru"):
    keyboard = []
    starshiy_dict = getattr(config, "STARSHIY_SMENA", {})
    
    if otdel and otdel in starshiy_dict:
        smena_list = starshiy_dict[otdel]
        for idx, u in enumerate(smena_list):
            name = u.get("name", f"{otdel}")
            icon = "🚚" if "Межсклад" in name else "👨‍✈️"
            display = f"{icon} {name}"
            keyboard.append([InlineKeyboardButton(text=display, callback_data=f"set_resp:{otdel}:{idx}")])
            
        other_otdel_text = "📂 Выбрать из другого отдела"
        keyboard.append([InlineKeyboardButton(text=other_otdel_text, callback_data="set_resp_otdel_menu")])
    else:
        # Department selection menu
        otdely = getattr(config, "OTDELY", ["ОКЗ", "ОТД", "РАО", "ГОВП", "СЕРВИС", "ЦПТ"])
        row = []
        for o in otdely:
            row.append(InlineKeyboardButton(text=f"🏢 {o}", callback_data=f"set_resp_otdel:{o}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
            
    skip_text = "⏭️ Никого (Пропустить)"
    keyboard.append([InlineKeyboardButton(text=skip_text, callback_data="set_resp:skip")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_starshiy_smena_members_keyboard(otdel: str, shift_idx: int):
    keyboard = []
    starshiy_dict = getattr(config, "STARSHIY_SMENA", {})
    smena_list = starshiy_dict.get(otdel, [])
    if 0 <= shift_idx < len(smena_list):
        u = smena_list[shift_idx]
        members = u.get("members", [])
        
        for m_idx, m in enumerate(members):
            role = m.get("role", "Сотрудник")
            username = m.get("username", "")
            icon = "👨‍✈️" if "Старший" in role else ("👨‍🏫" if "Наставник" in role else "👤")
            un_str = f" (@{username.lstrip('@')})" if username else ""
            btn_text = f"{icon} {role}{un_str}"
            keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"set_member:{otdel}:{shift_idx}:{m_idx}")])
            
        # Option to select all together
        keyboard.append([InlineKeyboardButton(text="👥 Вся смена (Все вместе)", callback_data=f"set_member:{otdel}:{shift_idx}:all")])
        
    # Back button
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад к сменам", callback_data=f"set_resp_otdel:{otdel}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)





def get_main_menu_keyboard(lang: str = "ru"):

    keyboard = [
        [KeyboardButton(text=LOCALIZATION['ru']['btn_new_check']), KeyboardButton(text=LOCALIZATION['ru']['btn_stats'])]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_date_selection_keyboard(lang: str = "ru"):
    now = datetime.now()
    d0 = now.date()
    
    all_btn_text = LOCALIZATION.get(lang, {}).get('btn_all_excel', "📁 ВСЕ отчеты (В одном файле)")
    
    keyboard = [
        [InlineKeyboardButton(text=all_btn_text, callback_data="sexcel:all")]
    ]
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
    date_info = statistics.get_date_info(date_key, lang)
    btn_excel = f"📥 Скачать Excel ({date_info['title']})"
    btn_all_excel = "📁 ВСЕ отчеты (В одном файле)"
    btn_change_date = "📅 Выбрать другую дату"
        
    keyboard = [
        [InlineKeyboardButton(text=btn_excel, callback_data=f"sexcel:{date_key}")],
        [InlineKeyboardButton(text=btn_all_excel, callback_data="sexcel:all")],
        [InlineKeyboardButton(text=btn_change_date, callback_data="sdate_select")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



def get_zone_keyboard(zone_statuses: dict = None, prefix: str = "szone:"):
    if zone_statuses is None:
        zone_statuses = {}
    keyboard = []
    
    for i, zone in enumerate(config.ZONES):
        status = zone_statuses.get(zone)
        prefix_icon = "✅ " if status == "Чисто" else ("⚠️ " if status == "Есть замечания" else "🔒 ")
        text = f"{prefix_icon}{zone}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"{prefix}{i}")])
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_status_keyboard(lang: str = "ru"):
    keyboard = [
        [InlineKeyboardButton(text=LOCALIZATION[lang]['btn_clean'], callback_data="status:clean")],
        [InlineKeyboardButton(text=LOCALIZATION[lang]['btn_issues'], callback_data="status:issues")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_checklist_keyboard(lang: str = 'ru'):
    keyboard = [
        [InlineKeyboardButton(text=f"📦 {LOCALIZATION[lang]['item_boxes']}", callback_data="toggle:boxes")],
        [InlineKeyboardButton(text=f"🪵 {LOCALIZATION[lang]['item_pallets']}", callback_data="toggle:pallets")],
        [InlineKeyboardButton(text=f"📦 {LOCALIZATION[lang]['item_floor']}", callback_data="toggle:floor")],
        [InlineKeyboardButton(text=f"⚠️ {LOCALIZATION[lang]['item_damaged']}", callback_data="toggle:damaged")],
        [InlineKeyboardButton(text=f"🛍 {LOCALIZATION[lang]['item_bags']}", callback_data="toggle:bags")],
        [InlineKeyboardButton(text=f"🧹 {LOCALIZATION[lang]['item_mess']}", callback_data="toggle:mess")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_photo_keyboard(lang: str, photo_count: int):
    if photo_count > 0:
        done_text = f"➡️ Готово ({photo_count} фото)"
    else:
        done_text = "➡️ Готово"
    
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
    state = data.get("state")
    current_state = await state.get_state() if state else None
    if current_state == CheckStates.uploading_fix_photo:
        return await handler(event, data)

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
        if event.data and event.data.startswith("fix_report:"):
            return await handler(event, data)
        return
    return await handler(event, data)



# START COMMAND
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext, command: CommandObject = None):
    await state.clear()
    user = ensure_user_registered(message.from_user)
    
    args = command.args if command else None
    if args and args.startswith("fix_"):
        try:
            report_id = int(args.split("fix_")[1])
            report = database.get_report_by_id(report_id)
            if not report:
                await message.answer("⚠️ Отчет не найден в базе данных.")
                return
                
            if report.get("is_fixed"):
                fixed_by = report.get("fixed_by", "")
                await message.answer(f"✅ Данное замечание уже исправлено! ({fixed_by})")
                return
                
            await state.update_data(fixing_report_id=report_id)
            await state.set_state(CheckStates.uploading_fix_photo)
            
            import html
            prompt = (
                f"🛠 <b>Исправление замечания по отчету #{report_id}</b>\n"
                f"📍 <b>Зона:</b> {html.escape(report.get('zone', ''))}\n\n"
                "📸 Пожалуйста, отправьте <b>фотографию</b>, подтверждающую исправление замечания.\n"
                "<i>(Вы можете добавить описание/комментарий в подписи к фото)</i>"
            )
            await message.answer(prompt, parse_mode="HTML")
            return
        except Exception as e:
            logger.error(f"Error handling deep link fix start: {e}")
            
    lang = 'ru'
    await state.update_data(lang=lang)
    await state.set_state(CheckStates.selecting_otdel)
    fio_esc = statistics.escape_markdown(user['fio']) if user else ""
    prompt = (
        f"Привет, *{fio_esc}*! Это чек-лист бот.\n\n"
        "🏢 *Пожалуйста, выберите ваш отдел:*"
    )
    await message.answer(
        prompt,
        parse_mode="Markdown",
        reply_markup=get_otdel_keyboard(prefix="start_otdel:")
    )

@dp.callback_query(F.data.startswith("start_otdel:"))
async def process_start_otdel(callback: types.CallbackQuery, state: FSMContext):
    otdel = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    
    database.update_user_otdel(user_id, otdel)
    await state.update_data(otdel=otdel)
    
    data = await state.get_data()
    lang = data.get("lang", "ru")
    user = database.get_user(user_id)
    fio_esc = statistics.escape_markdown(user['fio']) if user else ""
    
    await callback.message.edit_text(
        f"🏢 *Отдел сохранен:* {otdel}\n\n" + LOCALIZATION[lang]['welcome'].format(fio=fio_esc),
        parse_mode="Markdown"
    )
    await callback.message.answer(
        "Выберите действие ниже:",
        reply_markup=get_main_menu_keyboard(lang)
    )
    await state.set_state(CheckStates.main_menu)
    await callback.answer()


# MAIN MENU COMMAND HANDLING
@dp.message(StateFilter("*"), F.text & F.text.contains("Новая проверка"))
async def start_check(message: types.Message, state: FSMContext):
    user = ensure_user_registered(message.from_user)
    lang = 'ru'
    user_otdel = user.get('otdel') or "ОКЗ"
    await state.update_data(lang=lang, otdel=user_otdel)
    await state.set_state(CheckStates.selecting_zone)
    
    zone_statuses = database.get_zone_statuses_for_user(message.from_user.id, hours=3)
    
    await message.answer(
        LOCALIZATION[lang]['prompt_zone'],
        parse_mode="Markdown",
        reply_markup=get_zone_keyboard(zone_statuses=zone_statuses, prefix="szone:")
    )

@dp.callback_query(F.data.startswith("check_otdel:"))
async def process_check_otdel(callback: types.CallbackQuery, state: FSMContext):
    otdel = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    
    database.update_user_otdel(user_id, otdel)
    await state.update_data(otdel=otdel)
    
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    await state.set_state(CheckStates.selecting_zone)
    zone_statuses = database.get_zone_statuses_for_user(user_id, hours=3)
    
    prompt = f"🏢 *Отдел:* {otdel}\n\n" + LOCALIZATION[lang]['prompt_zone']
    await callback.message.edit_text(
        prompt,
        parse_mode="Markdown",
        reply_markup=get_zone_keyboard(zone_statuses, prefix="szone:")
    )
    await callback.answer()


@dp.message(StateFilter("*"), F.text & (F.text.contains("Проверить зону") | F.text.contains("проверка зона")))
async def start_query_zone(message: types.Message, state: FSMContext):
    ensure_user_registered(message.from_user)
    lang = 'ru'
    await state.update_data(lang=lang)
    await state.set_state(CheckStates.querying_zone)
    zone_statuses = database.get_zone_statuses_today()
    await message.answer(LOCALIZATION[lang]['prompt_query_zone'], reply_markup=get_zone_keyboard(zone_statuses, prefix="qzone:"))


@dp.message(F.text == "📊 Статистика")
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
        if report.get('has_empty_boxes'): issues_items.append(LOCALIZATION[lang]['item_boxes'])
        if report.get('has_empty_pallets'): issues_items.append(LOCALIZATION[lang]['item_pallets'])
        if report.get('has_goods_on_floor'): issues_items.append(LOCALIZATION[lang]['item_floor'])
        if report.get('has_damaged_goods'): issues_items.append(LOCALIZATION[lang]['item_damaged'])
        if report.get('has_empty_bags'): issues_items.append(LOCALIZATION[lang]['item_bags'])
        if report.get('has_mess'):  issues_items.append(LOCALIZATION[lang]['item_mess'])
        if issues_items:
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
        # User clicked "Есть замечания"
        await state.update_data(
            status="Есть замечания",
            has_empty_boxes=False,
            has_empty_pallets=False,
            has_goods_on_floor=False,
            has_damaged_goods=False,
            has_empty_bags=False,
            has_mess=False
        )
        await state.set_state(CheckStates.filling_checklist)
        try:
            await callback.message.edit_text(
                LOCALIZATION[lang]['prompt_checklist'],
                reply_markup=get_checklist_keyboard(lang)
            )
        except Exception:
            await callback.message.answer(
                LOCALIZATION[lang]['prompt_checklist'],
                reply_markup=get_checklist_keyboard(lang)
            )
    await callback.answer()

@dp.callback_query(StateFilter("*"), F.data.startswith("toggle:"))
async def process_checklist_toggle(callback: types.CallbackQuery, state: FSMContext):
    toggle_item = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    boxes = (toggle_item == "boxes")
    pallets = (toggle_item == "pallets")
    floor = (toggle_item == "floor")
    damaged = (toggle_item == "damaged")
    bags = (toggle_item == "bags")
    mess = (toggle_item == "mess")
        
    await state.update_data(
        has_empty_boxes=boxes,
        has_empty_pallets=pallets,
        has_goods_on_floor=floor,
        has_damaged_goods=damaged,
        has_empty_bags=bags,
        has_mess=mess
    )
    
    user = database.get_user(callback.from_user.id)
    user_otdel = data.get("otdel") or (user.get("otdel") if user else None) or "ОТД Входящий поток"
    
    await state.set_state(CheckStates.selecting_notified_user)
    
    prompt_resp = f"👨‍✈️ *Выберите ответственного за зону ({user_otdel}):*"
    try:
        await callback.message.edit_text(
            prompt_resp,
            parse_mode="Markdown",
            reply_markup=get_starshiy_smena_keyboard(otdel=user_otdel, lang='ru')
        )
    except Exception:
        await callback.message.answer(
            prompt_resp,
            parse_mode="Markdown",
            reply_markup=get_starshiy_smena_keyboard(otdel=user_otdel, lang='ru')
        )
    await callback.answer()


@dp.callback_query(StateFilter("*"), F.data == "set_resp_otdel_menu")
async def process_starshiy_smena_otdel_menu(callback: types.CallbackQuery, state: FSMContext):
    prompt_msg = "🏢 *Выберите отдел ответственного за зону:*"
    try:
        await callback.message.edit_text(
            prompt_msg,
            parse_mode="Markdown",
            reply_markup=get_starshiy_smena_keyboard(otdel=None, lang='ru')
        )
    except Exception:
        await callback.message.answer(
            prompt_msg,
            parse_mode="Markdown",
            reply_markup=get_starshiy_smena_keyboard(otdel=None, lang='ru')
        )
    await callback.answer()


@dp.callback_query(StateFilter("*"), F.data.startswith("set_resp_otdel:"))
async def process_starshiy_smena_otdel_select(callback: types.CallbackQuery, state: FSMContext):
    otdel = callback.data.split(":")[1]
    prompt_msg = f"👨‍✈️ *Выберите ответственного за зону ({otdel}):*"
    try:
        await callback.message.edit_text(
            prompt_msg,
            parse_mode="Markdown",
            reply_markup=get_starshiy_smena_keyboard(otdel=otdel, lang='ru')
        )
    except Exception:
        await callback.message.answer(
            prompt_msg,
            parse_mode="Markdown",
            reply_markup=get_starshiy_smena_keyboard(otdel=otdel, lang='ru')
        )
    await callback.answer()



@dp.callback_query(StateFilter("*"), F.data.startswith("set_resp:"))
async def process_responsible_user_selection(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    if parts[1] == "skip":
        notified_user = None
        await state.update_data(notified_user=notified_user, photos=[])
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
        return

    otdel_key = parts[1]
    u_idx = int(parts[2])
    starshiy_dict = getattr(config, "STARSHIY_SMENA", {})
    smena_list = starshiy_dict.get(otdel_key, [])
    
    if 0 <= u_idx < len(smena_list):
        u = smena_list[u_idx]
        members = u.get("members", [])
        
        # If this shift has multiple individual members, open member sub-menu!
        if len(members) > 1:
            name = u.get("name", f"{otdel_key}")
            prompt_msg = f"👨‍✈️ *Выберите ответственного за зону: {name}*"
            try:
                await callback.message.edit_text(
                    prompt_msg,
                    parse_mode="Markdown",
                    reply_markup=get_starshiy_smena_members_keyboard(otdel_key, u_idx)
                )
            except Exception:
                await callback.message.answer(
                    prompt_msg,
                    parse_mode="Markdown",
                    reply_markup=get_starshiy_smena_members_keyboard(otdel_key, u_idx)
                )
            await callback.answer()
            return
            
        name = u.get("name", "")
        username = u.get("username")
        if username:
            formatted_un = " ".join([un if un.startswith("@") else f"@{un}" for un in username.split()])
            notified_user = f"{name} ({formatted_un})"
        else:
            notified_user = name
    else:
        notified_user = None
        
    await state.update_data(notified_user=notified_user, photos=[])
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


@dp.callback_query(StateFilter("*"), F.data.startswith("set_member:"))
async def process_member_selection(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    otdel_key = parts[1]
    shift_idx = int(parts[2])
    m_val = parts[3]
    
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    starshiy_dict = getattr(config, "STARSHIY_SMENA", {})
    smena_list = starshiy_dict.get(otdel_key, [])
    
    if 0 <= shift_idx < len(smena_list):
        u = smena_list[shift_idx]
        shift_name = u.get("name", f"{otdel_key}")
        members = u.get("members", [])
        
        if m_val == "all":
            usernames = [m.get("username") for m in members if m.get("username")]
            formatted_un = " ".join([un if un.startswith("@") else f"@{un}" for un in usernames])
            notified_user = f"{shift_name} ({formatted_un})"
        else:
            m_idx = int(m_val)
            if 0 <= m_idx < len(members):
                m = members[m_idx]
                role = m.get("role", "")
                username = m.get("username", "")
                un_str = f" (@{username.lstrip('@')})" if username else ""
                notified_user = f"{shift_name} {role}{un_str}"
            else:
                notified_user = shift_name
    else:
        notified_user = None
        
    await state.update_data(notified_user=notified_user, photos=[])
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
        
        success_msg = f"✅ Фото успешно загружено! (Всего: {len(uploaded_photos)})"
        await message.answer(
            success_msg,
            reply_markup=get_photo_keyboard(lang, len(uploaded_photos))
        )
    except Exception as e:
        logger.error(f"Error downloading photo: {e}")
        err_msg = "⚠️ Не удалось загрузить фото. Пожалуйста, попробуйте еще раз."
        await message.answer(err_msg)

@dp.message(CheckStates.uploading_photos, F.text & (F.text.contains("Готово") | F.text.icontains("готово")))
async def process_photos_done(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    await state.set_state(CheckStates.writing_comment)
    await message.answer(
        LOCALIZATION[lang]['prompt_comment'],
        reply_markup=get_comment_keyboard(lang)
    )

@dp.message(CheckStates.uploading_photos, F.text & (F.text.contains("Пропустить") | F.text.icontains("пропустить")))
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
    comment = (message.text or message.caption or "").strip()
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    if comment == "⏭️ Пропустить комментарий":
        comment = ""
        
    zone = data.get("zone")
    status = data.get("status")
    boxes = data.get("has_empty_boxes", False)
    pallets = data.get("has_empty_pallets", False)
    floor = data.get("has_goods_on_floor", False)
    damaged = data.get("has_damaged_goods", False)
    bags = data.get("has_empty_bags", False)
    mess = data.get("has_mess", False)
    photos = data.get("photos", [])
    
    # Get user info and department
    user = database.get_user(message.from_user.id)
    otdel = data.get("otdel") or (user.get("otdel") if user else "ОКЗ")
    
    notified_user = data.get("notified_user")
    
    # Save to SQLite database
    report_id = database.save_report(
        user_id=message.from_user.id,
        zone=zone,
        status=status,
        has_empty_boxes=boxes,
        has_goods_on_floor=floor,
        has_mess=mess,
        comment=comment,
        photos=photos,
        otdel=otdel,
        notified_user=notified_user,
        has_empty_pallets=pallets,
        has_damaged_goods=damaged,
        has_empty_bags=bags
    )
    
    fio = user["fio"] if user else "Неизвестный"
    fio_esc = statistics.escape_markdown(fio)
    if user and user.get("username"):
        username_esc = statistics.escape_markdown(user['username'])
        fio_esc = f"{fio_esc} (@{username_esc})"
    
    # Construct summary message
    status_text = LOCALIZATION[lang]['status_clean'] if status == 'Чисто' else LOCALIZATION[lang]['status_issues']
    zone_esc = statistics.escape_markdown(zone)
    otdel_esc = statistics.escape_markdown(otdel)
    
    summary = f"📋 *Отчет #{report_id} успешно сохранен!*\n\n🏢 *Отдел:* {otdel_esc}\n📍 *Зона:* {zone_esc}\n👤 *Проверил:* {fio_esc}\n📊 *Состояние:* {status_text}\n"
    
    if status != "Чисто":
        issues_items = []
        if boxes: issues_items.append(LOCALIZATION[lang]['item_boxes'])
        if pallets: issues_items.append(LOCALIZATION[lang]['item_pallets'])
        if floor: issues_items.append(LOCALIZATION[lang]['item_floor'])
        if damaged: issues_items.append(LOCALIZATION[lang]['item_damaged'])
        if bags: issues_items.append(LOCALIZATION[lang]['item_bags'])
        if mess:  issues_items.append(LOCALIZATION[lang]['item_mess'])
        if issues_items:
            summary += f"🔍 *Замечания:* {', '.join(issues_items)}\n"
        if notified_user:
            notified_esc = statistics.escape_markdown(notified_user)
            summary += f"👨‍✈️ *Ответственное лицо за зону:* {notified_esc}\n"
        
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
        report_id=report_id,
        otdel=otdel,
        notified_user=notified_user,
        pallets=pallets,
        damaged=damaged,
        bags=bags
    ))

    await state.set_state(CheckStates.main_menu)
    await message.answer(
        summary,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(lang)
    )


# GROUP REPORT HELPERS & HANDLERS
async def send_single_report_to_group(
    bot: Bot,
    group_id: int,
    zone: str,
    status: str,
    fio: str,
    username: str,
    boxes: bool,
    floor: bool,
    mess: bool,
    comment: str,
    photos: list,
    report_id: int,
    otdel: str = "ОКЗ",
    notified_user: str = None,
    pallets: bool = False,
    damaged: bool = False,
    bags: bool = False
):
    import html
    fio_esc = html.escape(fio)
    otdel_esc = html.escape(otdel)
    if username:
        username_esc = html.escape(username)
        fio_display = f"{fio_esc} (@{username_esc})"
    else:
        fio_display = fio_esc
        
    zone_esc = html.escape(zone)
    status_text = "Чисто ✅" if status == 'Чисто' else "Есть замечания ⚠️"
    now_str = datetime.now().strftime("%Y-%m-%d - %H:%M:%S")
    
    msg = f"📋 <b>НОВЫЙ ОТЧЕТ ПРОВЕРКИ ЗОНЫ #{report_id}</b>\n\n"
    msg += f"🏢 <b>Отдел:</b> {otdel_esc}\n"
    msg += f"👤 <b>Проверяющий:</b> {fio_display}\n"
    msg += f"📍 <b>Зона / Этаж:</b> {zone_esc}\n"
    msg += f"📊 <b>Состояние:</b> {status_text}\n"
    msg += f"📅 <b>Дата проверки:</b> {now_str}\n"

    if status != "Чисто":
        issues_items = []
        if boxes: issues_items.append("Пустые коробки")
        if pallets: issues_items.append("Пустые поддоны")
        if floor: issues_items.append("Товары на полу")
        if damaged: issues_items.append("Брак товар")
        if bags: issues_items.append("Пустой пакет")
        if mess:  issues_items.append("Общий беспорядок")
        if issues_items:
            msg += f"🔍 <b>Замечания:</b> {', '.join(issues_items)}\n"
        if notified_user:
            msg += f"👨‍✈️ <b>Ответственное лицо за зону:</b> {html.escape(notified_user)}\n"

        
    if comment:
        comment_esc = html.escape(comment)
        msg += f"\n💬 <b>Комментарий:</b> <i>{comment_esc}</i>\n"
        
    target_chats = [group_id]
    raw_str = str(abs(group_id))
    if not str(group_id).startswith("-100"):
        target_chats.extend([int(f"-100{raw_str}"), int(f"-{raw_str}"), abs(group_id)])
    
    fix_keyboard = None
    if status != "Чисто":
        try:
            bot_info = await bot.get_me()
            bot_username = bot_info.username
            url = f"https://t.me/{bot_username}?start=fix_{report_id}"
            fix_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🛠 Исправить", url=url)
            ]])
        except Exception as e:
            logger.error(f"Error creating deep link url for fix keyboard: {e}")
            fix_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🛠 Исправить", callback_data=f"fix_report:{report_id}")
            ]])

    for chat_id in target_chats:
        try:
            if photos:
                from aiogram.types import InputMediaPhoto
                all_file_ids = [item[1] if isinstance(item, tuple) else item for item in photos]
                if len(all_file_ids) <= 10:
                    # Single album with caption on first photo
                    media_group = []
                    for idx, fid in enumerate(all_file_ids):
                        if idx == 0:
                            media_group.append(InputMediaPhoto(media=fid, caption=msg, parse_mode="HTML"))
                        else:
                            media_group.append(InputMediaPhoto(media=fid))
                    await bot.send_media_group(chat_id=chat_id, media=media_group)
                else:
                    # More than 10 photos: send report text message first, then send photos in albums
                    await bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")
                    for i in range(0, len(all_file_ids), 10):
                        chunk = all_file_ids[i:i+10]
                        media_group = [InputMediaPhoto(media=fid) for fid in chunk]
                        await bot.send_media_group(chat_id=chat_id, media=media_group)
                
                # Send fix button action message if report has issues
                if fix_keyboard:
                    fix_notice = f"⚠️ <b>Отчет #{report_id} ({zone_esc}):</b> Замечания зафиксированы.\nЕсли замечание устранено, нажмите кнопку ниже для отправки фото:"
                    await bot.send_message(chat_id=chat_id, text=fix_notice, parse_mode="HTML", reply_markup=fix_keyboard)
            else:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML", reply_markup=fix_keyboard)
            break
        except Exception as e:
            logger.error(f"Failed sending single report to group chat_id {chat_id}: {e}")


# FIX REPORT HANDLERS
@dp.callback_query(F.data.startswith("fix_report:"))
async def process_fix_report_callback(callback: types.CallbackQuery, state: FSMContext):
    try:
        report_id = int(callback.data.split(":")[1])
    except Exception:
        await callback.answer("⚠️ Неверный ID отчета.", show_alert=True)
        return
        
    report = database.get_report_by_id(report_id)
    if not report:
        await callback.answer("⚠️ Отчет не найден в базе данных.", show_alert=True)
        return
        
    if report.get("is_fixed"):
        fixed_by = report.get("fixed_by", "")
        await callback.answer(f"✅ Данное замечание уже исправлено! ({fixed_by})", show_alert=True)
        return
        
    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        url = f"https://t.me/{bot_username}?start=fix_{report_id}"
        await callback.answer("👉 Нажмите для перехода в бота", url=url)
    except Exception:
        await callback.answer("📸 Пожалуйста, откройте личные сообщения с ботом.", show_alert=True)


@dp.message(CheckStates.uploading_fix_photo, F.photo)
async def process_fix_photo_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    report_id = data.get("fixing_report_id")
    
    if not report_id:
        await state.clear()
        return
        
    user = database.get_user(message.from_user.id)
    fixer_name = user["fio"] if user else (message.from_user.full_name or "Пользователь")
    if message.from_user.username:
        fixer_name += f" (@{message.from_user.username})"
        
    comment = message.caption or ""
    
    photo_file = message.photo[-1]
    file_id = photo_file.file_id
    
    filename = f"fix_report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    dest_path = os.path.join(config.PHOTOS_DIR, filename)
    
    try:
        file_info = await bot.get_file(file_id)
        await bot.download_file(file_info.file_path, dest_path)
    except Exception as e:
        logger.error(f"Error downloading fix photo: {e}")
        dest_path = None
        
    database.mark_report_fixed(
        report_id=report_id,
        fixed_by=fixer_name,
        fix_photo_path=dest_path,
        fix_telegram_file_id=file_id,
        fix_comment=comment
    )
    
    report = database.get_report_by_id(report_id)
    zone_name = report["zone"] if report else ""
    
    import html
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fix_msg = (
        f"✅ <b>ЗАМЕЧАНИЕ ИСПРАВЛЕНО!</b>\n\n"
        f"📋 <b>Отчет:</b> #{report_id}\n"
        f"📍 <b>Зона / Этаж:</b> {html.escape(zone_name)}\n"
        f"👤 <b>Исправил:</b> {html.escape(fixer_name)}\n"
    )
    if comment:
        fix_msg += f"💬 <b>Комментарий:</b> <i>{html.escape(comment)}</i>\n"
    fix_msg += f"📅 <b>Дата исправления:</b> {now_str}"

    
    try:
        await bot.send_photo(
            chat_id=config.REPORT_GROUP_ID,
            photo=file_id,
            caption=fix_msg,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed sending fix photo to group: {e}")
        
    await state.set_state(CheckStates.main_menu)
    await message.answer(
        f"✅ *Отчет #{report_id} успешно отмечен как исправленный!*\nСпасибо за работу.",
        parse_mode="Markdown"
    )

@dp.message(CheckStates.uploading_fix_photo, ~F.photo)
async def process_fix_photo_missing(message: types.Message, state: FSMContext):
    data = await state.get_data()
    report_id = data.get("fixing_report_id", "")
    await message.answer(
        f"📸 *Пожалуйста, отправьте именно фотографию*, подтверждающую исправление замечания #{report_id}.\n"
        f"_(Вы можете добавить текстовое описание прямо в подписи к фото)_",
        parse_mode="Markdown"
    )





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
            if r.get('has_empty_boxes'): issues.append("Пустые коробки")
            if r.get('has_empty_pallets'): issues.append("Пустые поддоны")
            if r.get('has_goods_on_floor'): issues.append("Товары на полу")
            if r.get('has_damaged_goods'): issues.append("Брак товар")
            if r.get('has_empty_bags'): issues.append("Пустой пакет")
            if r.get('has_mess'): issues.append("Беспорядок")
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
    all_time = date_info.get("all_time", False) or (date_key in ["all", "all_time"])
    stats_text = statistics.generate_text_stats(
        lang=lang, 
        date_from=date_info["date_from"], 
        date_to=date_info["date_to"], 
        date_title=date_info["title"],
        all_time=all_time
    )
    
    await callback.message.edit_text(
        stats_text, 
        parse_mode="Markdown", 
        reply_markup=get_stats_actions_keyboard(lang, date_key)
    )
    
    # Send photos associated with the selected date range
    photos = database.get_photos_for_date_range(date_info["date_from"], date_info["date_to"], all_time=all_time)
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
    all_time = date_info.get("all_time", False) or (date_key in ["all", "all_time"])
    await callback.message.answer(LOCALIZATION[lang]['excel_loading'])
    try:
        excel_path = statistics.generate_excel_report(
            date_from=date_info["date_from"], 
            date_to=date_info["date_to"],
            all_time=all_time
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
        excel_path = statistics.generate_excel_report(all_time=True)
        file = types.FSInputFile(excel_path)
        title_all = "За всё время (Все отчеты)"
        caption_text = LOCALIZATION[lang]['excel_caption'].format(date=title_all)
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
            
            # Generate 3-hour statistics summary
            summary_stats_html = statistics.generate_3hour_summary_stats()
            
            # Send notification and 3-hour leaderboard to group
            target_chats = [config.REPORT_GROUP_ID]
            raw_str = str(abs(config.REPORT_GROUP_ID))
            if not str(config.REPORT_GROUP_ID).startswith("-100"):
                target_chats.extend([int(f"-100{raw_str}"), int(f"-{raw_str}"), abs(config.REPORT_GROUP_ID)])
            
            group_msg = (
                "🔔 <b>ВНИМАНИЕ! ПРИШЛО ВРЕМЯ ОБХОДА СКЛАДА!</b>\n"
                "📋 <i>Прошло 3 часа. Пожалуйста, начните новую проверку зон склада в боте.</i>\n\n"
                f"{summary_stats_html}"
            )
            for chat_id in target_chats:
                try:
                    await bot.send_message(chat_id=chat_id, text=group_msg, parse_mode="HTML")
                    break
                except Exception as e:
                    logger.error(f"Failed sending 3-hour reminder to group {chat_id}: {e}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in schedule_3_hour_reminders loop: {e}")
            await asyncio.sleep(60)


@dp.error()
async def global_error_handler(event: types.ErrorEvent):
    logger.error(f"Global error handler caught exception: {event.exception}", exc_info=event.exception)
    return True


# MAIN RUNNER FOR LOCAL POLLING
async def main():
    database.init_db()
    # Delete webhook to allow polling locally if it was set
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.warning(f"Could not delete webhook: {e}")
        
    asyncio.create_task(schedule_3_hour_reminders())
    
    logger.info("Bot main runner started with auto-reconnect polling loop.")
    while True:
        try:
            logger.info("Starting Telegram Bot Polling...")
            await dp.start_polling(bot, handle_signals=False)
        except Exception as e:
            logger.error(f"Polling error encountered: {e}. Restarting polling in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())

