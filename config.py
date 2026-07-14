import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не установлен в .env")


# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_JSON = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "./credentials.json")
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")

# Owner
OWNER_USER_ID = int(os.getenv("OWNER_USER_ID", "0"))
if OWNER_USER_ID == 0:
    raise ValueError("❌ OWNER_USER_ID должен быть указан в .env")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# OCR.space
OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY", "helloworld")
