import os

# Telegram bot token from @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Jamendo API client id (free, register at https://devportal.jamendo.com/)
JAMENDO_CLIENT_ID = os.getenv("JAMENDO_CLIENT_ID", "")

# Public base URL of this deployment, e.g. https://your-app.up.railway.app
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")

# Port the web server listens on (Railway sets PORT automatically)
PORT = int(os.getenv("PORT", "8000"))

# Local folder where uploaded audio files are stored
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
