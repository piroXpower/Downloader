"""
VidTube Universal Telegram Downloader Bot.
Powered by aiogram 3.x and the VidTube API (FastAPI backend).

Supports:
- Instagram Reels & Posts
- YouTube Videos & Shorts
- Facebook Watch & Reels
- Twitter / X Clips
- Pinterest Video Pins
- Terabox Cloud Files
- TikTok (No Watermark)
- Reddit, SoundCloud, and 1,000+ others!
"""
import os
import sys
import logging
import asyncio
import re
from pathlib import Path

import httpx
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile
)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
API_BASE_URL = os.getenv("VIDTUBE_API_URL", "http://127.0.0.1:8000")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VidTubeBot")

dp = Dispatcher()

# Regex pattern to detect URLs
URL_PATTERN = re.compile(r'https?://[^\s]+')

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    welcome_text = (
        "👋 **Welcome to VidTube Downloader Bot!**\n\n"
        "Send me any video link and I will download it directly into this chat!\n\n"
        "🌟 **Supported Platforms:**\n"
        "• 📸 **Instagram** (Reels, Posts, Stories)\n"
        "• ▶️ **YouTube** (Videos, Shorts, Music)\n"
        "• 📘 **Facebook** (Watch, Reels)\n"
        "• 🐦 **Twitter / X** (Video Tweets)\n"
        "• 📌 **Pinterest** (Video Pins)\n"
        "• 📦 **Terabox** (Shared Cloud Files)\n"
        "• 🎵 **TikTok** (Without Watermark)\n"
        "• 👽 **Reddit** (Videos with sound)\n"
        "• 🎶 **SoundCloud** (MP3 Audio)\n\n"
        "🚀 **Just paste any video URL to begin!**"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "💡 **How to Use:**\n\n"
        "1. Copy the share link of any video from Instagram, YouTube, Facebook, Twitter, Pinterest, or Terabox.\n"
        "2. Paste it in this chat.\n"
        "3. Choose **Download Video (MP4)** or **Audio (MP3)**.\n"
        "4. The bot will download and send the file directly to you!\n\n"
        "⚙️ *Powered by VidTube Media Engine*"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(F.text)
async def handle_link(message: types.Message):
    text = message.text.strip()
    match = URL_PATTERN.search(text)
    if not match:
        await message.answer("⚠️ Please send a valid video link (e.g. YouTube, Instagram, Facebook, Twitter, Terabox).")
        return

    url = match.group(0)
    status_msg = await message.answer("🔍 **Analyzing video link...**", parse_mode="Markdown")

    try:
        # Call VidTube API to extract metadata
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(f"{API_BASE_URL}/api/extract", json={"url": url})
            data = resp.json()

        if not data.get("success", False):
            err_msg = data.get("error", "Could not retrieve video details.")
            await status_msg.edit_text(f"❌ **Error:** {err_msg}", parse_mode="Markdown")
            return

        title = data.get("title", "Video")[:80]
        uploader = data.get("uploader", "Creator")
        duration = data.get("duration_formatted", "0:00")
        platform = data.get("platform", "Media")
        views = data.get("views", "0")

        # Encode job params in inline keyboard
        # Storing data in callback query (max 64 bytes for callback_data, so we cache or use query)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎬 Download Video (MP4)", callback_data=f"dl:v:{data['id'][:15]}"),
                InlineKeyboardButton(text="🎵 Download MP3 (Audio)", callback_data=f"dl:a:{data['id'][:15]}")
            ]
        ])

        # Cache url by id in memory for callback
        PENDING_URLS[data['id'][:15]] = {
            "url": url,
            "title": title,
            "duration": data.get("duration", 0),
            "uploader": uploader
        }

        caption = (
            f"🎬 **{title}**\n\n"
            f"👤 **Author:** {uploader}\n"
            f"⏱️ **Duration:** {duration}\n"
            f"🌐 **Platform:** {platform}\n"
            f"👁️ **Views:** {views}\n\n"
            f"👇 **Choose format to download:**"
        )

        thumb_url = data.get("thumbnail")
        if thumb_url and thumb_url.startswith("http"):
            try:
                await message.answer_photo(photo=thumb_url, caption=caption, reply_markup=kb, parse_mode="Markdown")
                await status_msg.delete()
                return
            except Exception:
                pass

        await status_msg.edit_text(caption, reply_markup=kb, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Extraction error: {e}")
        await status_msg.edit_text(f"❌ **Error connecting to VidTube server:**\n`{str(e)}`", parse_mode="Markdown")

# Cache to associate short ID with URL
PENDING_URLS = {}

@dp.callback_query(F.data.startswith("dl:"))
async def handle_download_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    media_type = "video" if parts[1] == "v" else "audio"
    short_id = parts[2]

    item = PENDING_URLS.get(short_id)
    if not item:
        await callback.answer("Link session expired. Please send the link again.", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    progress_msg = await callback.message.answer(
        f"⏳ **Downloading & converting {media_type.upper()}...**\nPlease wait a few moments...",
        parse_mode="Markdown"
    )

    try:
        # Call VidTube /api/bot/download endpoint
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{API_BASE_URL}/api/bot/download",
                json={"url": item["url"], "type": media_type}
            )
            result = resp.json()

        if not result.get("success", False):
            await progress_msg.edit_text(
                f"❌ **Download failed:** {result.get('error', 'Unknown error')}",
                parse_mode="Markdown"
            )
            return

        file_path_str = result.get("file_path")
        file_size_fmt = result.get("file_size_formatted", "")
        file_size = result.get("file_size", 0)
        title = result.get("title", "Downloaded Media")

        # Telegram bot upload limit: 50MB
        if file_size > 50 * 1024 * 1024:
            download_link = f"{API_BASE_URL}{result.get('download_url')}"
            await progress_msg.edit_text(
                f"⚠️ **File exceeds Telegram's 50MB bot upload limit!**\n\n"
                f"📁 **File:** `{result.get('file_name')}`\n"
                f"📦 **Size:** `{file_size_fmt}`\n\n"
                f"🔗 [Click here to download directly]({download_link})",
                parse_mode="Markdown"
            )
            return

        if not file_path_str or not Path(file_path_str).exists():
            await progress_msg.edit_text("❌ Downloaded file not found on disk.", parse_mode="Markdown")
            return

        input_file = FSInputFile(file_path_str, filename=result.get("file_name"))

        if media_type == "audio":
            await callback.message.answer_audio(
                audio=input_file,
                title=title[:60],
                performer=result.get("uploader", "VidTube")[:40],
                duration=result.get("duration", 0),
                caption=f"🎵 **{title}**\n💾 Size: {file_size_fmt}\n⚡ Downloaded with VidTube",
                parse_mode="Markdown"
            )
        else:
            await callback.message.answer_video(
                video=input_file,
                caption=f"🎬 **{title}**\n💾 Size: {file_size_fmt}\n⚡ Downloaded with VidTube",
                duration=result.get("duration", 0),
                supports_streaming=True,
                parse_mode="Markdown"
            )

        await progress_msg.delete()

    except Exception as e:
        logger.error(f"Download task error: {e}")
        await progress_msg.edit_text(f"❌ **Error:** {str(e)}", parse_mode="Markdown")

async def main():
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("\n" + "="*60)
        print("⚠️  TELEGRAM BOT TOKEN REQUIRED!")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot to create a bot and get your token")
        print("3. Run the bot with:")
        print("   BOT_TOKEN='123456:ABC-DEF...' python telegram_bot.py")
        print("="*60 + "\n")
        return

    bot = Bot(token=BOT_TOKEN)
    print("🤖 VidTube Telegram Bot is running!")
    print(f"📡 Connected to VidTube API at: {API_BASE_URL}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
