import os
import base64
import requests
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

# ================== TELEGRAM BOT ==================

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет!\n\n"
        "🎨 Открой Mini App и сгенерируй стикер."
    )

def run_bot():
    bot.infinity_polling(skip_pending=True)

# ================== FLASK ==================

@app.route("/")
def index():
    return "OK", 200


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)

    # ⬅️ ВАЖНО: принимаем text (как в index.html)
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"ok": False, "error": "empty text"}), 400

    hf_url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Accept": "image/png"
    }

    payload = {
        "inputs": f"cute telegram sticker, flat illustration, white outline, {text}"
    }

    resp = requests.post(hf_url, headers=headers, json=payload, timeout=60)

    if resp.status_code != 200:
        return jsonify({
            "ok": False,
            "error": "HF generation failed",
            "details": resp.text
        }), 500

    image_base64 = base64.b64encode(resp.content).decode("utf-8")

    # Mini App ждёт url — делаем data:image
    return jsonify({
        "ok": True,
        "url": f"data:image/png;base64,{image_base64}"
    })


# ================== MAIN ==================

if __name__ == "__main__":
    Thread(target=run_bot).start()
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
