import os
import base64
import requests
from threading import Thread

from flask import Flask, request, jsonify, render_template
import telebot

# ================== CONFIG ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # для survey
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("HF_MODEL", "stabilityai/sdxl-turbo")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

if not HF_API_KEY:
    raise RuntimeError("HF_API_KEY is not set")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
app = Flask(__name__)

LAST_IMAGE = {}

# ================== TELEGRAM BOT ==================

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Добро пожаловать в Astro AI Bot\n\n"
        "🎨 Открой Mini App для генерации стикеров."
    )

@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ Используй Mini App для генерации стикеров."
    )

def run_bot():
    # ⚠️ polling ТОЛЬКО один раз
    bot.infinity_polling(skip_pending=True)

# ================== MINI APP ==================

@app.route("/")
def index():
    # ✅ Mini App ВСЕГДА открывает /
    return render_template("index.html")

@app.route("/health")
def health():
    return "OK", 200

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)

    prompt = data.get("prompt", "").strip()
    chat_id = data.get("chat_id")

    if not prompt or not chat_id:
        return jsonify({"error": "prompt or chat_id missing"}), 400

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

    image_base64 = base64.b64encode(resp.content).decode("utf-8")
    LAST_IMAGE[str(chat_id)] = image_base64

    return jsonify({"ok": True})

@app.route("/send_to_chat", methods=["POST"])
def send_to_chat():
    data = request.get_json(force=True)
    chat_id = str(data.get("chat_id"))

    image_base64 = LAST_IMAGE.get(chat_id)
    if not image_base64:
        return jsonify({"error": "No image"}), 400

    image_bytes = base64.b64decode(image_base64)

    bot.send_photo(
        chat_id=int(chat_id),
        photo=image_bytes,
        caption="🎨 Стикер из Mini App"
    )

    return jsonify({"ok": True})

# ================== MAIN ==================

if name == "__main__":
    Thread(target=run_bot, daemon=True).start()

    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
