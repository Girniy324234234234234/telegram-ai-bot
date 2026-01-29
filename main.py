import threading
import os

from bot.run_bot import bot
from miniapp.app import app


def run_bot():
    print("🚀 Starting Telegram bot polling")
    bot.infinity_polling(skip_pending=True)


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting Flask on port {port}")
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


if __name__ == "__main__":
    t1 = threading.Thread(target=run_bot, daemon=True)
    t2 = threading.Thread(target=run_flask, daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
