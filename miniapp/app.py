import os
import base64
import requests
import threading
import time

from flask import Flask, request, jsonify, render_template
import telebot

# ================== CONFIG ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("HF_MODEL", "stabilityai/sdxl-turbo")
PORT = int(os.getenv("PORT", 8080))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

if not HF_API_KEY:
    raise RuntimeError("HF_API_KEY is not set")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__, template_folder="templates")

LAST_IMAGE = {}

# ================== TELEGRAM ==================

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Добро пожаловать в Astro AI Bot\n\n"
        "🎨 Открой Mini App и сгенерируй стикер"
    )

@bot.message_handler(commands=["creator"])
def creator(message):
    bot.send_message(message.chat.id, "👨‍💻 Проект разработан @astroanvt")

# ================== SAFE POLLING ==================

def safe_polling():
    """
    Запускаем polling ТОЛЬКО один раз.
    Если Telegram вернул 409 — просто ждём, не падаем.
    """
    while True:
        try:
            print("🚀 Telegram polling started")
            bot.infinity_polling(
                skip_pending=True,
                timeout=20,
                long_polling_timeout=20
            )
        except Exception as e:
            if "409" in str(e):
                print("⚠️ 409 conflict detected, waiting...")
                time.sleep(5)
            else:
                print("❌ polling error:", e)
                time.sleep(5)

# ================== FLASK ==================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)

    text = data.get("text", "").strip()
    chat_id = data.get("chat_id")

    if not text or not chat_id:
        return jsonify({"ok": False}), 400

    hf_url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Accept": "image/png"
    }

    payload = {
        "inputs": f"cute sticker style, flat illustration, white outline, {text}"
    }

    r = requests.post(hf_url, headers=headers, json=payload, timeout=90)

    if r.status_code != 200:
        print("HF error:", r.text)
        return jsonify({"ok": False}), 500

    image_b64 = base64.b64encode(r.content).decode()
    LAST_IMAGE[str(chat_id)] = image_b64

    return jsonify({"ok": True, "image": image_b64})

@app.route("/sendToChat", methods=["POST"])
def send_to_chat():
    data = request.get_json(force=True)
    chat_id = str(data.get("chat_id"))

    image_b64 = LAST_IMAGE.get(chat_id)
    if not image_b64:
        return jsonify({"ok": False}), 400

    bot.send_photo(
        chat_id=int(chat_id),
        photo=base64.b64decode(image_b64),
        caption="🎨 Стикер из Mini App"
    )

    return jsonify({"ok": True})

# ================== MAIN ==================

if __name__ == "__main__":
    # polling — в отдельном daemon-потоке
    threading.Thread(target=safe_polling, daemon=True).start()

    print(f"🌐 Flask started on port {PORT}")
    app.run(host="0.0.0.0", port=PORT)
