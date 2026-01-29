import os
import uuid
import base64

from flask import Flask, render_template, request, jsonify
from telebot import TeleBot

# ========================
# CONFIG
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = TeleBot(BOT_TOKEN, threaded=False)

app = Flask(
    name,
    template_folder="templates",
    static_folder="static"
)

# хранение последнего стикера для отправки в чат
LAST_IMAGE = {}

# ========================
# ROUTES
# ========================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt")
    chat_id = data.get("chat_id")

    if not prompt:
        return jsonify({"error": "No prompt"}), 400

    # ❗️заглушка генерации (у тебя она уже есть — тут логика не ломается)
    # предположим, что ты уже генерируешь PNG как base64
    # ниже — имитация результата

    fake_image_base64 = data.get("image_base64")
    if not fake_image_base64:
        return jsonify({"error": "Image generation failed"}), 500

    image_id = str(uuid.uuid4())
    LAST_IMAGE[chat_id] = fake_image_base64

    return jsonify({
        "success": True,
        "image_base64": fake_image_base64
    })


@app.route("/send", methods=["POST"])
def send_to_chat():
    data = request.json
    chat_id = data.get("chat_id")

    if not chat_id:
        return jsonify({"error": "No chat_id"}), 400

    image_base64 = LAST_IMAGE.get(chat_id)
    if not image_base64:
        return jsonify({"error": "No image to send"}), 400

    image_bytes = base64.b64decode(image_base64)

    bot.send_photo(
        chat_id=chat_id,
        photo=image_bytes,
        caption="🎨 Стикер сгенерирован в Mini App"
    )

    return jsonify({"success": True})


# ========================
# BOT COMMANDS
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
                        "url": os.getenv("MINIAPP_URL")
                    }
                }
            ]]
        }
    )

# 🔹 Генерация изображения (заглушка под твою AI-логику)
@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    prompt = data.get("text", "").strip()

    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    # ⚠️ ЗДЕСЬ ТВОЯ AI-ЛОГИКА
    # Сейчас просто пример
    filename = f"{uuid.uuid4()}.png"
    image_url = f"/static/generated/{filename}"

    return jsonify({
        "ok": True,
        "image_url": image_url
    })


# 🔹 Отправка картинки в чат бота
@app.route("/send_to_chat", methods=["POST"])
def send_to_chat():
    data = request.get_json(force=True)

    chat_id = data.get("chat_id")
    image_url = data.get("image_url")

    if not chat_id or not image_url:
        return jsonify({"error": "Missing data"}), 400

    # Абсолютный URL для Telegram
    if image_url.startswith("/"):
        image_url = request.host_url.rstrip("/") + image_url

    bot.send_photo(chat_id, image_url)
    return jsonify({"ok": True})


# ========================
# HEALTHCHECK (Railway)
# ========================
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200
