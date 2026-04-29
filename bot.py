from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import sqlite3
from flask import Flask
import threading
import asyncio

# 🔒 PUT YOUR NEW TOKEN HERE (DON’T USE OLD EXPOSED ONE)
TOKEN = "8603043590:AAHzOY5gfuf8_DrjMvDf6mvMluXUp0bGU1g"
BOT_USERNAME = "Refer_And_Earn11_bot"  

# ---------------- DATABASE ----------------
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    ref_by INTEGER,
    referrals INTEGER DEFAULT 0,
    balance REAL DEFAULT 0
)
""")
conn.commit()

# ---------------- ADD USER ----------------
def add_user(user_id, ref_by=None):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (user_id, ref_by, referrals, balance) VALUES (?, ?, 0, 0)",
            (user_id, ref_by)
        )
        conn.commit()

        # reward referrer
        if ref_by:
            reward = 5  # ₹ per referral
            cursor.execute(
                "UPDATE users SET referrals = referrals + 1, balance = balance + ? WHERE user_id=?",
                (reward, ref_by)
            )
            conn.commit()

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    ref_by = None
    if context.args:
        try:
            ref_by = int(context.args[0])
        except:
            ref_by = None

    add_user(user_id, ref_by)

    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    keyboard = [
        [InlineKeyboardButton("💰 Check Balance", callback_data="balance")],
        [InlineKeyboardButton("📤 Refer Friends", url=ref_link)],
        [InlineKeyboardButton("ℹ️ How to Earn", callback_data="help")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Welcome to Earn Bot!\n\n"
        f"💰 Earn rewards by inviting friends.\n\n"
        f"🔗 Your referral link:\n{ref_link}",
        reply_markup=reply_markup
    )

# ---------------- STATS ----------------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute("SELECT referrals FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()

    count = data[0] if data else 0

    await update.message.reply_text(f"📊 Your referrals: {count}")

# ---------------- BUTTON HANDLER ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "balance":
        cursor.execute("SELECT balance, referrals FROM users WHERE user_id=?", (user_id,))
        data = cursor.fetchone()

        bal, refs = data if data else (0, 0)

        await query.message.reply_text(
            f"💰 Balance: ₹{bal}\n👥 Referrals: {refs}"
        )

    elif query.data == "help":
        await query.message.reply_text(
            "📌 How to Earn:\n"
            "1. Share your referral link\n"
            "2. Friends join using your link\n"
            "3. You earn money 💰"
        )

# ---------------- FLASK (KEEP ALIVE) ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# ---------------- MAIN ----------------
def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("stats", stats))
    app_bot.add_handler(CallbackQueryHandler(button_handler))

    threading.Thread(target=run_flask).start()

    loop.run_until_complete(app_bot.initialize())
    loop.run_until_complete(app_bot.start())
    loop.run_until_complete(app_bot.updater.start_polling())
    loop.run_forever()

# ---------------- RUN ----------------
if __name__ == "__main__":
    main()
