"""
OmniTube - Modern YouTube-Style Video Streaming & Multi-Platform Media Downloader API.
"""
import os
import re
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Query
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

from downloader import (
    extract_info,
    start_download_job,
    JOBS,
    DOWNLOAD_DIR,
    detect_platform
)

app = FastAPI(title="OmniTube Media Engine", version="2.0.0")

# Enable CORS for flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path("/root/omnitube/static")
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Models
class ExtractRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    format_id: Optional[str] = "bestvideo+bestaudio/best"
    is_audio: Optional[bool] = False
    title: Optional[str] = "Media Video"

# Curated high-quality trending content for the YouTube homepage feed
TRENDING_ITEMS = [
    {
        "id": "rickroll_remaster",
        "title": "Rick Astley - Never Gonna Give You Up (Official Video 4K Remaster)",
        "uploader": "Rick Astley",
        "uploader_avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=RickAstley",
        "channel_verified": True,
        "views": "1.5B views",
        "time_ago": "2 years ago",
        "duration": "3:33",
        "thumbnail": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800&auto=format&fit=crop&q=80",
        "platform": "YouTube",
        "platform_icon": "youtube",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "category": "YouTube 4K",
        "likes": "16M"
    },
    {
        "id": "insta_tokyo_reel",
        "title": "Rainy Night in Shinjuku Tokyo 4K Cinematic Reel #japan #aesthetic",
        "uploader": "tokyo_wanderlust",
        "uploader_avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=tokyowander",
        "channel_verified": True,
        "views": "4.2M views",
        "time_ago": "3 days ago",
        "duration": "0:45",
        "thumbnail": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=800&auto=format&fit=crop&q=80",
        "platform": "Instagram",
        "platform_icon": "instagram",
        "url": "https://www.instagram.com/reel/C_example_shinjuku/",
        "category": "Instagram Reels",
        "likes": "890K"
    },
    {
        "id": "pinterest_kitchen_diy",
        "title": "Modern Minimalist Japandi Interior Architecture & Renovation Reveal",
        "uploader": "Aesthetic Spaces",
        "uploader_avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=AestheticSpaces",
        "channel_verified": False,
        "views": "820K views",
        "time_ago": "1 week ago",
        "duration": "1:15",
        "thumbnail": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&auto=format&fit=crop&q=80",
        "platform": "Pinterest",
        "platform_icon": "pinterest",
        "url": "https://www.pinterest.com/pin/123456789012345678/",
        "category": "Pinterest Video",
        "likes": "142K"
    },
    {
        "id": "twitter_ai_robotics",
        "title": "Autonomous Humanoid Robot Solves Rubik's Cube in Under 1 Second",
        "uploader": "TechBreakthroughs",
        "uploader_avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=TechBreakthroughs",
        "channel_verified": True,
        "views": "2.8M views",
        "time_ago": "12 hours ago",
        "duration": "0:30",
        "thumbnail": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&auto=format&fit=crop&q=80",
        "platform": "Twitter / X",
        "platform_icon": "twitter",
        "url": "https://x.com/tech/status/1838000000000000000",
        "category": "Twitter Clips",
        "likes": "310K"
    },
    {
        "id": "terabox_sample_archive",
        "title": "Nature Documentary Wildlife in Patagonia 4K UHD Master File",
        "uploader": "WildArchive_Cloud",
        "uploader_avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=WildArchive",
        "channel_verified": False,
        "views": "640K views",
        "time_ago": "4 days ago",
        "duration": "12:40",
        "thumbnail": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=800&auto=format&fit=crop&q=80",
        "platform": "Terabox",
        "platform_icon": "terabox",
        "url": "https://terabox.com/s/1patagonia_nature_4k",
        "category": "Terabox Files",
        "likes": "45K"
    },
    {
        "id": "fb_culinary_master",
        "title": "Street Food Masters: Crispy Woodfire Neapolitan Pizza in Napoli",
        "uploader": "Tasty Worldwide",
        "uploader_avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=TastyWorldwide",
        "channel_verified": True,
        "views": "9.1M views",
        "time_ago": "5 days ago",
        "duration": "5:20",
        "thumbnail": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=800&auto=format&fit=crop&q=80",
        "platform": "Facebook",
        "platform_icon": "facebook",
        "url": "https://www.facebook.com/watch/?v=987654321098765",
        "category": "Facebook Watch",
        "likes": "620K"
    },
    {
        "id": "tiktok_future_synth",
        "title": "Synthwave Cyberpunk Visualizer & Lo-Fi Beats to Relax / Study",
        "uploader": "NeonVibesAudio",
        "uploader_avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=NeonVibes",
        "channel_verified": True,
        "views": "5.6M views",
        "time_ago": "2 weeks ago",
        "duration": "3:45",
        "thumbnail": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=800&auto=format&fit=crop&q=80",
        "platform": "TikTok",
        "platform_icon": "tiktok",
        "url": "https://www.tiktok.com/@neonvibes/video/7300000000000000000",
        "category": "TikTok Viral",
        "likes": "1.1M"
    },
    {
        "id": "space_nebula_4k",
        "title": "James Webb Space Telescope Ultra Deep Field Exploration in 8K HDR",
        "uploader": "Cosmos Odyssey",
        "uploader_avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=CosmosOdyssey",
        "channel_verified": True,
        "views": "3.3M views",
        "time_ago": "1 month ago",
        "duration": "8:15",
        "thumbnail": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&auto=format&fit=crop&q=80",
        "platform": "YouTube",
        "platform_icon": "youtube",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "category": "YouTube 4K",
        "likes": "450K"
    }
]

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>OmniTube is loading...</h1>")
    return HTMLResponse(index_file.read_text(encoding="utf-8"))

@app.post("/api/extract")
async def handle_extract(payload: ExtractRequest):
    """
    Extracts high-resolution video metadata, thumbnails, and available formats
    from any supported platform URL.
    """
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    
    info = await extract_info(url)
    return info

@app.post("/api/download/start")
async def handle_download_start(payload: DownloadRequest):
    """
    Spawns background download and conversion task.
    Returns job_id for progress polling.
    """
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    
    job_id = await start_download_job(
        url=url,
        format_id=payload.format_id or "bestvideo+bestaudio/best",
        is_audio=payload.is_audio or False,
        title=payload.title or "Video"
    )
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/download/status/{job_id}")
async def handle_download_status(job_id: str):
    """
    Returns live progress, speed, ETA, and download link for a job.
    """
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Download job not found")
    return JOBS[job_id]

@app.api_route("/api/download/file/{job_id}", methods=["GET", "HEAD"])
async def handle_download_file(job_id: str):
    """
    Directly streams or downloads the finished MP4 or MP3 file.
    Checks memory state and disk cache.
    """
    file_path = None
    file_name = "download.mp4"
    is_audio = False

    if job_id in JOBS:
        job = JOBS[job_id]
        if job.get("status") == "completed":
            file_path = Path(job.get("file_path", ""))
            file_name = job.get("file_name", "download.mp4")
            is_audio = job.get("is_audio", False)
    
    if not file_path or not file_path.exists():
        job_dir = DOWNLOAD_DIR / job_id
        if job_dir.exists():
            files = list(job_dir.glob("*.*"))
            if files:
                file_path = files[0]
                file_name = file_path.name
                is_audio = file_path.suffix.lower() in [".mp3", ".m4a", ".aac", ".wav", ".opus"]
    
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Downloaded file not found on disk")
    
    clean_filename = re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', file_name)
    media_type = "audio/mpeg" if is_audio else "video/mp4"

    return FileResponse(
        path=str(file_path),
        filename=clean_filename,
        media_type=media_type
    )

class BotDownloadRequest(BaseModel):
    url: str
    type: Optional[str] = "video"  # "video" or "audio"

@app.post("/api/bot/download")
async def handle_bot_download(payload: BotDownloadRequest):
    """
    All-in-one endpoint designed specifically for Telegram bots.
    Accepts a media URL, extracts, converts, and returns the file path & details.
    """
    import asyncio
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    
    is_audio = payload.type.lower() == "audio"
    
    # 1. Extract metadata
    info = await extract_info(url)
    if not info.get("success", False) and info.get("error"):
        return {"success": False, "error": info.get("error")}
    
    title = info.get("title", "Media Download")
    format_id = "bestaudio/best" if is_audio else "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
    
    # 2. Trigger download
    job_id = await start_download_job(url, format_id, is_audio, title)
    
    # 3. Wait for completion (up to 90 seconds)
    for _ in range(180):
        await asyncio.sleep(0.5)
        if job_id in JOBS:
            job = JOBS[job_id]
            if job.get("status") == "completed":
                return {
                    "success": True,
                    "job_id": job_id,
                    "title": title,
                    "uploader": info.get("uploader", "Creator"),
                    "duration": info.get("duration", 0),
                    "duration_formatted": info.get("duration_formatted", "0:00"),
                    "thumbnail": info.get("thumbnail", ""),
                    "platform": info.get("platform", "Media"),
                    "file_path": job.get("file_path"),
                    "file_name": job.get("file_name"),
                    "file_size": job.get("file_size"),
                    "file_size_formatted": job.get("file_size_formatted"),
                    "download_url": f"/api/download/file/{job_id}",
                    "is_audio": is_audio
                }
            elif job.get("status") == "error":
                return {
                    "success": False,
                    "error": job.get("error", "Download failed")
                }
    
    return {
        "success": False,
        "error": "Download timed out."
    }

@app.get("/api/trending")
async def get_trending(category: Optional[str] = None):
    """
    Returns YouTube-like homepage feed with cross-platform media cards.
    """
    if not category or category.lower() in ["all", "trending"]:
        return {"items": TRENDING_ITEMS}
    
    filtered = [
        item for item in TRENDING_ITEMS
        if category.lower() in item.get("category", "").lower() or category.lower() in item.get("platform", "").lower()
    ]
    return {"items": filtered if filtered else TRENDING_ITEMS}

@app.get("/api/platforms")
async def get_supported_platforms():
    """
    Lists supported platforms with features and how-to guides.
    """
    platforms = [
        {
            "name": "YouTube",
            "icon": "youtube",
            "badge": "4K / 1080p / MP3",
            "formats": ["4K 2160p", "1080p 60fps", "720p", "MP3 320kbps"],
            "description": "Supports regular videos, YouTube Shorts, music tracks, live stream replays.",
            "sample": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        },
        {
            "name": "Instagram",
            "icon": "instagram",
            "badge": "Reels & Posts",
            "formats": ["1080p Full HD", "Reels MP4", "Audio Track"],
            "description": "Download Instagram Reels, public video posts, IGTV, and carousels with highest clarity.",
            "sample": "https://www.instagram.com/reel/C_example/"
        },
        {
            "name": "Facebook",
            "icon": "facebook",
            "badge": "Watch & Reels",
            "formats": ["HD 1080p", "SD 480p", "MP3 Audio"],
            "description": "Download Facebook Watch episodes, reels, public page videos without watermarks.",
            "sample": "https://www.facebook.com/watch/?v=123456789"
        },
        {
            "name": "Twitter / X",
            "icon": "twitter",
            "badge": "Clips & GIFs",
            "formats": ["1080p MP4", "720p MP4", "GIF / MP4"],
            "description": "Fast extraction of video tweets and clips from x.com and twitter.com.",
            "sample": "https://x.com/status/123456789"
        },
        {
            "name": "Pinterest",
            "icon": "pinterest",
            "badge": "Aesthetic Pins",
            "formats": ["1080p HD", "Original MP4"],
            "description": "Extract videos and story pins directly from Pinterest pin links (pin.it & pinterest.com).",
            "sample": "https://www.pinterest.com/pin/123456789/"
        },
        {
            "name": "Terabox",
            "icon": "terabox",
            "badge": "Cloud Storage",
            "formats": ["Original File", "HD Video Stream"],
            "description": "Bypass Terabox app requirements and download shared videos directly to your device.",
            "sample": "https://terabox.com/s/1abcdefg"
        },
        {
            "name": "TikTok",
            "icon": "tiktok",
            "badge": "No Watermark",
            "formats": ["Original HD MP4", "MP3 Audio Sound"],
            "description": "Download viral TikToks in high quality, including original audio sounds.",
            "sample": "https://www.tiktok.com/@user/video/123456789"
        },
        {
            "name": "Reddit",
            "icon": "reddit",
            "badge": "v.redd.it with Audio",
            "formats": ["Merged 1080p MP4", "720p HD", "Soundtrack"],
            "description": "Automatically merges separate video and audio streams into a single high quality MP4.",
            "sample": "https://www.reddit.com/r/videos/comments/..."
        },
        {
            "name": "SoundCloud",
            "icon": "soundcloud",
            "badge": "High Bitrate MP3",
            "formats": ["320kbps MP3", "Original Audio", "Album Art"],
            "description": "Rip and save music tracks, playlists, and podcast episodes in high fidelity MP3.",
            "sample": "https://soundcloud.com/artist/track"
        },
        {
            "name": "Vimeo & 1000+ More",
            "icon": "vimeo",
            "badge": "1000+ Platforms",
            "formats": ["Full HD 1080p", "4K Ultra HD", "MP4 / WEBM"],
            "description": "Supports Twitch clips, DailyMotion, Bilibili, Rumble, and 1,000+ video hosting sites.",
            "sample": "https://vimeo.com/123456789"
        }
    ]
    return {"platforms": platforms}

@app.get("/api/history")
async def get_history():
    """
    Returns list of all recent download tasks in the session.
    """
    history = list(JOBS.values())
    history.reverse()
    return {"history": history}

@app.get("/api/proxy/thumbnail")
async def proxy_thumbnail(url: str = Query(...)):
    """
    Proxies remote thumbnails that restrict hotlinking (e.g. Instagram/FB CDN).
    """
    if not url or not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://www.instagram.com/"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            content_type = resp.headers.get("content-type", "image/jpeg")
            return StreamingResponse(resp.aiter_bytes(), media_type=content_type)
    except Exception as e:
        # Fallback to standard placeholder
        raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")

class CookiePayload(BaseModel):
    cookies_text: str

@app.get("/api/cookies/status")
async def get_cookie_status():
    from downloader import COOKIES_FILE
    if COOKIES_FILE.exists() and COOKIES_FILE.stat().st_size > 10:
        lines = [line for line in COOKIES_FILE.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip() and not line.startswith("#")]
        return {
            "has_cookies": True,
            "cookie_count": len(lines),
            "file_size": COOKIES_FILE.stat().st_size
        }
    return {"has_cookies": False, "cookie_count": 0, "file_size": 0}

@app.post("/api/cookies/save")
async def save_cookies(payload: CookiePayload):
    from downloader import COOKIES_FILE
    text = payload.cookies_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Cookies content cannot be empty")
    COOKIES_FILE.write_text(text, encoding="utf-8")
    lines = [line for line in text.splitlines() if line.strip() and not line.startswith("#")]
    return {"success": True, "cookie_count": len(lines)}

@app.post("/api/cookies/clear")
async def clear_cookies():
    from downloader import COOKIES_FILE
    if COOKIES_FILE.exists():
        COOKIES_FILE.unlink()
    return {"success": True}

class ProxyPayload(BaseModel):
    proxy_url: str

@app.get("/api/proxy/status")
async def get_proxy_status():
    from downloader import get_proxy, PROXY_FILE
    proxy = get_proxy()
    return {
        "has_proxy": bool(proxy),
        "proxy": proxy or "",
        "source": "env" if (os.getenv("YTDL_PROXY") or os.getenv("HTTP_PROXY")) else "file" if PROXY_FILE.exists() else "none"
    }

@app.post("/api/proxy/save")
async def save_proxy(payload: ProxyPayload):
    from downloader import PROXY_FILE
    proxy = payload.proxy_url.strip()
    if not proxy:
        raise HTTPException(status_code=400, detail="Proxy URL cannot be empty")
    PROXY_FILE.write_text(proxy, encoding="utf-8")
    return {"success": True, "proxy": proxy}

@app.post("/api/proxy/clear")
async def clear_proxy():
    from downloader import PROXY_FILE
    if PROXY_FILE.exists():
        PROXY_FILE.unlink()
    return {"success": True}
