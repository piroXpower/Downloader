# 🎬 VidTube - YouTube-Style Video Platform & Universal Social Media Downloader

**VidTube** is a full-stack media platform featuring a modern YouTube dark/light interface combined with an **all-in-one universal media downloader engine** capable of downloading videos, reels, clips, pins, and files from **Instagram, YouTube, Facebook, Twitter (X), Pinterest, Terabox, TikTok, Reddit, Vimeo, SoundCloud**, and 1,000+ additional sources.

---

## 🌟 Key Features

### 1. 📺 Pixel-Perfect YouTube UI & Experience
- **Header**: YouTube Red logo, universal search & paste input bar, 1-click clipboard paste shortcut, notifications center, dark/light theme switch, user avatar menu.
- **Sidebar (Collapsible)**: Home, Shorts & Reels, Downloads Manager, Supported Platforms directory, History, Liked Videos, and quick platform filter buttons.
- **Top Filter Chips**: Dynamic filtering ("All", "Trending", "YouTube 4K", "Instagram Reels", "Twitter Clips", "Facebook Watch", "Pinterest Pins", "Terabox Files", "TikTok Viral", "Music & MP3").
- **YouTube Watch Page (`/watch`)**:
  - Embedded player with HTML5 streaming and custom control features.
  - Video title, platform badge, verified channel row, subscribe/subscribed button.
  - Interactive Action pills: Like (with counter), Dislike, Share (copies URL to clipboard), **Prominent Red Download Pill**, Save.
  - Expandable description box with hashtags, views, and upload timestamp.
  - Full comments section with real-time public commenting, like counts, and reply action.
  - "Up Next" / Related recommendations column.
- **Shorts / Reels View**:
  - Full-height 9:16 vertical player like YouTube Shorts & Instagram Reels.
  - Direct 1-click "Download Reel" action button.

### 2. ⚡ Universal All-in-One Downloader Engine
- **Supported Platforms**:
  - **YouTube**: 4K (2160p), 1440p, 1080p 60fps, 720p, 480p, 360p MP4, and 320kbps MP3 audio.
  - **Instagram**: Reels, public video posts, IGTV, and stories in original 1080p clarity.
  - **Facebook**: Facebook Watch episodes, reels, public videos without watermarks.
  - **Twitter / X**: Video tweets and clips from x.com and twitter.com.
  - **Pinterest**: Video pins and story pins from `pinterest.com` and `pin.it`.
  - **Terabox**: Cloud storage link resolution and direct media downloading.
  - **TikTok**: HD MP4 downloads without watermarks + original audio extraction.
  - **Reddit**: Merges separate `v.redd.it` video and audio streams seamlessly with FFmpeg.
  - **SoundCloud & Music**: High-bitrate MP3 extractions.
  - **1,000+ More**: Twitch clips, Vimeo, DailyMotion, Bilibili, and any yt-dlp supported source.

### 3. 🛠️ Technology Stack
- **Backend**: Python 3.14 + FastAPI + Uvicorn (high-performance asynchronous REST API)
- **Downloader Core**: `yt-dlp` + Node.js JS runtime + `ffmpeg 8.0` for stream merging & MP3 audio conversion
- **Cloud Resolver**: Custom Terabox parser & gateway
- **Frontend**: YouTube-styled HTML5, CSS3 variables (Dark/Light mode), and Vanilla JavaScript (zero heavy build dependencies)

---

## 🚀 Running the Application

### Start Server:
```bash
cd /root/omnitube
./run.sh
```

Or manually:
```bash
/root/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at:
`http://localhost:8000`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the main YouTube web app |
| `POST` | `/api/extract` | Extracts video metadata, thumbnail, duration, and available quality formats from any URL |
| `POST` | `/api/download/start` | Initiates asynchronous video/audio download and conversion job |
| `GET` | `/api/download/status/{job_id}` | Polls real-time progress %, download speed, ETA, and status |
| `GET` | `/api/download/file/{job_id}` | Downloads or streams the converted MP4 / MP3 file with proper headers |
| `GET` | `/api/trending` | Returns curated cross-platform trending video catalog |
| `GET` | `/api/platforms` | Returns list of supported platforms and sample links |
| `GET` | `/api/history` | Lists recent download jobs |
