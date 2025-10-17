import asyncio
import logging
import os
import shlex
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    filename='log.log',
    format='%(asctime)s %(levelname)s - %(name)s - %(message)s'
)

DOMAIN = os.getenv("DOMAIN")
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH")

Path(DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)


async def _run_command(*args: str) -> tuple[int, str, str]:
    """Run a command asynchronously and return (code, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_b, stderr_b = await proc.communicate()
    return proc.returncode, stdout_b.decode().strip(), stderr_b.decode().strip()


async def video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if context.args:
            url = context.args[0]
        else:
            # Fallback: try to parse the message text after the command
            # e.g. "/video <url>"
            text = update.message.text or ""
            parts = text.split(maxsplit=1)
            url = parts[1].strip() if len(parts) > 1 else ""

        if not url:
            await update.message.reply_text("Usage: /video <youtube_url>")
            return

        await update.message.reply_text("Downloading... This may take a minute.")

        # Use a deterministic, web-safe filename template
        template = f"{DOWNLOAD_PATH}/%(title)s-%(id)s.%(ext)s"
        # First, compute the final filename without downloading
        code, filename, err = await _run_command(
            "yt-dlp",
            "--restrict-filenames",
            "-o",
            template,
            "--get-filename",
            url,
        )
        if code != 0 or not filename:
            logging.error("yt-dlp --get-filename failed: code=%s, err=%s", code, err)
            await update.message.reply_text("Failed to analyze the video URL. Please check the link and try again.")
            return

        # Now download the file to the same path
        code, out, err = await _run_command(
            "yt-dlp",
            "--restrict-filenames",
            "-o",
            template,
            url,
        )
        if code != 0:
            logging.error("yt-dlp download failed: code=%s, err=%s", code, err)
            await update.message.reply_text("Download failed. The video may be unavailable or blocked.")
            return

        file_path = Path(filename)
        if not file_path.exists():
            # Try to locate the downloaded file within DOWNLOAD_PATH (edge cases with extensions)
            try:
                vid_id = file_path.stem.split("-")[-1]
                matches = list(Path(DOWNLOAD_PATH).glob(f"*-{vid_id}.*"))
                if matches:
                    file_path = matches[0]
            except Exception:
                pass

        if not file_path.exists():
            await update.message.reply_text("Downloaded, but could not locate the file. Please try again later.")
            return

        public_url = f"{DOMAIN.rstrip('/')}/{DOWNLOAD_PATH.strip('/')}/{file_path.name}"
        await update.message.reply_text(f"Done! Download link: {public_url}")
    except Exception as e:
        logging.exception("Unhandled error in /video")
        await update.message.reply_text("Unexpected error while processing the request.")


token = os.getenv("BOT_TOKEN")
if not token:
    raise RuntimeError(
        "BOT_TOKEN is not set. Please set it in your environment or in a .env file."
    )

app = ApplicationBuilder().token(token).build()

app.add_handler(CommandHandler("video", video))

app.run_polling()
