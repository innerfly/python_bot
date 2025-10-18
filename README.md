# Telegram YouTube Downloader Bot

A simple Telegram bot that downloads videos or extracts audio from YouTube links using yt-dlp and exposes the downloaded files via a public URL you host.

The bot provides two commands:
- /v <youtube_url> — download the full video
- /a <youtube_url> — download audio only (MP3)


## Features
- Uses yt-dlp for reliable YouTube downloading
- Optional audio-only extraction via ffmpeg
- Generates a public download link based on your configured domain
- Asynchronous, built on python-telegram-bot v20+


## Prerequisites
- Python 3.10+
- Telegram Bot Token (from @BotFather)
- System packages:
  - yt-dlp
  - ffmpeg
- A publicly accessible domain or URL to serve the downloaded files (e.g., Nginx serving a directory)


### Install yt-dlp and ffmpeg
- Debian/Ubuntu:
  - sudo apt update && sudo apt install -y yt-dlp ffmpeg
- Fedora:
  - sudo dnf install -y yt-dlp ffmpeg
- Arch:
  - sudo pacman -S yt-dlp ffmpeg
- macOS (Homebrew):
  - brew install yt-dlp ffmpeg


## Get a Telegram Bot Token from BotFather
1. Open Telegram and start a chat with @BotFather.
2. Send the command /newbot and follow the prompts (choose a name and a username).
3. BotFather will reply with an HTTP API token — copy this token; you will use it as BOT_TOKEN.
4. You can also set your bot description, profile photo, and commands via BotFather if you wish.


## Environment Variables
Create a .env file in the project root or provide these variables via your environment.

Required variables:
- BOT_TOKEN — the token from @BotFather
- DOWNLOAD_DOMAIN — the base public URL from which your files will be served (e.g., https://files.example.com)
- DOWNLOAD_PATH — absolute path on the server where the bot will write files (this directory must be served by your web server)


Notes:
- The bot will create the DOWNLOAD_PATH directory if it doesn’t exist.
- Ensure your web server (e.g., Nginx/Apache/Caddy) serves DOWNLOAD_PATH at DOWNLOAD_DOMAIN so that generated links are reachable.


## Installation
1. Clone the repository:
   git clone https://github.com/innerfly/yt-dlp-telegram-bot.git
   cd yt-dlp-telegram-bot

2. Create and activate a virtual environment (recommended):
   python -m venv .venv
   source .venv/bin/activate

3. Install Python dependencies:
   pip install -r requirements.txt

4. Ensure yt-dlp and ffmpeg are installed at the system level (see above).

5. Set environment variables (via .env or your process manager) as described.


## Running the bot
- python bot.py

- Use a process manager (supervisor, systemd, docker, etc.) to keep the bot running.

The bot will start polling. In your Telegram client, message your bot `/v <youtube_url>`, and if the download succeeds, the bot replies with a public link like:
https://files.example.com/Some_Title-VIDEOID.mp4


## Security considerations
- Downloads are publicly accessible if your DOWNLOAD_DOMAIN is public. Consider periodic cleanup or restricted access if necessary.
- Never commit your .env or bot token to version control.

