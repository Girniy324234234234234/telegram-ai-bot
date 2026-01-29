import os
import uuid
import base64
from flask import Flask, request, jsonify, render_template
from telebot import TeleBot, types
from openai import OpenAI

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("❌ TELEGRAM_BOT_TOKEN is not set in environment variables")

if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY is not set in environment variables")

BASE_DIR = os.path.dirname(__file__)
GENERATED_DIR = os.path.join(BASE_DIR, "static", "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)

bot = TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__, static_folder="static", template_folder="templates")

# ================== ROUTES ==================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    prompt = data.get("text", "").strip()

    if not prompt:
        return jsonify({"ok": False, "error": "Empty prompt"}), 400

    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=f"Sticker, flat cartoon style, white outline, transparent background. {prompt}",
            size="1024x1024"
        )

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(GENERATED_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        return jsonify({
            "ok": True,
            "url": f"/static/generated/{filename}",
            "file": filename
        })

    except Exception as e:
        print("IMAGE ERROR:", e)
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


# ================== START ==================
if name == "__main__":
    print("🚀 Bot started")

    import threading
    threading.Thread(target=lambda: bot.infinity_polling()).start()

    app.run(host="0.0.0.0", port=8080)
