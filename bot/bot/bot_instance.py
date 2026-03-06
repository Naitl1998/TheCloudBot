"""
Singleton Bot and Dispatcher instances shared across the whole application.

Imported by:
- bot/main.py        (sets webhook, runs tasks)
- webapp/app.py      (feeds Telegram updates via /webhook endpoint)
- handlers/*         (call.bot / message.bot — injected automatically by aiogram)
"""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import bot.config as cfg
from bot.middlewares.i18n import I18nMiddleware
from bot.handlers import start, booking, admin

# ── Single Bot instance (reused everywhere) ───────────────────────────────────
bot = Bot(
    token=cfg.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

# ── Single Dispatcher instance ────────────────────────────────────────────────
dp = Dispatcher()

dp.message.middleware(I18nMiddleware())
dp.callback_query.middleware(I18nMiddleware())

dp.include_router(start.router)
dp.include_router(admin.router)
dp.include_router(booking.router)
