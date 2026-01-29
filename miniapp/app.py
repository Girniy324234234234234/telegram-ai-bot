import os
import base64
import requests
from io import BytesIO

from flask import Flask, request, jsonify
import telebot
from threading import Thread

# ================== CONFIG ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("HF_MODEL", "stabilityai/sdxl-turbo")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

if not HF_API_KEY:
    raise RuntimeError("HF_API_KEY is not set")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Храним последнее изображение для каждого чата
LAST_IMAGE = {}

# ================== TELEGRAM BOT ==================

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет!\n\n"
        "🎨 Открой Mini App, сгенерируй стикер и отправь его сюда."
    )

@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ Используй Mini App для генерации стикеров.\n"
        "Команда /start — начало."
    )

def run_bot():
    bot.infinity_polling(skip_pending=True)

# ================== FLASK ==================

@app.route("/")
def index():
    return "OK", 200


@app.route("/generate", methods=["POST"])
def generate():
    """
    Вызывается Mini App
    {
        "prompt": "кот в шапке",
        "chat_id": 123456789
    }
    """
    data = request.get_json(force=True)

    prompt = data.get("prompt", "").strip()
    chat_id = data.get("chat_id")

    if not prompt or not chat_id:
        return jsonify({"error": "prompt or chat_id missing"}), 400

    # ===== HF IMAGE GENERATION =====
    hf_url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Accept": "image/png"
    }

    payload = {
        "inputs": f"cute sticker style, flat illustration, white outline, {prompt}"
    }

    resp = requests.post(hf_url, headers=headers, json=payload, timeout=60)

    if resp.status_code != 200:
        return jsonify({
            "error": "HF generation failed",
            "details": resp.text
        }), 500

    image_bytes = resp.content
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    LAST_IMAGE[str(chat_id)] = image_base64

    return jsonify({"ok": True})


@app.route("/send_to_chat", methods=["POST"])
def send_to_chat():
    """
    Вызывается Mini App после генерации
    {
        "chat_id": 123456789
    }
    """
    data = request.get_json(force=True)
    chat_id = str(data.get("chat_id"))

    image_base64 = LAST_IMAGE.get(chat_id)

    if not image_base64:
        return jsonify({"error": "No image to send"}), 400

    image_bytes = base64.b64decode(image_base64)

    bot.send_photo(
        chat_id=int(chat_id),
        photo=image_bytes,
        caption="🎨 Стикер из Mini App"
    )

    return jsonify({"ok": True})

# ================== MAIN ==================

if name == "__main__":
    Thread(target=run_bot).start()

    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
