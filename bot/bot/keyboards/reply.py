from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, WebAppInfo

import bot.config as _cfg  # import module so runtime changes to WEBAPP_URL are visible


def main_menu_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    webapp_btn = None
    hub_btn = None
    if _cfg.WEBAPP_URL:
        base = _cfg.WEBAPP_URL.rstrip("/")
        if lang == "ru":
            label     = "🗺 Карта столов"
            hub_label = "🌍 Витрина · Nha Trang"
        elif lang == "vi":
            label     = "🗺 Sơ đồ bàn"
            hub_label = "🌍 Nha Trang Hub"
        else:
            label     = "🗺 Table Map"
            hub_label = "🌍 Nha Trang Hub"
        webapp_btn = KeyboardButton(text=label,     web_app=WebAppInfo(url=base + "/"))
        hub_btn    = KeyboardButton(text=hub_label, web_app=WebAppInfo(url=base + "/hub"))

    if lang == "ru":
        rows = [
            [KeyboardButton(text="📅 Забронировать столик")],
            [KeyboardButton(text="📋 Мои брони"), KeyboardButton(text="📞 Контакты")],
        ]
        if webapp_btn:
            rows.insert(1, [webapp_btn])
        if hub_btn:
            rows.insert(2, [hub_btn])
        rows.append([KeyboardButton(text="🌐 English"), KeyboardButton(text="🌐 Tiếng Việt")])
        return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
    elif lang == "vi":
        rows = [
            [KeyboardButton(text="📅 Đặt bàn")],
            [KeyboardButton(text="📋 Đặt chỗ của tôi"), KeyboardButton(text="📞 Liên hệ")],
        ]
        if webapp_btn:
            rows.insert(1, [webapp_btn])
        if hub_btn:
            rows.insert(2, [hub_btn])
        rows.append([KeyboardButton(text="🌐 Русский"), KeyboardButton(text="🌐 English")])
        return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
    else:
        rows = [
            [KeyboardButton(text="📅 Book a Table")],
            [KeyboardButton(text="📋 My Bookings"), KeyboardButton(text="📞 Contact Us")],
        ]
        if webapp_btn:
            rows.insert(1, [webapp_btn])
        if hub_btn:
            rows.insert(2, [hub_btn])
        rows.append([KeyboardButton(text="🌐 Русский"), KeyboardButton(text="🌐 Tiếng Việt")])
        return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def phone_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    if lang == "ru":
        label = "📱 Поделиться номером"
        back = "◀️ Назад"
    elif lang == "vi":
        label = "📱 Chia sẻ số điện thoại"
        back = "◀️ Quay lại"
    else:
        label = "📱 Share Phone Number"
        back = "◀️ Back"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=label, request_contact=True)],
            [KeyboardButton(text=back)],
        ],
        resize_keyboard=True,
    )


def back_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    label = "◀️ Назад" if lang == "ru" else ("◀️ Quay lại" if lang == "vi" else "◀️ Back")
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label)]],
        resize_keyboard=True,
    )


def skip_back_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    if lang == "ru":
        skip = "➡️ Пропустить"
        back = "◀️ Назад"
    elif lang == "vi":
        skip = "➡️ Bỏ qua"
        back = "◀️ Quay lại"
    else:
        skip = "➡️ Skip"
        back = "◀️ Back"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=skip)],
            [KeyboardButton(text=back)],
        ],
        resize_keyboard=True,
    )


remove_keyboard = ReplyKeyboardRemove()
