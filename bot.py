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
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "downloads")

Path(DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)


async def talk_to_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("User: %s, chat_id: %s, msg: %s", update.message.chat.username, update.message.chat.id,
                 update.message.text)
    await update.message.reply_text('reply: ' + update.message.text)


async def yt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Usage:
    /yt video <url>
    /yt audio <url>
    """
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /yt <video|audio> <url>")
        return

    mode = context.args[0].lower()
    url = context.args[1]

    if mode not in {"video", "audio"}:
        await update.message.reply_text("First argument must be 'video' or 'audio'. Example: /yt video <url>")
        return

    await update.message.reply_text("Starting download... This may take a while.")

    outtmpl = str(Path(DOWNLOAD_PATH) / "%(title)s-%(id)s.%(ext)s")

    if mode == "audio":
        cmd = [
            "yt-dlp",
            "-f", "bestaudio",
            "--extract-audio",
            "--audio-format", "mp3",
            "--no-progress",
            "--print", "filename",
            "-o", outtmpl,
            url,
        ]
    else:  # video
        cmd = [
            "yt-dlp",
            "--merge-output-format", "mp4",
            "--no-progress",
            "--print", "filename",
            "-o", outtmpl,
            url,
        ]

    logging.info("Running command: %s", shlex.join(cmd))

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        code = proc.returncode
    except FileNotFoundError:
        await update.message.reply_text("yt-dlp is not installed on the server. Please install it and try again.")
        return
    except Exception as e:
        logging.exception("Failed to start yt-dlp")
        await update.message.reply_text(f"Failed to start yt-dlp: {e}")
        return

    if code != 0:
        err_text = stderr.decode(errors="ignore")[-1000:]
        logging.error("yt-dlp failed (%s): %s", code, err_text)
        await update.message.reply_text("Download failed. Details logged.")
        return

    # Parse printed filenames, pick the last existing path
    lines = [ln.strip() for ln in stdout.decode(errors="ignore").splitlines() if ln.strip()]
    file_path = None
    for ln in reversed(lines):
        p = Path(ln)
        if p.exists():
            file_path = p
            break
    if not file_path:
        await update.message.reply_text("Download finished but output file was not found.")
        return

    # Build public link
    # Prefer a URL in the form: DOMAIN/DOWNLOAD_PATH/filename
    try:
        cwd = Path.cwd()
        rel = file_path.relative_to(cwd)
    except Exception:
        # Fallback to DOWNLOAD_PATH/filename
        rel = Path(DOWNLOAD_PATH) / file_path.name

    # Normalize URL parts
    base = (DOMAIN or "").rstrip("/")
    url_path = str(rel).replace(os.sep, "/")
    public_url = f"{base}/{url_path}" if base else url_path

    await update.message.reply_text(f"Done. Download link: {public_url}")


token = os.getenv("BOT_TOKEN")
if not token:
    raise RuntimeError(
        "BOT_TOKEN is not set. Please set it in your environment or in a .env file."
    )

app = ApplicationBuilder().token(token).build()

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), talk_to_me))
app.add_handler(CommandHandler("yt", yt))

app.run_polling()
