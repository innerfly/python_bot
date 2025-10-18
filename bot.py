import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    filename='log.log',
    format='%(asctime)s %(levelname)s - %(name)s - %(message)s'
)

DOMAIN = os.getenv("DOWNLOAD_DOMAIN")
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH")

Path(DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)

FILE_PATH = f"{DOWNLOAD_PATH}/%(title)s-%(id)s.%(ext)s"


async def get_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if not context.args or not context.args[0]:
            await update.message.reply_text("Usage: /v <youtube_url>")
            return

        url = context.args[0]

        filename = await _check_url(update, url, FILE_PATH)

        code, out, err = await _run_command(
            "yt-dlp",
            "--restrict-filenames",
            "-o",
            FILE_PATH,
            url,
        )
        if code != 0:
            logging.error("yt-dlp download failed: code=%s, err=%s", code, err)
            await update.message.reply_text("Download failed. The video may be unavailable or blocked.")
            return

        await _get_link(filename)
    except Exception as e:
        logging.exception("Unhandled error in /v")
        await update.message.reply_text("Unexpected error while processing the request.")


async def get_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if not context.args or not context.args[0]:
            await update.message.reply_text("Usage: /a <youtube_url>")
            return

        url = context.args[0]

        filename = await _check_url(update, url, FILE_PATH)

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
            await update.message.reply_text("Download failed. The video may be unavailable or blocked.")
            return
        await _get_link(filename)

    except Exception as e:
        logging.exception("Unhandled error in /v")
        await update.message.reply_text("Unexpected error while processing the request.")


async def _run_command(*args: str) -> tuple[int, str, str]:
    """Run a command asynchronously and return (code, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_b, stderr_b = await proc.communicate()
    return proc.returncode, stdout_b.decode().strip(), stderr_b.decode().strip()


async def _check_url(update: Update, url: str, file_path: str):
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
        await update.message.reply_text("Failed to analyze the video URL. Please check the link and try again.")
        return

    await update.message.reply_text("Downloading... This may take a minute.")

    return filename


async def _get_link(update: Update, filename: str):
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
        await update.message.reply_text("Downloaded, but could not locate the file. Please try again later.")
        return

    file_size = os.path.getsize(file_path)
    size_mb = file_size / (1024 * 1024)

    public_url = f"{DOMAIN.rstrip('/')}/{file_path.name}"

    await update.message.reply_text(f"Done! Download link: {public_url}\nFile size: {size_mb:.2f} MB")


app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

app.add_handler(CommandHandler("v", get_video))
app.add_handler(CommandHandler("a", get_audio))

app.run_polling()
