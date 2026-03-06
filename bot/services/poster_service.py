"""
Poster POS API integration.
Docs: https://dev.joinposter.com/docs/v3
"""
import logging
import aiohttp

from bot.config import POSTER_TOKEN, POSTER_BASE_URL, POSTER_ACCOUNT

logger = logging.getLogger(__name__)


async def create_reservation(
    hall: str,
    date: str,
    time: str,
    guests_count: str,
    name: str,
    phone: str,
    comment: str | None = None,
) -> int | None:
    """
    Create a reservation in Poster POS.
    Returns the Poster reservation_id on success, or None on failure.
    """
    if not POSTER_TOKEN or not POSTER_ACCOUNT:
        logger.warning("Poster credentials not configured, skipping sync.")
        return None

    # Map our hall keys to Poster spot IDs (update these after checking your Poster setup)
    hall_spot_map = {
        "main": 1,    # Основной зал spot_id in Poster
        "second": 2,  # 2nd Floor spot_id in Poster
    }
    spot_id = hall_spot_map.get(hall)

    # Convert guests_count string like "3–4" to integer (take lower bound)
    try:
        guests_int = int(guests_count.split("–")[0].replace("+", "").strip())
    except (ValueError, AttributeError):
        guests_int = 2

    # Poster expects datetime as "YYYY-MM-DD HH:MM:SS"
    reservation_start = f"{date} {time}:00"

    payload = {
        "token": POSTER_TOKEN,
        "spot_id": spot_id,
        "date_start": reservation_start,
        "guests_count": guests_int,
        "client_name": name,
        "client_phone": phone,
        "comment": comment or "",
    }

    url = f"https://{POSTER_ACCOUNT}.joinposter.com/api/reservations.createReservation"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if data.get("response"):
                    reservation_id = data["response"].get("reservation_id")
                    logger.info(f"Poster reservation created: {reservation_id}")
                    return reservation_id
                else:
                    logger.error(f"Poster API error: {data}")
                    return None
    except Exception as e:
        logger.error(f"Poster API request failed: {e}")
        return None


async def cancel_reservation(reservation_id: int) -> bool:
    """Cancel a reservation in Poster POS. Returns True on success."""
    if not POSTER_TOKEN or not POSTER_ACCOUNT or not reservation_id:
        return False

    url = f"https://{POSTER_ACCOUNT}.joinposter.com/api/reservations.deleteReservation"
    payload = {
        "token": POSTER_TOKEN,
        "reservation_id": reservation_id,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                success = bool(data.get("response"))
                if success:
                    logger.info(f"Poster reservation {reservation_id} cancelled.")
                else:
                    logger.error(f"Poster cancel error: {data}")
                return success
    except Exception as e:
        logger.error(f"Poster cancel request failed: {e}")
        return False
