"""
Aiogram Telegram Bot Handlers for 1,000+ Games Bot.
Includes commands, callback queries, and inline query search like Gamee.
"""
import random
from typing import List
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)

import database
from config import WEBAPP_URL, BOT_USERNAME
from webapp.server import games_cache
from bot.keyboards import (
    get_main_menu_keyboard,
    get_categories_keyboard,
    get_games_list_keyboard,
    get_game_play_keyboard
)

router = Router()

PAGE_SIZE = 8

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handles /start command: registers user and shows main interactive menu."""
    user = message.from_user
    await database.register_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

    welcome_text = (
        f"🎮 *Welcome to Game Hub, {user.first_name}!* ⚡\n\n"
        f"We have over *1,000+ instant HTML5 games* ready to play directly inside Telegram — "
        f"no downloads, no waiting, 100% free!\n\n"
        f"✨ *Highlights:*\n"
        f"• 🕹️ Arcade, Puzzle, Action, Racing & Retro classics\n"
        f"• 🏆 Global leaderboards and high-score ranking\n"
        f"• ⚔️ Challenge your friends in any chat using `@` inline mode\n"
        f"• 📱 Instant smooth 60fps Mini App experience\n\n"
        f"Tap the button below to launch the catalog and start playing!"
    )

    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handles /help command with bot instructions."""
    help_text = (
        "🕹️ *Telegram Game Hub - Bot Guide*\n\n"
        "Here are all available commands:\n"
        "• /start - Open the main game launcher menu\n"
        "• /games - Browse categories and all 1,000 games\n"
        "• /random - Play a surprise random game\n"
        "• /search `<name>` - Quick search games in chat\n"
        "• /leaderboard - View the global top players\n"
        "• /profile - View your personal stats & high scores\n\n"
        "💡 *Inline Game Sharing:*\n"
        f"You can type `@{BOT_USERNAME} <game name>` in *any* group or private chat "
        "to instantly share and challenge friends with any game!"
    )
    await message.answer(help_text, parse_mode="Markdown")

@router.message(Command("games"))
async def cmd_games(message: Message):
    """Handles /games command: displays category selection."""
    await message.answer(
        "📂 *Choose a Category to Explore:*",
        parse_mode="Markdown",
        reply_markup=get_categories_keyboard()
    )

@router.message(Command("random"))
async def cmd_random(message: Message):
    """Handles /random: picks a random game from the 1,000 catalog."""
    if not games_cache:
        await message.answer("Games catalog is loading. Try again in a moment!")
        return

    game = random.choice(games_cache)
    caption = (
        f"🎲 *Random Game Picked:*\n\n"
        f"*{game['title']}*\n"
        f"📂 Category: `{game['category']}` | ★ {game.get('rating', '4.8')}\n"
        f"📝 {game['description']}\n\n"
        f"Ready to play?"
    )
    await message.answer(caption, parse_mode="Markdown", reply_markup=get_game_play_keyboard(game))

@router.message(Command("search"))
async def cmd_search(message: Message):
    """Handles /search <term> in chat."""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("🔍 Usage: `/search <game name>`\nExample: `/search 2048` or `/search racing`", parse_mode="Markdown")
        return

    query = args[1].strip().lower()
    matches = [
        g for g in games_cache
        if query in g["title"].lower() or query in g["category"].lower() or any(query in t for t in g.get("tags", []))
    ][:8]

    if not matches:
        await message.answer(f"🔍 No games found matching `{query}`. Try another keyword or browse `/games`.", parse_mode="Markdown")
        return

    buttons = []
    for g in matches:
        buttons.append([
            InlineKeyboardButton(
                text=f"{g['title']} ({g['category']})",
                callback_data=f"game_{g['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="⚡ Open Full App (1,000 Games)", web_app=WebAppInfo(url=WEBAPP_URL))])

    await message.answer(
        f"🔍 Found *{len(matches)}* matching games for `{query}`:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@router.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message):
    """Handles /leaderboard command: top players."""
    leaders = await database.get_global_leaderboard(limit=10)
    if not leaders:
        await message.answer("🏆 No high scores recorded yet! Launch a game and be the first to set a record.")
        return

    text = "🏆 *GLOBAL TOP 10 PLAYERS* 🏆\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, u in enumerate(leaders):
        icon = medals[i] if i < 3 else f"`#{i+1}`"
        name = u.get("first_name") or u.get("username") or "Player"
        text += f"{icon} *{name}* — ⭐ `{u['total_score']:,}` pts ({u['total_games_played']} games)\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Play & Beat Scores", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Handles /profile command: user statistics."""
    user = message.from_user
    stats = await database.get_user_stats(user.id)

    text = (
        f"👤 *Player Profile: {user.first_name}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⭐ *Total Score:* `{stats['total_score']:,}`\n"
        f"🏅 *Global Rank:* `#{stats['rank']}`\n"
        f"🎮 *Games Played:* `{stats['total_games_played']}`\n"
    )

    if stats.get("top_games"):
        text += "\n🏆 *Your Top Scores:*\n"
        for tg in stats["top_games"]:
            # Find game title
            g = next((x for x in games_cache if x["id"] == tg["game_id"]), None)
            g_title = g["title"] if g else tg["game_id"]
            text += f"• {g_title}: `{tg['best_score']:,}` pts\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Play Now", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

# ----------------- CALLBACK QUERY HANDLERS -----------------

@router.callback_query(F.data == "nav_main")
async def cb_nav_main(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎮 *Game Hub - 1,000+ Games Available:*",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "nav_categories")
async def cb_nav_categories(callback: CallbackQuery):
    await callback.message.edit_text(
        "📂 *Select a Category to Browse:*",
        parse_mode="Markdown",
        reply_markup=get_categories_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "nav_popular")
async def cb_nav_popular(callback: CallbackQuery):
    popular = sorted(games_cache, key=lambda x: x.get("plays", 0), reverse=True)[:8]
    buttons = []
    for g in popular:
        buttons.append([
            InlineKeyboardButton(text=f"🔥 {g['title']}", callback_data=f"game_{g['id']}")
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Main Menu", callback_data="nav_main")])

    await callback.message.edit_text(
        "🔥 *Most Popular Games Right Now:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@router.callback_query(F.data == "nav_random")
async def cb_nav_random(callback: CallbackQuery):
    game = random.choice(games_cache)
    caption = (
        f"🎲 *Random Game Picked:*\n\n"
        f"*{game['title']}*\n"
        f"📂 Category: `{game['category']}` | ★ {game.get('rating', '4.8')}\n"
        f"📝 {game['description']}"
    )
    await callback.message.edit_text(
        caption,
        parse_mode="Markdown",
        reply_markup=get_game_play_keyboard(game)
    )
    await callback.answer()

@router.callback_query(F.data == "nav_leaderboard")
async def cb_nav_leaderboard(callback: CallbackQuery):
    leaders = await database.get_global_leaderboard(limit=10)
    if not leaders:
        await callback.answer("No scores recorded yet!")
        return

    text = "🏆 *GLOBAL TOP 10 PLAYERS* 🏆\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, u in enumerate(leaders):
        icon = medals[i] if i < 3 else f"`#{i+1}`"
        name = u.get("first_name") or u.get("username") or "Player"
        text += f"{icon} *{name}* — ⭐ `{u['total_score']:,}` pts\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Play in Mini App", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="🔙 Back", callback_data="nav_main")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("cat_"))
async def cb_category(callback: CallbackQuery):
    cat_name = callback.data.split("cat_", 1)[1]
    filtered = [g for g in games_cache if g["category"] == cat_name]
    total_pages = (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE
    page = 1
    slice_games = filtered[:PAGE_SIZE]

    text = f"📂 *{cat_name} Games* (Total: {len(filtered)})\nSelect a game to play:"
    kb = get_games_list_keyboard(cat_name, page, total_pages, slice_games)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("cpage_"))
async def cb_category_page(callback: CallbackQuery):
    parts = callback.data.split("_")
    cat_name = parts[1]
    page = int(parts[2])

    filtered = [g for g in games_cache if g["category"] == cat_name]
    total_pages = (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE
    start = (page - 1) * PAGE_SIZE
    slice_games = filtered[start:start + PAGE_SIZE]

    text = f"📂 *{cat_name} Games* (Page {page}/{total_pages})\nSelect a game to play:"
    kb = get_games_list_keyboard(cat_name, page, total_pages, slice_games)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("game_"))
async def cb_game_details(callback: CallbackQuery):
    game_id = callback.data.split("game_", 1)[1]
    game = next((g for g in games_cache if g["id"] == game_id), None)
    if not game:
        await callback.answer("Game not found!")
        return

    text = (
        f"🎮 *{game['title']}*\n\n"
        f"📂 Category: `{game['category']}`\n"
        f"⭐ Rating: `{game.get('rating', '4.8')} / 5.0`\n"
        f"👥 Plays: `{game.get('plays', 1000):,}`\n"
        f"📝 {game['description']}\n\n"
        f"Click the button below to launch the game instantly!"
    )
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_game_play_keyboard(game)
    )
    await callback.answer()

@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()

# ----------------- INLINE QUERY (LIKE GAMEE) -----------------
@router.inline_query()
async def inline_game_search(inline_query: InlineQuery):
    """
    Inline Query Handler:
    Allows users to type `@YourBotName flappy` or `@YourBotName puzzle` in ANY Telegram chat or group
    to share game cards with instant playable buttons.
    """
    query = inline_query.query.strip().lower()

    if not query or query == "play":
        # Return popular games
        matches = sorted(games_cache, key=lambda x: x.get("plays", 0), reverse=True)[:25]
    else:
        matches = [
            g for g in games_cache
            if query in g["title"].lower() or query in g["category"].lower() or any(query in t for t in g.get("tags", []))
        ][:25]

    results = []
    for g in matches:
        game_url = f"{WEBAPP_URL}#play={g['id']}"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"▶ Play {g['title']} 🎮",
                        web_app=WebAppInfo(url=game_url)
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚡ Play More Games (1,000+)",
                        web_app=WebAppInfo(url=WEBAPP_URL)
                    )
                ]
            ]
        )

        content = InputTextMessageContent(
            message_text=(
                f"🎮 *{g['title']}*\n"
                f"📂 Category: `{g['category']}` | ★ {g.get('rating', '4.8')}\n"
                f"📝 {g['description']}\n\n"
                f"Can you beat my high score? Tap below to play!"
            ),
            parse_mode="Markdown"
        )

        article = InlineQueryResultArticle(
            id=g["id"],
            title=g["title"],
            description=f"[{g['category']}] ★ {g.get('rating', '4.8')} - {g['description'][:50]}...",
            input_message_content=content,
            reply_markup=kb
        )
        results.append(article)

    await inline_query.answer(results, cache_time=10, is_personal=True)
