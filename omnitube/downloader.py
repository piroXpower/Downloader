"""
OmniTube Core Downloader & Metadata Extraction Engine.
Powered by yt-dlp, ffmpeg, and custom resolvers for 1000+ social platforms.
"""
import os
import re
import uuid
import asyncio
import logging
import urllib.parse
from typing import Dict, Any, List, Optional
from pathlib import Path
import yt_dlp

from terabox_handler import is_terabox_url, resolve_terabox

logger = logging.getLogger("downloader")
logging.basicConfig(level=logging.INFO)

DOWNLOAD_DIR = Path("/root/omnitube/downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Active background download jobs: job_id -> dict
JOBS: Dict[str, Dict[str, Any]] = {}

def detect_platform(url: str) -> tuple[str, str]:
    """Returns (platform_name, platform_icon_key)"""
    url_lower = url.lower()
    if is_terabox_url(url):
        return ("Terabox", "terabox")
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return ("YouTube", "youtube")
    if "instagram.com" in url_lower:
        return ("Instagram", "instagram")
    if "facebook.com" in url_lower or "fb.watch" in url_lower or "fb.com" in url_lower:
        return ("Facebook", "facebook")
    if "twitter.com" in url_lower or "x.com" in url_lower:
        return ("Twitter / X", "twitter")
    if "pinterest.com" in url_lower or "pin.it" in url_lower:
        return ("Pinterest", "pinterest")
    if "tiktok.com" in url_lower:
        return ("TikTok", "tiktok")
    if "reddit.com" in url_lower or "redd.it" in url_lower:
        return ("Reddit", "reddit")
    if "soundcloud.com" in url_lower:
        return ("SoundCloud", "soundcloud")
    if "vimeo.com" in url_lower:
        return ("Vimeo", "vimeo")
    if "twitch.tv" in url_lower:
        return ("Twitch", "twitch")
    if "dailymotion.com" in url_lower or "dai.ly" in url_lower:
        return ("Dailymotion", "dailymotion")
    return ("Web Media", "globe")

def format_bytes(size: Optional[int]) -> str:
    if not size or size <= 0:
        return "~"
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.1f} {power_labels.get(n, '')}"

def format_duration(seconds: Optional[int]) -> str:
    if not seconds or seconds <= 0:
        return "0:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def format_count(count: Optional[int]) -> str:
    if not count:
        return "0"
    if count >= 1_000_000_000:
        return f"{count / 1_000_000_000:.1f}B"
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)

COOKIES_FILE = Path("/root/omnitube/cookies.txt")
PROXY_FILE = Path("/root/omnitube/proxy.txt")

def get_cookie_path() -> Optional[str]:
    if COOKIES_FILE.exists() and COOKIES_FILE.stat().st_size > 10:
        return str(COOKIES_FILE)
    return None

def get_proxy() -> Optional[str]:
    proxy = os.getenv("YTDL_PROXY") or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
    if proxy:
        return proxy.strip()
    if PROXY_FILE.exists() and PROXY_FILE.stat().st_size > 4:
        content = PROXY_FILE.read_text(encoding="utf-8").strip()
        if content and (content.startswith("http://") or content.startswith("https://") or content.startswith("socks5://") or content.startswith("socks4://")):
            return content
    return None

def get_base_ydl_opts(player_clients: Optional[List[str]] = None) -> dict:
    clients = player_clients or ['android', 'ios', 'mweb', 'web']
    opts = {
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'js_runtimes': {'node': {'path': '/usr/bin/node'}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'extractor_args': {
            'youtube': {
                'player_client': clients,
            }
        }
    }
    cookie_path = get_cookie_path()
    if cookie_path:
        opts['cookiefile'] = cookie_path
    
    proxy = get_proxy()
    if proxy:
        opts['proxy'] = proxy
    return opts

def extract_metadata_sync(url: str) -> dict:
    """
    Synchronous metadata extraction using yt-dlp with multi-client anti-bot fallback.
    Tries android/ios/mweb/web clients in order to bypass 'Sign in to confirm you are not a bot'.
    """
    client_strategies = [
        ['android', 'ios', 'web'],
        ['ios', 'mweb'],
        ['android'],
        ['web']
    ]
    
    last_error = None
    for strategy in client_strategies:
        opts = get_base_ydl_opts(player_clients=strategy)
        opts.update({
            'extract_flat': False,
            'skip_download': True,
        })
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    return info
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            # If bot error, try next client strategy
            if "bot" in err_str or "sign in" in err_str or "confirm" in err_str:
                logger.warning(f"Bot detection hit on strategy {strategy}, trying alternative client...")
                continue
            else:
                # If non-bot fatal error, re-raise or break
                logger.warning(f"Strategy {strategy} failed: {e}")
                continue

    if last_error:
        raise last_error
    raise RuntimeError("Failed to extract metadata with all client strategies.")

async def extract_info(url: str) -> dict:
    """Async wrapper that extracts clean metadata and formats."""
    url = url.strip()
    platform_name, platform_icon = detect_platform(url)

    # Check for Terabox
    if is_terabox_url(url):
        return await resolve_terabox(url)

    loop = asyncio.get_running_loop()
    try:
        raw_info = await loop.run_in_executor(None, extract_metadata_sync, url)
    except Exception as e:
        err_msg = str(e)
        logger.error(f"yt-dlp extract failed for {url}: {err_msg}")
        is_bot = "sign in to confirm" in err_msg.lower() or "not a bot" in err_msg.lower() or "bot" in err_msg.lower()
        clean_err = (
            "YouTube Bot Check Detected: 'Sign in to confirm you're not a bot'. You can bypass this immediately by adding your cookies.txt in the Anti-Bot Manager (top right)."
            if is_bot else f"Could not extract media info: {err_msg}"
        )
        return {
            "success": False,
            "error": clean_err,
            "is_bot_error": is_bot,
            "url": url,
            "platform": platform_name
        }

    # Extract best thumbnail
    thumbnail = raw_info.get("thumbnail") or ""
    if not thumbnail and raw_info.get("thumbnails"):
        thumbnail = raw_info["thumbnails"][-1].get("url", "")

    # Video stream url for in-browser playback
    stream_url = ""
    # Process formats
    raw_formats = raw_info.get("formats", [])
    
    # Organize video and audio formats
    video_formats = []
    audio_formats = []
    seen_heights = set()
    seen_audio = set()

    # Find playable progressive stream URL if available
    for f in reversed(raw_formats):
        if f.get("vcodec") != "none" and f.get("acodec") != "none" and f.get("url"):
            stream_url = f.get("url")
            break
    if not stream_url and raw_formats:
        for f in reversed(raw_formats):
            if f.get("url") and "http" in f.get("url", ""):
                stream_url = f.get("url")
                break

    # Categorize formats
    for f in raw_formats:
        f_id = f.get("format_id")
        ext = f.get("ext", "mp4")
        filesize = f.get("filesize") or f.get("filesize_approx")
        height = f.get("height")
        vcodec = f.get("vcodec", "none")
        acodec = f.get("acodec", "none")
        fps = f.get("fps")

        # Audio-only format
        if vcodec == "none" and acodec != "none":
            abr = f.get("abr") or 128
            abr_key = int(abr)
            if abr_key not in seen_audio and abr_key > 32:
                seen_audio.add(abr_key)
                audio_formats.append({
                    "format_id": f_id,
                    "ext": "mp3" if ext in ["m4a", "webm", "opus"] else ext,
                    "quality": f"Audio MP3 ({int(abr)} kbps)",
                    "type": "audio",
                    "bitrate": f"{int(abr)} kbps",
                    "filesize_formatted": format_bytes(filesize),
                    "note": f.get("format_note") or f"{int(abr)}k",
                    "direct_url": f.get("url") if "http" in (f.get("url") or "") else None
                })

        # Video format
        elif height and height > 140:
            # We want unique standard resolutions: 2160p (4K), 1440p (2K), 1080p, 720p, 480p, 360p, 240p
            target_bucket = (
                2160 if height >= 2160 else
                1440 if height >= 1440 else
                1080 if height >= 1080 else
                720 if height >= 720 else
                480 if height >= 480 else
                360 if height >= 360 else
                240
            )

            if target_bucket not in seen_heights:
                seen_heights.add(target_bucket)
                res_title = {
                    2160: "4K Ultra HD (2160p)",
                    1440: "2K Quad HD (1440p)",
                    1080: "Full HD (1080p)",
                    720: "HD (720p)",
                    480: "Standard (480p)",
                    360: "Medium (360p)",
                    240: "Low (240p)"
                }.get(target_bucket, f"{height}p")

                # If format has no audio, yt-dlp will automatically merge with bestaudio on download
                video_formats.append({
                    "format_id": f"bestvideo[height<={target_bucket}]+bestaudio/best[height<={target_bucket}]/best",
                    "single_format_id": f_id,
                    "ext": "mp4",
                    "resolution": res_title,
                    "height": target_bucket,
                    "type": "video",
                    "fps": fps or 30,
                    "filesize_formatted": format_bytes(filesize),
                    "has_audio": acodec != "none",
                    "direct_url": f.get("url") if (acodec != "none" and "http" in (f.get("url") or "")) else None
                })

    # Sort video formats highest quality first
    video_formats.sort(key=lambda x: x.get("height", 0), reverse=True)
    
    # If no video formats parsed, add a universal best fallback
    if not video_formats:
        video_formats.append({
            "format_id": "bestvideo+bestaudio/best",
            "ext": "mp4",
            "resolution": "Best Available Quality",
            "height": 1080,
            "type": "video",
            "filesize_formatted": "Auto",
            "has_audio": True,
            "direct_url": stream_url
        })

    # Always ensure standard MP3 option is present
    if not any("320" in a.get("quality", "") or "High" in a.get("quality", "") for a in audio_formats):
        audio_formats.insert(0, {
            "format_id": "bestaudio/best",
            "ext": "mp3",
            "quality": "Best Audio (320 kbps MP3)",
            "type": "audio",
            "bitrate": "320 kbps",
            "filesize_formatted": "~5-10 MB",
            "note": "Ultra High Quality MP3",
            "convert_mp3": True
        })

    duration_sec = raw_info.get("duration") or 0
    duration_str = format_duration(duration_sec)

    return {
        "success": True,
        "id": raw_info.get("id") or str(uuid.uuid4())[:8],
        "title": raw_info.get("title") or "Video",
        "description": raw_info.get("description") or "",
        "uploader": raw_info.get("uploader") or raw_info.get("channel") or raw_info.get("creator") or platform_name,
        "uploader_url": raw_info.get("uploader_url") or raw_info.get("channel_url") or "",
        "channel_avatar": f"https://api.dicebear.com/7.x/identicon/svg?seed={urllib.parse.quote(raw_info.get('uploader') or 'creator')}",
        "thumbnail": thumbnail,
        "duration": duration_sec,
        "duration_formatted": duration_str,
        "views": format_count(raw_info.get("view_count")),
        "likes": format_count(raw_info.get("like_count")),
        "upload_date": raw_info.get("upload_date") or "",
        "platform": platform_name,
        "platform_icon": platform_icon,
        "url": url,
        "video_formats": video_formats,
        "audio_formats": audio_formats,
        "stream_url": stream_url
    }

def run_download_task(job_id: str, url: str, format_spec: str, is_audio: bool, title: str):
    """Executes yt-dlp download in background with progress callbacks."""
    out_dir = DOWNLOAD_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(out_dir / "%(title).100s.%(ext)s")

    def progress_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0
            percent = (downloaded / total * 100) if total > 0 else 0
            speed = d.get('speed') or 0
            eta = d.get('eta') or 0
            JOBS[job_id].update({
                "status": "downloading",
                "progress": round(percent, 1),
                "speed": f"{format_bytes(speed)}/s" if speed else "--",
                "eta": f"{eta}s" if eta else "--",
                "downloaded_bytes": downloaded,
                "total_bytes": total,
                "downloaded_formatted": format_bytes(downloaded),
                "total_formatted": format_bytes(total)
            })
        elif d['status'] == 'finished':
            JOBS[job_id]["status"] = "processing"
            JOBS[job_id]["progress"] = 99.0

    opts = get_base_ydl_opts()
    opts.update({
        'outtmpl': out_template,
        'progress_hooks': [progress_hook],
        'merge_output_format': 'mp4',
    })

    if is_audio:
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        })
    else:
        # Format spec: bestvideo+bestaudio or specified format
        opts.update({
            'format': format_spec if format_spec else 'bestvideo+bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        })

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # Find output file
        downloaded_files = list(out_dir.glob("*.*"))
        if downloaded_files:
            target_file = downloaded_files[0]
            file_size = target_file.stat().st_size
            JOBS[job_id].update({
                "status": "completed",
                "progress": 100.0,
                "file_path": str(target_file),
                "file_name": target_file.name,
                "file_size": file_size,
                "file_size_formatted": format_bytes(file_size),
                "download_url": f"/api/download/file/{job_id}"
            })
            logger.info(f"Download completed for job {job_id}: {target_file.name}")
        else:
            JOBS[job_id].update({
                "status": "error",
                "error": "File was not generated by downloader."
            })
    except Exception as e:
        logger.error(f"Download failed for job {job_id}: {e}")
        JOBS[job_id].update({
            "status": "error",
            "error": str(e)
        })

async def start_download_job(url: str, format_id: str, is_audio: bool, title: str) -> str:
    """Initiates an async background download job and returns job_id."""
    job_id = str(uuid.uuid4())[:12]
    platform_name, platform_icon = detect_platform(url)

    JOBS[job_id] = {
        "job_id": job_id,
        "url": url,
        "title": title or "Media File",
        "platform": platform_name,
        "platform_icon": platform_icon,
        "is_audio": is_audio,
        "status": "queued",
        "progress": 0.0,
        "speed": "--",
        "eta": "--",
        "file_name": "",
        "download_url": ""
    }

    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, run_download_task, job_id, url, format_id, is_audio, title)
    return job_id
