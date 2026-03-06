import sys
import os
import logging
import calendar
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8780268115:AAEeOZ1vAjTd2BiLaAA_IS_Pz2cuPnkuMGM")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

PHOTO_PATH = "the_cloud.jpg"

# --- Состояния бронирования ---
PICK_DATE, PICK_TIME, PICK_GUESTS, PICK_NAME, CONFIRM = range(5)

# Хранилище бронирований {user_id: [list of bookings]}
bookings = {}


# --- Inline-календарь ---
def build_calendar(year, month):
    """Создаёт inline-клавиатуру с календарём на месяц."""
    now = datetime.now()
    today = now.date()

    kb = []
    # Заголовок: < Март 2026 >
    month_name = [
        "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ][month]
    kb.append([
        InlineKeyboardButton("◀️", callback_data=f"cal_prev_{year}_{month}"),
        InlineKeyboardButton(f"{month_name} {year}", callback_data="cal_ignore"),
        InlineKeyboardButton("▶️", callback_data=f"cal_next_{year}_{month}"),
    ])

    # Дни недели
    kb.append([InlineKeyboardButton(d, callback_data="cal_ignore")
               for d in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]])

    # Дни месяца
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="cal_ignore"))
            else:
                date_obj = datetime(year, month, day).date()
                if date_obj < today:
                    row.append(InlineKeyboardButton("·", callback_data="cal_ignore"))
                else:
                    row.append(InlineKeyboardButton(
                        str(day), callback_data=f"cal_day_{year}_{month}_{day}"
                    ))
        kb.append(row)

    kb.append([InlineKeyboardButton("❌ Отмена", callback_data="cal_cancel")])
    return InlineKeyboardMarkup(kb)


def build_time_keyboard():
    """Кнопки с временными слотами."""
    times = [
        "12:00", "13:00", "14:00", "15:00",
        "16:00", "17:00", "18:00", "19:00",
        "20:00", "21:00", "22:00", "23:00",
        "00:00", "01:00"
    ]
    kb = []
    for i in range(0, len(times), 3):
        row = [InlineKeyboardButton(t, callback_data=f"time_{t}") for t in times[i:i+3]]
        kb.append(row)
    kb.append([InlineKeyboardButton("❌ Отмена", callback_data="cal_cancel")])
    return InlineKeyboardMarkup(kb)


def build_guests_keyboard():
    """Кнопки с количеством гостей."""
    kb = [
        [InlineKeyboardButton(f"{n} чел.", callback_data=f"guests_{n}") for n in [1, 2, 3]],
        [InlineKeyboardButton(f"{n} чел.", callback_data=f"guests_{n}") for n in [4, 5, 6]],
        [InlineKeyboardButton(f"{n} чел.", callback_data=f"guests_{n}") for n in [7, 8, 10]],
        [InlineKeyboardButton("❌ Отмена", callback_data="cal_cancel")],
    ]
    return InlineKeyboardMarkup(kb)

# Главное меню
def main_menu():
    keyboard = [
        [KeyboardButton("📅 Забронировать столик")],
        [KeyboardButton("📋 Мои бронирования")],
        [KeyboardButton("ℹ️ О нас"), KeyboardButton("📞 Контакты")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет картинку + приветствие при /start"""
    try:
        with open(PHOTO_PATH, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=(
                    "☁️ *Добро пожаловать в The Cloud!*\n\n"
                    "Мы рады видеть вас 🎉\n"
                    "Нажмите кнопку ниже, чтобы забронировать столик."
                ),
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
    except FileNotFoundError:
        # Если картинки нет — просто текст
        await update.message.reply_text(
            "☁️ *Добро пожаловать в The Cloud!*\n\n"
            "Мы рады видеть вас 🎉\n"
            "Нажмите кнопку ниже, чтобы забронировать столик.",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )


# ====== Бронирование: ConversationHandler ======

async def booking_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинаем бронирование — показываем календарь."""
    now = datetime.now()
    context.user_data["booking"] = {}
    msg = await update.message.reply_text(
        "📅 Выберите дату:",
        reply_markup=build_calendar(now.year, now.month),
    )
    context.user_data["calendar_msg_id"] = msg.message_id
    return PICK_DATE


async def calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем нажатия в календаре."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cal_ignore":
        return PICK_DATE

    if data == "cal_cancel":
        await query.edit_message_text("❌ Бронирование отменено.")
        return ConversationHandler.END

    if data.startswith("cal_prev_"):
        _, _, y, m = data.rsplit("_", 3)
        y, m = int(y), int(m)
        m -= 1
        if m < 1:
            m, y = 12, y - 1
        await query.edit_message_reply_markup(reply_markup=build_calendar(y, m))
        return PICK_DATE

    if data.startswith("cal_next_"):
        _, _, y, m = data.rsplit("_", 3)
        y, m = int(y), int(m)
        m += 1
        if m > 12:
            m, y = 1, y + 1
        await query.edit_message_reply_markup(reply_markup=build_calendar(y, m))
        return PICK_DATE

    if data.startswith("cal_day_"):
        parts = data.split("_")
        y, m, d = int(parts[2]), int(parts[3]), int(parts[4])
        chosen = datetime(y, m, d).date()
        context.user_data["booking"]["date"] = chosen.strftime("%d.%m.%Y")
        await query.edit_message_text(
            f"📅 Дата: *{chosen.strftime('%d.%m.%Y')}*\n\n🕐 Выберите время:",
            parse_mode="Markdown",
            reply_markup=build_time_keyboard(),
        )
        return PICK_TIME

    return PICK_DATE


async def time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем выбор времени."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cal_cancel":
        await query.edit_message_text("❌ Бронирование отменено.")
        return ConversationHandler.END

    if data.startswith("time_"):
        chosen_time = data.replace("time_", "")
        context.user_data["booking"]["time"] = chosen_time
        date_str = context.user_data["booking"]["date"]
        await query.edit_message_text(
            f"📅 Дата: *{date_str}*\n"
            f"🕐 Время: *{chosen_time}*\n\n"
            "👥 Сколько гостей?",
            parse_mode="Markdown",
            reply_markup=build_guests_keyboard(),
        )
        return PICK_GUESTS

    return PICK_TIME


async def guests_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем выбор количества гостей."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cal_cancel":
        await query.edit_message_text("❌ Бронирование отменено.")
        return ConversationHandler.END

    if data.startswith("guests_"):
        n = data.replace("guests_", "")
        context.user_data["booking"]["guests"] = n
        bd = context.user_data["booking"]
        await query.edit_message_text(
            f"📅 Дата: *{bd['date']}*\n"
            f"🕐 Время: *{bd['time']}*\n"
            f"👥 Гостей: *{n}*\n\n"
            "✏️ Введите ваше имя для бронирования:",
            parse_mode="Markdown",
        )
        return PICK_NAME

    return PICK_GUESTS


async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем имя и просим подтвердить."""
    name = update.message.text.strip()
    context.user_data["booking"]["name"] = name
    bd = context.user_data["booking"]

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Отмена", callback_data="confirm_no"),
        ]
    ])

    await update.message.reply_text(
        "📋 *Проверьте бронирование:*\n\n"
        f"📅 Дата: *{bd['date']}*\n"
        f"🕐 Время: *{bd['time']}*\n"
        f"👥 Гостей: *{bd['guests']}*\n"
        f"👤 Имя: *{name}*\n\n"
        "Всё верно?",
        parse_mode="Markdown",
        reply_markup=kb,
    )
    return CONFIRM


async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение или отмена бронирования."""
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_no":
        await query.edit_message_text("❌ Бронирование отменено.")
        return ConversationHandler.END

    if query.data == "confirm_yes":
        bd = context.user_data["booking"]
        uid = update.effective_user.id

        bookings.setdefault(uid, []).append(dict(bd))

        await query.edit_message_text(
            "✅ *Бронирование подтверждено!*\n\n"
            f"📅 {bd['date']}  🕐 {bd['time']}\n"
            f"👥 {bd['guests']} чел.  👤 {bd['name']}\n\n"
            "Ждём вас в The Cloud! ☁️",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    return CONFIRM


async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /cancel — выход из бронирования."""
    await update.message.reply_text("❌ Бронирование отменено.", reply_markup=main_menu())
    return ConversationHandler.END


# ====== Обычные кнопки меню ======

async def handle_my_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_bookings = bookings.get(uid, [])
    if not user_bookings:
        await update.message.reply_text("У вас пока нет активных бронирований.")
        return
    lines = ["📋 *Ваши бронирования:*\n"]
    for i, b in enumerate(user_bookings, 1):
        lines.append(
            f"{i}. 📅 {b['date']}  🕐 {b['time']}  "
            f"👥 {b['guests']} чел.  👤 {b['name']}"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def handle_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "☁️ *The Cloud*\n"
        "EAT • SMOKE • DRINK\n\n"
        "📍 Адрес: 163 Nguyen Thien Thuat\n"
        "🕐 Режим работы: 12:00 — 02:00",
        parse_mode="Markdown",
    )


async def handle_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 +84 (794) 533-508\n"
        "📞 +84 (825) 190-251\n"
        "📸 Instagram: @thecloudbar_nt\n"
        "📍 163 Nguyen Thien Thuat"
    )


def main():
    # Порт назначает Render автоматически, по умолчанию 10000
    PORT = int(os.environ.get("PORT", 10000))
    # Адрес твоего сервера на Render
    WEBHOOK_DOMAIN = os.environ.get("WEBHOOK_DOMAIN", "https://the-cloud-booking.onrender.com")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Conversation для бронирования
    booking_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📅 Забронировать столик$"), booking_start),
        ],
        states={
            PICK_DATE:  [CallbackQueryHandler(calendar_handler)],
            PICK_TIME:  [CallbackQueryHandler(time_handler)],
            PICK_GUESTS:[CallbackQueryHandler(guests_handler)],
            PICK_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            CONFIRM:    [CallbackQueryHandler(confirm_handler)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_booking),
            MessageHandler(filters.Regex("^📅 Забронировать столик$"), booking_start),
        ],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(booking_conv)
    app.add_handler(MessageHandler(filters.Regex("^📋 Мои бронирования$"), handle_my_bookings))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ О нас$"), handle_about))
    app.add_handler(MessageHandler(filters.Regex("^📞 Контакты$"), handle_contacts))

    print(f"Bot The Cloud started (webhook mode) on port {PORT}...")
    # Webhook режим: Телеграм сам присылает обновления на сервер Render
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=f"{WEBHOOK_DOMAIN}/webhook",
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
