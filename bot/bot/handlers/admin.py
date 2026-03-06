from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from datetime import date

from bot.config import ADMIN_CHAT_ID, STAFF_IDS, TABLES as TABLES_CFG
from bot.database.models import BookingStatus, UserRole
from bot.middlewares.i18n import t
from bot.services import booking_service, poster_service
from bot.keyboards.inline import admin_dates_keyboard, floor_plan_view_keyboard, release_table_keyboard

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_CHAT_ID


def is_admin_or_staff(user_id: int) -> bool:
    return user_id == ADMIN_CHAT_ID or user_id in STAFF_IDS

# ─── /today — bookings for today ──────────────────────────────────────────

@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    if not is_admin_or_staff(message.from_user.id):
        return
    today_str = date.today().isoformat()
    bookings = await booking_service.get_today_bookings()
    if not bookings:
        await message.answer(f"💭 Броней на сегодня ({today_str}) нет.")
        return
    header = f"📅 <b>Брони на сегодня ({today_str}):</b> {len(bookings)} шт."
    text = header + "\n\n" + "\n\n".join(b.summary("ru") for b in bookings)
    await message.answer(text, parse_mode="HTML")

# ─── /bookings — list active bookings ─────────────────────────────────────────

@router.message(Command("bookings"))
async def cmd_bookings(message: Message) -> None:
    if not is_admin_or_staff(message.from_user.id):
        return
    bookings = await booking_service.get_all_active_bookings()
    if not bookings:
        await message.answer(t("admin_no_bookings", "ru"))
        return
    text = "\n\n".join(b.summary("ru") for b in bookings)
    await message.answer(text, parse_mode="HTML")


# ─── /stats ───────────────────────────────────────────────────────────────────

@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not is_admin_or_staff(message.from_user.id):
        return
    stats = await booking_service.get_stats()
    await message.answer(
        t("admin_stats", "ru", **stats),
        parse_mode="HTML",
    )


# ─── /cancel <id> ─────────────────────────────────────────────────────────────

@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /cancel <id>")
        return
    booking_id = int(parts[1])
    existing = await booking_service.get_booking(booking_id)
    if not existing:
        await message.answer(f"Бронь #{booking_id} не найдена.")
        return
    prev_status = existing.status
    booking = await booking_service.set_booking_status(booking_id, BookingStatus.CANCELLED)
    if booking.poster_reservation_id:
        await poster_service.cancel_reservation(booking.poster_reservation_id)

    await message.answer(t("admin_rejected", "ru", id=booking_id))

    # Notify guest only if they hadn't already arrived
    prev_status_str = str(prev_status).replace("BookingStatus.", "").lower()
    if prev_status_str != "confirmed":
        try:
            from aiogram import Bot
            bot: Bot = message.bot
            user_lang = await booking_service.get_user_lang(booking.user_id)
            await bot.send_message(
                booking.user_id,
                t("booking_rejected", user_lang or "ru", id=booking_id),
                parse_mode="HTML",
            )
        except Exception:
            pass


# ─── Inline admin callbacks (✅ Accept / ❌ Reject) ──────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith("admin:accept:"))
async def admin_accept(call: CallbackQuery) -> None:
    if not is_admin_or_staff(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return

    booking_id = int(call.data.split(":")[2])
    booking = await booking_service.get_booking(booking_id)
    if not booking:
        await call.answer("Бронь не найдена", show_alert=True)
        return

    # Sync to Poster
    poster_id = await poster_service.create_reservation(
        hall=booking.hall,
        date=booking.date,
        time=booking.time,
        guests_count=booking.guests_count,
        name=booking.name,
        phone=booking.phone,
        comment=booking.comment,
    )

    await booking_service.set_booking_status(booking_id, BookingStatus.EN_ROUTE, poster_id)

    await call.message.edit_text(
        call.message.text + f"\n\n✅ {t('admin_accepted', 'ru', id=booking_id)}\n🟠 Ожидаем гостя",
        parse_mode="HTML",
    )

    # Notify guest
    try:
        user_lang = await booking_service.get_user_lang(booking.user_id)
        await call.bot.send_message(
            booking.user_id,
            t("booking_accepted", user_lang or "ru", id=booking_id),
            parse_mode="HTML",
        )
    except Exception:
        pass

    await call.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("admin:reject:"))
async def admin_reject(call: CallbackQuery) -> None:
    if not is_admin_or_staff(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return

    booking_id = int(call.data.split(":")[2])
    existing = await booking_service.get_booking(booking_id)
    if not existing:
        await call.answer("Бронь не найдена", show_alert=True)
        return
    prev_status = existing.status
    booking = await booking_service.set_booking_status(booking_id, BookingStatus.CANCELLED)
    if not booking:
        await call.answer("Бронь не найдена", show_alert=True)
        return

    await call.message.edit_text(
        call.message.text + f"\n\n❌ {t('admin_rejected', 'ru', id=booking_id)}",
        parse_mode="HTML",
    )

    # Notify guest only if they hadn't already arrived (don't send cancel msg when guests left after visiting)
    prev_status_str = str(prev_status).replace("BookingStatus.", "").lower()
    if prev_status_str != "confirmed":
        try:
            user_lang = await booking_service.get_user_lang(booking.user_id)
            await call.bot.send_message(
                booking.user_id,
                t("booking_rejected", user_lang or "ru", id=booking_id),
                parse_mode="HTML",
            )
        except Exception:
            pass

    await call.answer()


# ─── 🟠 En Route — guest is on the way ───────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith("admin:enroute:"))
async def admin_en_route(call: CallbackQuery) -> None:
    if not is_admin_or_staff(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return

    booking_id = int(call.data.split(":")[2])
    booking = await booking_service.get_booking(booking_id)
    if not booking:
        await call.answer("Бронь не найдена", show_alert=True)
        return

    await booking_service.set_booking_status(booking_id, BookingStatus.EN_ROUTE)

    await call.message.edit_text(
        call.message.text + f"\n\n🟠 Гость #{booking_id} в пути",
        parse_mode="HTML",
    )

    # Notify guest
    try:
        user_lang = await booking_service.get_user_lang(booking.user_id)
        msg = {
            "ru": f"🟠 <b>Вы отмечены как «в пути»!</b>\n\n📋 Бронь #{booking_id}\nМы ждём вас!",
            "vi": f"🟠 <b>Bạn đã được đánh dấu đang trên đường!</b>\n\n📋 Đặt chỗ #{booking_id}\nChúng tôi đang chờ bạn!",
            "en": f"🟠 <b>You're marked as on the way!</b>\n\n📋 Booking #{booking_id}\nWe're waiting for you!",
        }
        await call.bot.send_message(
            booking.user_id,
            msg.get(user_lang or "ru", msg["ru"]),
            parse_mode="HTML",
        )
    except Exception:
        pass

    await call.answer()


# ─── ✅ Arrived — guest has arrived at venue ─────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith("admin:arrived:"))
async def admin_arrived(call: CallbackQuery) -> None:
    if not is_admin_or_staff(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return

    booking_id = int(call.data.split(":")[2])
    booking = await booking_service.get_booking(booking_id)
    if not booking:
        await call.answer("Бронь не найдена", show_alert=True)
        return

    await booking_service.set_booking_status(booking_id, BookingStatus.CONFIRMED)

    await call.message.edit_text(
        call.message.text + f"\n\n🔴 Гость #{booking_id} прибыл — стол занят",
        parse_mode="HTML",
        reply_markup=release_table_keyboard(booking_id),
    )

    await call.answer()


# ─── 🔓 Release table — guests have left (no guest notification) ─────────────

@router.callback_query(lambda c: c.data and c.data.startswith("admin:release:"))
async def admin_release(call: CallbackQuery) -> None:
    if not is_admin_or_staff(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return

    booking_id = int(call.data.split(":")[2])
    booking = await booking_service.set_booking_status(booking_id, BookingStatus.COMPLETED)
    if not booking:
        await call.answer("Бронь не найдена", show_alert=True)
        return

    await call.message.edit_text(
        call.message.text + f"\n\n✅ Стол освобождён — гости ушли (#{booking_id})",
        parse_mode="HTML",
    )

    # No notification sent to guest intentionally
    await call.answer("Стол освобождён", show_alert=False)


# ─── /enroute — list guests on the way ────────────────────────────────────────

@router.message(Command("enroute"))
async def cmd_enroute(message: Message) -> None:
    if not is_admin_or_staff(message.from_user.id):
        return
    bookings = await booking_service.get_en_route_today_bookings()
    if not bookings:
        await message.answer("🟠 Нет гостей в пути на сегодня.")
        return
    header = f"🟠 <b>Гости в пути ({len(bookings)}):</b>"
    lines = []
    for b in bookings:
        lines.append(b.summary("ru"))
    text = header + "\n\n" + "\n\n".join(lines)

    from bot.keyboards.inline import en_route_bookings_keyboard
    await message.answer(text, parse_mode="HTML", reply_markup=en_route_bookings_keyboard(bookings))


# ─── /guests — list all guest profiles ────────────────────────────────────────

@router.message(Command("guests"))
async def cmd_guests(message: Message) -> None:
    if not is_admin_or_staff(message.from_user.id):
        return
    guests = await booking_service.get_all_guests(limit=30)
    if not guests:
        await message.answer("👥 Гости ещё не зарегистрированы.")
        return
    lines = []
    for g in guests:
        vip = "⭐ VIP" if g.is_vip else ""
        lines.append(f"• {g.name} | {g.phone} | визиты: {g.total_visits} {vip}")
    await message.answer(f"👥 <b>Гости ({len(guests)}):</b>\n" + "\n".join(lines), parse_mode="HTML")


@router.message(Command("guest"))
async def cmd_guest(message: Message) -> None:
    if not is_admin_or_staff(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /guest <телефон>")
        return
    phone = parts[1].strip()
    g = await booking_service.get_guest_by_phone(phone)
    if not g:
        await message.answer(f"❓ Гость с номером {phone} не найден.")
        return
    vip = "⭐ VIP" if g.is_vip else "Обычный гость"
    notes = g.notes or "—"
    await message.answer(
        f"👤 <b>{g.name}</b>\n"
        f"📞 {g.phone}\n"
        f"🏷 Статус: {vip}\n"
        f"🔢 Визитов: {g.total_visits}\n"
        f"📝 Заметки: {notes}",
        parse_mode="HTML",
    )


@router.message(Command("vip"))
async def cmd_vip(message: Message) -> None:
    """Toggle VIP status: /vip <phone> or /vip remove <phone>"""
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /vip <телефон> | /vip remove <телефон>")
        return
    if parts[1] == "remove" and len(parts) >= 3:
        phone = parts[2]
        g = await booking_service.set_guest_vip(phone, False)
        await message.answer(f"✅ Статус VIP снят с {g.name} ({phone})." if g else f"❓ Гость {phone} не найден.")
    else:
        phone = parts[1]
        g = await booking_service.set_guest_vip(phone, True)
        await message.answer(f"⭐ {g.name} ({phone}) теперь VIP!" if g else f"❓ Гость {phone} не найден.")


# ─── /staff — show staff members ──────────────────────────────────────────────

@router.message(Command("staff"))
async def cmd_staff(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    staff_list = await booking_service.get_all_staff()
    all_ids    = await booking_service.get_all_staff_ids()
    env_staff  = ", ".join(str(i) for i in STAFF_IDS) if STAFF_IDS else "не задано"

    lines = []
    for u in staff_list:
        if u.id == ADMIN_CHAT_ID:
            lines.append(f"👑 <b>Администратор</b> — ID: <code>{u.id}</code>")
        else:
            lines.append(f"🧑‍💼 {u.first_name or '—'} — ID: <code>{u.id}</code> ({u.role})")

    # Show IDs that are in env STAFF_IDS but not yet in DB
    db_ids = {u.id for u in staff_list}
    for sid in STAFF_IDS:
        if sid not in db_ids:
            lines.append(f"🔑 <i>env-only</i> — ID: <code>{sid}</code>")

    text = (
        f"🧑‍💼 <b>Персонал</b> — {len(all_ids)} чел.:\n\n"
        + ("\n".join(lines) if lines else "<i>пусто</i>")
        + f"\n\n<b>Добавить:</b> /addstaff &lt;user_id&gt; [имя]\n"
        + f"<b>Удалить:</b> /removestaff &lt;user_id&gt;"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("addstaff"))
async def cmd_addstaff(message: Message) -> None:
    """Usage: /addstaff <user_id> [display name]
    Adds user to staff whitelist (DB + in-memory). They immediately get access."""
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await message.answer(
            "ℹ️ <b>Добавление сотрудника:</b>\n"
            "<code>/addstaff <user_id> [имя]</code>\n\n"
            "Узнать свой ID можно через @userinfobot",
            parse_mode="HTML"
        )
        return
    target_id = int(parts[1])
    name = parts[2] if len(parts) > 2 else str(target_id)
    # Add to DB
    await booking_service.upsert_user_role(target_id, UserRole.STAFF, name)
    # Add to in-memory whitelist immediately (no restart needed)
    from bot import config as cfg
    cfg.STAFF_IDS.add(target_id)
    await message.answer(
        f"✅ <b>{name}</b> (ID: <code>{target_id}</code>) добавлен в список сотрудников.\n"
        f"Теперь он может принимать/отклонять брони.",
        parse_mode="HTML"
    )


@router.message(Command("removestaff"))
async def cmd_removestaff(message: Message) -> None:
    """Usage: /removestaff <user_id>"""
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await message.answer("Использование: /removestaff <user_id>")
        return
    target_id = int(parts[1])
    await booking_service.upsert_user_role(target_id, UserRole.GUEST, str(target_id))
    from bot import config as cfg
    cfg.STAFF_IDS.discard(target_id)
    await message.answer(f"❌ Пользователь <code>{target_id}</code> удалён из сотрудников.", parse_mode="HTML")


@router.message(Command("setrole"))
async def cmd_setrole(message: Message) -> None:
    """Usage: /setrole <user_id> <role>  (roles: guest/staff/vip/admin)"""
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Использование: /setrole <user_id> <guest|staff|vip|admin>")
        return
    try:
        target_id = int(parts[1])
        role = parts[2].lower()
    except ValueError:
        await message.answer("❌ Неверный ID.")
        return
    valid_roles = {"guest", "staff", "vip", "admin"}
    if role not in valid_roles:
        await message.answer(f"❌ Роль должна быть одной из: {', '.join(valid_roles)}")
        return
    await booking_service.set_user_role(target_id, role)
    await message.answer(f"✅ Пользователю {target_id} назначена роль: {role}")


# ─── Global noop (admin floor-plan free cells / legend) ─────────────────────

@router.callback_query(lambda c: c.data == "noop")
async def admin_noop(call: CallbackQuery) -> None:
    await call.answer()


# ─── /tables — view floor plan bookings by date ────────────────────────────────

_HALL_NAMES = {
    "main":   ("🏛", "Основной зал"),
    "second": ("🔝", "2nd Floor"),
}


@router.message(Command("tables"))
async def cmd_tables(message: Message) -> None:
    """Admin command: show bookings floor-plan for any date."""
    if not is_admin_or_staff(message.from_user.id):
        return
    await message.answer(
        "📅 <b>Просмотр столов по дате</b>\n\nВыберите дату — столы, на которые есть брони, будут подсвечены:",
        parse_mode="HTML",
        reply_markup=admin_dates_keyboard("ru"),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("vtables_date:"))
async def vtables_show_floor(call: CallbackQuery) -> None:
    if not is_admin_or_staff(call.from_user.id):
        await call.answer("⛔", show_alert=True)
        return
    view_date = call.data[len("vtables_date:"):]
    await _vtables_render(call, hall="main", view_date=view_date)


@router.callback_query(lambda c: c.data and c.data.startswith("vtables_hall:"))
async def vtables_switch_hall(call: CallbackQuery) -> None:
    if not is_admin_or_staff(call.from_user.id):
        await call.answer("⛔", show_alert=True)
        return
    # format: vtables_hall:<hall>:<YYYY-MM-DD>
    _, hall, view_date = call.data.split(":", 2)
    await _vtables_render(call, hall=hall, view_date=view_date)


async def _vtables_render(call: CallbackQuery, hall: str, view_date: str) -> None:
    """Shared helper: fetch booked tables and render the floor plan."""
    booked = await booking_service.get_booked_tables_for_date(hall, view_date)
    icon, hall_title = _HALL_NAMES.get(hall, ("🏛", hall))
    count = len(booked)
    if count:
        status_line = f"Занято столов: <b>{count}</b>  (🔴 подтверждено / � в пути / �🟡 ожидает)"
    else:
        status_line = "✅ Все столы свободны"
    text = (
        f"🗺 <b>Столы на {view_date}</b>\n"
        f"{icon} {hall_title}\n\n"
        f"{status_line}\n\n"
        f"Нажмите на занятый стол, чтобы увидеть брони."
    )
    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=floor_plan_view_keyboard(hall, booked, view_date, "ru"),
    )
    await call.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("vtables_info:"))
async def vtables_table_info(call: CallbackQuery) -> None:
    """Show a popup with bookings for a booked table on the selected date."""
    if not is_admin_or_staff(call.from_user.id):
        await call.answer("⛔", show_alert=True)
        return
    # format: vtables_info:<table>:<YYYY-MM-DD>
    _, table_name, view_date = call.data.split(":", 2)
    hall = next((h for h, tables in TABLES_CFG.items() if table_name in tables), "main")
    bookings = await booking_service.get_bookings_for_table(hall, table_name, view_date)
    if not bookings:
        await call.answer("Брони не найдены", show_alert=True)
        return
    lines = []
    for b in bookings:
        icon = "✅" if b.status in (BookingStatus.CONFIRMED, "confirmed") else ("🟠" if b.status in (BookingStatus.EN_ROUTE, "en_route") else "🟡")
        lines.append(f"{icon} {b.time} — {b.name}, {b.guests_count} чел., {b.phone} (#{b.id})")
    text = "\n".join(lines)
    if len(text) > 195:
        text = text[:192] + "…"
    await call.answer(text, show_alert=True)


@router.callback_query(lambda c: c.data == "vtables_back")
async def vtables_back(call: CallbackQuery) -> None:
    if not is_admin_or_staff(call.from_user.id):
        await call.answer("⛔", show_alert=True)
        return
    await call.message.edit_text(
        "📅 <b>Просмотр столов по дате</b>\n\nВыберите дату — столы, на которые есть брони, будут подсвечены:",
        parse_mode="HTML",
        reply_markup=admin_dates_keyboard("ru"),
    )
    await call.answer()
