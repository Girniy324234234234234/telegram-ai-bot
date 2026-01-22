import threading
import os

# --- импорт твоих файлов ---
from bot.run_bot import bot   # твой Telegram-бот
from miniapp import app   # твой Flask app

# --- запуск Telegram-бота ---
def run_bot():
    print("🚀 Starting Telegram bot polling")
    bot.infinity_polling(skip_pending=True)

# --- запуск Flask ---
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    t1 = threading.Thread(target=run_bot)
    t2 = threading.Thread(target=run_flask)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
