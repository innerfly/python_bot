import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


async def greet_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'got /start from  {update.effective_user.first_name}')


# Load variables from .env if present
load_dotenv()

# Read token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN is not set. Please set it in your environment or in a .env file."
    )

bot = ApplicationBuilder().token(TOKEN).build()

bot.add_handler(CommandHandler("start", greet_user))

bot.run_polling()
