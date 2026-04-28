import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
import threading

TOKEN = "8603043590:AAHzOY5gfuf8_DrjMvDf6mvMluXUp0bGU1g"
BOT_USERNAME = "@Refer_And_Earn11_bot"

# Database setup
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    ref_by INTEGER,
    referrals INTEGER DEFAULT 0
)
""")
conn.commit()

# Add user
def add_user(user_id, ref_by=None):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (user_id, ref_by, referrals) VALUES (?, ?, 0)",
            (user_id, ref_by)
        )
        conn.commit()

        # Increase ref count
        if ref_by:
            cursor.execute(
                "UPDATE users SET referrals = referrals + 1 WHERE user_id=?",
                (ref_by,)
            )
            conn.commit()

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    ref_by = None
    if context.args:
        ref_by = int(context.args[0])

    add_user(user_id, ref_by)

    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    await update.message.reply_text(
        f"👋 Welcome!\n\n"
        f"Your referral link:\n{ref_link}\n\n"
        f"Invite friends and earn rewards!"
    )

# Check referrals
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT referrals FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()

    count = data[0] if data else 0

    await update.message.reply_text(
        f"📊 Your referrals: {count}"
    )

# Flask app to keep Render alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Run bot
import asyncio
import threading

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("stats", stats))

    threading.Thread(target=run_flask).start()

    loop.run_until_complete(app_bot.initialize())
    loop.run_until_complete(app_bot.start())
    loop.run_until_complete(app_bot.updater.start_polling())
    loop.run_forever()

if __name__ == "__main__":
    main()
