import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile

from bot.config import VENUE_ADDRESS, VENUE_PHONE, LOGO_PATH, LOGO_URL, ADMIN_CHAT_ID, STAFF_IDS
from bot.database.models import UserRole
from bot.keyboards.inline import language_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.middlewares.i18n import t
from bot.services.booking_service import upsert_user

router = Router()
logger = logging.getLogger(__name__)

WELCOME_CAPTION = (
    "🇷🇺 Добро пожаловать в <b>The Cloud</b>!\n"
    "🇬🇧 Welcome to <b>The Cloud</b>!\n"
    "🇻🇳 Chào mừng đến <b>The Cloud</b>!\n\n"
    "Выберите язык / Choose language / Chọn ngôn ngữ:"
)


async def _send_welcome(message: Message) -> None:
    """Try local file → Telegram file_id/URL → text fallback."""
    kb = language_keyboard()

    # 1️⃣ Local PNG file (bot/assets/logo.png)
    if LOGO_PATH.exists():
        try:
            sent = await message.answer_photo(
                photo=FSInputFile(LOGO_PATH),
                caption=WELCOME_CAPTION,
                parse_mode="HTML",
                reply_markup=kb,
            )
            # Log file_id once — paste it into LOGO_URL in .env for faster loading
            logger.info(f"Logo file_id: {sent.photo[-1].file_id}")
            return
        except Exception as e:
            logger.warning(f"Local logo send failed: {e}")

    # 2️⃣ Telegram file_id or remote URL from .env
    if LOGO_URL:
        try:
            await message.answer_photo(
                photo=LOGO_URL,
                caption=WELCOME_CAPTION,
                parse_mode="HTML",
                reply_markup=kb,
            )
            return
        except Exception as e:
            logger.warning(f"Logo URL send failed: {e}")

    # 3️⃣ Text-only fallback
    await message.answer(WELCOME_CAPTION, parse_mode="HTML", reply_markup=kb)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, lang: str) -> None:
    # Сбрасываем незавершённое бронирование — иначе /start будет игнорироваться
    # когда пользователь застрял в середине формы бронирования
    await state.clear()

    try:
        role = await upsert_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            language=lang,
        )
        # Role-specific greeting logged (not shown — welcome photo is shown to all)
        if role == UserRole.ADMIN:
            logger.info(f"Admin {message.from_user.id} signed in")
        elif role == UserRole.STAFF:
            logger.info(f"Staff member {message.from_user.id} signed in")
        elif role == UserRole.VIP:
            logger.info(f"VIP guest {message.from_user.id} signed in")
    except Exception as e:
        logger.error(f"upsert_user failed for {message.from_user.id}: {e}", exc_info=True)
        # DB error — still show welcome, user can use the bot

    try:
        await _send_welcome(message)
    except Exception as e:
        logger.error(f"_send_welcome failed: {e}", exc_info=True)
        try:
            await message.answer(WELCOME_CAPTION, parse_mode="HTML")
        except Exception:
            pass


_LANG_GREETING = {
    "ru": "🇷🇺 Язык выбран: <b>Русский</b>",
    "en": "🇬🇧 Language selected: <b>English</b>",
    "vi": "🇻🇳 Đã chọn ngôn ngữ: <b>Tiếng Việt</b>",
}

@router.callback_query(lambda c: c.data and c.data.startswith("lang:"))
async def set_language(call: CallbackQuery, lang: str) -> None:
    chosen = call.data.split(":")[1]
    await upsert_user(
        user_id=call.from_user.id,
        username=call.from_user.username,
        first_name=call.from_user.first_name,
        language=chosen,
    )
    await call.message.delete()
    greeting = _LANG_GREETING.get(chosen, _LANG_GREETING["ru"])
    await call.message.answer(
        f"{greeting}\n\n{t('main_menu', chosen)}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(chosen),
    )
    await call.answer()


@router.message(lambda m: m.text in ("🌐 English", "🌐 Русский", "🌐 Tiếng Việt"))
async def switch_language(message: Message, lang: str) -> None:
    if message.text == "🌐 English":
        new_lang = "en"
    elif message.text == "🌐 Tiếng Việt":
        new_lang = "vi"
    else:
        new_lang = "ru"
    await upsert_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        language=new_lang,
    )
    greeting = _LANG_GREETING.get(new_lang, _LANG_GREETING["ru"])
    await message.answer(
        f"{greeting}\n\n{t('main_menu', new_lang)}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(new_lang),
    )


@router.message(lambda m: m.text in ("📞 Контакты", "📞 Contact Us", "📞 Liên hệ"))
async def contact_handler(message: Message, lang: str) -> None:
    from bot.keyboards.inline import contact_keyboard
    await message.answer(
        t("contact_info", lang, address=VENUE_ADDRESS, phone=VENUE_PHONE),
        parse_mode="HTML",
        reply_markup=contact_keyboard(lang),
    )
