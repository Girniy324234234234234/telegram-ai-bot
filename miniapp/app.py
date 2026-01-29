import os
import uuid
import base64

from flask import Flask, request, jsonify, render_template
from telebot import TeleBot, types
from openai import OpenAI

# ================= CONFIG =================

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(__file__)
GENERATED_DIR = os.path.join(BASE_DIR, "static", "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)

# ================= ROUTES =================
bot = TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__, static_folder="static", template_folder="templates")

# ================== ROUTES ==================
@app.route("/")
def index():
    return render_template("index.html")
@@ -33,10 +33,9 @@ def generate():
        return jsonify({"ok": False, "error": "Empty prompt"}), 400

    try:
        # 🔥 Генерация изображения
        result = client.images.generate(
            model="gpt-image-1",
            prompt=f"Sticker, simple, flat, vector style, transparent background. {prompt}",
            prompt=f"Sticker, simple, flat, cartoon style, white border, transparent background, {prompt}",
            size="1024x1024"
        )

@@ -49,23 +48,56 @@ def generate():
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        # ✅ ВАЖНО: полный HTTPS URL для Telegram Mini App
        base_url = request.host_url.rstrip("/")

        return jsonify({
            "ok": True,
            "url": f"{base_url}/static/generated/{filename}"
            "url": f"/static/generated/{filename}",
            "file": filename
        })

    except Exception as e:
        print("IMAGE ERROR:", e)
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500
        return jsonify({"ok": False, "error": str(e)}), 500


# ================== TELEGRAM BOT ==================
@bot.message_handler(commands=["start"])
def start(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            "🎨 Открыть генератор",
            web_app=types.WebAppInfo(
                url="https://telegram-ai-bot-production-5a64.up.railway.app"
            )
        )
    )
    bot.send_message(
        message.chat.id,
        "Привет! Создай AI-стикер 👇",
        reply_markup=kb
    )


@bot.message_handler(content_types=["web_app_data"])
def handle_webapp_data(message):
    try:
        filename = message.web_app_data.data
        filepath = os.path.join(GENERATED_DIR, filename)

        if not os.path.exists(filepath):
            bot.send_message(message.chat.id, "❌ Файл не найден")
            return

        with open(filepath, "rb") as f:
            bot.send_sticker(message.chat.id, f)

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

# ================= START =================

if __name__ == "__main__":
# ================== START ==================
if name == "__main__":
    print("🚀 Bot started")
    import threading
    threading.Thread(target=lambda: bot.infinity_polling()).start()
    app.run(host="0.0.0.0", port=8080)
