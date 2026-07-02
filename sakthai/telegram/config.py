import os

# Telegram Bot API Token
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

# List of allowed user IDs for security
ALLOWED_USER_IDS = [
    # 123456789, # Example user ID
]
