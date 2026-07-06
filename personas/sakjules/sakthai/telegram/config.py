"""Telegram configuration re-exported from the central SakThai config module."""

from __future__ import annotations

from ..config import telegram_allowed_user_ids, telegram_bot_token

TELEGRAM_BOT_TOKEN = telegram_bot_token()
ALLOWED_USER_IDS = telegram_allowed_user_ids()
