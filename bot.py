import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    filename='log.log',
    format='%(asctime)s %(levelname)s - %(name)s - %(message)s'
)

DOMAIN = os.getenv("DOWNLOAD_DOMAIN")
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH")
CLEANING_INTERVAL_DAYS = int(os.getenv("CLEANING_INTERVAL_DAYS"))

Path(DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)

FILE_PATH = f"{DOWNLOAD_PATH}/%(title)s-%(id)s.%(ext)s"

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming URL messages and show video/audio buttons."""
    url = update.message.text.strip()

    # Store URL in user data for later use
    context.user_data['url'] = url

    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("audio", callback_data="audio"),
            InlineKeyboardButton("video", callback_data="video")
        ]
    ])

    await update.message.reply_text(
        "Choose an option:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks for video/audio download."""
    query = update.callback_query
    await query.answer()

    url = context.user_data.get('url')
    if not url:
        await query.edit_message_text("Error: URL not found. Please send the video URL again.")
        return

    choice = query.data

    try:
        filename = await _check_url(url, FILE_PATH)
        if filename is None:
            await query.edit_message_text("Failed to analyze the video URL. Please check the link and try again.")
            return

        if choice == "video":
            await query.edit_message_text("Downloading video... This may take a minute.")

            code, out, err = await _run_command(
                "yt-dlp",
                "--restrict-filenames",
                "-o",
                FILE_PATH,
                url,
            )
        elif choice == "audio":
            await query.edit_message_text("Downloading and extracting audio... This may take a minute.")

            code, out, err = await _run_command(
                "yt-dlp",
                "--format",
                "bestaudio",
                "--extract-audio",
                "--audio-format",
                "mp3",
                "--restrict-filenames",
                "-o",
                FILE_PATH,
                url,
            )

        if code != 0:
            logging.error("yt-dlp download failed: code=%s, err=%s", code, err)
            await query.message.edit_reply_markup(reply_markup=None)
            await query.message.edit_text("Download failed. The video may be unavailable or blocked.")
            return

        download_url, size = await _get_link(query, filename)
        if download_url:
            await query.message.edit_reply_markup(reply_markup=None)
            await query.message.edit_text(f"Done! Download link: {download_url}\nFile size: {size:.2f} MB")

    except Exception as e:
        logging.exception("Unhandled error in button_callback")
        await query.message.edit_reply_markup(reply_markup=None)
        await query.message.edit_text("Unexpected error while processing the request.")


async def _run_command(*args: str) -> tuple[int, str, str]:
    """Run a command asynchronously and return (code, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_b, stderr_b = await proc.communicate()
    return proc.returncode, stdout_b.decode().strip(), stderr_b.decode().strip()


async def _check_url(url: str, file_path: str):
    # Compute the final filename without downloading
    code, filename, err = await _run_command(
        "yt-dlp",
        "--restrict-filenames",
        "-o",
        file_path,
        "--get-filename",
        url,
    )

    if code != 0 or not filename:
        logging.error("yt-dlp --get-filename failed: code=%s, err=%s", code, err)
        return None

    return filename


async def _get_link(query, filename: str) -> tuple[str, float]|None:
    file_path = Path(filename)
    if not file_path.exists():
        # Try to locate the downloaded file within DOWNLOAD_PATH (edge cases with extensions)
        try:
            vid_id = file_path.stem.split("-")[-1]
            matches = list(Path(DOWNLOAD_PATH).glob(f"*-{vid_id}.*"))
            if matches:
                file_path = matches[0]
        except Exception as e:
            logging.error(f"Error finding downloaded file: {e}")
            pass

    if not file_path.exists():
        await query.edit_message_text("Downloaded, but could not locate the file. Please try again later.")
        return None

    file_size = os.path.getsize(file_path)
    size_mb = file_size / (1024 * 1024)

    public_url = f"{DOMAIN.rstrip('/')}/{file_path.name}"

    return public_url, size_mb


app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()


async def _cleanup_old_files() -> None:
    if CLEANING_INTERVAL_DAYS == 0:
        return

    try:
        threshold = datetime.now().timestamp() - CLEANING_INTERVAL_DAYS * 24 * 60 * 60
        base = Path(DOWNLOAD_PATH)
        if not base.exists():
            return
        removed = 0
        for p in base.iterdir():
            try:
                # Only consider regular files
                if not p.is_file():
                    continue
                # Skip files that are currently being written by yt-dlp (temporary .part files)
                if p.suffix == ".part":
                    continue
                mtime = p.stat().st_mtime
                if mtime < threshold:
                    p.unlink(missing_ok=True)
                    removed += 1
            except Exception as e:
                logging.warning("Failed to consider/remove %s: %s", p, e)
        if removed:
            logging.info("Cleanup: removed %d old files from %s", removed, DOWNLOAD_PATH)
    except Exception:
        logging.exception("Cleanup job failed")


# Handle URLs sent as messages (filter for text that looks like a URL)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'https?://'), handle_url))

# Handle button callbacks
app.add_handler(CallbackQueryHandler(button_callback))

# Schedule cleanup to run immediately and then every 24 hours
job_queue = app.job_queue
job_queue.run_repeating(_cleanup_old_files, interval=24 * 60 * 60, first=0)

app.run_polling()
