import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID: int = int(os.getenv("ADMIN_CHAT_ID", "0"))
POSTER_TOKEN: str = os.getenv("POSTER_TOKEN", "")
POSTER_ACCOUNT: str = os.getenv("POSTER_ACCOUNT", "")
POSTER_BASE_URL: str = "https://joinposter.com/api"

# Staff whitelist: comma-separated Telegram user IDs (set in .env or Render dashboard)
_staff_raw = os.getenv("STAFF_IDS", "")
STAFF_IDS: set[int] = {int(x.strip()) for x in _staff_raw.split(",") if x.strip().isdigit()}

# Telegram Mini App
# On Render: auto-detected from RENDER_EXTERNAL_URL in main.py
# Locally: set manually or auto-populated by cloudflared/ngrok
WEBAPP_URL: str = os.getenv("WEBAPP_URL", "")
WEBAPP_PORT: int = int(os.getenv("PORT", os.getenv("WEBAPP_PORT", "8080")))

# Tunnel config (local development only — not used on Render)
NGROK_AUTHTOKEN: str = os.getenv("NGROK_AUTHTOKEN", "")
NGROK_DOMAIN: str = os.getenv("NGROK_DOMAIN", "")

# Venue info
VENUE_NAME = "The Cloud"
VENUE_ADDRESS = os.getenv("VENUE_ADDRESS", "Your Address Here")
VENUE_PHONE = os.getenv("VENUE_PHONE", "+X XXX XXX XXXX")

# Logo
LOGO_PATH: Path = Path(__file__).parent / "assets" / "logo.jpg"
LOGO_URL: str = os.getenv("LOGO_URL", "")

# Booking slots: 12:00 - 02:00 (next day) every 30 min
# Hours above 23 wrap to next day: 24=00:00, 25=01:00, 26=02:00
BOOKING_OPEN_HOUR = 12
BOOKING_CLOSE_HOUR = 26
BOOKING_SLOT_MINUTES = 30
BOOKING_DAYS_AHEAD = 14

# Halls
HALLS = {
    "🏛 Основной зал": "main",
    "🔝 2nd Floor": "second",
}

# Tables per hall - must match Poster POS, HALL_LAYOUTS (inline.py) and LAYOUTS (app.js)
# main = Основной зал: T2, T3 + bar stools B1-B8
# second = 2nd Floor: tables 4-11
TABLES = {
    "main":   ["T2", "T3", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"],
    "second": ["4", "5", "6", "7", "8", "9", "10", "11"],
}

# Capacity per table (must match TABLE_INFO in app.js)
TABLE_CAPACITIES: dict[str, dict[str, int]] = {
    "main": {
        "T2": 4, "T3": 2,
        "B1": 1, "B2": 1, "B3": 1, "B4": 1,
        "B5": 1, "B6": 1, "B7": 1, "B8": 1,
    },
    "second": {
        "4": 6, "5": 4, "6": 4, "7": 2,
        "8": 4, "9": 2, "10": 2, "11": 2,
    },
}


def table_duration_minutes(capacity: int) -> int:
    """Occupancy duration in minutes based on table capacity."""
    if capacity >= 5:
        return 180   # 3 hours  (6+ seats)
    elif capacity >= 3:
        return 150   # 2.5 hours (3-4 seats)
    else:
        return 120   # 2 hours  (1-2 seats)
