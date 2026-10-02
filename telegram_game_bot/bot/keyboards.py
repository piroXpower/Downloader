"""
Inline and Reply Keyboards for the Telegram Game Bot.
Supports Telegram Mini App WebApp buttons and interactive menu navigation.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import WEBAPP_URL

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main start menu keyboard with WebApp launcher and quick access buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚡ PLAY 1,000+ GAMES 🎮",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ],
            [
                InlineKeyboardButton(text="🔥 Popular Games", callback_data="nav_popular"),
                InlineKeyboardButton(text="🎲 Random Game", callback_data="nav_random")
            ],
            [
                InlineKeyboardButton(text="📂 Categories", callback_data="nav_categories"),
                InlineKeyboardButton(text="🏆 Leaderboard", callback_data="nav_leaderboard")
            ],
            [
                InlineKeyboardButton(
                    text="📢 Share Bot with Friends",
                    switch_inline_query="play"
                )
            ]
        ]
    )

def get_categories_keyboard() -> InlineKeyboardMarkup:
    """Category selector keyboard."""
    cats = [
        ("🕹️ Arcade", "cat_Arcade"),
        ("🧩 Puzzle", "cat_Puzzle"),
        ("⚔️ Action", "cat_Action"),
        ("🏎️ Racing", "cat_Racing"),
        ("⚽ Sports", "cat_Sports"),
        ("👾 Retro", "cat_Retro"),
        ("🃏 Cards & Board", "cat_Cards & Board"),
        ("🎯 Casual", "cat_Casual")
    ]
    buttons = []
    for i in range(0, len(cats), 2):
        row = [InlineKeyboardButton(text=cats[i][0], callback_data=cats[i][1])]
        if i + 1 < len(cats):
            row.append(InlineKeyboardButton(text=cats[i+1][0], callback_data=cats[i+1][1]))
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="nav_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_games_list_keyboard(category: str, page: int, total_pages: int, games_slice: list) -> InlineKeyboardMarkup:
    """Paginated list of games within a category."""
    buttons = []

    # Game selection buttons
    for g in games_slice:
        buttons.append([
            InlineKeyboardButton(
                text=f"{g.get('title')} ({g.get('rating', '4.8')}★)",
                callback_data=f"game_{g['id']}"
            )
        ])

    # Navigation pagination row
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="◀ Prev", callback_data=f"cpage_{category}_{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Next ▶", callback_data=f"cpage_{category}_{page + 1}"))
    buttons.append(nav_row)

    # Return row
    buttons.append([
        InlineKeyboardButton(text="📂 Categories", callback_data="nav_categories"),
        InlineKeyboardButton(text="🔙 Main Menu", callback_data="nav_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_game_play_keyboard(game: dict) -> InlineKeyboardMarkup:
    """Individual game card keyboard with Play WebApp button and sharing."""
    # Play URL with direct game routing
    game_url = f"{WEBAPP_URL}#play={game['id']}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"▶ PLAY {game['title']} NOW 🎮",
                    web_app=WebAppInfo(url=game_url)
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Challenge Friends",
                    switch_inline_query=game['title']
                ),
                InlineKeyboardButton(
                    text="🏆 Scores",
                    callback_data=f"scores_{game['id']}"
                )
            ],
            [
                InlineKeyboardButton(text="🎲 Another Random", callback_data="nav_random"),
                InlineKeyboardButton(text="🔙 Back", callback_data="nav_categories")
            ]
        ]
    )
