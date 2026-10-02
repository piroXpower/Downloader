"""
Database management for Telegram Game Bot using aiosqlite.
Manages users, game scores, favorites, and leaderboards.
"""
import aiosqlite
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import DATABASE_PATH

async def init_db():
    """Initialize database tables and indexes."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_games_played INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game_id TEXT,
                score INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER,
                game_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, game_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS game_stats (
                game_id TEXT PRIMARY KEY,
                play_count INTEGER DEFAULT 0,
                high_score INTEGER DEFAULT 0,
                high_scorer_id INTEGER,
                high_scorer_name TEXT
            )
        """)

        # Indexes for fast querying
        await db.execute("CREATE INDEX IF NOT EXISTS idx_scores_user ON scores(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_scores_game ON scores(game_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_scores_score ON scores(score DESC)")
        await db.commit()

async def register_or_update_user(user_id: int, username: Optional[str], first_name: str):
    """Registers user or updates last active timestamp and username."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, last_active)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_active = CURRENT_TIMESTAMP
        """, (user_id, username or "", first_name))
        await db.commit()

async def record_score(user_id: int, game_id: str, score: int, user_display_name: str = "") -> Dict[str, Any]:
    """Records a game score, updates user totals and checks for new high scores."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Insert score log
        await db.execute(
            "INSERT INTO scores (user_id, game_id, score) VALUES (?, ?, ?)",
            (user_id, game_id, score)
        )

        # Update user total stats (creating user if not already present)
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, total_games_played, total_score, last_active)
            VALUES (?, '', ?, 1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                total_games_played = total_games_played + 1,
                total_score = total_score + excluded.total_score,
                last_active = CURRENT_TIMESTAMP
        """, (user_id, user_display_name or "Player", score))

        # Check existing game stats
        async with db.execute("SELECT high_score, play_count FROM game_stats WHERE game_id = ?", (game_id,)) as cursor:
            row = await cursor.fetchone()

        is_new_high_score = False
        if row is None:
            await db.execute("""
                INSERT INTO game_stats (game_id, play_count, high_score, high_scorer_id, high_scorer_name)
                VALUES (?, 1, ?, ?, ?)
            """, (game_id, score, user_id, user_display_name))
            is_new_high_score = True
        else:
            current_high, play_cnt = row
            if score > current_high:
                is_new_high_score = True
                await db.execute("""
                    UPDATE game_stats
                    SET play_count = play_count + 1,
                        high_score = ?,
                        high_scorer_id = ?,
                        high_scorer_name = ?
                    WHERE game_id = ?
                """, (score, user_id, user_display_name, game_id))
            else:
                await db.execute("UPDATE game_stats SET play_count = play_count + 1 WHERE game_id = ?", (game_id,))

        await db.commit()
        return {
            "is_new_high_score": is_new_high_score,
            "recorded_score": score,
            "game_id": game_id
        }

async def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Returns a user's stats: games played, total score, best game scores, rank."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
        
        if not user:
            return {
                "user_id": user_id,
                "total_games_played": 0,
                "total_score": 0,
                "rank": "-"
            }

        # Calculate user global rank based on total score
        async with db.execute("SELECT COUNT(*) + 1 as rank FROM users WHERE total_score > ?", (user["total_score"],)) as cursor:
            rank_row = await cursor.fetchone()
            rank = rank_row["rank"] if rank_row else 1

        # Get top 5 high scores per game for this user
        async with db.execute("""
            SELECT game_id, MAX(score) as best_score
            FROM scores
            WHERE user_id = ?
            GROUP BY game_id
            ORDER BY best_score DESC
            LIMIT 5
        """, (user_id,)) as cursor:
            top_games = [dict(r) for r in await cursor.fetchall()]

        return {
            "user_id": user_id,
            "username": user["username"],
            "first_name": user["first_name"],
            "total_games_played": user["total_games_played"],
            "total_score": user["total_score"],
            "rank": rank,
            "top_games": top_games
        }

async def get_global_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
    """Returns top players by total score."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT user_id, username, first_name, total_score, total_games_played
            FROM users
            WHERE total_score > 0
            ORDER BY total_score DESC
            LIMIT ?
        """, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_game_leaderboard(game_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Returns top scores for a specific game."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT s.score, s.created_at, u.user_id, u.username, u.first_name
            FROM scores s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.game_id = ?
            ORDER BY s.score DESC
            LIMIT ?
        """, (game_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def toggle_favorite(user_id: int, game_id: str) -> bool:
    """Toggles a game in the user's favorites. Returns True if now favorited, False if removed."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT 1 FROM favorites WHERE user_id = ? AND game_id = ?", (user_id, game_id)) as cursor:
            exists = await cursor.fetchone() is not None

        if exists:
            await db.execute("DELETE FROM favorites WHERE user_id = ? AND game_id = ?", (user_id, game_id))
            await db.commit()
            return False
        else:
            await db.execute("INSERT INTO favorites (user_id, game_id) VALUES (?, ?)", (user_id, game_id))
            await db.commit()
            return True

async def get_user_favorites(user_id: int) -> List[str]:
    """Returns a list of game_ids favorited by the user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT game_id FROM favorites WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

async def increment_game_play(game_id: str):
    """Increments the play counter for a game."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO game_stats (game_id, play_count)
            VALUES (?, 1)
            ON CONFLICT(game_id) DO UPDATE SET play_count = play_count + 1
        """, (game_id,))
        await db.commit()
