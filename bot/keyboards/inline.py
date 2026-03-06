from datetime import date, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import HALLS, BOOKING_OPEN_HOUR, BOOKING_CLOSE_HOUR, BOOKING_SLOT_MINUTES, BOOKING_DAYS_AHEAD

# ─── Floor plan layouts (None = invisible spacer) ─────────────────────────────
# Matches the Poster POS floor map photo exactly.

# Layout matches Poster POS floor plan exactly
# main = Основной зал (T2, T3 + Bar stools B1-B8)
# second = 2nd Floor (tables 4-11)
MAIN_HALL_LAYOUT: list[list[str | None]] = [
    ["T3",  None, "T2",  None],
    ["B1",  "B2", "B3",  "B4"],
    ["B5",  "B6", "B7",  "B8"],
]

SECOND_FLOOR_LAYOUT: list[list[str | None]] = [
    ["8",   "7"  ],
    ["9",   "6"  ],
    ["10",  "5"  ],
    ["11",  None ],
    ["4",   None ],
]

HALL_LAYOUTS: dict[str, list[list[str | None]]] = {
    "main": MAIN_HALL_LAYOUT,
    "second": SECOND_FLOOR_LAYOUT,
}


def floor_plan_keyboard(
    hall: str,
    table_statuses: dict[str, str],   # {table_name: "confirmed"|"pending"}
    lang: str = "ru",
    back_callback: str | None = "back:main_menu",
) -> InlineKeyboardMarkup:
    """
    Render an interactive floor plan with hall switcher tabs.
    🟢 = free   🟡 = pending (waiting confirm)   🔴 = confirmed (taken)
    · = invisible spacer (noop)
    back_callback=None → no back button (used at entry step)
    """
    layout = HALL_LAYOUTS.get(hall, [])
    builder = InlineKeyboardBuilder()
    row_widths: list[int] = []

    # ── Hall switcher tabs (top row) ──────────────────────────────────────────
    second_text  = "2 этаж" if lang == "ru" else "2nd Floor"
    main_label   = "▶ 🏛 Осн. зал"          if hall == "main"   else "🏛 Осн. зал"
    second_label = f"▶ 🔝 {second_text}"    if hall == "second" else f"🔝 {second_text}"
    builder.button(text=main_label,   callback_data="noop"               if hall == "main"   else "switch_hall:main")
    builder.button(text=second_label, callback_data="noop"               if hall == "second" else "switch_hall:second")
    row_widths.append(2)

    # ── Floor plan grid ───────────────────────────────────────────────────────
    for row in layout:
        for cell in row:
            if cell is None:
                builder.button(text="·", callback_data="noop")
            elif cell in table_statuses:
                status = table_statuses[cell]
                icon = "🔴" if status == "confirmed" else ("🟠" if status == "en_route" else "🟡")
                builder.button(text=f"{icon}{cell}", callback_data="table:busy")
            else:
                builder.button(text=f"🟢{cell}", callback_data=f"table:{cell}")
        row_widths.append(len(row))

    # ── Legend ────────────────────────────────────────────────────────────────
    legend = "🟢своб 🟡ожид 🟠в пути 🔴занят" if lang == "ru" else "🟢free 🟡pend 🟠route 🔴busy"
    builder.button(text=legend, callback_data="noop")
    row_widths.append(1)

    # ── Back button (optional) ────────────────────────────────────────────────
    if back_callback is not None:
        back_label = "◀️ Назад" if lang == "ru" else "◀️ Back"
        builder.button(text=back_label, callback_data=back_callback)
        row_widths.append(1)

    builder.adjust(*row_widths)
    return builder.as_markup()


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский", callback_data="lang:ru")
    builder.button(text="🇬🇧 English", callback_data="lang:en")
    builder.button(text="🇻🇳 Tiếng Việt", callback_data="lang:vi")
    builder.adjust(3)
    return builder.as_markup()


def halls_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, key in HALLS.items():
        builder.button(text=label, callback_data=f"hall:{key}")
    builder.adjust(1)
    return builder.as_markup()


def dates_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    today = date.today()

    DAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    DAYS_EN = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    DAYS_VI = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    days = DAYS_RU if lang == "ru" else (DAYS_VI if lang == "vi" else DAYS_EN)

    MONTHS_RU = ["", "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
                 "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
    MONTHS_EN = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    MONTHS_VI = ["", "Th1", "Th2", "Th3", "Th4", "Th5", "Th6",
                 "Th7", "Th8", "Th9", "Th10", "Th11", "Th12"]
    months = MONTHS_RU if lang == "ru" else (MONTHS_VI if lang == "vi" else MONTHS_EN)

    for i in range(BOOKING_DAYS_AHEAD):
        d = today + timedelta(days=i)
        day_name = days[d.weekday()]
        label = f"{day_name}, {d.day} {months[d.month]}"
        builder.button(text=label, callback_data=f"date:{d.isoformat()}")

    back_label = "◀️ Назад" if lang == "ru" else ("◀️ Quay lại" if lang == "vi" else "◀️ Back")
    builder.button(text=back_label, callback_data="back:table")
    builder.adjust(2)
    return builder.as_markup()


def times_keyboard(booked_times: list[str] | None = None, lang: str = "ru") -> InlineKeyboardMarkup | None:
    """
    Generate time slot buttons showing ONLY free (unbooked) slots.
    Returns None if there are no available slots at all.
    """
    booked_times = booked_times or []
    builder = InlineKeyboardBuilder()
    slot_count = 0

    hour = BOOKING_OPEN_HOUR
    minute = 0
    while hour < BOOKING_CLOSE_HOUR or (hour == BOOKING_CLOSE_HOUR and minute == 0):
        slot = f"{hour:02d}:{minute:02d}"
        if slot not in booked_times:
            builder.button(text=slot, callback_data=f"time:{slot}")
            slot_count += 1
        minute += BOOKING_SLOT_MINUTES
        if minute >= 60:
            minute -= 60
            hour += 1

    if slot_count == 0:
        return None  # caller must handle "no free slots" case

    back_label = "◀️ Назад" if lang == "ru" else ("◀️ Quay lại" if lang == "vi" else "◀️ Back")
    builder.button(text=back_label, callback_data="back:date")
    builder.adjust(4)
    return builder.as_markup()


def guests_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    options = ["1–2", "3–4", "5–6", "7–10", "10+"]
    for opt in options:
        if lang == "ru":
            label = f"👥 {opt} чел."
        elif lang == "vi":
            label = f"👥 {opt} khách"
        else:
            label = f"👥 {opt} ppl"
        builder.button(text=label, callback_data=f"guests:{opt}")
    back_label = "◀️ Назад" if lang == "ru" else ("◀️ Quay lại" if lang == "vi" else "◀️ Back")
    builder.button(text=back_label, callback_data="back:time")
    builder.adjust(2, 2, 1, 1)  # 5 options (2,2,1) + back alone
    return builder.as_markup()


def confirm_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if lang == "ru":
        builder.button(text="✅ Подтвердить", callback_data="booking:confirm")
        builder.button(text="✏️ Изменить", callback_data="booking:edit")
        builder.button(text="❌ Отменить", callback_data="booking:cancel")
    elif lang == "vi":
        builder.button(text="✅ Xác nhận", callback_data="booking:confirm")
        builder.button(text="✏️ Chỉnh sửa", callback_data="booking:edit")
        builder.button(text="❌ Huỷ", callback_data="booking:cancel")
    else:
        builder.button(text="✅ Confirm", callback_data="booking:confirm")
        builder.button(text="✏️ Edit", callback_data="booking:edit")
        builder.button(text="❌ Cancel", callback_data="booking:cancel")
    builder.adjust(2, 1)
    return builder.as_markup()


def admin_booking_keyboard(booking_id: int, user_phone: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять", callback_data=f"admin:accept:{booking_id}")
    builder.button(text="❌ Отклонить", callback_data=f"admin:reject:{booking_id}")
    builder.button(text="🟠 В пути", callback_data=f"admin:enroute:{booking_id}")
    builder.button(text=f"📞 {user_phone}", url=f"tel:{user_phone}")
    builder.adjust(3, 1)
    return builder.as_markup()


def en_route_bookings_keyboard(bookings: list) -> InlineKeyboardMarkup:
    """Keyboard for /enroute command — each en-route booking gets an Arrived button."""
    builder = InlineKeyboardBuilder()
    for b in bookings:
        label = f"✅ Прибыл: #{b.id} • {b.table or '—'} • {b.name or ''}"
        builder.button(text=label, callback_data=f"admin:arrived:{b.id}")
    builder.adjust(1)
    return builder.as_markup()


def release_table_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    """Shown after guest is marked as arrived — lets admin release the table when guests leave."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔓 Снять бронь (гости ушли)", callback_data=f"admin:release:{booking_id}")
    builder.adjust(1)
    return builder.as_markup()


def cancel_bookings_keyboard(bookings: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for b in bookings:
        label = f"#{b.id} • {b.date} {b.time} • {b.hall}"
        builder.button(text=label, callback_data=f"cancel_booking:{b.id}")
    builder.adjust(1)
    return builder.as_markup()


ADMIN_PHONE = "+84792533508"
INSTAGRAM_URL = "https://www.instagram.com/thecloudbar_nt/"
GOOGLE_MAPS_URL = "https://www.google.com/maps/place/The+Cloud/@12.236706,109.1941066,17z"


def contact_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline buttons for contacting the admin."""
    builder = InlineKeyboardBuilder()
    if lang == "ru":
        builder.button(text="💬 WhatsApp",       url=f"https://wa.me/84792533508")
        builder.button(text="📞 Позвонить",      url=f"tel:{ADMIN_PHONE}")
        builder.button(text="📸 Instagram",      url=INSTAGRAM_URL)
        builder.button(text="📍 На карте",       url=GOOGLE_MAPS_URL)
    elif lang == "vi":
        builder.button(text="💬 WhatsApp",       url=f"https://wa.me/84792533508")
        builder.button(text="📞 Gọi điện",       url=f"tel:{ADMIN_PHONE}")
        builder.button(text="📸 Instagram",      url=INSTAGRAM_URL)
        builder.button(text="📍 Bản đồ",        url=GOOGLE_MAPS_URL)
    else:
        builder.button(text="💬 WhatsApp",       url=f"https://wa.me/84792533508")
        builder.button(text="📞 Call",           url=f"tel:{ADMIN_PHONE}")
        builder.button(text="📸 Instagram",      url=INSTAGRAM_URL)
        builder.button(text="📍 Map",            url=GOOGLE_MAPS_URL)
    builder.adjust(2, 2)
    return builder.as_markup()


# ─── Admin: view tables by date ───────────────────────────────────────────────

def admin_dates_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Date picker for admin 'view tables' feature."""
    builder = InlineKeyboardBuilder()
    today = date.today()

    DAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    DAYS_EN = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    days = DAYS_RU if lang == "ru" else DAYS_EN

    MONTHS_RU = ["", "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
                 "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
    MONTHS_EN = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    months = MONTHS_RU if lang == "ru" else MONTHS_EN

    for i in range(BOOKING_DAYS_AHEAD):
        d = today + timedelta(days=i)
        day_name = days[d.weekday()]
        label = f"{day_name}, {d.day} {months[d.month]}"
        builder.button(text=label, callback_data=f"vtables_date:{d.isoformat()}")

    builder.adjust(2)
    return builder.as_markup()


def floor_plan_view_keyboard(
    hall: str,
    table_statuses: dict[str, str],  # {table_name: "confirmed"|"pending"}
    view_date: str,                   # "YYYY-MM-DD"
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    """
    Read-only floor plan for admin — shows which tables are booked on a given date.
    🟢 = free   🟡 = pending   🔴 = confirmed
    Tapping a booked table shows booking details. Free tables → noop.
    Hall switcher updates the view without leaving the date context.
    """
    layout = HALL_LAYOUTS.get(hall, [])
    builder = InlineKeyboardBuilder()
    row_widths: list[int] = []

    # ── Hall switcher tabs ─────────────────────────────────────────────────────
    main_label   = "▶ 🏛 Осн. зал"   if hall == "main"   else "🏛 Осн. зал"
    second_label = "▶ 🔝 Tầng 2" if (hall == "second" and lang == "vi") else ("▶ 🔝 2nd Floor" if hall == "second" else ("🔝 Tầng 2" if lang == "vi" else "🔝 2nd Floor"))
    builder.button(text=main_label,   callback_data="noop"                              if hall == "main"   else f"vtables_hall:main:{view_date}")
    builder.button(text=second_label, callback_data="noop"                              if hall == "second" else f"vtables_hall:second:{view_date}")
    row_widths.append(2)

    # ── Floor plan grid ────────────────────────────────────────────────────────
    for row in layout:
        for cell in row:
            if cell is None:
                builder.button(text="·", callback_data="noop")
            elif cell in table_statuses:
                status = table_statuses[cell]
                icon = "🔴" if status == "confirmed" else ("🟠" if status == "en_route" else "🟡")
                builder.button(text=f"{icon}{cell}", callback_data=f"vtables_info:{cell}:{view_date}")
            else:
                builder.button(text=f"🟢{cell}", callback_data="noop")
        row_widths.append(len(row))

    # ── Legend ────────────────────────────────────────────────────────────────
    if lang == "ru":
        legend = "🟢своб 🟡ожид 🟠в пути 🔴занят"
    elif lang == "vi":
        legend = "🟢trống 🟡chờ 🟠trên đường 🔴bận"
    else:
        legend = "🟢free 🟡pend 🟠route 🔴busy"
    builder.button(text=legend, callback_data="noop")
    row_widths.append(1)

    # ── Back to date picker ───────────────────────────────────────────────────
    back_label = "◀️ К датам" if lang == "ru" else ("◀️ Quay lại" if lang == "vi" else "◀️ Back to dates")
    builder.button(text=back_label, callback_data="vtables_back")
    row_widths.append(1)

    builder.adjust(*row_widths)
    return builder.as_markup()

