"""
FastAPI Server for Telegram Game Bot WebApp and Game Catalog API.
Serves 1,000+ games, static assets, and manages user score tracking.
"""
import json
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database
from config import BASE_DIR, GAMES_DATA_PATH

app = FastAPI(title="Telegram Game Hub API", version="1.0.0")

# Enable CORS for Telegram WebApp environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load 1,000 Games Catalog into memory for high-speed sub-millisecond querying
games_cache: List[dict] = []
categories_cache: List[dict] = []

def load_games_data():
    global games_cache, categories_cache
    if GAMES_DATA_PATH.exists():
        with open(GAMES_DATA_PATH, "r", encoding="utf-8") as f:
            games_cache = json.load(f)
    else:
        games_cache = []

    # Calculate categories
    cat_map = {}
    for g in games_cache:
        c = g["category"]
        cat_map[c] = cat_map.get(c, 0) + 1

    categories_cache = [{"name": c, "count": cnt} for c, cnt in cat_map.items()]

load_games_data()

# Static directories
STATIC_DIR = BASE_DIR / "webapp" / "static"
GAMES_DIR = STATIC_DIR / "games"

# Mount static and games assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/games", StaticFiles(directory=str(GAMES_DIR)), name="games")

# Models
class ScoreSubmission(BaseModel):
    user_id: int
    username: Optional[str] = ""
    first_name: Optional[str] = "Player"
    game_id: str
    score: int

class FavoriteRequest(BaseModel):
    user_id: int
    game_id: str

@app.on_event("startup")
async def startup():
    await database.init_db()

@app.get("/")
async def root_index():
    """Serves the main Telegram Mini App."""
    index_file = STATIC_DIR / "index.html"
    return FileResponse(index_file)

@app.get("/api/games")
async def get_games(
    category: Optional[str] = Query(None, description="Category filter"),
    search: Optional[str] = Query(None, description="Search keyword in title or tags"),
    sort: Optional[str] = Query("popular", description="Sort by popular, rating, or title"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000)
):
    """Returns paginated/filtered games from the 1,000 games catalog."""
    results = games_cache

    if category and category.lower() != "all":
        results = [g for g in results if g["category"].lower() == category.lower()]

    if search:
        q = search.strip().lower()
        results = [
            g for g in results
            if q in g["title"].lower()
            or q in g["category"].lower()
            or any(q in t.lower() for t in g.get("tags", []))
        ]

    # Sorting
    if sort == "rating":
        results = sorted(results, key=lambda x: x.get("rating", 0), reverse=True)
    elif sort == "title":
        results = sorted(results, key=lambda x: x.get("title", ""))
    elif sort == "popular":
        results = sorted(results, key=lambda x: x.get("plays", 0), reverse=True)

    total = len(results)
    start = (page - 1) * limit
    end = start + limit
    paged = results[start:end]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "games": paged
    }

@app.get("/api/games/{game_id}")
async def get_game_details(game_id: str):
    """Returns single game details."""
    game = next((g for g in games_cache if g["id"] == game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@app.get("/api/categories")
async def get_categories():
    """Returns all game categories and counts."""
    return {"categories": categories_cache}

@app.post("/api/score")
async def submit_score(payload: ScoreSubmission):
    """Submits game score from WebApp game session."""
    # Register/update user
    await database.register_or_update_user(
        user_id=payload.user_id,
        username=payload.username,
        first_name=payload.first_name or "Player"
    )

    result = await database.record_score(
        user_id=payload.user_id,
        game_id=payload.game_id,
        score=payload.score,
        user_display_name=payload.first_name or payload.username or "Player"
    )
    return {"status": "success", **result}

@app.get("/api/leaderboard")
async def get_global_leaderboard(limit: int = 20):
    """Returns top ranked players."""
    leaders = await database.get_global_leaderboard(limit=limit)
    return {"leaderboard": leaders}

@app.get("/api/leaderboard/{game_id}")
async def get_game_leaderboard(game_id: str, limit: int = 10):
    """Returns top scores for specific game."""
    scores = await database.get_game_leaderboard(game_id=game_id, limit=limit)
    return {"game_id": game_id, "scores": scores}

@app.post("/api/favorite")
async def toggle_favorite(payload: FavoriteRequest):
    """Toggles bookmark favorite."""
    is_fav = await database.toggle_favorite(user_id=payload.user_id, game_id=payload.game_id)
    return {"game_id": payload.game_id, "is_favorite": is_fav}

@app.get("/api/user/{user_id}/favorites")
async def get_user_favorites(user_id: int):
    """Returns user's bookmarked game IDs."""
    favs = await database.get_user_favorites(user_id)
    return {"user_id": user_id, "favorites": favs}

@app.get("/api/user/{user_id}/stats")
async def get_user_stats(user_id: int, first_name: str = "Player", username: str = ""):
    """Returns user player profile statistics."""
    await database.register_or_update_user(user_id=user_id, username=username, first_name=first_name)
    stats = await database.get_user_stats(user_id)
    return stats

@app.post("/api/games/{game_id}/play")
async def increment_play(game_id: str):
    """Increment play counter for a game."""
    await database.increment_game_play(game_id)
    return {"status": "ok"}
