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


async def talk_to_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("User: %s, chat_id: %s, msg: %s", update.message.chat.username, update.message.chat.id,
                 update.message.text)
    await update.message.reply_text('reply: ' + update.message.text)

token = os.getenv("BOT_TOKEN")
if not token:
    raise RuntimeError(
        "BOT_TOKEN is not set. Please set it in your environment or in a .env file."
    )

app = ApplicationBuilder().token(token).build()

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), talk_to_me))

app.run_polling()
