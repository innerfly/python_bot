import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    filename='log.log',
    format='%(asctime)s %(levelname)s - %(name)s - %(message)s'
)

async def greet_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = f'got /start from  {update.effective_user.first_name}'
    logging.info(msg)
    await update.message.reply_text(msg)

async def talk_to_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("User: %s, chat_id: %s, msg: %s", update.message.chat.username, update.message.chat.id, update.message.text)
    await update.message.reply_text('reply: ' + update.message.text)

token = os.getenv("BOT_TOKEN")
if not token:
    raise RuntimeError(
        "BOT_TOKEN is not set. Please set it in your environment or in a .env file."
    )

app = ApplicationBuilder().token(token).build()

app.add_handler(CommandHandler("start", greet_user))

app.add_handler(MessageHandler(filters.TEXT, talk_to_me))

app.run_polling()