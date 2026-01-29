import os
import base64
import requests
from flask import Flask, request, jsonify, send_file
import telebot
from threading import Thread
from io import BytesIO

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

# Храним изображения по chat_id
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
        "ℹ️ Используй Mini App для генерации стикеров."
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
    Mini App -> backend
    {
        "text": "кот в шапке",
        "chat_id": 123
    }
    """
    data = request.get_json(force=True)

    prompt = data.get("text", "").strip()
    chat_id = str(data.get("chat_id"))

    if not prompt or not chat_id:
        return jsonify({"error": "text or chat_id missing"}), 400

    hf_url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Accept": "image/png"
    }

    payload = {
        "inputs": f"cute sticker, flat illustration, white outline, {prompt}"
    }

    resp = requests.post(hf_url, headers=headers, json=payload, timeout=60)

    if resp.status_code != 200:
        return jsonify({"error": "HF failed", "details": resp.text}), 500

    image_bytes = resp.content
    LAST_IMAGE[chat_id] = image_bytes

    return jsonify({
        "ok": True,
        "url": f"/image/{chat_id}"
    })


@app.route("/image/<chat_id>")
def get_image(chat_id):
    img = LAST_IMAGE.get(chat_id)
    if not img:
        return "Not found", 404
    return send_file(BytesIO(img), mimetype="image/png")


@app.route("/send_to_chat", methods=["POST"])
def send_to_chat():
    data = request.get_json(force=True)
    chat_id = str(data.get("chat_id"))

    img = LAST_IMAGE.get(chat_id)
    if not img:
        return jsonify({"error": "No image"}), 400

    bot.send_photo(
        chat_id=int(chat_id),
        photo=img,
        caption="🎨 Стикер из Mini App"
    )

    return jsonify({"ok": True})

# ================== MAIN ==================

if __name__ == "__main__":
    Thread(target=run_bot).start()
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
