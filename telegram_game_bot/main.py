"""
Unified Runner for Telegram Game Bot and WebApp Server.
Runs FastAPI and the Aiogram Telegram Bot concurrently using asyncio.
"""
import sys
import asyncio
import logging
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

import database
from config import (
    BOT_TOKEN,
    BOT_USERNAME,
    SERVER_HOST,
    SERVER_PORT,
    WEBAPP_URL
)
from webapp.server import app as fastapi_app
from bot.handlers import router as bot_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("GameHub")

async def run_fastapi_server():
    """Runs Uvicorn server for the Telegram Mini App and API."""
    config = uvicorn.Config(
        app=fastapi_app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
        access_log=False
    )
    server = uvicorn.Server(config)
    logger.info(f"🌐 Telegram Mini App & API server starting at http://{SERVER_HOST}:{SERVER_PORT}")
    logger.info(f"🚀 WebApp URL configured as: {WEBAPP_URL}")
    await server.serve()

async def run_telegram_bot():
    # Check if token is default or unset
    is_placeholder = (
        not BOT_TOKEN or
        BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or
        BOT_TOKEN.startswith("1234567890:")
    )

    if is_placeholder:
        logger.warning(
            "⚠️ BOT_TOKEN is not configured yet!\n"
            "   -> The WebApp and 1,000 Games Server is running at http://%s:%s\n"
            "   -> To connect your Telegram Bot:\n"
            "      1. Open @BotFather on Telegram and send /newbot\n"
            "      2. Copy your BOT TOKEN and put it in /root/telegram_game_bot/.env\n"
            "      3. Set your WebApp URL with @BotFather (/newapp or /setmenubutton)",
            SERVER_HOST, SERVER_PORT
        )
        while True:
            await asyncio.sleep(3600)

    try:
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        dp.include_router(bot_router)

        # Fast timeout check
        logger.info("Connecting to Telegram Bot API...")
        bot_info = await asyncio.wait_for(bot.get_me(), timeout=8.0)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info(f"🤖 Bot connected successfully as @{bot_info.username} ({bot_info.first_name})")

        logger.info("🎮 Bot polling started. Ready to serve 1,000+ games!")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Error starting Telegram Bot: {e}")
        logger.info("WebApp server continues running...")
        while True:
            await asyncio.sleep(3600)

async def main():
    # Initialize database
    await database.init_db()
    logger.info("📦 Database initialized successfully.")

    # Concurrently run WebApp server and Telegram Bot
    await asyncio.gather(
        run_fastapi_server(),
        run_telegram_bot()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Shutting down Telegram Game Bot...")
