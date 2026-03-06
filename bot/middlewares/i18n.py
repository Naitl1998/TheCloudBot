import json
import os
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

_locales: Dict[str, Dict[str, str]] = {}

def _load_locales() -> None:
    locales_dir = os.path.join(os.path.dirname(__file__), "..", "locales")
    for lang in ("ru", "en", "vi"):
        path = os.path.join(locales_dir, f"{lang}.json")
        with open(path, encoding="utf-8") as f:
            _locales[lang] = json.load(f)


_load_locales()


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Translate a key for the given language with optional format params."""
    text = _locales.get(lang, _locales["ru"]).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text


class I18nMiddleware(BaseMiddleware):
    """Injects `lang` into handler data based on User.language_code or stored preference."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        lang = "ru"  # default

        if user:
            # Try to get stored language from DB (injected by booking service)
            try:
                from bot.services.booking_service import get_user_lang
                stored_lang = await get_user_lang(user.id)
            except Exception:
                stored_lang = None  # DB unavailable — fall back to language_code
            if stored_lang:
                lang = stored_lang
            elif user.language_code and user.language_code.startswith("vi"):
                lang = "vi"
            elif user.language_code and user.language_code.startswith("en"):
                lang = "en"

        data["lang"] = lang
        return await handler(event, data)
