import re
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.config import ADMIN_CHAT_ID, TABLES
from bot.keyboards.inline import (
    dates_keyboard, times_keyboard,
    guests_keyboard, confirm_keyboard, admin_booking_keyboard,
    cancel_bookings_keyboard, floor_plan_keyboard,
)
from bot.keyboards.reply import (
    main_menu_keyboard, phone_keyboard, skip_back_keyboard, back_keyboard
)
from bot.middlewares.i18n import t
from bot.services import booking_service, poster_service

router = Router()

PHONE_REGEX = re.compile(r"^\+?[\d\s\-\(\)]{7,15}$")

# Map each table name → its hall key
TABLE_TO_HALL: dict[str, str] = {
    table: hall
    for hall, tables in TABLES.items()
    for table in tables
}

_HALL_TITLES = {
    "main":   "🏛 Основной зал",
    "second": "🔝 2nd Floor",
}


class BookingFSM(StatesGroup):
    table   = State()   # Step 1: floor plan — pick a table
    date    = State()   # Step 2: pick a date for that table
    time    = State()   # Step 3: pick an available time slot
    guests  = State()   # Step 4
    name    = State()   # Step 5
    phone   = State()   # Step 6
    comment = State()   # Step 7
    confirm = State()   # Step 8


_HAPPY_HOURS_BANNER_RU = (
    "\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "      ✦  <b>HAPPY HOURS</b>  ✦\n"
    "        🕐  12:00 — 16:00\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "💨  <b>Кальян</b>\n"
    "     <s>549 000 ₫</s>  ⟶  <b>459 000 ₫</b>  <i>· экономия 90 000 ₫</i>\n\n"
    "🍽  Меню кухни  ·  скидка <b>10 %</b>\n"
    "🥂  Пиво & коктейли  ·  <b>1 + 1</b>"
)

_HAPPY_HOURS_BANNER_VI = (
    "\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "      ✦  <b>HAPPY HOURS</b>  ✦\n"
    "        🕐  12:00 — 16:00\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "💨  <b>Thuốc lào / Sưa</b>\n"
    "     <s>549 000 ₫</s>  ⟶  <b>459 000 ₫</b>  <i>· tiết kiệm 90 000 ₫</i>\n\n"
    "🍽  Thực đơn  ·  <b>giảm 10%</b>\n"
    "🍺  Bia & cocktail  ·  <b>1 + 1</b>"
)


def _floor_caption_initial(lang: str, hall: str) -> str:
    hall_title = _HALL_TITLES.get(hall, hall)
    if lang == "ru":
        banner = _HAPPY_HOURS_BANNER_RU
        return (
            f"🗺 <b>Выберите стол</b>\n"
            f"{hall_title}\n\n"
            f"Переключайте этажи кнопками вверху\n"
            f"Нажмите на зелёный стол для бронирования"
            f"{banner}"
        )
    elif lang == "vi":
        banner = _HAPPY_HOURS_BANNER_VI
        return (
            f"🗺 <b>Chọn bàn</b>\n"
            f"{hall_title}\n\n"
            f"Chuyển tầng bằng các nút phía trên\n"
            f"Nhấn vào bàn màu xanh để đặt chỗ"
            f"{banner}"
        )
    else:
        banner = _HAPPY_HOURS_BANNER_EN
        return (
            f"🗺 <b>Select a table</b>\n"
            f"{hall_title}\n\n"
            f"Switch floors using the buttons above\n"
            f"Tap a green table to book it"
            f"{banner}"
        )


# ─── Entry point ──────────────────────────────────────────────────────────────
@router.message(lambda m: m.text in ("📅 Забронировать столик", "📅 Book a Table", "📅 Đặt bàn"))
async def start_booking(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    hall = "main"
    await state.update_data(lang=lang, hall=hall)
    caption = _floor_caption_initial(lang, hall)
    await message.answer(
        caption,
        parse_mode="HTML",
        reply_markup=floor_plan_keyboard(hall, {}, lang, back_callback=None),
    )
    await state.set_state(BookingFSM.table)


# ─── Back navigation ──────────────────────────────────────────────────────────

@router.callback_query(BookingFSM.date, lambda c: c.data == "back:table")
async def back_to_table(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    hall = data.get("hall", "main")
    caption = _floor_caption_initial(lang, hall)
    await call.message.edit_text(
        caption, parse_mode="HTML",
        reply_markup=floor_plan_keyboard(hall, {}, lang, back_callback=None),
    )
    await state.set_state(BookingFSM.table)
    await call.answer()


@router.callback_query(BookingFSM.time, lambda c: c.data == "back:date")
async def back_to_date(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await call.message.edit_text(t("choose_date", lang), reply_markup=dates_keyboard(lang))
    await state.set_state(BookingFSM.date)
    await call.answer()


@router.callback_query(BookingFSM.guests, lambda c: c.data == "back:time")
async def back_to_time(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    hall  = data.get("hall", "main")
    table = data.get("table", "")
    date  = data.get("date", "")
    booked = await booking_service.get_booked_times_for_table(hall, table, date)
    kb = times_keyboard(booked, lang)
    if kb is None:
        no_slots_msg = (
            "😔 На этот день все слоты заняты. Выберите другую дату."
            if lang == "ru" else (
            "😔 Hôm nay đã hết chỗ. Vui lòng chọn ngày khác."
            if lang == "vi" else
            "😔 All slots for this day are taken. Please choose another date.")
        )
        await call.answer(no_slots_msg, show_alert=True)
        return
    await call.message.edit_text(t("choose_time", lang), reply_markup=kb)
    await state.set_state(BookingFSM.time)
    await call.answer()


@router.message(BookingFSM.name, lambda m: m.text in ("◀️ Назад", "◀️ Back", "◀️ Quay lại"))
async def back_from_name(message: Message, state: FSMContext, lang: str) -> None:
    await message.answer(t("choose_guests", lang), reply_markup=guests_keyboard(lang))
    await state.set_state(BookingFSM.guests)


@router.message(BookingFSM.phone, lambda m: m.text in ("◀️ Назад", "◀️ Back", "◀️ Quay lại"))
async def back_from_phone(message: Message, state: FSMContext, lang: str) -> None:
    await message.answer(t("enter_name", lang), reply_markup=back_keyboard(lang))
    await state.set_state(BookingFSM.name)


@router.message(BookingFSM.comment, lambda m: m.text in ("◀️ Назад", "◀️ Back", "◀️ Quay lại"))
async def back_from_comment(message: Message, state: FSMContext, lang: str) -> None:
    await message.answer(t("enter_phone", lang), reply_markup=phone_keyboard(lang))
    await state.set_state(BookingFSM.phone)


# ─── Step 1: Table (floor plan) ───────────────────────────────────────────────

@router.callback_query(BookingFSM.table, lambda c: c.data == "noop")
async def noop_handler(call: CallbackQuery) -> None:
    await call.answer()


@router.callback_query(BookingFSM.table, lambda c: c.data and c.data.startswith("switch_hall:"))
async def switch_hall(call: CallbackQuery, state: FSMContext) -> None:
    """Switch the floor plan to another hall without leaving the table step."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    hall = call.data.split(":")[1]
    await state.update_data(hall=hall)
    caption = _floor_caption_initial(lang, hall)
    await call.message.edit_text(
        caption, parse_mode="HTML",
        reply_markup=floor_plan_keyboard(hall, {}, lang, back_callback=None),
    )
    await call.answer()


@router.callback_query(BookingFSM.table, lambda c: c.data == "table:busy")
async def step_table_busy(call: CallbackQuery) -> None:
    await call.answer("⛔ Стол занят / Table is taken", show_alert=True)


@router.callback_query(BookingFSM.table, lambda c: c.data and c.data.startswith("table:"))
async def step_table(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    table = call.data.split(":")[1]
    hall = TABLE_TO_HALL.get(table, data.get("hall", "main"))
    await state.update_data(table=table, hall=hall)
    await call.message.edit_text(t("choose_date", lang), reply_markup=dates_keyboard(lang))
    await state.set_state(BookingFSM.date)
    await call.answer()


# ─── Step 2: Date ─────────────────────────────────────────────────────────────

@router.callback_query(BookingFSM.date, lambda c: c.data and c.data.startswith("date:"))
async def step_date(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang  = data.get("lang", "ru")
    hall  = data.get("hall", "main")
    table = data.get("table", "")
    chosen_date = call.data.split(":")[1]
    await state.update_data(date=chosen_date)
    # Show only slots where THIS specific table is free
    booked = await booking_service.get_booked_times_for_table(hall, table, chosen_date)
    kb = times_keyboard(booked, lang)
    if kb is None:
        no_slots_msg = (
            "😔 На этот день все слоты для выбранного стола заняты.\n"
            "Пожалуйста, выберите другую дату."
            if lang == "ru" else (
            "😔 Bàn này đã kín chỗ vào ngày đó.\nVui lòng chọn ngày khác."
            if lang == "vi" else
            "😔 All time slots for this table on the selected date are taken.\n"
            "Please choose a different date.")
        )
        await call.answer(no_slots_msg, show_alert=True)
        return
    await call.message.edit_text(t("choose_time", lang), reply_markup=kb)
    await state.set_state(BookingFSM.time)
    await call.answer()


# ─── Step 3: Time ─────────────────────────────────────────────────────────────

@router.callback_query(BookingFSM.time, lambda c: c.data and c.data.startswith("time:"))
async def step_time(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    chosen_time = call.data.split(":")[1]
    await state.update_data(time=chosen_time)
    await call.message.edit_text(t("choose_guests", lang), reply_markup=guests_keyboard(lang))
    await state.set_state(BookingFSM.guests)
    await call.answer()


# ─── Step 4: Guests ───────────────────────────────────────────────────────────

@router.callback_query(BookingFSM.guests, lambda c: c.data and c.data.startswith("guests:"))
async def step_guests(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    guests = call.data.split(":")[1]
    await state.update_data(guests_count=guests)
    await call.message.delete()
    await call.message.answer(t("enter_name", lang), reply_markup=back_keyboard(lang))
    await state.set_state(BookingFSM.name)
    await call.answer()


# ─── Step 5: Name ─────────────────────────────────────────────────────────────

@router.message(BookingFSM.name)
async def step_name(message: Message, state: FSMContext, lang: str) -> None:
    name = message.text.strip() if message.text else ""
    if len(name) < 2:
        await message.answer(t("invalid_name", lang))
        return
    await state.update_data(name=name)
    await message.answer(t("enter_phone", lang), reply_markup=phone_keyboard(lang))
    await state.set_state(BookingFSM.phone)


# ─── Step 6: Phone ────────────────────────────────────────────────────────────

@router.message(BookingFSM.phone, F.contact)
async def step_phone_contact(message: Message, state: FSMContext, lang: str) -> None:
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await message.answer(t("enter_comment", lang), reply_markup=skip_back_keyboard(lang))
    await state.set_state(BookingFSM.comment)


@router.message(BookingFSM.phone)
async def step_phone_text(message: Message, state: FSMContext, lang: str) -> None:
    phone = message.text.strip() if message.text else ""
    if not PHONE_REGEX.match(phone):
        await message.answer(t("invalid_phone", lang))
        return
    await state.update_data(phone=phone)
    await message.answer(t("enter_comment", lang), reply_markup=skip_back_keyboard(lang))
    await state.set_state(BookingFSM.comment)


# ─── Step 7: Comment ──────────────────────────────────────────────────────────

@router.message(BookingFSM.comment, lambda m: m.text in ("➡️ Пропустить", "➡️ Skip", "➡️ Bỏ qua"))
async def step_comment_skip(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(comment=None)
    await _show_summary(message, state, lang)


@router.message(BookingFSM.comment)
async def step_comment(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(comment=message.text.strip() if message.text else None)
    await _show_summary(message, state, lang)


# ─── Summary helper ───────────────────────────────────────────────────────────

async def _show_summary(message: Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    if lang == "ru":
        _h = {"main": "🏛 Основной зал", "second": "🔝 2-й этаж"}
        _l = {"Hall": "Зал", "Table": "Стол", "Date": "Дата", "Time": "Время",
              "Guests": "Гостей", "Name": "Имя", "Phone": "Телефон", "Comment": "Комментарий"}
    elif lang == "vi":
        _h = {"main": "🏛 Khu chính", "second": "🔝 Tầng 2"}
        _l = {"Hall": "Khu vực", "Table": "Bàn", "Date": "Ngày", "Time": "Giờ",
              "Guests": "Khách", "Name": "Tên", "Phone": "Điện thoại", "Comment": "Ghi chú"}
    else:
        _h = {"main": "🏛 Main Hall", "second": "🔝 2nd Floor"}
        _l = {"Hall": "Hall", "Table": "Table", "Date": "Date", "Time": "Time",
              "Guests": "Guests", "Name": "Name", "Phone": "Phone", "Comment": "Comment"}
    hall_label = _h.get(data.get("hall", ""), "—")

    text = (
        f"{t('booking_summary_title', lang)}\n\n"
        f"🏛 {_l['Hall']}: {hall_label}\n"
        f"🪑 {_l['Table']}: {data.get('table', '—')}\n"
        f"📅 {_l['Date']}: {data.get('date')}\n"
        f"⏰ {_l['Time']}: {data.get('time')}\n"
        f"👥 {_l['Guests']}: {data.get('guests_count')}\n"
        f"👤 {_l['Name']}: {data.get('name')}\n"
        f"📞 {_l['Phone']}: {data.get('phone')}\n"
        f"💬 {_l['Comment']}: {data.get('comment') or '—'}"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=confirm_keyboard(lang))
    await state.set_state(BookingFSM.confirm)


# ─── Step 8: Confirm / Edit / Cancel ─────────────────────────────────────────

@router.callback_query(BookingFSM.confirm, lambda c: c.data == "booking:cancel")
async def booking_cancel(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await call.message.delete()
    await call.message.answer(t("main_menu", lang), reply_markup=main_menu_keyboard(lang))
    await call.answer()


@router.callback_query(BookingFSM.confirm, lambda c: c.data == "booking:edit")
async def booking_edit(call: CallbackQuery, state: FSMContext) -> None:
    """Return to the very start — floor plan."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    hall = data.get("hall", "main")
    caption = _floor_caption_initial(lang, hall)
    await call.message.delete()
    await call.message.answer(
        caption, parse_mode="HTML",
        reply_markup=floor_plan_keyboard(hall, {}, lang, back_callback=None),
    )
    await state.set_state(BookingFSM.table)
    await call.answer()


@router.callback_query(BookingFSM.confirm, lambda c: c.data == "booking:confirm")
async def booking_confirm(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()

    booking = await booking_service.create_booking(
        user_id=call.from_user.id,
        name=data["name"],
        phone=data["phone"],
        guests_count=data["guests_count"],
        hall=data["hall"],
        date=data["date"],
        time=data["time"],
        comment=data.get("comment"),
        table=data.get("table"),
        source="bot",
        tg_username=call.from_user.username or None,
    )

    await call.message.edit_text(t("booking_confirmed_user", lang, id=booking.id), parse_mode="HTML")
    await call.message.answer(t("main_menu", lang), reply_markup=main_menu_keyboard(lang))
    await state.clear()

    from aiogram import Bot
    bot: Bot = call.bot
    admin_text = t("admin_new_booking", "ru", summary=booking.summary("ru"))
    await bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_text,
        parse_mode="HTML",
        reply_markup=admin_booking_keyboard(booking.id, booking.phone),
    )
    await call.answer()


# ─── My Bookings ──────────────────────────────────────────────────────────────

@router.message(lambda m: m.text in ("📋 Мои брони", "📋 My Bookings", "📋 Đặt chỗ của tôi"))
async def my_bookings(message: Message, lang: str) -> None:
    bookings = await booking_service.get_user_active_bookings(message.from_user.id)
    if not bookings:
        await message.answer(t("no_bookings", lang))
        return
    text = "\n\n".join(b.summary(lang) for b in bookings)
    await message.answer(text, parse_mode="HTML", reply_markup=cancel_bookings_keyboard(bookings))


@router.callback_query(lambda c: c.data and c.data.startswith("cancel_booking:"))
async def cancel_user_booking(call: CallbackQuery, lang: str) -> None:
    booking_id = int(call.data.split(":")[1])
    booking = await booking_service.get_booking(booking_id)

    if not booking or booking.user_id != call.from_user.id:
        await call.answer("❌", show_alert=True)
        return

    from bot.database.models import BookingStatus
    updated = await booking_service.set_booking_status(booking_id, BookingStatus.CANCELLED)

    if updated and updated.poster_reservation_id:
        await poster_service.cancel_reservation(updated.poster_reservation_id)

    await call.message.edit_text(t("booking_cancelled_user", lang, id=booking_id), parse_mode="HTML")
    await call.answer()


