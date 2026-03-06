from sqlalchemy import select, update, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import date, datetime

from bot.config import TABLES, ADMIN_CHAT_ID, STAFF_IDS
from bot.database.db import AsyncSessionLocal, _IS_SQLITE, with_db_retry
from bot.database.models import Booking, BookingStatus, User, UserRole, GuestProfile, BlacklistedGuest, _utcnow

# Dialect-aware upsert: SQLite and PostgreSQL both support ON CONFLICT
if _IS_SQLITE:
    from sqlalchemy.dialects.sqlite import insert as _upsert_insert
else:
    from sqlalchemy.dialects.postgresql import insert as _upsert_insert


# ─── User helpers ─────────────────────────────────────────────────────────────

@with_db_retry()
async def get_user_lang(user_id: int) -> str | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user.language if user else None


@with_db_retry()
async def upsert_user(user_id: int, username: str | None,
                      first_name: str | None, language: str = "ru") -> str:
    """Create or update user record atomically. Returns the user's role."""
    # Determine role from config (config always wins over DB)
    if user_id == ADMIN_CHAT_ID:
        forced_role = UserRole.ADMIN
    elif user_id in STAFF_IDS:
        forced_role = UserRole.STAFF
    else:
        forced_role = None

    async with AsyncSessionLocal() as session:
        # ON CONFLICT DO UPDATE — atomic upsert (works on SQLite + PostgreSQL)
        stmt = _upsert_insert(User).values(
            id=user_id,
            username=username,
            first_name=first_name,
            language=language,
            role=forced_role or UserRole.GUEST,
        ).on_conflict_do_update(
            index_elements=["id"],
            set_={
                "username":    username,
                "first_name":  first_name,
                "language":    language,
                # Only override role if config forces it (admin/staff)
                **({"role": forced_role} if forced_role else {}),
            },
        )
        await session.execute(stmt)
        await session.commit()

        # Re-read role from DB (covers VIP and other stored roles)
        result = await session.execute(select(User.role).where(User.id == user_id))
        db_role = result.scalar_one_or_none()
        return db_role or forced_role or UserRole.GUEST


# ─── Booking helpers ───────────────────────────────────────────────────────────

@with_db_retry()
async def create_booking(
    user_id: int, name: str, phone: str, guests_count: str,
    hall: str, date: str, time: str, comment: str | None,
    table: str | None = None,
    source: str = "bot",
    tg_username: str | None = None,
) -> Booking:
    async with AsyncSessionLocal() as session:
        booking = Booking(
            user_id=user_id,
            name=name,
            phone=phone,
            guests_count=guests_count,
            hall=hall,
            table=table,
            date=date,
            time=time,
            comment=comment,
            tg_username=tg_username or None,
            status=BookingStatus.PENDING,
            source=source,
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)

    return booking


@with_db_retry()
async def get_booking(booking_id: int) -> Booking | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Booking).where(Booking.id == booking_id))
        return result.scalar_one_or_none()


@with_db_retry()
async def get_user_active_bookings(user_id: int) -> list[Booking]:
    import datetime as _dt
    _vn_tz = _dt.timezone(_dt.timedelta(hours=7))
    today = _dt.datetime.now(_vn_tz).strftime("%Y-%m-%d")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.user_id == user_id)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.EN_ROUTE]))
            .where(Booking.date >= today)
            .order_by(Booking.date, Booking.time)
        )
        return list(result.scalars().all())


@with_db_retry()
async def get_all_active_bookings() -> list[Booking]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.EN_ROUTE]))
            .order_by(Booking.date, Booking.time)
        )
        return list(result.scalars().all())


@with_db_retry()
async def expire_pending_bookings() -> list["Booking"]:
    """
    Cancel all PENDING bookings whose created_at is older than 15 minutes.
    Returns the list of just-cancelled bookings (for notifications).
    """
    from datetime import datetime, timedelta
    cutoff = _utcnow() - timedelta(minutes=15)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.status == BookingStatus.PENDING.value)
            .where(Booking.created_at <= cutoff)
        )
        expired = list(result.scalars().all())
        now = _utcnow()
        for b in expired:
            b.status = BookingStatus.CANCELLED.value
            b.updated_at = now
        if expired:
            await session.commit()
        return expired


@with_db_retry()
async def get_pending_bookings() -> list[Booking]:
    """Return only bookings with status='pending' for today and future, ordered by date/time."""
    import datetime as _dt
    _vn_tz = _dt.timezone(_dt.timedelta(hours=7))
    today = _dt.datetime.now(_vn_tz).strftime("%Y-%m-%d")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.status == BookingStatus.PENDING.value)
            .where(Booking.date >= today)
            .order_by(Booking.date, Booking.time)
        )
        return list(result.scalars().all())


@with_db_retry()
async def get_confirmed_today_bookings() -> list[Booking]:
    """Return bookings with status='confirmed' for today only."""
    import datetime as _dt
    _vn_tz = _dt.timezone(_dt.timedelta(hours=7))
    today = _dt.datetime.now(_vn_tz).strftime("%Y-%m-%d")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.status == BookingStatus.CONFIRMED.value)
            .where(Booking.date == today)
            .order_by(Booking.time)
        )
        return list(result.scalars().all())


@with_db_retry()
async def set_booking_status(booking_id: int, status: BookingStatus,
                              poster_id: int | None = None) -> Booking | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()
        if booking:
            booking.status = status
            booking.updated_at = _utcnow()
            if poster_id is not None:
                booking.poster_reservation_id = poster_id
            await session.commit()
            await session.refresh(booking)
        return booking


@with_db_retry()
async def update_booking_table(booking_id: int, new_table: str, new_hall: str | None = None) -> Booking | None:
    """Move a booking to a different table (and optionally a different hall). Returns updated booking or None if not found."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()
        if booking:
            booking.table = new_table
            booking.updated_at = _utcnow()
            if new_hall:
                booking.hall = new_hall
            await session.commit()
            await session.refresh(booking)
        return booking


def _time_to_min(t: str) -> int:
    """Convert HH:MM → total minutes. 00:xx-02:xx treated as next-day (24-26h)."""
    h, m = map(int, t.split(":"))
    if h <= 2:
        h += 24  # overnight slots: 00→24, 01→25, 02→26
    return h * 60 + m


@with_db_retry()
async def get_booked_tables(hall: str, date: str, requested_time: str) -> dict[str, str]:
    """
    Return {table: status} for tables occupied at requested_time,
    accounting for booking duration (2h / 2.5h / 3h based on capacity).
    """
    from bot.config import TABLE_CAPACITIES, table_duration_minutes
    req_min = _time_to_min(requested_time)
    caps = TABLE_CAPACITIES.get(hall, {})

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking.table, Booking.status, Booking.time)
            .where(Booking.hall == hall)
            .where(Booking.date == date)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.EN_ROUTE]))
            .where(Booking.table.isnot(None))
        )
        occupied: dict[str, str] = {}
        for table, status, btime in result.all():
            if not table:
                continue
            cap = caps.get(table, 2)
            dur = table_duration_minutes(cap)
            start = _time_to_min(btime)
            # Table is blocked during [start, start + dur)
            if start <= req_min < start + dur:
                # confirmed wins over pending
                if table not in occupied or status == BookingStatus.CONFIRMED:
                    occupied[table] = status
        return occupied


@with_db_retry()
async def get_live_booked_tables(hall: str, date: str, current_minutes: int) -> dict[str, dict]:
    """
    Return {table: {"status": ..., "remaining_min": ...}} for tables to show as occupied.

    Rules:
    - CONFIRMED bookings → shown as "confirmed" (burgundy) all day.
      remaining_min = minutes until booking ends if active, else 0 (upcoming).
    - PENDING bookings → shown as "pending" (purple) all day.
      remaining_min = minutes until booking ends if active, else 0 (upcoming).
    - If a table has both: active confirmed wins; otherwise confirmed wins over pending.
    """
    from bot.config import TABLE_CAPACITIES, table_duration_minutes
    caps = TABLE_CAPACITIES.get(hall, {})

    async with AsyncSessionLocal() as session:
        # Fetch set of VIP phones for quick lookup
        vip_result = await session.execute(
            select(GuestProfile.phone).where(GuestProfile.is_vip == True)
        )
        vip_phones: set[str] = {row[0] for row in vip_result.all()}

        result = await session.execute(
            select(Booking.table, Booking.status, Booking.time, Booking.phone)
            .where(Booking.hall == hall)
            .where(Booking.date == date)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.EN_ROUTE]))
            .where(Booking.table.isnot(None))
        )
        occupied: dict[str, dict] = {}
        for table, status, btime, phone in result.all():
            if not table:
                continue
            cap = caps.get(table, 2)
            dur = table_duration_minutes(cap)
            start = _time_to_min(btime)
            end   = start + dur
            is_active = start <= current_minutes < end
            remaining = (end - current_minutes) if is_active else 0
            is_vip = bool(phone and phone in vip_phones)

            existing = occupied.get(table)

            if status == BookingStatus.CONFIRMED:
                # Confirmed always wins over pending/en_route
                if existing and existing["status"] == BookingStatus.CONFIRMED and existing["remaining_min"] > 0:
                    continue  # keep the active one if we already have active confirmed
                occupied[table] = {"status": status, "remaining_min": remaining, "is_vip": is_vip}

            elif status == BookingStatus.EN_ROUTE:
                # En-route wins over pending but not over confirmed
                if existing and existing["status"] == BookingStatus.CONFIRMED:
                    continue
                occupied[table] = {"status": status, "remaining_min": remaining, "is_vip": is_vip}

            elif status == BookingStatus.PENDING:
                # Pending only shown if no confirmed booking already set for this table
                if existing and existing["status"] == BookingStatus.CONFIRMED:
                    continue
                occupied[table] = {"status": status, "remaining_min": remaining, "is_vip": is_vip}

        return occupied


@with_db_retry()
async def get_booked_times(hall: str, date: str) -> list[str]:
    """
    Return slot times where ALL tables in the hall are occupied (considers duration).
    A slot is unavailable if every table is blocked by some booking at that time.
    """
    from bot.config import TABLE_CAPACITIES, table_duration_minutes, BOOKING_OPEN_HOUR, BOOKING_CLOSE_HOUR, BOOKING_SLOT_MINUTES
    all_tables = set(TABLES.get(hall, []))
    if not all_tables:
        return []
    caps = TABLE_CAPACITIES.get(hall, {})

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking.time, Booking.table)
            .where(Booking.hall == hall)
            .where(Booking.date == date)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.EN_ROUTE]))
            .where(Booking.table.isnot(None))
        )
        bookings = [(btime, btable) for btime, btable in result.all() if btable]

    # Build all valid slots
    slots: list[str] = []
    total_minutes = (BOOKING_CLOSE_HOUR - BOOKING_OPEN_HOUR) * 60
    for offset in range(0, total_minutes + 1, BOOKING_SLOT_MINUTES):
        h = BOOKING_OPEN_HOUR + offset // 60
        m = offset % 60
        if h > BOOKING_CLOSE_HOUR or (h == BOOKING_CLOSE_HOUR and m > 0):
            break
        slots.append(f"{h % 24:02d}:{m:02d}")

    # For each slot, check if all tables are covered by some booking
    unavailable: list[str] = []
    for slot in slots:
        slot_min = _time_to_min(slot)
        covered: set[str] = set()
        for btime, btable in bookings:
            cap = caps.get(btable, 2)
            dur = table_duration_minutes(cap)
            start = _time_to_min(btime)
            if start <= slot_min < start + dur:
                covered.add(btable)
        if all_tables <= covered:
            unavailable.append(slot)
    return unavailable


@with_db_retry()
async def get_booked_times_for_table(hall: str, table: str, date: str) -> list[str]:
    """
    Return slot times where this specific table is already occupied (pending or confirmed).
    A slot is unavailable if it overlaps with an existing booking's duration window.
    """
    from bot.config import TABLE_CAPACITIES, table_duration_minutes, BOOKING_OPEN_HOUR, BOOKING_CLOSE_HOUR, BOOKING_SLOT_MINUTES
    cap = TABLE_CAPACITIES.get(hall, {}).get(table, 2)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking.time)
            .where(Booking.table == table)
            .where(Booking.date == date)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.EN_ROUTE]))
        )
        booked_raw = [row[0] for row in result.all()]

    if not booked_raw:
        return []

    dur = table_duration_minutes(cap)

    # Build all valid slots for the day
    slots: list[str] = []
    total_minutes = (BOOKING_CLOSE_HOUR - BOOKING_OPEN_HOUR) * 60
    for offset in range(0, total_minutes + 1, BOOKING_SLOT_MINUTES):
        h = BOOKING_OPEN_HOUR + offset // 60
        m = offset % 60
        if h > BOOKING_CLOSE_HOUR or (h == BOOKING_CLOSE_HOUR and m > 0):
            break
        slots.append(f"{h % 24:02d}:{m:02d}")

    # Mark slots that overlap with any existing booking for this table
    unavailable: list[str] = []
    for slot in slots:
        slot_min = _time_to_min(slot)
        for btime in booked_raw:
            start = _time_to_min(btime)
            if start <= slot_min < start + dur:
                unavailable.append(slot)
                break
    return unavailable


@with_db_retry()
async def get_booked_tables_for_date(hall: str, date: str) -> dict[str, str]:
    """Return {table: status} for all tables that have ANY active booking on the given date (any time).
    'confirmed' wins over 'en_route' wins over 'pending' if a table has both."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking.table, Booking.status)
            .where(Booking.hall == hall)
            .where(Booking.date == date)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.EN_ROUTE]))
            .where(Booking.table.isnot(None))
        )
        occupied: dict[str, str] = {}
        STATUS_PRIORITY = {BookingStatus.CONFIRMED.value: 3, BookingStatus.EN_ROUTE.value: 2, BookingStatus.PENDING.value: 1}
        for table_name, status in result.all():
            if not table_name:
                continue
            status_val = status.value if hasattr(status, "value") else status
            existing_priority = STATUS_PRIORITY.get(occupied.get(table_name, ""), 0)
            new_priority = STATUS_PRIORITY.get(status_val, 0)
            if new_priority > existing_priority:
                occupied[table_name] = status_val
        return occupied


@with_db_retry()
async def get_bookings_for_table(hall: str, table: str, date: str) -> list[Booking]:
    """Return all active (pending/confirmed) bookings for a specific table on a given date, ordered by time."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.hall == hall)
            .where(Booking.table == table)
            .where(Booking.date == date)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.EN_ROUTE]))
            .order_by(Booking.time)
        )
        return list(result.scalars().all())


@with_db_retry()
async def close_table_bookings(hall: str, table: str, date: str) -> int:
    """Mark only CURRENT (already started) bookings for this table as COMPLETED.
    Future bookings (time > current time) are preserved and NOT touched.
    Counts real guest visits (skips walk-ins with phone '—')."""
    import datetime as _dt
    vn_offset = _dt.timezone(_dt.timedelta(hours=7))
    current_time = _dt.datetime.now(vn_offset).strftime("%H:%M")

    closed_visits: list[tuple[str, str]] = []  # (phone, name) for visit counting
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.hall == hall)
            .where(Booking.table == table)
            .where(Booking.date == date)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.EN_ROUTE]))
            .where(Booking.time <= current_time)
        )
        bookings = result.scalars().all()
        for b in bookings:
            b.status = BookingStatus.COMPLETED
            # Collect real guests only (skip walkin placeholder '—')
            if b.phone and b.phone not in ("—", "-", ""):
                closed_visits.append((b.phone, b.name or ""))
        await session.commit()

    # Increment visit counter AFTER session is closed — failure here never
    # affects the already-committed COMPLETED status.
    for phone, name in closed_visits:
        await _increment_guest_visits(phone=phone, name=name)

    return len(bookings)


@with_db_retry()
async def get_today_bookings() -> list[Booking]:
    """Return all pending/confirmed bookings for today, ordered by time."""
    import datetime as _dt
    _vn_tz = _dt.timezone(_dt.timedelta(hours=7))
    today = _dt.datetime.now(_vn_tz).strftime("%Y-%m-%d")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.date == today)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.EN_ROUTE]))
            .order_by(Booking.time)
        )
        return list(result.scalars().all())


@with_db_retry()
async def get_stats() -> dict:
    async with AsyncSessionLocal() as session:
        total = (await session.execute(select(func.count()).select_from(Booking))).scalar()
        pending = (await session.execute(
            select(func.count()).select_from(Booking).where(Booking.status == BookingStatus.PENDING)
        )).scalar()
        confirmed = (await session.execute(
            select(func.count()).select_from(Booking).where(Booking.status == BookingStatus.CONFIRMED)
        )).scalar()
        cancelled = (await session.execute(
            select(func.count()).select_from(Booking).where(Booking.status == BookingStatus.CANCELLED)
        )).scalar()
        return {"total": total, "pending": pending, "confirmed": confirmed, "cancelled": cancelled}


# ─── Guest Profile helpers ─────────────────────────────────────────────────────

async def _increment_guest_visits(phone: str, name: str) -> None:
    """
    Atomically create or increment guest profile after a booking is committed.
    Runs in its own session — failure here NEVER affects the booking.
    Auto-promotes guest to VIP after 5 confirmed bookings.
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = _upsert_insert(GuestProfile).values(
                phone=phone, name=name, total_visits=1, is_vip=False,
                created_at=_utcnow(), updated_at=_utcnow(),
            ).on_conflict_do_update(
                index_elements=["phone"],
                set_={
                    "total_visits": GuestProfile.total_visits + 1,
                    "updated_at":   _utcnow(),
                },
            )
            await session.execute(stmt)
            # Auto-promote to VIP after 5 visits
            await session.execute(
                update(GuestProfile)
                .where(GuestProfile.phone == phone)
                .where(GuestProfile.total_visits >= 5)
                .values(is_vip=True, updated_at=_utcnow())
            )
            await session.commit()
    except Exception as exc:
        import logging as _log
        _log.getLogger(__name__).warning(
            "guest visit increment failed for phone %s: %s", phone, exc
        )


async def _increment_guest_visits_internal(session: AsyncSession, phone: str, name: str) -> None:
    """Deprecated shim — use _increment_guest_visits() instead."""
    await _increment_guest_visits(phone=phone, name=name)


@with_db_retry()
async def get_guest_by_phone(phone: str) -> GuestProfile | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(GuestProfile).where(GuestProfile.phone == phone))
        return result.scalar_one_or_none()


async def get_all_guests(limit: int = 50) -> list[GuestProfile]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(GuestProfile).order_by(GuestProfile.total_visits.desc()).limit(limit)
        )
        return list(result.scalars().all())


@with_db_retry()
async def search_guests(q: str = "", limit: int = 200) -> list[GuestProfile]:
    """Search guests by name or phone fragment, ordered by visit count desc."""
    from sqlalchemy import or_
    async with AsyncSessionLocal() as session:
        stmt = select(GuestProfile).order_by(GuestProfile.total_visits.desc())
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(GuestProfile.name.ilike(like), GuestProfile.phone.ilike(like))
            )
        result = await session.execute(stmt.limit(limit))
        return list(result.scalars().all())


@with_db_retry()
async def create_guest_profile(phone: str, name: str, notes: str = "", is_vip: bool = False) -> GuestProfile:
    """Manually create or update a guest profile (staff-initiated). Returns the profile."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(GuestProfile).where(GuestProfile.phone == phone))
        profile = result.scalar_one_or_none()
        if profile:
            profile.name     = name
            profile.notes    = notes or profile.notes
            profile.is_vip   = is_vip
            profile.updated_at = _utcnow()
        else:
            profile = GuestProfile(phone=phone, name=name, notes=notes or None,
                                   is_vip=is_vip, total_visits=0,
                                   created_at=_utcnow(), updated_at=_utcnow())
            session.add(profile)
        await session.commit()
        await session.refresh(profile)
        return profile


async def set_guest_vip(phone: str, is_vip: bool) -> GuestProfile | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(GuestProfile).where(GuestProfile.phone == phone))
        profile = result.scalar_one_or_none()
        if profile:
            profile.is_vip = is_vip
            profile.updated_at = _utcnow()
            await session.commit()
            await session.refresh(profile)
        return profile


async def set_guest_notes(phone: str, notes: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(GuestProfile).where(GuestProfile.phone == phone))
        profile = result.scalar_one_or_none()
        if profile:
            profile.notes = notes
            profile.updated_at = _utcnow()
            await session.commit()


@with_db_retry()
async def get_user_role(user_id: int) -> str:
    """Get user role from DB, falling back to config."""
    if user_id == ADMIN_CHAT_ID:
        return UserRole.ADMIN
    if user_id in STAFF_IDS:
        return UserRole.STAFF
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user.role if user else UserRole.GUEST


async def set_user_role(user_id: int, role: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.role = role
            await session.commit()


async def upsert_user_role(user_id: int, role: str, display_name: str = "") -> None:
    """Create user if not exists and set their role."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.role = role
            if display_name:
                user.first_name = display_name
        else:
            session.add(User(
                id=user_id,
                first_name=display_name or str(user_id),
                role=role,
            ))
        await session.commit()


async def get_all_staff() -> list[User]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.role.in_([UserRole.STAFF, UserRole.ADMIN]))
        )
        return list(result.scalars().all())


@with_db_retry()
async def get_bookings_by_phone(phone: str) -> list[Booking]:
    """Return recent bookings for a guest phone number (newest first)."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.phone == phone)
            .order_by(Booking.date.desc(), Booking.time.desc())
            .limit(15)
        )
        return list(result.scalars().all())


@with_db_retry()
async def get_all_staff_ids() -> set[int]:
    """Return all staff+admin user IDs from DB ― for notifications and access checks."""
    ids: set[int] = set()
    if ADMIN_CHAT_ID:
        ids.add(ADMIN_CHAT_ID)
    ids |= set(STAFF_IDS)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User.id).where(User.role.in_([UserRole.STAFF, UserRole.ADMIN]))
        )
        ids |= {row[0] for row in result.all()}
    return ids


@with_db_retry()
async def get_en_route_bookings() -> list[Booking]:
    """Return only bookings with status='en_route', ordered by date/time."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.status == BookingStatus.EN_ROUTE.value)
            .order_by(Booking.date, Booking.time)
        )
        return list(result.scalars().all())


@with_db_retry()
async def get_en_route_today_bookings() -> list[Booking]:
    """Return bookings with status='en_route' for today only."""
    import datetime as _dt
    _vn_tz = _dt.timezone(_dt.timedelta(hours=7))
    today = _dt.datetime.now(_vn_tz).strftime("%Y-%m-%d")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.status == BookingStatus.EN_ROUTE.value)
            .where(Booking.date == today)
            .order_by(Booking.time)
        )
        return list(result.scalars().all())


# ─── Blacklist helpers ────────────────────────────────────────────────────────

@with_db_retry()
async def get_blacklist(q: str = "", limit: int = 500) -> list[BlacklistedGuest]:
    """Return all blacklisted guests, optionally filtered by name/phone/tg_username."""
    async with AsyncSessionLocal() as session:
        stmt = select(BlacklistedGuest).order_by(BlacklistedGuest.created_at.desc())
        if q:
            like = f"%{q}%"
            from sqlalchemy import or_
            stmt = stmt.where(
                or_(
                    BlacklistedGuest.phone.ilike(like),
                    BlacklistedGuest.tg_username.ilike(like),
                    BlacklistedGuest.name.ilike(like),
                )
            )
        stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())


@with_db_retry()
async def check_blacklist(phone: str = "", tg_username: str = "") -> BlacklistedGuest | None:
    """Check if a guest is blacklisted by phone or Telegram username. Returns matching record or None."""
    from sqlalchemy import or_
    async with AsyncSessionLocal() as session:
        conditions = []
        if phone and phone.strip():
            conditions.append(BlacklistedGuest.phone == phone.strip())
        if tg_username and tg_username.strip():
            tg_clean = tg_username.lstrip("@").strip().lower()
            conditions.append(func.lower(BlacklistedGuest.tg_username) == tg_clean)
        if not conditions:
            return None
        result = await session.execute(
            select(BlacklistedGuest).where(or_(*conditions)).limit(1)
        )
        return result.scalar_one_or_none()


@with_db_retry()
async def add_to_blacklist(
    phone: str = "",
    tg_username: str = "",
    name: str = "",
    reason: str = "",
    added_by: int = 0,
) -> BlacklistedGuest:
    """Add a guest to the blacklist. At least phone or tg_username must be provided."""
    async with AsyncSessionLocal() as session:
        entry = BlacklistedGuest(
            phone=phone.strip() or None,
            tg_username=tg_username.lstrip("@").strip().lower() or None,
            name=name.strip() or None,
            reason=reason.strip() or None,
            added_by=added_by or None,
            created_at=_utcnow(),
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return entry


@with_db_retry()
async def remove_from_blacklist(blacklist_id: int) -> bool:
    """Remove a blacklist entry by ID. Returns True if deleted, False if not found."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BlacklistedGuest).where(BlacklistedGuest.id == blacklist_id)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return False
        await session.delete(entry)
        await session.commit()
        return True
