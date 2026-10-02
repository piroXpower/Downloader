# 🎮 Telegram Game Hub (1,000+ Games Bot & Mini App)

A full-featured Telegram Gaming platform modeled after **Gamee**, featuring **1,000+ built-in and curated games**, a sleek **Telegram Mini App (Web App)**, high-score leaderboards, favorites, and **inline query sharing** to play and challenge friends in any Telegram chat.

---

## 🌟 Key Features

- **🕹️ 1,000+ Games Catalog:**
  - **Arcade (130 games):** Brick Breakers, Neon Runners, Pinball, Bounce Ball, Orbit Dodge, etc.
  - **Puzzle (130 games):** 2048 Neon, Sudoku, Block Collapse, Water Sort, Match 3, Brain Out, etc.
  - **Action (130 games):** Space Blaster, Galaxy Defender, Alien Swarm, Shadow Knight, etc.
  - **Racing (125 games):** Turbo Drift, Moto Extreme, Highway Speed, Formula Dash, Kart Mania, etc.
  - **Sports (125 games):** Neon Pong, Penalty Kick, Basketball Slam, 8 Ball Pool, Bowling, etc.
  - **Retro (120 games):** Retro Snake 97, Space Invaders 80s, Pong 1972, Tetromino Classic, etc.
  - **Cards & Board (120 games):** Tic Tac Toe Cyber, Solitaire, Chess 3D, Checkers, Uno Party, etc.
  - **Casual (120 games):** Flappy Wing 2.0, Tower Stack 3D, Speed Tap Frenzy, Fruit Slicer, etc.

- **⚡ Instant Built-in Playable Mini-Games:**
  Zero external loading lag. Directly playable offline inside Telegram:
  1. `2048 Neon Deluxe` - Tile merging with swipe & keyboard support
  2. `Flappy Wing 2.0` - Physics flapper with pipe obstacles & high-score tracking
  3. `Retro Snake 97` - Classic Nokia CRT snake with on-screen D-pad
  4. `Neon Pong Arena` - Fast table tennis vs intelligent AI bot
  5. `Space Blaster 3000` - Space shooter with auto-fire, shields, & particle effects
  6. `Tetris Block Master` - Falling block puzzle with rotation, line clears, & score combos
  7. `Memory Matrix Flip` - Cyber card matching with timer & move counter
  8. `Tic Tac Toe Cyber` - Glow board with Minimax smart AI & 2-player mode
  9. `Tower Stack 3D` - Precision stacking game with dynamic block slicing
  10. `Speed Tap Frenzy` - 15-second reflex frenzy clicker with combo multipliers
  11. `Universal Web Runner` - Dynamic high-speed arcade engine for the remaining catalog games

- **📱 Telegram Mini App (Web App):**
  - Modern dark cyberpunk UI optimized for 60fps mobile browsers.
  - Instant real-time search across all 1,000 games.
  - Category selector tabs with play counters.
  - In-app modal player with Fullscreen, Close, and Telegram Share buttons.
  - Score sync: automatically syncs high scores from games to the database.
  - Personal favorites/bookmarks stored locally & in the cloud database.

- **🤖 Telegram Bot Features:**
  - `/start` - Welcome card with direct "⚡ PLAY 1,000+ GAMES 🎮" WebApp button.
  - `/games` - Interactive category browser with pagination.
  - `/search <keyword>` - Instant in-chat search through all 1,000 games.
  - `/random` - Launches a surprise random game.
  - `/leaderboard` - Displays top global players and personal rank.
  - `/profile` - Player profile with score, rank, and game stats.
  - **Inline Mode (`@BotUsername <query>`):** Type your bot username in any Telegram group or private chat to share playable game cards with friends (just like Gamee).

---

## 📁 Project Structure

```
telegram_game_bot/
├── config.py                 # Configuration settings and environment variables
├── database.py               # Async SQLite database (users, scores, favorites, stats)
├── main.py                   # Unified runner for FastAPI WebApp & Telegram Bot
├── requirements.txt          # Python dependencies
├── .env                      # Bot token and server config
├── .env.example              # Template configuration
├── data/
│   ├── games_catalog.py      # 1,000 games catalog generator
│   ├── games.json            # 1,000 games database
│   └── games_bot.db          # SQLite database (auto-created on first run)
├── bot/
│   ├── handlers.py           # Commands, callbacks, and inline query handlers
│   └── keyboards.py          # Keyboards with WebAppInfo integration
└── webapp/
    ├── server.py             # FastAPI REST API & static file server
    └── static/
        ├── index.html        # Telegram Mini App frontend
        ├── css/style.css     # Cyberpunk responsive styling
        ├── js/app.js         # Mini App logic & score bridge
        └── games/            # Built-in HTML5 canvas games
            ├── 2048/
            ├── flappy/
            ├── snake/
            ├── pong/
            ├── space_blaster/
            ├── tetris/
            ├── memory/
            ├── tictactoe/
            ├── tower_stack/
            ├── speed_clicker/
            └── web_runner/
```

---

## 🚀 Quick Start Guide

### 1. Configure Telegram Bot with @BotFather

1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the instructions to pick a name and username.
3. Save the **Bot Token** provided by BotFather.
4. **Enable Inline Mode (for game sharing):**
   - Send `/setinline` to @BotFather.
   - Select your bot.
   - Set a placeholder text, e.g., `Search 1,000+ games...`.
5. **Configure the Menu Button (Optional, for instant WebApp launch):**
   - Send `/setmenubutton` to @BotFather.
   - Select your bot, choose "Configure menu button", enter button text `🎮 Games`, and paste your HTTPS WebApp URL.

### 2. Configure `.env`

Edit `/root/telegram_game_bot/.env`:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxyz
BOT_USERNAME=YourBotUsernameWithoutAt
WEBAPP_URL=https://your-domain-or-ngrok-url.com
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
```

> **Note for Telegram WebApps:** Telegram requires an **HTTPS** URL to open WebApps inside the mobile Telegram app. For local development or testing, use a free tunnel (see section below).

### 3. Start the Server and Bot

```bash
# Activate your virtual environment
source /root/venv/bin/activate

# Navigate to the bot directory
cd /root/telegram_game_bot

# Run the unified server
python main.py
```

The console will show:
```
🌐 Telegram Mini App & API server starting at http://0.0.0.0:8080
🤖 Bot connected successfully as @YourBotUsername
🎮 Bot polling started. Ready to serve 1,000+ games!
```

---

## 🌐 Setting Up an HTTPS URL for Telegram WebApp

### Option A: Free Cloudflare Tunnel (Recommended)
```bash
# Install cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Run temporary quick tunnel to port 8080
cloudflared tunnel --url http://localhost:8080
```
Copy the generated `https://xxxx.trycloudflare.com` URL into `WEBAPP_URL` in `.env`.

### Option B: Free ngrok Tunnel
```bash
# Start ngrok tunnel
ngrok http 8080
```
Copy the HTTPS URL into `WEBAPP_URL` in `.env`.

---

## 🎮 How to Use the Bot

| Action | How to Trigger | Description |
|---|---|---|
| **Launch 1,000 Games** | Send `/start` and tap `⚡ PLAY 1,000+ GAMES 🎮` | Opens full Telegram Mini App with search, categories & games |
| **Search Games** | Send `/search 2048` or `/search racer` | Searches all 1,000 games and returns playable cards |
| **Random Game** | Send `/random` | Picks a surprise game with instant play button |
| **Browse Categories** | Send `/games` | Interactive category browser with pagination |
| **Leaderboard** | Send `/leaderboard` | Shows top 10 global players and total scores |
| **Profile** | Send `/profile` | Shows your total score, global rank, and high scores |
| **Challenge Friends** | Type `@YourBotName flappy` in any chat | Sends inline game card for friends to play |

---

## ⚙️ Running in the Background (Systemd Service)

To keep your bot running 24/7 on your Linux VPS:

Create `/etc/systemd/system/telegram-game-bot.service`:
```ini
[Unit]
Description=Telegram Game Bot & Mini App Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/telegram_game_bot
ExecStart=/root/venv/bin/python /root/telegram_game_bot/main.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
systemctl daemon-reload
systemctl enable telegram-game-bot
systemctl start telegram-game-bot
systemctl status telegram-game-bot
```
