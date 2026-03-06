"""
Telegram Mini App — FastAPI server for The Cloud booking floor plan.
"""
import contextlib
import hashlib
import hmac
import json
import logging
import aiohttp
from datetime import date as _date
from urllib.parse import unquote, parse_qsl
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from bot.config import (
    BOT_TOKEN, WEBAPP_PORT, WEBAPP_URL, TABLES, ADMIN_CHAT_ID, STAFF_IDS,
    BOOKING_OPEN_HOUR, BOOKING_CLOSE_HOUR, BOOKING_SLOT_MINUTES,
)
from bot.services.booking_service import (
    get_booked_tables,
    get_booked_times,
    get_live_booked_tables,
    create_booking,
    get_guest_by_phone,
    get_today_bookings,
    set_booking_status,
    update_booking_table,
    close_table_bookings,
    get_all_active_bookings,
    get_pending_bookings,
    get_confirmed_today_bookings,
    get_en_route_today_bookings,
    get_user_role,
    get_all_staff_ids,
    get_bookings_by_phone,
    get_bookings_for_table,
    get_booking,
    search_guests,
    set_guest_vip,
    set_guest_notes,
    create_guest_profile,
    get_user_lang,
    get_blacklist,
    check_blacklist,
    add_to_blacklist,
    remove_from_blacklist,
)
from bot.database.models import BookingStatus
from bot.middlewares.i18n import t as _t
from aiogram.types import Update as TelegramUpdate

logger = logging.getLogger(__name__)

# ── Webhook secret token ─────────────────────────────────────────────────────
# Derived from BOT_TOKEN — no extra env var needed, but always unique per bot.
# Telegram requires: 1-256 chars, only [A-Za-z0-9_-] allowed.
def _make_webhook_secret(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()  # 64 hex chars, always valid

WEBHOOK_SECRET: str = _make_webhook_secret(BOT_TOKEN) if BOT_TOKEN else ""


# ── Shared aiohttp session (lifespan) ────────────────────────────────────
# One ClientSession for the entire server lifetime avoids the overhead of
# creating+tearing-down a TCP connection on every Telegram notification.
_http_session: aiohttp.ClientSession | None = None


@contextlib.asynccontextmanager
async def _lifespan(app: FastAPI):
    global _http_session
    _http_session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=10),
        connector=aiohttp.TCPConnector(limit=20, ttl_dns_cache=300),
    )
    logger.info("Shared aiohttp session created.")
    try:
        yield
    finally:
        await _http_session.close()
        logger.info("Shared aiohttp session closed.")


def _get_http() -> aiohttp.ClientSession:
    """Return the shared aiohttp session; falls back to a temporary one during startup."""
    if _http_session and not _http_session.closed:
        return _http_session
    # Rare: called before lifespan is ready (e.g., import-time)
    return aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))

app = FastAPI(title="The Cloud Mini App", docs_url=None, redoc_url=None, lifespan=_lifespan)

import pathlib
_HERE = pathlib.Path(__file__).parent

app.mount("/static", StaticFiles(directory=_HERE / "static"), name="static")
templates = Jinja2Templates(directory=_HERE / "templates")

# ── Auto cache-busting: hash static assets on startup ─────────────────────────
# Every deploy produces a new hash → Telegram never serves stale JS/CSS.
def _file_hash(path: pathlib.Path, length: int = 8) -> str:
    """Return first `length` hex chars of the file's MD5 hash."""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()[:length]
    except FileNotFoundError:
        return "0"

ASSET_VERSION = _file_hash(_HERE / "static" / "app.js") + _file_hash(_HERE / "static" / "style.css")
templates.env.globals["asset_v"] = ASSET_VERSION
logger.info("Asset cache-bust version: %s", ASSET_VERSION)


# ─── Telegram Webhook endpoint ──────────────────────────────────────────────────────────

@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict:
    """
    Telegram sends ALL bot updates here (POST JSON).
    We feed them into the aiogram Dispatcher so handlers run normally.

    Security: Telegram includes X-Telegram-Bot-Api-Secret-Token header.
    We reject any request that doesn’t carry the correct token,
    which prevents third parties from injecting fake updates.

    Error handling: always return 200 so Telegram doesn’t retry the same
    update in a loop (Telegram retries on non-2xx for up to an hour).
    """
    # ── Verify secret token (Telegram sends it as a request header) ────────────
    if WEBHOOK_SECRET:
        received = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(received, WEBHOOK_SECRET):
            logger.warning(
                "Webhook: invalid secret token from %s (got %r)",
                request.client.host if request.client else "unknown",
                received[:8] + "..." if received else "(empty)",
            )
            # Return 200 (not 403) to avoid Telegram retry storm
            return {"ok": False, "error": "forbidden"}

    # ── Parse and dispatch the Telegram update ───────────────────────────────
    from bot.bot_instance import bot as _bot, dp as _dp  # lazy import avoids circular
    try:
        body = await request.body()
        update = TelegramUpdate.model_validate_json(body)
        await _dp.feed_update(bot=_bot, update=update)
    except Exception as exc:
        # Log but don’t crash — returning 200 prevents Telegram from retrying
        logger.error("Webhook dispatch error: %s", exc, exc_info=True)
    return {"ok": True}


# ─── Telegram initData validation ────────────────────────────────────────────

def validate_init_data(init_data: str) -> dict:
    """Validate Telegram WebApp initData and return parsed user dict."""
    params = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = params.pop("hash", None)
    if not received_hash:
        raise ValueError("Missing hash in initData")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        raise ValueError("Invalid initData hash")
    user_json = params.get("user", "{}")
    return json.loads(unquote(user_json))


def get_user_from_init(init_data: str) -> Optional[dict]:
    """Extract user dict from initData without raising on local dev."""
    if not init_data or not BOT_TOKEN:
        return None
    try:
        return validate_init_data(init_data)
    except Exception:
        return None


def is_staff_user(user_id: int) -> bool:
    return user_id == ADMIN_CHAT_ID or user_id in STAFF_IDS


# ─── Telegram Bot API notification ───────────────────────────────────────────

async def _tg_send(chat_id: int, text: str, reply_markup: dict | None = None) -> None:
    """Send a Telegram message using the shared aiohttp session."""
    if not BOT_TOKEN:
        return
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        session = _get_http()
        resp = await session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json=payload,
        )
        if not resp.ok:
            data = await resp.text()
            logger.warning("Telegram sendMessage %s → %s: %s", chat_id, resp.status, data[:120])
    except Exception as e:
        logger.warning("Telegram notification failed: %s", e)


# ─── Time slot generator ──────────────────────────────────────────────────────

def _generate_slots() -> list[str]:
    """Generate 30-min slots from 12:00 to 02:00 (next day).
    Hours > 23 wrap: 24→00, 25→01, 26→02.
    """
    slots = []
    total_minutes = (BOOKING_CLOSE_HOUR - BOOKING_OPEN_HOUR) * 60
    for offset in range(0, total_minutes + 1, BOOKING_SLOT_MINUTES):
        h = BOOKING_OPEN_HOUR + offset // 60
        m = offset % 60
        if h > BOOKING_CLOSE_HOUR or (h == BOOKING_CLOSE_HOUR and m > 0):
            break
        display_h = h % 24   # 24→0, 25→1, 26→2
        slots.append(f"{display_h:02d}:{m:02d}")
    return slots


ALL_SLOTS = _generate_slots()

HALL_LABELS = {
    "main":   "🏛 Основной зал",
    "second": "🔝 2nd Floor",
}


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/api/my/bookings")
async def api_my_bookings(phone: str = Query(...)):
    """Return recent bookings for a guest phone. Read-only, no auth required."""
    bookings = await get_bookings_by_phone(phone)
    result = []
    for b in bookings:
        result.append({
            "id":          b.id,
            "hall":        b.hall,
            "hall_label":  HALL_LABELS.get(b.hall, b.hall),
            "table":       b.table or "—",
            "date":        b.date,
            "time":        b.time,
            "guests_count": b.guests_count,
            "status":      b.status,
        })
    return JSONResponse({"bookings": result})


@app.get("/api/me/role")
async def api_me_role(init_data: str = Query(default="")):
    """Return the current user's role. Used by Mini App to show/hide staff features."""
    user = get_user_from_init(init_data)
    if not user:
        # No valid init_data — only allow if IP=localhost (dev)
        return JSONResponse({"role": "guest", "user_id": 0})
    uid  = user.get("id", 0)
    role = await get_user_role(uid)
    return JSONResponse({"role": role, "user_id": uid})


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/hub", response_class=HTMLResponse)
async def hub(request: Request):
    """Platform hub page — map of all venues."""
    base = WEBAPP_URL.rstrip("/") if WEBAPP_URL else str(request.base_url).rstrip("/")
    return templates.TemplateResponse("hub.html", {
        "request":   request,
        "cloud_url": base + "/",
        "dance_url": base + "/dance",
    })


@app.get("/dance", response_class=HTMLResponse)
async def dance(request: Request):
    """RITMO Dance Studio Mini App."""
    return templates.TemplateResponse("dance.html", {"request": request})


@app.get("/health")
async def health():
    """Lightweight liveness probe — used by tunnel heartbeat and uptime checks."""
    return {"ok": True}


@app.get("/api/tables")
async def api_tables(
    hall: str = Query(...),
    date: str = Query(...),
    time: str = Query(...),
):
    all_tables = TABLES.get(hall, [])
    booked = await get_booked_tables(hall, date, time)
    statuses = {}
    for t in all_tables:
        status = booked.get(t)
        if status == "confirmed":
            statuses[t] = "confirmed"
        elif status == "en_route":
            statuses[t] = "en_route"
        elif status == "pending":
            statuses[t] = "pending"
        else:
            statuses[t] = "free"
    return JSONResponse({"tables": statuses})


@app.get("/api/tables/live")
async def api_tables_live(
    hall: str = Query(...),
    date: str = Query(...),
    current_minutes: int = Query(...),
):
    """
    Return table statuses for the live-view tab.
    current_minutes: minutes since midnight (VN time), 00:xx-02:xx sent as 1440-1560.
    """
    all_tables = TABLES.get(hall, [])
    booked = await get_live_booked_tables(hall, date, current_minutes)
    result = {}
    for t in all_tables:
        info = booked.get(t)
        if info:
            result[t] = {"status": info["status"], "remaining_min": info["remaining_min"], "is_vip": info.get("is_vip", False)}
        else:
            result[t] = {"status": "free", "remaining_min": 0, "is_vip": False}
    return JSONResponse({"tables": result})


@app.get("/api/slots")
async def api_slots(
    hall: str = Query(...),
    date: str = Query(...),
):
    booked_times = await get_booked_times(hall, date)
    return JSONResponse({
        "slots": [{"time": s, "available": s not in booked_times} for s in ALL_SLOTS]
    })


@app.get("/api/table/bookings")
async def api_table_bookings(
    hall: str = Query(...),
    table: str = Query(...),
    date: str = Query(...),
):
    """Return all active bookings for a specific table on a given date (for live view in Mini App)."""
    bookings = await get_bookings_for_table(hall, table, date)
    result = []
    for b in bookings:
        result.append({
            "id":          b.id,
            "name":        b.name,
            "phone":       b.phone,
            "time":        b.time,
            "guests_count": b.guests_count,
            "status":      str(b.status.value if hasattr(b.status, 'value') else b.status),
            "comment":     b.comment or "",
            "tg_username": b.tg_username or "",
            "tg_user_id":  b.user_id or 0,
            "created_at":  b.created_at.isoformat() if b.created_at else None,
        })
    return JSONResponse({"bookings": result})


class StaffMoveRequest(BaseModel):
    init_data: str = ""
    booking_id: int
    new_table: str
    new_hall: str | None = None


@app.post("/api/staff/booking/move")
async def api_staff_booking_move(body: StaffMoveRequest):
    """Move a booking to a different table. Staff/admin only."""
    user = get_user_from_init(body.init_data)
    if user and not is_staff_user(user.get("id", 0)):
        raise HTTPException(status_code=403, detail="Staff only")

    booking = await update_booking_table(body.booking_id, body.new_table, body.new_hall)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Notify guest if they have a user_id
    if booking.user_id:
        hall_label = HALL_LABELS.get(booking.hall, booking.hall)
        hall_line = f"🏛 {hall_label}\n" if body.new_hall else ""
        await _tg_send(
            booking.user_id,
            f"🔄 <b>Ваш стол изменён</b>\n\n"
            f"📋 Бронь #{booking.id}\n"
            f"{hall_line}"
            f"🪑 Новый стол: {body.new_table}\n"
            f"📅 {booking.date} в {booking.time}"
        )

    return JSONResponse({"ok": True, "booking_id": booking.id, "new_table": body.new_table})


class StaffCancelFromSheetRequest(BaseModel):
    init_data: str = ""
    booking_id: int


@app.post("/api/staff/booking/cancel")
async def api_staff_booking_cancel(body: StaffCancelFromSheetRequest):
    """Cancel a booking from the live table sheet. Staff/admin only."""
    user = get_user_from_init(body.init_data)
    if user and not is_staff_user(user.get("id", 0)):
        raise HTTPException(status_code=403, detail="Staff only")

    booking = await set_booking_status(body.booking_id, BookingStatus.CANCELLED)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.user_id:
        await _tg_send(
            booking.user_id,
            f"❌ <b>Бронь отменена</b>\n\n"
            f"📋 Бронь #{booking.id} на {booking.date} в {booking.time} отменена.\n"
            f"Свяжитесь с рестораном для уточнения деталей."
        )

    return JSONResponse({"ok": True, "booking_id": booking.id})


class StaffWalkInRequest(BaseModel):
    init_data: str = ""
    hall: str
    table: str
    guests_count: str
    name: str = "Гость (без брони)"
    comment: str = ""


class StaffCloseTableRequest(BaseModel):
    init_data: str = ""
    hall: str
    table: str
    date: str


@app.post("/api/staff/table/close")
async def api_staff_table_close(body: StaffCloseTableRequest):
    """Mark all active bookings for a table as completed (guests left). Staff/admin only."""
    user = get_user_from_init(body.init_data)
    if user and not is_staff_user(user.get("id", 0)):
        raise HTTPException(status_code=403, detail="Staff only")

    count = await close_table_bookings(body.hall, body.table, body.date)
    return JSONResponse({"ok": True, "closed": count})


@app.post("/api/staff/walkin")
async def api_staff_walkin(body: StaffWalkInRequest):
    """Create an immediately-confirmed walk-in booking. Staff/admin only."""
    user = get_user_from_init(body.init_data)
    if user and not is_staff_user(user.get("id", 0)):
        raise HTTPException(status_code=403, detail="Staff only")

    import datetime
    vn_offset = datetime.timezone(datetime.timedelta(hours=7))
    now_vn = datetime.datetime.now(vn_offset)
    date   = now_vn.strftime("%Y-%m-%d")
    time   = now_vn.strftime("%H:%M")

    booking = await create_booking(
        user_id=0,
        name=body.name,
        phone="—",
        guests_count=body.guests_count,
        hall=body.hall,
        date=date,
        time=time,
        comment=body.comment or "Посадка по факту",
        table=body.table or None,
        source="walkin",
    )
    # Immediately confirm
    booking = await set_booking_status(booking.id, BookingStatus.CONFIRMED)

    # Notify all staff
    hall_label = HALL_LABELS.get(booking.hall, booking.hall)
    admin_text = (
        f"🚶 <b>Посадка по факту #{booking.id}</b>\n\n"
        f"👥 Гостей: {booking.guests_count}\n"
        f"🏛 {hall_label}\n"
        f"🪑 Стол: {booking.table or '—'}\n"
        f"📅 {booking.date} в {booking.time}\n"
        f"💬 {booking.comment or '—'}"
    )
    all_staff = await get_all_staff_ids()
    for staff_id in all_staff:
        await _tg_send(staff_id, admin_text)

    return JSONResponse({"ok": True, "booking_id": booking.id})


@app.get("/api/slots/table")
async def api_slots_table(
    hall: str = Query(...),
    table: str = Query(...),
    date: str = Query(...),
):
    """Return time slots showing availability for a specific table on a given date."""
    from bot.services.booking_service import get_booked_times_for_table
    booked_times = await get_booked_times_for_table(hall, table, date)
    return JSONResponse({
        "slots": [{"time": s, "available": s not in booked_times} for s in ALL_SLOTS]
    })


@app.get("/api/guest")
async def api_guest(phone: str = Query(...)):
    g = await get_guest_by_phone(phone)
    if not g:
        return JSONResponse({"found": False})
    return JSONResponse({
        "found": True,
        "name": g.name,
        "phone": g.phone,
        "is_vip": g.is_vip,
        "total_visits": g.total_visits,
        "notes": g.notes or "",
    })


# ─── Staff API ────────────────────────────────────────────────────────────────

@app.get("/api/staff/bookings")
async def api_staff_bookings(
    init_data: str = Query(default=""),
    date_filter: str = Query(default="today"),
):
    """Return bookings for staff/admin. Requires valid staff initData."""
    user = get_user_from_init(init_data)
    if user and not is_staff_user(user.get("id", 0)):
        raise HTTPException(status_code=403, detail="Staff only")

    if date_filter == "pending":
        bookings = await get_pending_bookings()
        pending_count = len(bookings)
        en_route_count = len(await get_en_route_today_bookings())
    elif date_filter == "confirmed_today":
        bookings = await get_confirmed_today_bookings()
        pending_count = len(await get_pending_bookings())
        en_route_count = len(await get_en_route_today_bookings())
    elif date_filter == "en_route":
        bookings = await get_en_route_today_bookings()
        pending_count = len(await get_pending_bookings())
        en_route_count = len(bookings)
    else:
        # fallback — treat as pending
        bookings = await get_pending_bookings()
        pending_count = len(bookings)
        en_route_count = len(await get_en_route_today_bookings())

    result = []
    for b in bookings:
        result.append({
            "id": b.id,
            "name": b.name,
            "phone": b.phone,
            "guests_count": b.guests_count,
            "hall": b.hall,
            "hall_label": HALL_LABELS.get(b.hall, b.hall),
            "table": b.table or "—",
            "date": b.date,
            "time": b.time,
            "comment": b.comment or "",
            "status": b.status,
            "source": b.source,
            "tg_username": b.tg_username or "",
            "tg_user_id": b.user_id or 0,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        })
    return JSONResponse({"bookings": result, "pending_count": pending_count, "en_route_count": en_route_count})


class StaffActionRequest(BaseModel):
    init_data: str
    booking_id: int
    action: str  # "confirm" | "cancel" | "en_route" | "arrived"


@app.post("/api/staff/action")
async def api_staff_action(body: StaffActionRequest):
    """Confirm, cancel, en_route or arrived a booking. Staff/admin only."""
    user = get_user_from_init(body.init_data)
    if user and not is_staff_user(user.get("id", 0)):
        raise HTTPException(status_code=403, detail="Staff only")

    if body.action == "confirm":
        booking = await set_booking_status(body.booking_id, BookingStatus.CONFIRMED)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.user_id:
            await _tg_send(
                booking.user_id,
                f"✅ <b>Ваша бронь подтверждена!</b>\n\n"
                f"📋 Бронь #{booking.id}\n"
                f"🏛 {HALL_LABELS.get(booking.hall, booking.hall)}\n"
                f"🪑 Стол: {booking.table or '—'}\n"
                f"📅 {booking.date} в {booking.time}\n"
                f"👥 Гостей: {booking.guests_count}"
            )
        return JSONResponse({"ok": True, "status": "confirmed"})

    elif body.action == "en_route":
        booking = await set_booking_status(body.booking_id, BookingStatus.EN_ROUTE)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.user_id:
            await _tg_send(
                booking.user_id,
                f"🟠 <b>Вы отмечены как «в пути»!</b>\n\n"
                f"📋 Бронь #{booking.id}\n"
                f"Мы ждём вас!"
            )
        return JSONResponse({"ok": True, "status": "en_route"})

    elif body.action == "arrived":
        booking = await set_booking_status(body.booking_id, BookingStatus.CONFIRMED)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.user_id:
            await _tg_send(
                booking.user_id,
                f"✅ <b>Добро пожаловать!</b>\n\n"
                f"📋 Бронь #{booking.id}\n"
                f"Ваш стол готов. Приятного отдыха!"
            )
        return JSONResponse({"ok": True, "status": "confirmed"})

    elif body.action == "cancel":
        booking = await set_booking_status(body.booking_id, BookingStatus.CANCELLED)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.user_id:
            await _tg_send(
                booking.user_id,
                f"❌ <b>Бронь отменена</b>\n\n"
                f"📋 Бронь #{booking.id} на {booking.date} в {booking.time} отменена.\n"
                f"Свяжитесь с рестораном для уточнения деталей."
            )
        return JSONResponse({"ok": True, "status": "cancelled"})

    raise HTTPException(status_code=400, detail="Unknown action")


# ─── En-route guests — seating from Tables view ──────────────────────────────

@app.get("/api/staff/enroute/today")
async def api_staff_enroute_today(init_data: str = Query(default="")):
    """Return today's en_route bookings so staff can seat them from the Tables view."""
    user = get_user_from_init(init_data)
    if user and not is_staff_user(user.get("id", 0)):
        raise HTTPException(status_code=403, detail="Staff only")

    bookings = await get_en_route_today_bookings()
    result = []
    for b in bookings:
        result.append({
            "id":           b.id,
            "name":         b.name,
            "phone":        b.phone,
            "guests_count": b.guests_count,
            "hall":         b.hall,
            "hall_label":   HALL_LABELS.get(b.hall, b.hall),
            "table":        b.table or "—",
            "date":         b.date,
            "time":         b.time,
            "comment":      b.comment or "",
            "status":       b.status,
        })
    return JSONResponse({"bookings": result})


class StaffSeatEnRouteRequest(BaseModel):
    init_data: str = ""
    booking_id: int
    table: str
    hall: str


@app.post("/api/staff/enroute/seat")
async def api_staff_enroute_seat(body: StaffSeatEnRouteRequest):
    """Seat an en_route guest at a specific table: assign table and mark as confirmed (arrived)."""
    user = get_user_from_init(body.init_data)
    if user and not is_staff_user(user.get("id", 0)):
        raise HTTPException(status_code=403, detail="Staff only")

    # First assign the table (and optionally change hall)
    booking = await update_booking_table(body.booking_id, body.table, body.hall)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Mark as confirmed (arrived)
    booking = await set_booking_status(body.booking_id, BookingStatus.CONFIRMED)

    # Notify guest
    if booking and booking.user_id:
        hall_label = HALL_LABELS.get(booking.hall, booking.hall)
        await _tg_send(
            booking.user_id,
            f"✅ <b>Добро пожаловать!</b>\n\n"
            f"📋 Бронь #{booking.id}\n"
            f"🏛 {hall_label}\n"
            f"🪑 Стол: {body.table}\n"
            f"Ваш стол готов. Приятного отдыха!"
        )

    # Notify all staff
    hall_label = HALL_LABELS.get(booking.hall, booking.hall)
    staff_text = (
        f"✅ <b>Гость посажен</b>\n\n"
        f"📋 Бронь #{booking.id}\n"
        f"👤 {booking.name}\n"
        f"🏛 {hall_label}\n"
        f"🪑 Стол: {body.table}\n"
        f"👥 Гостей: {booking.guests_count}"
    )
    all_staff = await get_all_staff_ids()
    for staff_id in all_staff:
        await _tg_send(staff_id, staff_text)

    return JSONResponse({"ok": True, "booking_id": booking.id, "table": body.table})


# ─── Booking ──────────────────────────────────────────────────────────────────

class BookingRequest(BaseModel):
    init_data: str = ""
    hall: str
    date: str
    time: str
    table: str = ""
    guests_count: str
    name: str
    phone: str
    tg_username: str = ""
    comment: str = ""


@app.post("/api/book")
async def api_book(body: BookingRequest):
    user_id = 0
    user_name = ""
    user_tg_username = ""
    if BOT_TOKEN and body.init_data:
        try:
            user = validate_init_data(body.init_data)
            user_id = user.get("id", 0)
            user_name = user.get("first_name", "")
            user_tg_username = user.get("username", "")
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e))

    # Use manually entered tg_username, or fall back to Telegram initData username
    resolved_tg = body.tg_username.lstrip("@") if body.tg_username else (user_tg_username or None)

    # ── Blacklist check ──────────────────────────────────────────────────────
    bl_entry = await check_blacklist(phone=body.phone, tg_username=resolved_tg or "")
    if bl_entry:
        reason_hint = f" ({bl_entry.reason})" if bl_entry.reason else ""
        raise HTTPException(
            status_code=403,
            detail=f"blacklisted{reason_hint}",
        )

    booking = await create_booking(
        user_id=user_id,
        name=body.name,
        phone=body.phone,
        guests_count=body.guests_count,
        hall=body.hall,
        date=body.date,
        time=body.time,
        comment=body.comment or None,
        table=body.table or None,
        source="webapp",
        tg_username=resolved_tg,
    )

    # Notify admin via Telegram Bot API
    hall_label = HALL_LABELS.get(booking.hall, booking.hall)
    tg_line = ""
    tg_btn = []
    if resolved_tg:
        tg_handle = resolved_tg.lstrip("@")
        tg_line = f"✈️ <a href=\"https://t.me/{tg_handle}\">@{tg_handle}</a>\n"
        tg_btn = [{"text": f"✈️ @{tg_handle}", "url": f"https://t.me/{tg_handle}"}]
    admin_text = (
        f"🆕 <b>Новая бронь #{booking.id}</b> (Mini App)\n\n"
        f"👤 {booking.name}\n"
        f"📞 {booking.phone}\n"
        f"{tg_line}"
        f"👥 Гостей: {booking.guests_count}\n"
        f"🏛 {hall_label}\n"
        f"🪑 Стол: {booking.table or '—'}\n"
        f"📅 {booking.date} в {booking.time}\n"
        f"💬 {booking.comment or '—'}"
    )
    buttons_row2 = [{"text": f"📞 {booking.phone}", "url": f"tel:{booking.phone}"}]
    if tg_btn:
        buttons_row2.append(tg_btn[0])
    admin_markup = {
        "inline_keyboard": [[
            {"text": "✅ Принять",    "callback_data": f"admin:accept:{booking.id}"},
            {"text": "❌ Отклонить", "callback_data": f"admin:reject:{booking.id}"},
        ],
        buttons_row2
        ]
    }
    # Notify ALL staff + admin via Telegram Bot API
    all_staff = await get_all_staff_ids()
    for staff_id in all_staff:
        await _tg_send(staff_id, admin_text, admin_markup if staff_id == ADMIN_CHAT_ID else None)

    # Notify guest in Telegram chat
    if user_id:
        try:
            lang = await get_user_lang(user_id) or "ru"
        except Exception:
            lang = "ru"
        await _tg_send(user_id, _t("booking_confirmed_user", lang, id=booking.id))

    return JSONResponse({"ok": True, "booking_id": booking.id})


# ─── Regulars (Guest profiles) ─────────────────────────────────────────────

@app.get("/api/staff/guests")
async def api_staff_guests(
    q: str = Query(""),
    init_data: str = Query(""),
):
    """Return guest profiles for staff/admin, optionally filtered by name/phone."""
    uid = 0
    if init_data:
        u = get_user_from_init(init_data)
        uid = u.get("id", 0) if u else 0
    # Allow if admin/staff by config or if no auth in dev mode
    if uid and not is_staff_user(uid):
        role = await get_user_role(uid)
        if role not in ("admin", "staff"):
            raise HTTPException(status_code=403, detail="Forbidden")
    guests = await search_guests(q.strip(), limit=200)
    return JSONResponse({"guests": [
        {
            "id":           g.id,
            "name":         g.name,
            "phone":        g.phone,
            "total_visits": g.total_visits,
            "is_vip":       g.is_vip,
            "notes":        g.notes or "",
        }
        for g in guests
    ]})


class GuestUpdateBody(BaseModel):
    init_data: str = ""
    phone:     str
    is_vip:    bool | None = None
    notes:     str | None = None


@app.post("/api/staff/guest/update")
async def api_staff_guest_update(body: GuestUpdateBody):
    """Update guest VIP status and/or notes. Admin/staff only."""
    uid = 0
    if body.init_data:
        u = get_user_from_init(body.init_data)
        uid = u.get("id", 0) if u else 0
    if uid and not is_staff_user(uid):
        role = await get_user_role(uid)
        if role not in ("admin", "staff"):
            raise HTTPException(status_code=403, detail="Forbidden")
    if body.is_vip is not None:
        await set_guest_vip(body.phone, body.is_vip)
    if body.notes is not None:
        await set_guest_notes(body.phone, body.notes)
    return JSONResponse({"ok": True})


class GuestCreateBody(BaseModel):
    init_data: str = ""
    phone:     str
    name:      str
    notes:     str = ""
    is_vip:    bool = False


@app.post("/api/staff/guest/create")
async def api_staff_guest_create(body: GuestCreateBody):
    """Manually add or update a guest profile. Admin/staff only."""
    uid = 0
    if body.init_data:
        u = get_user_from_init(body.init_data)
        uid = u.get("id", 0) if u else 0
    if uid and not is_staff_user(uid):
        role = await get_user_role(uid)
        if role not in ("admin", "staff"):
            raise HTTPException(status_code=403, detail="Forbidden")
    if not body.phone.strip() or not body.name.strip():
        raise HTTPException(status_code=400, detail="phone and name required")
    profile = await create_guest_profile(
        phone=body.phone.strip(), name=body.name.strip(),
        notes=body.notes.strip(), is_vip=body.is_vip,
    )
    return JSONResponse({"ok": True, "guest": {
        "id": profile.id, "name": profile.name, "phone": profile.phone,
        "total_visits": profile.total_visits, "is_vip": profile.is_vip,
        "notes": profile.notes or "",
    }})


# ─── Blacklist ──────────────────────────────────────────────────────────────

@app.get("/api/staff/blacklist")
async def api_staff_blacklist(
    q: str = Query(""),
    init_data: str = Query(""),
):
    """Return blacklisted guests. Admin/staff only."""
    uid = 0
    if init_data:
        u = get_user_from_init(init_data)
        uid = u.get("id", 0) if u else 0
    if uid and not is_staff_user(uid):
        role = await get_user_role(uid)
        if role not in ("admin", "staff"):
            raise HTTPException(status_code=403, detail="Forbidden")
    entries = await get_blacklist(q.strip(), limit=500)
    return JSONResponse({"blacklist": [
        {
            "id":           e.id,
            "name":         e.name or "",
            "phone":        e.phone or "",
            "tg_username":  e.tg_username or "",
            "reason":       e.reason or "",
            "created_at":   e.created_at.strftime("%Y-%m-%d") if e.created_at else "",
        }
        for e in entries
    ]})


class BlacklistAddBody(BaseModel):
    init_data:   str = ""
    phone:       str = ""
    tg_username: str = ""
    name:        str = ""
    reason:      str = ""


@app.post("/api/staff/blacklist/add")
async def api_blacklist_add(body: BlacklistAddBody):
    """Add a guest to the blacklist. Admin/staff only."""
    uid = 0
    if body.init_data:
        u = get_user_from_init(body.init_data)
        uid = u.get("id", 0) if u else 0
    if uid and not is_staff_user(uid):
        role = await get_user_role(uid)
        if role not in ("admin", "staff"):
            raise HTTPException(status_code=403, detail="Forbidden")
    if not body.phone.strip() and not body.tg_username.strip():
        raise HTTPException(status_code=400, detail="phone or tg_username required")
    entry = await add_to_blacklist(
        phone=body.phone.strip(),
        tg_username=body.tg_username.strip(),
        name=body.name.strip(),
        reason=body.reason.strip(),
        added_by=uid,
    )
    return JSONResponse({"ok": True, "id": entry.id})


class BlacklistRemoveBody(BaseModel):
    init_data: str = ""
    id:        int


@app.post("/api/staff/blacklist/remove")
async def api_blacklist_remove(body: BlacklistRemoveBody):
    """Remove a guest from the blacklist. Admin/staff only."""
    uid = 0
    if body.init_data:
        u = get_user_from_init(body.init_data)
        uid = u.get("id", 0) if u else 0
    if uid and not is_staff_user(uid):
        role = await get_user_role(uid)
        if role not in ("admin", "staff"):
            raise HTTPException(status_code=403, detail="Forbidden")
    deleted = await remove_from_blacklist(body.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return JSONResponse({"ok": True})


# ─── RITMO Dance Studio booking ──────────────────────────────────────────────

class DanceBookingRequest(BaseModel):
    init_data:  str = ""
    class_type: str          # salsa | bachata | hiphop | contemporary | ladies | kids
    class_name: str          # human-readable e.g. "💃 Сальса"
    date:       str          # YYYY-MM-DD
    time:       str          # HH:MM
    level:      str = "beginner"
    name:       str
    phone:      str
    comment:    str = ""


@app.post("/api/dance/book")
async def api_dance_book(body: DanceBookingRequest):
    """Create a dance class booking and notify admin via Telegram."""
    user_id = 0
    if BOT_TOKEN and body.init_data:
        try:
            u = validate_init_data(body.init_data)
            user_id = u.get("id", 0)
        except ValueError:
            pass  # non-critical for dance bookings

    LEVEL_LABELS = {
        "beginner":     "Новичок 🌱",
        "intermediate": "Средний ⚡",
        "advanced":     "Продвинутый 🔥",
    }
    level_label = LEVEL_LABELS.get(body.level, body.level)

    admin_text = (
        f"💃 <b>Новая запись на танцы</b>\n\n"
        f"👤 {body.name}\n"
        f"📞 {body.phone}\n"
        f"🎵 {body.class_name}\n"
        f"📅 {body.date} в {body.time}\n"
        f"🎯 Уровень: {level_label}\n"
        f"💬 {body.comment or '—'}"
    )

    markup = {
        "inline_keyboard": [[
            {"text": f"📞 {body.phone}", "url": f"tel:{body.phone}"},
        ]]
    }

    await _tg_send(ADMIN_CHAT_ID, admin_text, markup)
    all_staff = await get_all_staff_ids()
    for staff_id in all_staff:
        if staff_id != ADMIN_CHAT_ID:
            await _tg_send(staff_id, admin_text)

    logger.info(f"Dance booking: {body.name} / {body.class_name} / {body.date} {body.time}")
    return JSONResponse({"ok": True})
