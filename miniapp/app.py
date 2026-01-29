import os
import base64
import requests
from flask import Flask, request, jsonify, render_template
import telebot
from threading import Thread
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("HF_MODEL", "stabilityai/sdxl-turbo")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__, template_folder="templates")

LAST_IMAGE = {}

# ================= TELEGRAM =================

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Открой Mini App и сгенерируй стикер"
    )

def run_bot():
    bot.infinity_polling(skip_pending=True)

# ================= FLASK ====================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    text = data.get("text")
    chat_id = data.get("chat_id")

    if not text or not chat_id:
        return jsonify({"ok": False}), 400

    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Accept": "image/png"
    }

    payload = {
        "inputs": f"cute sticker, cartoon style, white outline, {text}"
    }

    # 🔁 RETRY LOOP — ЭТО КЛЮЧЕВО
    for _ in range(3):
        resp = requests.post(url, headers=headers, json=payload, timeout=60)

        # HF иногда возвращает JSON "loading"
        if resp.headers.get("content-type", "").startswith("image"):
            img_b64 = base64.b64encode(resp.content).decode()
            LAST_IMAGE[str(chat_id)] = img_b64
            return jsonify({"ok": True, "image": img_b64})

        time.sleep(2)

    print("HF ERROR:", resp.text)
    return jsonify({"ok": False}), 500

@app.route("/send_to_chat", methods=["POST"])
def send_to_chat():
    chat_id = str(request.get_json(force=True).get("chat_id"))
    img = LAST_IMAGE.get(chat_id)

    if not img:
        return jsonify({"ok": False}), 400

    bot.send_photo(
        chat_id=int(chat_id),
        photo=base64.b64decode(img),
        caption="🎨 Стикер из Mini App"
    )
    return jsonify({"ok": True})

# ================= MAIN =====================

if __name__ == "__main__":
    Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
