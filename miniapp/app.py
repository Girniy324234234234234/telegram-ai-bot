import os
import uuid
import base64

from flask import Flask, render_template, request, jsonify
from telebot import TeleBot

# ========================
# CONFIG
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
MINIAPP_URL = os.getenv("MINIAPP_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = TeleBot(BOT_TOKEN, threaded=False)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

# хранение последней картинки по chat_id
LAST_IMAGE = {}

# ========================
# ROUTES
# ========================

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)

    prompt = data.get("prompt", "").strip()
    chat_id = data.get("chat_id")

    if not prompt or not chat_id:
        return jsonify({"error": "prompt or chat_id missing"}), 400

    # ⚠️ ЗДЕСЬ ТВОЯ РЕАЛЬНАЯ AI-ГЕНЕРАЦИЯ
    # сейчас ожидаем base64 от фронта или AI
    image_base64 = data.get("image_base64")

    if not image_base64:
        return jsonify({"error": "image_base64 missing"}), 400

    LAST_IMAGE[chat_id] = image_base64

    return jsonify({"ok": True})


@app.route("/send_to_chat", methods=["POST"])
def send_to_chat():
    data = request.get_json(force=True)
    chat_id = data.get("chat_id")

    if not chat_id:
        return jsonify({"error": "chat_id missing"}), 400

    image_base64 = LAST_IMAGE.get(chat_id)
    if not image_base64:
        return jsonify({"error": "no image generated"}), 400

    image_bytes = base64.b64decode(image_base64)

    bot.send_photo(
        chat_id=chat_id,
        photo=image_bytes,
        caption="🎨 Стикер из Mini App"
    )

    return jsonify({"ok": True})


# ========================
# BOT COMMAND
# ========================

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Открой Mini App и сгенерируй стикер",
        reply_markup={
            "inline_keyboard": [[
                {
                    "text": "🎨 Открыть Mini App",
                    "web_app": {
                        "url": MINIAPP_URL
                    }
                }
            ]]
        }
    )


# ========================
# HEALTHCHECK
# ========================
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200
