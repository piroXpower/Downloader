"""
Configuration settings for the Telegram Game Bot and WebApp Server.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Telegram Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME", "game_hub_bot")

# WebApp / Mini App Configuration
# For local testing, can be localhost or an ngrok/cloudflared/vps https URL
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:8080")

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8080"))

# Database Configuration
DATABASE_PATH = BASE_DIR / "data" / "games_bot.db"
GAMES_DATA_PATH = BASE_DIR / "data" / "games.json"

# Bot Administrator User IDs (list of ints)
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
