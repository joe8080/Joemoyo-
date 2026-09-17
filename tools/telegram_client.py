"""
Minimal Telegram notifier.

Sends short text messages to a Telegram chat via the Bot API, so the
auto-trader can ping you when it places trades. Fully optional: if the
bot token or chat id aren't configured, every call is a safe no-op.

Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the environment/.env.
- Token comes from @BotFather when you create the bot.
- Chat id is where alerts go (your user id for a DM). Message the bot once,
  then read it from https://api.telegram.org/bot<token>/getUpdates, or ask
  @userinfobot on Telegram.
"""

import requests

from config.settings import settings

API_BASE = "https://api.telegram.org"


def telegram_configured() -> bool:
    return bool(settings.telegram_bot_token and settings.telegram_chat_id)


def send_telegram(text: str) -> bool:
    """
    Send a Telegram message. Returns True on success, False otherwise.
    Never raises — notification failures must not break trading.
    """
    if not telegram_configured():
        return False
    url = f"{API_BASE}/bot{settings.telegram_bot_token}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        return resp.status_code == 200
    except requests.RequestException:
        return False
