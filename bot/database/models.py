from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, BigInteger, String, DateTime, Text, Boolean,
    Index, func,
)
from sqlalchemy.orm import DeclarativeBase
import enum


def _utcnow() -> datetime:
    """Returns current UTC time (timezone-aware). Replaces deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC for SQLite compat


class Base(DeclarativeBase):
    pass


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EN_ROUTE = "en_route"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STAFF = "staff"
    VIP = "vip"
    GUEST = "guest"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)           # Telegram user_id
    username = Column(String(64), nullable=True)
    first_name = Column(String(128), nullable=True)
    language = Column(String(4), default="ru")
    role = Column(String(16), default=UserRole.GUEST)   # guest/staff/vip/admin
    created_at = Column(DateTime, default=_utcnow)

    __table_args__ = (
        Index("ix_users_role", "role"),
    )


class BlacklistedGuest(Base):
    """Blacklisted guests — blocked from making reservations."""
    __tablename__ = "blacklisted_guests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(32), nullable=True)           # phone number (optional)
    tg_username = Column(String(64), nullable=True)     # @username without @ (optional)
    name = Column(String(128), nullable=True)           # display name
    reason = Column(Text, nullable=True)                # why blacklisted
    added_by = Column(BigInteger, nullable=True)        # admin/staff Telegram user_id
    created_at = Column(DateTime, default=_utcnow)

    __table_args__ = (
        Index("ix_blacklist_phone", "phone"),
        Index("ix_blacklist_tg_username", "tg_username"),
    )


class GuestProfile(Base):
    """Extended profile for guests — linked by phone number."""
    __tablename__ = "guest_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)         # Telegram user_id (if known)
    name = Column(String(128), nullable=False)
    phone = Column(String(32), nullable=False, unique=True)
    total_visits = Column(Integer, default=0)
    is_vip = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)                 # Admin internal notes
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow)      # updated manually in service layer

    __table_args__ = (
        Index("ix_guest_profiles_is_vip", "is_vip"),
        Index("ix_guest_profiles_total_visits", "total_visits"),
    )


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    name = Column(String(128), nullable=False)
    phone = Column(String(32), nullable=False)
    guests_count = Column(String(16), nullable=False)
    hall = Column(String(32), nullable=False)           # "main" or "second"
    table = Column(String(16), nullable=True)           # e.g. "T2", "B5"
    date = Column(String(16), nullable=False)           # "YYYY-MM-DD"
    time = Column(String(8), nullable=False)            # "HH:MM"
    comment = Column(Text, nullable=True)
    tg_username = Column(String(64), nullable=True)      # @username from Telegram
    status = Column(String(16), default=BookingStatus.PENDING, nullable=False)
    source = Column(String(16), default="bot")          # "bot" or "webapp"
    poster_reservation_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow)      # updated manually in service layer

    # ── Indexes for frequently-queried columns ────────────────────────────────
    # Most queries filter by (hall, date, status) — composite index covers all three.
    __table_args__ = (
        Index("ix_bookings_hall_date_status", "hall", "date", "status"),
        Index("ix_bookings_date_status",      "date", "status"),
        Index("ix_bookings_user_id",          "user_id"),
        Index("ix_bookings_phone",            "phone"),
        Index("ix_bookings_status",           "status"),
        Index("ix_bookings_table_date",       "table", "date"),
    )

    def summary(self, lang: str = "ru") -> str:
        _halls = {
            "ru": {"main": "🏛 Основной зал", "second": "🔝 2-й этаж"},
            "vi": {"main": "🏛 Khu chính",    "second": "🔝 Tầng 2"},
            "en": {"main": "🏛 Main Hall",     "second": "🔝 2nd Floor"},
        }
        hall_label = _halls.get(lang, _halls["en"]).get(self.hall, self.hall)
        role_icon = {"confirmed": "✅", "pending": "🟡", "en_route": "🟠", "cancelled": "❌"}.get(self.status, "🔖")

        if lang == "ru":
            return (
                f"📋 Бронь #{self.id} {role_icon}\n"
                f"👤 Гость: {self.name}\n"
                f"📞 Телефон: {self.phone}\n"
                f"👥 Гостей: {self.guests_count}\n"
                f"🏛 Зал: {hall_label}\n"
                f"🪑 Стол: {self.table or '—'}\n"
                f"📅 Дата: {self.date}\n"
                f"⏰ Время: {self.time}\n"
                f"💬 Комментарий: {self.comment or '—'}\n"
                f"📱 Источник: {self.source}"
            )
        elif lang == "vi":
            return (
                f"📋 Đặt chỗ #{self.id} {role_icon}\n"
                f"👤 Khách: {self.name}\n"
                f"📞 Điện thoại: {self.phone}\n"
                f"👥 Số khách: {self.guests_count}\n"
                f"🏛 Khu vực: {hall_label}\n"
                f"🪑 Bàn: {self.table or '—'}\n"
                f"📅 Ngày: {self.date}\n"
                f"⏰ Giờ: {self.time}\n"
                f"💬 Ghi chú: {self.comment or '—'}\n"
                f"📱 Nguồn: {self.source}"
            )
        else:
            return (
                f"📋 Booking #{self.id} {role_icon}\n"
                f"👤 Guest: {self.name}\n"
                f"📞 Phone: {self.phone}\n"
                f"👥 Guests: {self.guests_count}\n"
                f"🏛 Hall: {hall_label}\n"
                f"🪑 Table: {self.table or '—'}\n"
                f"📅 Date: {self.date}\n"
                f"⏰ Time: {self.time}\n"
                f"💬 Comment: {self.comment or '—'}\n"
                f"📱 Source: {self.source}"
            )
