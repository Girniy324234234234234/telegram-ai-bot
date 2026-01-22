import threading
import os

from bot.run_bot import bot
from miniapp import app


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    # Flask в фоне
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Telegram bot в главном потоке
    print("🚀 Starting Telegram bot polling")
    bot.infinity_polling(skip_pending=True)


    t1.start()
    t2.start()

    t1.join()
    t2.join()
