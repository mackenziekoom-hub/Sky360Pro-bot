import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running @Sky130Probot"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Sky130Pro Bot is LIVE Boss! 🚀 Send me a signal!")

def echo(update: Update, context: CallbackContext):
    update.message.reply_text(f"You said: {update.message.text}")

def run_bot():
    print("Bot is running @Sky130Probot - Starting...")
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    print("Bot is running @Sky130Probot")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
