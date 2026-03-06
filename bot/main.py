import asyncio
import logging
import os
import pathlib
import platform
import re
import socket as _socket
import stat
import subprocess
import sys
import threading
import time
import urllib.request
from typing import Callable, Awaitable

import uvicorn

import bot.config as cfg
from bot.database.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_PROJECT_ROOT = pathlib.Path(__file__).parent.parent

# ── Singleton lock — prevents two bot instances from running at once ──────────
_LOCK_SOCK: _socket.socket | None = None
_LOCK_PORT = 47374  # arbitrary local UDP port used only as a mutex

# ── Production webhook guard ──────────────────────────────────────────────────
# Prevents local runs from hijacking the live Render webhook.
# Set LOCAL_BOT_OVERRIDE=true in .env ONLY if you intentionally need local dev.
_PRODUCTION_HOSTS = ("onrender.com", "railway.app", "fly.dev", "heroku.com")


def _check_production_webhook() -> None:
    """Abort if webhook already points to a production host and we are NOT on a server."""
    # If running on a cloud server, RENDER_EXTERNAL_URL / similar are set — skip check.
    if os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("RAILWAY_ENVIRONMENT"):
        return
    # Allow override for intentional local dev
    if os.environ.get("LOCAL_BOT_OVERRIDE", "").lower() == "true":
        logger.warning("LOCAL_BOT_OVERRIDE=true — skipping production webhook guard.")
        return
    token = os.environ.get("BOT_TOKEN", "")
    if not token:
        return
    try:
        import urllib.request as _req
        r = _req.urlopen(
            f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=8
        )
        info = __import__("json").loads(r.read()).get("result", {})
        wh_url: str = info.get("url", "")
        if any(host in wh_url for host in _PRODUCTION_HOSTS):
            logger.error(
                "🛑 ЗАПУСК ОТКЛОНЁН: webhook уже настроен на production-сервер:\n"
                "   %s\n"
                "   Локальный запуск перехватит webhook и сломает бот на сервере!\n"
                "   Если вы хотите запустить локально, установите LOCAL_BOT_OVERRIDE=true в .env",
                wh_url,
            )
            sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        logger.warning("Production webhook guard check failed (non-fatal): %s", e)


def _acquire_instance_lock() -> None:
    """Bind a local TCP socket as a process-level singleton lock.
    TCP (unlike UDP) reliably rejects a second bind on the same port on Windows.
    SO_EXCLUSIVEADDRUSE (Windows) + no SO_REUSEADDR guarantees full exclusivity.
    set_inheritable(False) prevents child processes from inheriting the handle.
    The OS releases the socket automatically when the process dies.
    """
    global _LOCK_SOCK
    sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    # Windows-specific: prevent any other process from binding same port
    if hasattr(_socket, "SO_EXCLUSIVEADDRUSE"):
        sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_EXCLUSIVEADDRUSE, 1)  # type: ignore[attr-defined]
    # Prevent child processes (e.g. uvicorn workers) from inheriting this socket
    sock.set_inheritable(False)
    try:
        sock.bind(("127.0.0.1", _LOCK_PORT))
        sock.listen(1)
        _LOCK_SOCK = sock  # keep reference so GC doesn't close it
        logger.info("Instance lock acquired (TCP :%s).", _LOCK_PORT)
    except OSError:
        sock.close()
        logger.error(
            "Another bot instance is already running (TCP lock port %s busy). "
            "Stop it first with stop.ps1, then retry.",
            _LOCK_PORT,
        )
        sys.exit(0)

# ── Cloudflared — cross-platform auto-download ────────────────────────────────
def _cf_binary_info() -> tuple[pathlib.Path, str]:
    """Return (local_path, download_url) for the current OS/arch."""
    _machine = platform.machine().lower()
    if sys.platform == "win32":
        return _PROJECT_ROOT / "cloudflared.exe", (
            "https://github.com/cloudflare/cloudflared/releases/latest/download/"
            "cloudflared-windows-amd64.exe"
        )
    # Linux / macOS
    if "arm" in _machine or "aarch64" in _machine:
        _suffix, _arch_slug = "", "arm64"
    else:
        _suffix, _arch_slug = "", "amd64"
    _os = "darwin" if sys.platform == "darwin" else "linux"
    return (
        _PROJECT_ROOT / "cloudflared",
        f"https://github.com/cloudflare/cloudflared/releases/latest/download/"
        f"cloudflared-{_os}-{_arch_slug}",
    )

_CF_EXE, _CF_URL = _cf_binary_info()

_URL_RE = re.compile(r"https://[a-z0-9]+-[a-z0-9\-]+\.trycloudflare\.com")

# Cloudflare Quick Tunnel rate-limit indicator (HTTP 429 / error code 1015)
_CF_RATE_LIMIT_RE = re.compile(r"error code: 1015|status_code=.429|Error rate limit", re.IGNORECASE)


class CloudflaredRateLimitError(RuntimeError):
    """Raised when cloudflared gets HTTP 429 / error 1015 from trycloudflare.com.
    Signals to the caller to skip further retries and fall back to polling.
    """
    pass


def _ensure_cloudflared() -> pathlib.Path:
    """Download cloudflared binary automatically if not present. Returns path."""
    if _CF_EXE.exists():
        return _CF_EXE
    logger.info("cloudflared not found — downloading from GitHub (~35 MB)...")
    tmp = _CF_EXE.with_suffix(".tmp")
    try:
        urllib.request.urlretrieve(_CF_URL, tmp)
        tmp.rename(_CF_EXE)
        # Make executable on Linux/macOS
        if sys.platform != "win32":
            _CF_EXE.chmod(_CF_EXE.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        logger.info("cloudflared downloaded successfully → %s", _CF_EXE)
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to download cloudflared: {exc}") from exc
    return _CF_EXE


# ── Stable Tunnel Watchdog ────────────────────────────────────────────────────

class TunnelWatchdog:
    """
    Manages a cloudflared Quick Tunnel with automatic restart on failure.

    - Keeps stdout reader alive for the full process lifetime (proper log drain).
    - Watchdog thread polls every 5 s; restarts process with exponential backoff
      (5 s → 10 s → 20 s … capped at 120 s) on crash.
    - On each restart a new URL is obtained; an async callback fires so the
      Telegram menu button can be updated immediately.
    """

    _STARTUP_TIMEOUT = 45  # seconds to wait for URL on first/subsequent launches

    def __init__(self, port: int,
                 on_url_change: Callable[[str], Awaitable[None]] | None = None):
        self.port = port
        self.on_url_change = on_url_change  # async (new_url: str) -> None
        self._proc: subprocess.Popen | None = None
        self._stop = threading.Event()
        self.current_url: str = ""
        self._loop: asyncio.AbstractEventLoop | None = None

    # ── public ────────────────────────────────────────────────────────────────

    def start_sync(self, loop: asyncio.AbstractEventLoop) -> str:
        """Launch tunnel, block until URL ready, then start watchdog + heartbeat threads.
        Tries QUIC first; on DNS/connection failure falls back to http2 protocol.
        On HTTP 429 rate-limit, raises CloudflaredRateLimitError immediately —
        caller should fall back to polling mode instead of retrying.
        """
        self._loop = loop  # passed from the running async event loop
        # Try QUIC first, fall back to http2 on failure (but NOT on rate limit)
        try:
            self.current_url = self._launch(protocol="quic")
        except CloudflaredRateLimitError:
            raise  # propagate directly — don't waste time retrying http2
        except Exception as quic_err:
            logger.warning("QUIC tunnel failed (%s) — retrying with http2 protocol…", quic_err)
            self._flush_dns()
            time.sleep(3)
            self.current_url = self._launch(protocol="http2")
        wt = threading.Thread(target=self._watchdog_loop, name="cf-watchdog", daemon=True)
        wt.start()
        ht = threading.Thread(target=self._heartbeat_loop, name="cf-heartbeat", daemon=True)
        ht.start()
        return self.current_url

    def stop(self) -> None:
        self._stop.set()
        self._kill_proc()

    # ── internals ─────────────────────────────────────────────────────────────

    def _kill_proc(self) -> None:
        p = self._proc
        if p and p.poll() is None:
            try:
                p.kill()
                p.wait(timeout=5)
            except Exception:
                pass
        self._proc = None

    @staticmethod
    def _kill_stale_cloudflared() -> None:
        """Kill any lingering cloudflared processes from previous runs (Windows-safe)."""
        try:
            import psutil  # type: ignore[import]
            for proc in psutil.process_iter(["name", "pid"]):
                try:
                    if "cloudflared" in (proc.info["name"] or "").lower():
                        proc.kill()
                        logger.info("Killed stale cloudflared PID %s.", proc.info["pid"])
                except Exception:
                    pass
        except ImportError:
            # psutil not installed — fall back to subprocess kill on Windows
            if sys.platform == "win32":
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/IM", "cloudflared.exe"],
                        capture_output=True, check=False,
                    )
                except Exception:
                    pass

    @staticmethod
    def _flush_dns() -> None:
        """Flush OS DNS cache before launching cloudflared (Windows & Linux)."""
        try:
            if sys.platform == "win32":
                subprocess.run(["ipconfig", "/flushdns"], capture_output=True, check=False, timeout=10)
                logger.info("DNS cache flushed (ipconfig /flushdns).")
            else:
                subprocess.run(["systemd-resolve", "--flush-caches"], capture_output=True, check=False, timeout=10)
        except Exception:
            pass  # not critical

    def _launch(self, protocol: str = "quic") -> str:
        """
        (Re)start cloudflared, monitor output until URL appears, return URL.

        Uses a temp LOG FILE instead of subprocess.PIPE to avoid Windows pipe
        buffering. When stdout is a pipe (not a TTY), cloudflared may hold
        output in a 64 KB OS buffer before flushing, causing URL detection to
        time out even when cloudflared is working fine. Writing to a regular
        file bypasses this — each write is immediately readable by the reader.

        A UUID-based unique filename is used on every launch so that a locked
        log file from a previous cloudflared instance (WinError 32) never
        blocks the new launch.  Old tmp files are cleaned up best-effort.

        protocol: "quic" (default) or "http2" (fallback if QUIC/DNS fails).
        """
        self._kill_proc()
        self._kill_stale_cloudflared()
        self._flush_dns()
        # Small pause so OS releases the port binding from the old process
        time.sleep(1)

        cf_exe = _ensure_cloudflared()

        import tempfile, uuid
        _tmp_dir = pathlib.Path(tempfile.gettempdir())
        # Unique filename per launch — avoids WinError 32 (file locked by old process)
        log_path = _tmp_dir / f"cloudflared_{uuid.uuid4().hex}.log"
        # Best-effort cleanup of old cloudflared log files (non-blocking)
        for _old in _tmp_dir.glob("cloudflared_*.log"):
            try:
                _old.unlink(missing_ok=True)
            except OSError:
                pass  # still locked — ignore

        # Open log file in BINARY mode for subprocess, then close parent handle
        # (child process inherits its own duplicated handle via Popen internals)
        _log_f = open(log_path, "wb")
        proc = subprocess.Popen(
            [
                str(cf_exe), "tunnel",
                "--url", f"http://localhost:{self.port}",
                "--ha-connections", "4",   # 4 connections to edge — more resilient
                "--protocol", protocol,    # "quic" or "http2" fallback
            ],
            stdout=_log_f,
            stderr=subprocess.STDOUT,
        )
        _log_f.close()  # parent closes its end; child keeps its inherited handle
        self._proc = proc

        url_found: list[str] = []
        url_event = threading.Event()
        rate_limited = threading.Event()  # set when cloudflared reports HTTP 429 / error 1015

        def _drain() -> None:
            """
            Tail the temp log file until URL appears or process dies.
            readline() on a regular file returns '' on EOF (no data yet) so
            we sleep briefly and retry — this is the 'tail -f' pattern.
            """
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    line_count = 0
                    while True:
                        line = f.readline()
                        if not line:
                            if proc.poll() is not None:
                                logger.info("cloudflared exited (code=%s) after %s lines.", proc.returncode, line_count)
                                break  # process exited — no more output
                            time.sleep(0.05)
                            continue
                        line_count += 1
                        line = line.rstrip()
                        if line:
                            logger.info("cloudflared[%s]: %s", line_count, line[:160])
                        if not url_event.is_set():
                            m = _URL_RE.search(line)
                            if m:
                                url_found.append(m.group(0))
                                url_event.set()
                        # Fast 429 detection: cloudflared exits immediately on rate limit
                        if not rate_limited.is_set() and _CF_RATE_LIMIT_RE.search(line):
                            logger.warning(
                                "cloudflared rate-limited (HTTP 429 / error 1015) — "
                                "will skip retries and fall back to polling."
                            )
                            rate_limited.set()
            except Exception as exc:
                logger.warning("cloudflared drain error: %s", exc)

        drain_t = threading.Thread(target=_drain, name="cf-drain", daemon=True)
        drain_t.start()

        # Poll every 0.5 s so we can react to rate-limit / early process exit quickly
        # instead of always waiting the full _STARTUP_TIMEOUT.
        _deadline = time.monotonic() + self._STARTUP_TIMEOUT
        while time.monotonic() < _deadline:
            if url_event.wait(timeout=0.5):
                break
            # Process exited before we got a URL — check why
            if proc.poll() is not None:
                # Give drain thread a moment to finish reading the last lines
                drain_t.join(timeout=2)
                if rate_limited.is_set():
                    self._proc = None
                    raise CloudflaredRateLimitError(
                        "cloudflared: HTTP 429 / error 1015 — trycloudflare.com rate limit"
                    )
                raise RuntimeError(
                    f"cloudflared: exited (code={proc.poll()}) before returning a URL"
                )
        else:
            self._kill_proc()
            drain_t.join(timeout=2)
            if rate_limited.is_set():
                raise CloudflaredRateLimitError(
                    "cloudflared: HTTP 429 / error 1015 — trycloudflare.com rate limit"
                )
            raise RuntimeError(
                f"cloudflared: no URL received within {self._STARTUP_TIMEOUT} s"
            )

        return url_found[0]

    def _heartbeat_loop(self) -> None:
        """
        Periodically verify the tunnel URL is reachable via HTTP HEAD.
        Kills the cloudflared process after 3 consecutive failures so that
        the watchdog can restart it — catches the case where cloudflared is
        still running as a process but the QUIC connection is silently broken.
        Check interval: 30 s.  Failure threshold: 3 (= ~90 s dead before restart).
        """
        _MAX_FAILURES = 3
        consecutive_failures = 0
        # Give the tunnel a moment to be fully reachable before we start pinging
        self._stop.wait(timeout=30)
        while not self._stop.is_set():
            url = self.current_url
            if url:
                try:
                    req = urllib.request.Request(url.rstrip("/") + "/health", method="GET")
                    with urllib.request.urlopen(req, timeout=10):
                        pass  # any HTTP response means tunnel is alive
                    if consecutive_failures:
                        logger.info("Tunnel heartbeat recovered after %s failure(s).", consecutive_failures)
                    consecutive_failures = 0
                except Exception as exc:
                    consecutive_failures += 1
                    logger.warning(
                        "Tunnel heartbeat failure %s/%s: %s",
                        consecutive_failures, _MAX_FAILURES, exc,
                    )
                    if consecutive_failures >= _MAX_FAILURES:
                        logger.warning(
                            "Tunnel appears dead (process alive but unreachable) — "
                            "forcing cloudflared restart."
                        )
                        consecutive_failures = 0
                        self._kill_proc()  # watchdog will detect poll()!=None and restart
            self._stop.wait(timeout=30)

    def _watchdog_loop(self) -> None:
        backoff = 5
        while not self._stop.is_set():
            time.sleep(5)
            proc = self._proc
            if proc is None or proc.poll() is not None:
                exit_code = proc.poll() if proc else "?"
                logger.warning(
                    "cloudflared exited (code=%s). Restarting in %s s…",
                    exit_code, backoff,
                )
                self._stop.wait(timeout=backoff)
                if self._stop.is_set():
                    break

                try:
                    # Try QUIC first, fall back to http2 on failure
                    try:
                        new_url = self._launch(protocol="quic")
                    except CloudflaredRateLimitError as rl_err:
                        logger.warning(
                            "Tunnel rate-limited (%s). Backing off 5 min before retry.", rl_err
                        )
                        # Don't try http2 — it will also be rate-limited.
                        # Use a very long backoff (300 s) and keep trying periodically.
                        backoff = min(backoff * 2, 300)
                        continue
                    except Exception as quic_err:
                        logger.warning("QUIC restart failed (%s) — retrying with http2…", quic_err)
                        self._flush_dns()
                        time.sleep(3)
                        new_url = self._launch(protocol="http2")
                    backoff = 5  # reset on success
                    self.current_url = new_url
                    logger.info("Tunnel restarted → %s", new_url)
                    if self.on_url_change and self._loop:
                        asyncio.run_coroutine_threadsafe(
                            self.on_url_change(new_url), self._loop
                        )
                except Exception as exc:
                    logger.error("Tunnel restart failed: %s — retry in %s s", exc, backoff)
                    backoff = min(backoff * 2, 120)


# Singleton watchdog kept alive for full app lifetime
_watchdog: TunnelWatchdog | None = None


def _start_ngrok(port: int) -> str:
    """Start ngrok tunnel (requires NGROK_AUTHTOKEN in .env).
    If NGROK_DOMAIN is set, uses the free static domain for a permanent URL.
    """
    from pyngrok import ngrok, conf as ngrok_conf
    ngrok_conf.get_default().auth_token = cfg.NGROK_AUTHTOKEN

    if cfg.NGROK_DOMAIN:
        # Static domain — permanent URL, never changes across restarts
        tunnel = ngrok.connect(
            port,
            "http",
            domain=cfg.NGROK_DOMAIN,
        )
        logger.info("ngrok tunnel with STATIC domain: %s", cfg.NGROK_DOMAIN)
    else:
        tunnel = ngrok.connect(port, "http")

    url: str = tunnel.public_url
    if url.startswith("http://"):
        url = "https://" + url[7:]
    return url


async def get_tunnel_url(
    port: int,
    on_url_change: Callable[[str], Awaitable[None]] | None = None,
) -> str:
    """
    Priority:
      1. ngrok  — if NGROK_AUTHTOKEN is set in .env
           With NGROK_DOMAIN → permanent static URL (best for webhook) ✅
           Without NGROK_DOMAIN → random URL (re-registers on restart)
      2. Cloudflare Quick Tunnel — free, auto-downloaded, watchdog auto-restarts
    """
    global _watchdog
    loop = asyncio.get_running_loop()

    if cfg.NGROK_AUTHTOKEN:
        if cfg.NGROK_DOMAIN:
            logger.info("NGROK_AUTHTOKEN + NGROK_DOMAIN found — using ngrok with STATIC domain %s.", cfg.NGROK_DOMAIN)
        else:
            logger.info("NGROK_AUTHTOKEN found — using ngrok tunnel (dynamic URL).")
        return await loop.run_in_executor(None, _start_ngrok, port)

    logger.info("Using Cloudflare Quick Tunnel with auto-restart watchdog.")
    _watchdog = TunnelWatchdog(port=port, on_url_change=on_url_change)
    return await loop.run_in_executor(None, _watchdog.start_sync, loop)


async def _set_menu_button(webapp_url: str) -> None:
    """Set the Telegram menu button to open the Mini App for all users."""
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"https://api.telegram.org/bot{cfg.BOT_TOKEN}/setChatMenuButton",
                json={
                    "menu_button": {
                        "type": "web_app",
                        "text": "\U0001F4C5 Забронировать",
                        "web_app": {"url": webapp_url},
                    }
                },
                timeout=aiohttp.ClientTimeout(total=8),
            )
            data = await resp.json()
            if data.get("ok"):
                logger.info("Telegram menu button → Mini App URL set.")
            else:
                logger.warning("setChatMenuButton failed: %s", data)
    except Exception as e:
        logger.warning("Could not set menu button: %s", e)


async def _notify_admin_url(webapp_url: str, restarted: bool = False) -> None:
    """Send the new Mini App URL to admin in Telegram."""
    if not cfg.ADMIN_CHAT_ID or not cfg.BOT_TOKEN:
        return
    import aiohttp
    if restarted:
        text = (
            f"♻️ <b>Туннель перезапущен автоматически</b>\n\n"
            f"📱 Новый Mini App URL:\n"
            f"<code>{webapp_url}</code>\n\n"
            f"Кнопка меню в Telegram уже обновлена."
        )
    else:
        text = (
            f"🚀 <b>Бот запущен</b>\n\n"
            f"📱 Mini App URL:\n"
            f"<code>{webapp_url}</code>\n\n"
            f"Кнопка меню в Telegram уже обновлена автоматически."
        )
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"https://api.telegram.org/bot{cfg.BOT_TOKEN}/sendMessage",
                json={"chat_id": cfg.ADMIN_CHAT_ID, "text": text, "parse_mode": "HTML"},
                timeout=aiohttp.ClientTimeout(total=8),
            )
    except Exception as e:
        logger.warning("Could not notify admin: %s", e)


def _start_webapp_thread() -> uvicorn.Server:
    """
    Run uvicorn in a daemon thread — 100% guaranteed no subprocess spawn.

    Unlike `await server.serve()` inside asyncio.gather(), running uvicorn.Server.run()
    in a daemon thread:
    - Uses its OWN event loop inside the thread (no conflict with main loop)
    - Never calls multiprocessing or subprocess
    - Dies automatically when the parent process exits

    This is the official uvicorn-recommended embedding strategy:
    https://www.uvicorn.org/#running-programmatically
    """
    from webapp.app import app as webapp_app

    config = uvicorn.Config(
        app=webapp_app,
        host="0.0.0.0",
        port=cfg.WEBAPP_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    def _run() -> None:
        try:
            server.run()   # blocking; creates its own event loop inside the thread
        except Exception as exc:
            logger.error("Webapp server thread crashed: %s", exc)

    t = threading.Thread(target=_run, name="uvicorn", daemon=True)
    t.start()
    logger.info("Webapp (uvicorn) started in background thread on port %s.", cfg.WEBAPP_PORT)
    return server


async def run_webapp() -> None:
    """Async shim: start webapp in thread, then keep coroutine alive with the main loop."""
    server = _start_webapp_thread()
    # Wait until uvicorn is up (port bound) before we register the webhook
    for _ in range(30):
        await asyncio.sleep(0.5)
        if server.started:
            break


async def run_server_monitor() -> None:
    """
    Server-side health monitor — runs inside the bot process 24/7.
    - Checks every 5 min: webhook URL correctness, DB, guest & admin reachability.
    - Auto-fixes webhook if URL points to wrong host (e.g. old Koyeb).
    - Sends a compact table report to admin every 1 hour when all OK.
    - Sends an immediate alert on any issue + auto-fix applied.
    """
    import aiohttp as _aiohttp
    import datetime as _dt

    _CHECK_INTERVAL = 300       # 5 min — frequent checks for fast self-healing
    _OK_REPORT_INTERVAL = 3600  # 1 hour — don't spam when everything is fine

    last_ok_report = _dt.datetime.now() - _dt.timedelta(seconds=_OK_REPORT_INTERVAL)
    startup_time   = _dt.datetime.now()
    logger.info("Server monitor started (check every 5 min, report every 1 h, auto-fix webhook URL).")

    async def _send(text: str) -> None:
        if not cfg.ADMIN_CHAT_ID or not cfg.BOT_TOKEN:
            return
        try:
            async with _aiohttp.ClientSession() as sess:
                await sess.post(
                    f"https://api.telegram.org/bot{cfg.BOT_TOKEN}/sendMessage",
                    json={"chat_id": cfg.ADMIN_CHAT_ID, "text": text, "parse_mode": "HTML"},
                    timeout=_aiohttp.ClientTimeout(total=10),
                )
        except Exception as e:
            logger.warning("server_monitor: send failed: %s", e)

    async def _check_webhook() -> tuple[str, str]:
        """Returns (status_str, webhook_url)."""
        try:
            async with _aiohttp.ClientSession() as sess:
                r = await sess.get(
                    f"https://api.telegram.org/bot{cfg.BOT_TOKEN}/getWebhookInfo",
                    timeout=_aiohttp.ClientTimeout(total=8),
                )
                data = (await r.json()).get("result", {})
            url  = data.get("url", "")
            pending = data.get("pending_update_count", 0)
            err  = data.get("last_error_message", "")
            if url and not err:
                return f"🟢 OK ({pending} pending)", url
            if url and err:
                return f"🟡 {err[:35]}", url
            if not url:
                return "🔴 нет webhook", ""
            return f"🟡 {url[:30]}", url
        except Exception as exc:
            return f"🔴 {str(exc)[:35]}", ""

    async def _check_webhook_deep() -> dict:
        """Get full webhook info for deeper diagnostics."""
        try:
            async with _aiohttp.ClientSession() as sess:
                r = await sess.get(
                    f"https://api.telegram.org/bot{cfg.BOT_TOKEN}/getWebhookInfo",
                    timeout=_aiohttp.ClientTimeout(total=8),
                )
                return (await r.json()).get("result", {})
        except Exception:
            return {}

    async def _check_db() -> str:
        try:
            from bot.database.db import async_session
            from sqlalchemy import text as _sql_text
            async with async_session() as db_sess:
                await db_sess.execute(_sql_text("SELECT 1"))
            return "🟢 OK"
        except Exception as exc:
            return f"🔴 {str(exc)[:35]}"

    async def _check_db_tables() -> str:
        """Verify critical tables exist and are queryable."""
        try:
            from bot.database.db import async_session
            from sqlalchemy import text as _sql_text
            async with async_session() as db_sess:
                # Check bookings table (most critical)
                r = await db_sess.execute(
                    _sql_text("SELECT COUNT(*) FROM bookings WHERE 1=0")
                )
                r.scalar()
                # Check users table
                r2 = await db_sess.execute(
                    _sql_text("SELECT COUNT(*) FROM users WHERE 1=0")
                )
                r2.scalar()
            return "🟢 OK"
        except Exception as exc:
            return f"🔴 {str(exc)[:40]}"

    async def _check_db_wal() -> str:
        """Check SQLite WAL mode is active."""
        try:
            from bot.database.db import async_session, _IS_SQLITE
            if not _IS_SQLITE:
                return "🟢 N/A (не SQLite)"
            from sqlalchemy import text as _sql_text
            async with async_session() as db_sess:
                r = await db_sess.execute(_sql_text("PRAGMA journal_mode"))
                mode = r.scalar()
            if mode and mode.lower() == "wal":
                return "🟢 WAL"
            return f"🟡 {mode}"
        except Exception as exc:
            return f"🔴 {str(exc)[:35]}"

    async def _fix_db() -> str:
        """Try to repair database: re-init tables, reset pool, re-apply pragmas."""
        fixes = []
        try:
            # Step 1: Dispose stale connections (fixes "database is locked")
            from bot.database.db import engine
            await engine.dispose()
            fixes.append("pool reset")
            logger.info("server_monitor: DB pool disposed.")
            # Wait for PostgreSQL server to release connection slots.
            # Without this pause, init_db() immediately fails with
            # "remaining connection slots are reserved" again.
            await asyncio.sleep(4)
        except Exception as exc:
            logger.warning("server_monitor: DB pool dispose failed: %s", exc)

        try:
            # Step 2: Re-create all tables (fixes missing tables after Render restart)
            await init_db()
            fixes.append("таблицы пересозданы")
            logger.info("server_monitor: DB init_db() completed.")
        except Exception as exc:
            logger.warning("server_monitor: DB init_db() failed: %s", exc)
            fixes.append(f"init_db ошибка: {str(exc)[:30]}")

        try:
            # Step 3: Verify DB is now working
            from bot.database.db import async_session
            from sqlalchemy import text as _sql_text
            async with async_session() as db_sess:
                await db_sess.execute(_sql_text("SELECT 1"))
            fixes.append("✅ проверка пройдена")
        except Exception as exc:
            fixes.append(f"❌ всё ещё сломано: {str(exc)[:30]}")

        return " → ".join(fixes)

    # ngrok free tier shows interstitial page for browser requests;
    # this header bypasses it for programmatic health checks.
    _NGROK_HEADERS = {"ngrok-skip-browser-warning": "1", "User-Agent": "HealthCheck/1.0"}

    async def _check_guest(webapp_url: str) -> str:
        """Check if guests can reach the Mini App (HTTP GET /). """
        url = (webapp_url or cfg.WEBAPP_URL or "").rstrip("/")
        # Strip /webhook suffix — we need the base URL, not the bot endpoint
        if url.endswith("/webhook"):
            url = url[:-len("/webhook")]
        if not url:
            return "🟡 URL неизвестен"
        try:
            async with _aiohttp.ClientSession() as sess:
                r = await sess.get(
                    f"{url}/",
                    timeout=_aiohttp.ClientTimeout(total=10),
                    allow_redirects=True,
                    headers=_NGROK_HEADERS,
                )
                code = r.status
            if code < 400:
                return f"🟢 OK ({code})"
            return f"🟡 HTTP {code}"
        except Exception as exc:
            return f"🔴 {str(exc)[:40]}"

    async def _check_menu_button() -> tuple[str, str]:
        """Check Telegram menu button URL. Returns (status_str, menu_url)."""
        try:
            async with _aiohttp.ClientSession() as sess:
                r = await sess.get(
                    f"https://api.telegram.org/bot{cfg.BOT_TOKEN}/getChatMenuButton",
                    timeout=_aiohttp.ClientTimeout(total=8),
                )
                data = (await r.json()).get("result", {})
            btn_type = data.get("type", "")
            if btn_type == "web_app":
                menu_url = data.get("web_app", {}).get("url", "")
                return f"🟢 OK", menu_url
            elif btn_type == "default":
                return "🟡 не задана (default)", ""
            else:
                return f"🟡 тип: {btn_type}", ""
        except Exception as exc:
            return f"🔴 {str(exc)[:35]}", ""

    async def _fix_menu_button(correct_url: str) -> bool:
        """Re-set Telegram menu button to the correct Mini App URL."""
        if not correct_url:
            return False
        try:
            await _set_menu_button(correct_url)
            logger.info("server_monitor: menu button fixed → %s", correct_url)
            return True
        except Exception as exc:
            logger.warning("server_monitor: menu button fix failed: %s", exc)
            return False

    async def _wake_up_render() -> str:
        """Ping /health to wake up Render free tier from sleep."""
        url = (cfg.WEBAPP_URL or os.environ.get("RENDER_EXTERNAL_URL", "")).rstrip("/")
        if not url:
            return "URL неизвестен"
        try:
            async with _aiohttp.ClientSession() as sess:
                r = await sess.get(
                    f"{url}/health",
                    timeout=_aiohttp.ClientTimeout(total=20),
                    headers=_NGROK_HEADERS,
                )
                code = r.status
            if code < 400:
                return f"OK ({code})"
            return f"HTTP {code}"
        except Exception as exc:
            return f"ошибка: {str(exc)[:30]}"

    async def _check_admin(webhook_url: str) -> str:
        """Check if Telegram/admin can reach API endpoint (simulates Telegram ping)."""
        base = webhook_url.rstrip("/").replace("/webhook", "") if webhook_url else ""
        if not base:
            return "🟡 URL неизвестен"
        import datetime as _dt2
        today = _dt2.date.today().isoformat()
        test_url = f"{base}/api/tables/live?hall=main&date={today}&current_minutes=0"
        try:
            async with _aiohttp.ClientSession() as sess:
                r = await sess.get(
                    test_url,
                    timeout=_aiohttp.ClientTimeout(total=10),
                    allow_redirects=True,
                    headers=_NGROK_HEADERS,
                )
                code = r.status
            if code < 400:
                return f"🟢 OK ({code})"
            return f"🟡 HTTP {code}"
        except Exception as exc:
            return f"🔴 {str(exc)[:40]}"

    async def _fix_webhook(correct_url: str) -> bool:
        """Re-register webhook to the CORRECT URL (cfg.WEBAPP_URL based)."""
        if not correct_url:
            return False
        try:
            from webapp.app import WEBHOOK_SECRET as _wh_secret
            payload: dict = {"url": correct_url, "drop_pending_updates": False}
            if _wh_secret:
                payload["secret_token"] = _wh_secret
            async with _aiohttp.ClientSession() as sess:
                r = await sess.post(
                    f"https://api.telegram.org/bot{cfg.BOT_TOKEN}/setWebhook",
                    json=payload,
                    timeout=_aiohttp.ClientTimeout(total=10),
                )
                data = await r.json()
            if data.get("ok"):
                logger.info("server_monitor: webhook fixed → %s", correct_url)
                return True
        except Exception as exc:
            logger.warning("server_monitor: webhook fix failed: %s", exc)
        return False

    def _get_expected_webhook_url() -> str:
        """Build the correct webhook URL from cfg.WEBAPP_URL."""
        base = (cfg.WEBAPP_URL or os.environ.get("RENDER_EXTERNAL_URL", "")).rstrip("/")
        return f"{base}/webhook" if base else ""

    # Give the bot a moment to fully start before first check
    await asyncio.sleep(60)

    _consecutive_failures = 0  # escalation counter

    while True:
        ts = _dt.datetime.now().strftime("%d.%m %H:%M")

        # Uptime
        uptime_m = int((_dt.datetime.now() - startup_time).total_seconds() // 60)
        uptime_s = f"{uptime_m // 60}ч {uptime_m % 60}м" if uptime_m >= 60 else f"{uptime_m}м"

        wh_st, wh_url = await _check_webhook()
        wh_deep        = await _check_webhook_deep()
        db_st          = await _check_db()
        db_tables_st   = await _check_db_tables()
        db_wal_st      = await _check_db_wal()
        guest_st       = await _check_guest(wh_url)
        admin_st       = await _check_admin(wh_url)
        menu_st, menu_url = await _check_menu_button()

        # Deep webhook diagnostics
        wh_pending     = wh_deep.get("pending_update_count", 0)
        wh_error       = wh_deep.get("last_error_message", "")
        wh_allowed     = sorted(wh_deep.get("allowed_updates", []))
        wh_pending_st  = f"🟢 {wh_pending}" if wh_pending < 50 else f"🔴 {wh_pending} (бот не обрабатывает!)"
        wh_error_st    = "🟢 нет" if not wh_error else f"🟡 {wh_error[:40]}"

        fix_applied = ""
        db_fix_applied = ""
        guest_fix_applied = ""
        admin_fix_applied = ""
        expected_wh = _get_expected_webhook_url()
        expected_base = (cfg.WEBAPP_URL or os.environ.get("RENDER_EXTERNAL_URL", "")).rstrip("/")

        # ── AUTO-FIX DB: connection fail, missing tables, or WAL off ──────────
        if "🔴" in db_st or "🔴" in db_tables_st or "🟡" in db_wal_st:
            logger.warning(
                "server_monitor: DB issue detected (conn=%s tables=%s wal=%s) → auto-fixing...",
                db_st, db_tables_st, db_wal_st,
            )
            db_fix_result = await _fix_db()
            db_fix_applied = f"🔧 БД: {db_fix_result}"
            # Re-check after fix
            db_st        = await _check_db()
            db_tables_st = await _check_db_tables()
            db_wal_st    = await _check_db_wal()

        # ── AUTO-FIX 1: Webhook URL mismatch (e.g. old Koyeb URL) ────────────
        if expected_wh and wh_url and wh_url.rstrip("/") != expected_wh.rstrip("/"):
            logger.warning(
                "server_monitor: WEBHOOK URL MISMATCH!\n"
                "  Current:  %s\n"
                "  Expected: %s\n"
                "  → Auto-fixing...", wh_url, expected_wh,
            )
            fixed = await _fix_webhook(expected_wh)
            if fixed:
                await asyncio.sleep(5)
                wh_st, wh_url = await _check_webhook()
                admin_st      = await _check_admin(wh_url)
                guest_st      = await _check_guest(wh_url)
                fix_applied = f"🔧 Webhook URL исправлен: {expected_wh}"

        # ── AUTO-FIX 2: Webhook exists but admin/API not reachable ────────────
        elif ("🔴" in admin_st or "🟡" in admin_st) and expected_wh:
            logger.warning("server_monitor: admin connectivity issue (%s) — trying wake-up + webhook fix", admin_st)
            # Step 1: Wake up Render (might be asleep)
            wake_result = await _wake_up_render()
            await asyncio.sleep(8)
            # Step 2: Re-check after wake
            admin_st = await _check_admin(expected_base)
            if "🟢" not in admin_st:
                # Step 3: Still broken — re-register webhook
                fixed = await _fix_webhook(expected_wh)
                if fixed:
                    await asyncio.sleep(10)
                    wh_st, wh_url = await _check_webhook()
                    admin_st = await _check_admin(wh_url)
                    admin_fix_applied = f"♻️ Admin API: wake({wake_result}) + webhook перерегистрирован"
                else:
                    admin_fix_applied = f"⚠️ Admin API: wake({wake_result}), webhook fix не удался"
            else:
                admin_fix_applied = f"☀️ Admin API: Render разбужен ({wake_result})"

        # ── AUTO-FIX 3: No webhook at all ─────────────────────────────────────
        elif not wh_url and expected_wh:
            logger.warning("server_monitor: no webhook set — registering %s", expected_wh)
            fixed = await _fix_webhook(expected_wh)
            if fixed:
                await asyncio.sleep(5)
                wh_st, wh_url = await _check_webhook()
                admin_st      = await _check_admin(wh_url)
                fix_applied = f"🆕 Webhook зарегистрирован: {expected_wh}"

        # ── AUTO-FIX GUEST: Mini App unreachable → wake up Render ─────────────
        if "🔴" in guest_st or "🟡" in guest_st:
            if "🟡 URL" not in guest_st:  # skip if URL is simply unknown
                logger.warning("server_monitor: Guest Mini App unreachable (%s) → waking up Render...", guest_st)
                wake_result = await _wake_up_render()
                await asyncio.sleep(8)
                # Re-check after wake-up
                guest_st = await _check_guest(wh_url or expected_base)
                if "🟢" in guest_st:
                    guest_fix_applied = f"☀️ Render разбужен ({wake_result}), Mini App восстановлен"
                else:
                    guest_fix_applied = f"⚠️ Render пинг: {wake_result}, Mini App всё ещё: {guest_st}"

        # ── AUTO-FIX MENU: Button URL mismatch ───────────────────────────────
        if expected_base and menu_url and menu_url.rstrip("/") != expected_base.rstrip("/"):
            logger.warning(
                "server_monitor: MENU BUTTON URL MISMATCH!\n"
                "  Current:  %s\n"
                "  Expected: %s", menu_url, expected_base,
            )
            fixed = await _fix_menu_button(expected_base)
            if fixed:
                menu_st, menu_url = await _check_menu_button()
                guest_fix_applied += f"\n🔧 Кнопка меню исправлена → {expected_base}"
        elif "🟡" in menu_st and expected_base:
            # Menu button not set at all
            logger.warning("server_monitor: menu button not set — fixing → %s", expected_base)
            fixed = await _fix_menu_button(expected_base)
            if fixed:
                menu_st, menu_url = await _check_menu_button()
                guest_fix_applied += "\n🆕 Кнопка меню установлена"

        # ── AUTO-FIX PENDING: Too many pending updates → bot not processing ──
        if wh_pending >= 50 and expected_wh:
            logger.warning("server_monitor: %d pending updates — bot may be stuck! Re-registering webhook...", wh_pending)
            # Drop pending and re-register to force Telegram to resend
            fixed = await _fix_webhook(expected_wh)
            if fixed:
                await asyncio.sleep(5)
                wh_st, wh_url = await _check_webhook()
                wh_deep = await _check_webhook_deep()
                new_pending = wh_deep.get("pending_update_count", 0)
                fix_applied += f"\n🔄 Pending {wh_pending}→{new_pending}: webhook перерегистрирован"

        # ── AUTO-FIX WEBHOOK ERROR: Telegram reports persistent error ─────────
        if wh_error and expected_wh and "🟢" not in wh_st:
            logger.warning("server_monitor: Webhook error from Telegram: %s — re-registering", wh_error)
            wake_result = await _wake_up_render()
            await asyncio.sleep(5)
            fixed = await _fix_webhook(expected_wh)
            if fixed:
                await asyncio.sleep(8)
                wh_st, wh_url = await _check_webhook()
                wh_deep = await _check_webhook_deep()
                new_error = wh_deep.get("last_error_message", "")
                fix_applied += f"\n🩹 Webhook ошибка '{wh_error[:25]}' → wake + re-register"

        # ── ESCALATION: consecutive full-failures → full system reset ─────────
        all_statuses = [wh_st, db_st, db_tables_st, db_wal_st, guest_st, menu_st, admin_st, wh_pending_st, wh_error_st]
        all_ok = all("🔴" not in s and "🟡" not in s for s in all_statuses)
        combined = "".join(all_statuses)
        icon = "✅" if all_ok else ("🚨" if "🔴" in combined else "⚠️")

        if not all_ok:
            _consecutive_failures += 1
        else:
            _consecutive_failures = 0

        escalation_applied = ""
        if _consecutive_failures >= 3:
            logger.warning("server_monitor: %d CONSECUTIVE FAILURES — full system reset!", _consecutive_failures)
            # Full reset: dispose DB pool, init_db, re-register webhook, fix menu, wake Render
            try:
                from bot.database.db import engine as _eng
                await _eng.dispose()
                # Wait for PostgreSQL to release connection slots before reconnecting
                await asyncio.sleep(6)
            except Exception:
                pass
            try:
                await init_db()
            except Exception:
                pass
            if expected_wh:
                await _fix_webhook(expected_wh)
            if expected_base:
                await _fix_menu_button(expected_base)
            await _wake_up_render()
            await asyncio.sleep(10)
            # Re-check everything
            wh_st, wh_url      = await _check_webhook()
            db_st               = await _check_db()
            db_tables_st        = await _check_db_tables()
            db_wal_st           = await _check_db_wal()
            guest_st            = await _check_guest(wh_url or expected_base)
            admin_st            = await _check_admin(wh_url or expected_base)
            menu_st, menu_url   = await _check_menu_button()
            wh_deep             = await _check_webhook_deep()
            wh_pending          = wh_deep.get("pending_update_count", 0)
            wh_error            = wh_deep.get("last_error_message", "")
            wh_pending_st       = f"🟢 {wh_pending}" if wh_pending < 50 else f"🔴 {wh_pending}"
            wh_error_st         = "🟢 нет" if not wh_error else f"🟡 {wh_error[:40]}"
            escalation_applied  = f"🚨 ПОЛНЫЙ СБРОС (попытка #{_consecutive_failures}): БД + Webhook + Меню + Wake"
            _consecutive_failures = 0  # reset counter after full fix

        any_fix = fix_applied or db_fix_applied or guest_fix_applied or admin_fix_applied or escalation_applied
        now = _dt.datetime.now()
        sec_since_ok = (now - last_ok_report).total_seconds()
        should_report = not all_ok or any_fix or sec_since_ok >= _OK_REPORT_INTERVAL

        if should_report:
            if all_ok and not any_fix:
                last_ok_report = now
                next_in = " · след. через 60 мин"
            else:
                next_in = ""

            # Show webhook URL in report for easy diagnostics
            wh_short = wh_url[:50] + "…" if len(wh_url) > 50 else wh_url
            menu_short = menu_url[:50] + "…" if len(menu_url) > 50 else menu_url
            report = (
                f"{icon} <b>Server Monitor</b> · {ts}{next_in}\n\n"
                f"<code>"
                f"Параметр           Статус\n"
                f"──────────────────────────────────\n"
                f"Webhook (API)      {wh_st}\n"
                f"Webhook URL        {wh_short}\n"
                f"Webhook pending    {wh_pending_st}\n"
                f"Webhook ошибка     {wh_error_st}\n"
                f"БД подключение     {db_st}\n"
                f"БД таблицы         {db_tables_st}\n"
                f"БД WAL режим       {db_wal_st}\n"
                f"Гость → Mini App   {guest_st}\n"
                f"Кнопка меню        {menu_st}\n"
                f"Кнопка URL         {menu_short}\n"
                f"Админ → Server API {admin_st}\n"
                f"Uptime             {uptime_s}\n"
                f"</code>"
            )
            if fix_applied:
                report += f"\n{fix_applied.strip()}"
            if db_fix_applied:
                report += f"\n{db_fix_applied}"
            if guest_fix_applied:
                report += f"\n{guest_fix_applied.strip()}"
            if admin_fix_applied:
                report += f"\n{admin_fix_applied}"
            if escalation_applied:
                report += f"\n{escalation_applied}"

            await _send(report)
            logger.info("Server monitor report sent. all_ok=%s fix=%s", all_ok, fix_applied)

        await asyncio.sleep(_CHECK_INTERVAL)



async def run_expire_task() -> None:
    """
    Background task: every 60 s cancel PENDING bookings older than 15 min
    and notify guests via Telegram Bot API.
    """
    from bot.services.booking_service import expire_pending_bookings
    import aiohttp as _aiohttp
    logger.info("Expire-task started (checks every 60 s, window = 15 min).")
    while True:
        await asyncio.sleep(60)
        try:
            expired = await expire_pending_bookings()
            for b in expired:
                logger.info("Auto-expired booking #%s (pending > 15 min)", b.id)
                if not b.user_id:
                    continue
                try:
                    async with _aiohttp.ClientSession() as sess:
                        await sess.post(
                            f"https://api.telegram.org/bot{cfg.BOT_TOKEN}/sendMessage",
                            json={
                                "chat_id": b.user_id,
                                "parse_mode": "HTML",
                                "text": (
                                    f"⏳ <b>Бронь автоматически отменена</b>\n\n"
                                    f"Администратор не подтвердил бронь в течение 15 минут.\n"
                                    f"📅 {b.date} · {b.time}"
                                    f"{ ' · Стол ' + b.table if b.table else ''}\n\n"
                                    f"Вы можете создать новую бронь через меню."
                                ),
                            },
                            timeout=_aiohttp.ClientTimeout(total=5),
                        )
                except Exception as notify_err:
                    logger.warning("expire notify failed for user %s: %s", b.user_id, notify_err)
        except Exception as e:
            logger.warning("expire_pending_bookings error: %s", e)


async def run_bot(public_url: str) -> None:
    """Register webhook with Telegram and wait forever (updates arrive via uvicorn → /webhook)."""
    from bot.bot_instance import bot, dp
    from webapp.app import WEBHOOK_SECRET

    webhook_url = f"{public_url.rstrip('/')}/webhook"

    # Give uvicorn a moment to bind the port before Telegram tries to verify the endpoint
    await asyncio.sleep(3)

    # Telegram verifies the webhook URL by connecting to it.
    # cloudflare quick tunnel DNS may need a few seconds to propagate globally.
    # Retry up to 10 times with 5-second delays.
    for attempt in range(1, 11):
        try:
            await bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=False,
                allowed_updates=dp.resolve_used_update_types(),
                secret_token=WEBHOOK_SECRET or None,  # rejects requests without valid header
            )
            logger.info("Webhook registered → %s (attempt %s, secret=%s)",
                        webhook_url, attempt, bool(WEBHOOK_SECRET))
            break
        except Exception as exc:
            if attempt < 10:
                logger.warning(
                    "Webhook registration failed (attempt %s/10): %s — retrying in 8 s...",
                    attempt, exc,
                )
                await asyncio.sleep(8)
            else:
                logger.error("Webhook registration failed after 10 attempts: %s", exc)
                raise

    logger.info("Bot is live (webhook mode — no polling, no ConflictError).")

    # Stay alive; Telegram pushes updates via HTTP → uvicorn → /webhook → dp
    stop_event = asyncio.Event()
    await stop_event.wait()   # waits forever until the process is killed


async def _run_polling_mode() -> None:
    """
    Fallback: run bot with long-polling when no public tunnel is available.
    Safe because uvicorn runs in a daemon thread (no subprocess spawn) and the
    singleton lock prevents a second instance from racing for getUpdates.
    """
    from bot.bot_instance import bot, dp

    logger.info("=" * 62)
    logger.info("  \U0001f504 Bot running in POLLING mode (no Mini App).")
    logger.info("=" * 62)

    # ── Step 1: Delete any stale webhook ─────────────────────────────────────
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook cleared.")
    except Exception as exc:
        logger.warning("Could not clear webhook: %s", exc)

    # ── Step 2: Force-claim the Telegram getUpdates session ───────────────────
    # ROOT-CAUSE FIX: When an old bot instance is killed abruptly the TCP
    # connection stays "open" on Telegram's side.  If our new bot immediately
    # retries getUpdates, Telegram returns ConflictError and RESETS the old
    # session's expiry timer — creating an infinite deadlock that can last
    # minutes.  The solution: call getUpdates(timeout=0) once.  Telegram
    # immediately terminates the old session and grants ownership to us.
    for attempt in range(1, 6):
        try:
            await bot.get_updates(offset=-1, limit=1, timeout=0)
            logger.info("getUpdates session claimed successfully (attempt %s).", attempt)
            break
        except Exception as exc:
            if attempt < 5:
                logger.warning(
                    "Session claim attempt %s/5 failed: %s — retrying in 3 s...",
                    attempt, exc,
                )
                await asyncio.sleep(3)
            else:
                logger.warning("Could not claim session after 5 attempts — starting polling anyway.")

    await asyncio.sleep(1)  # let Telegram finish tearing down old session

    await asyncio.gather(
        dp.start_polling(bot, drop_pending_updates=True),
        run_expire_task(),
    )


async def run_keep_alive() -> None:
    """
    Self-ping keep-alive for Render.com free tier.
    Render spins down free web services after 15 min of no inbound requests.
    This task pings our own /health endpoint every 13 min to prevent sleeping.
    Only active when running on Render (RENDER_EXTERNAL_URL is set).
    """
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "")
    if not render_url:
        return  # not on Render — no need for keep-alive
    health_url = f"{render_url.rstrip('/')}/health"
    logger.info("Render keep-alive pinger started → %s (every 10 min)", health_url)
    import aiohttp as _ka_aiohttp
    while True:
        await asyncio.sleep(10 * 60)  # 10 minutes — safe margin below Render's 15 min timeout
        try:
            async with _ka_aiohttp.ClientSession() as _ka_sess:
                async with _ka_sess.get(health_url, timeout=_ka_aiohttp.ClientTimeout(total=15)) as _ka_r:
                    pass
            logger.debug("Keep-alive ping OK → %s", health_url)
        except Exception as exc:
            logger.warning("Keep-alive ping failed: %s — retrying in 30s...", exc)
            await asyncio.sleep(30)
            try:
                async with _ka_aiohttp.ClientSession() as _ka_sess:
                    async with _ka_sess.get(health_url, timeout=_ka_aiohttp.ClientTimeout(total=15)) as _ka_r:
                        pass
                logger.debug("Keep-alive retry OK → %s", health_url)
            except Exception as exc2:
                logger.warning("Keep-alive retry also failed: %s", exc2)


async def main() -> None:
    _check_production_webhook()  # abort if production webhook is already set
    _acquire_instance_lock()  # abort immediately if another instance is running

    # ── Database init with retry (PostgreSQL on Render may be cold) ───────────
    # On Render rolling deploys, old + new container overlap briefly → all PG
    # connection slots are taken. We retry 10 times with growing delays (up to
    # 30 s each = ~3 min total) so the old container has time to shut down.
    # If all attempts fail we log the error and CONTINUE anyway — the server
    # monitor will auto-fix the DB once the slots become available.
    _db_ok = False
    for db_attempt in range(1, 11):
        try:
            from bot.database.db import engine as _startup_engine
            await _startup_engine.dispose()   # release any leftover connections
            await asyncio.sleep(2)            # brief pause before reconnecting
            await init_db()
            logger.info("Database initialised (attempt %d).", db_attempt)
            _db_ok = True
            break
        except Exception as db_exc:
            wait_s = min(db_attempt * 4, 30)  # 4s, 8s, 12s … cap at 30s
            logger.warning(
                "Database init failed (attempt %d/10): %s — retrying in %ds...",
                db_attempt, db_exc, wait_s,
            )
            await asyncio.sleep(wait_s)
    if not _db_ok:
        logger.error(
            "Database unavailable after 10 attempts — starting anyway. "
            "Server monitor will repair the connection automatically."
        )

    # ── Auto-detect Render.com environment ───────────────────────────────────
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "")
    if render_url and not cfg.WEBAPP_URL:
        cfg.WEBAPP_URL = render_url.rstrip("/")
        logger.info("Render.com detected → WEBAPP_URL = %s", cfg.WEBAPP_URL)

    # ── Callback fired by TunnelWatchdog every time the tunnel restarts ──────
    async def _on_tunnel_restart(new_url: str) -> None:
        from webapp.app import WEBHOOK_SECRET
        cfg.WEBAPP_URL = new_url
        logger.info("=" * 62)
        logger.info("  ♻️  Tunnel restarted → %s", new_url)
        logger.info("=" * 62)
        # Re-register webhook with new URL (keep same secret token)
        from bot.bot_instance import bot as _bot, dp as _dp
        webhook_url = f"{new_url.rstrip('/')}/webhook"
        await _bot.set_webhook(url=webhook_url, drop_pending_updates=False,
                               allowed_updates=_dp.resolve_used_update_types(),
                               secret_token=WEBHOOK_SECRET or None)
        logger.info("Webhook re-registered → %s", webhook_url)
        await _set_menu_button(new_url)
        await _notify_admin_url(new_url, restarted=True)

    # ── Если WEBAPP_URL уже задан в env (Render / production) ──────────────────
    if cfg.WEBAPP_URL:
        public_url = cfg.WEBAPP_URL.rstrip("/")
        logger.info("=" * 62)
        logger.info("  ✅ Mini App URL (from env): %s", public_url)
        logger.info("=" * 62)
        await _set_menu_button(public_url)
        await _notify_admin_url(public_url, restarted=False)
        _start_webapp_thread()  # uvicorn runs in daemon thread, no subprocess
        await asyncio.gather(run_bot(public_url), run_expire_task(), run_server_monitor(), run_keep_alive())
        return

    # ── Иначе — поднимаем cloudflared туннель (локальная разработка) ────────
    logger.info("Starting Cloudflare Quick Tunnel on port %s...", cfg.WEBAPP_PORT)
    try:
        public_url = await get_tunnel_url(cfg.WEBAPP_PORT, on_url_change=_on_tunnel_restart)
        cfg.WEBAPP_URL = public_url

        logger.info("=" * 62)
        logger.info("  ✅ Mini App LIVE: %s", public_url)
        logger.info("  Open in Telegram → menu button, or paste URL in browser.")
        logger.info("=" * 62)

        await _set_menu_button(public_url)
        await _notify_admin_url(public_url, restarted=False)

    except CloudflaredRateLimitError as exc:
        logger.warning(
            "Cloudflare Quick Tunnel rate-limited (HTTP 429) — "
            "falling back to LONG-POLLING mode immediately (Mini App disabled)."
        )
        await _run_polling_mode()
        return
    except Exception as exc:
        logger.error("Tunnel failed: %s", exc)
        logger.warning(
            "Tunnel unavailable — falling back to LONG-POLLING mode (Mini App disabled)."
        )
        # Polling is safe: uvicorn runs in a daemon thread (no subprocess spawn),
        # and the singleton TCP lock prevents a second instance from connecting.
        await _run_polling_mode()
        return

    # Start uvicorn in background thread (no subprocess!), then register webhook and run forever
    _start_webapp_thread()
    try:
        await asyncio.gather(run_bot(public_url), run_expire_task(), run_server_monitor())
    except Exception as exc:
        logger.warning(
            "⚠️  Webhook registration failed (%s). "
            "Mini App server stays alive at %s — switching to POLLING mode.",
            exc, public_url,
        )
        # uvicorn (daemon thread) is still running — mini app remains accessible.
        # Fall back to long-polling so bot commands keep working.
        await _run_polling_mode()


if __name__ == "__main__":
    # Required on Windows: prevents multiprocessing 'spawn' from re-running main
    # when any library (uvicorn, sqlalchemy, etc.) spawns a worker.
    import multiprocessing
    multiprocessing.freeze_support()
    asyncio.run(main())
