import os
import uuid
import requests
from flask import Flask, request, jsonify, send_from_directory
from telebot import TeleBot
from telebot.types import InputFile

# =======================
# ENV
# =======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN is not set")

# =======================
# TELEGRAM BOT
# =======================
bot = TeleBot(BOT_TOKEN, threaded=False)

# =======================
# FLASK APP
# =======================
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_DIR = os.path.join(BASE_DIR, "static", "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)

# =======================
# IMAGE GENERATION (OpenAI Images)
# =======================
def generate_image(prompt: str) -> str:
    filename = f"{uuid.uuid4()}.png"
    filepath = os.path.join(GENERATED_DIR, filename)

    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-image-1",
            "prompt": f"cute cartoon sticker, telegram style, white outline, {prompt}",
            "size": "1024x1024"
        },
        timeout=60
    )

    response.raise_for_status()
    image_url = response.json()["data"][0]["url"]

    img = requests.get(image_url, timeout=60).content
    with open(filepath, "wb") as f:
        f.write(img)

    return filename

# =======================
# API: GENERATE
# =======================
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    filename = generate_image(prompt)
    return jsonify({
        "image": f"/static/generated/{filename}",
        "file": filename
    })

# =======================
# API: SEND TO CHAT
# =======================
@app.route("/send_to_chat", methods=["POST"])
def send_to_chat():
    data = request.json
    chat_id = data.get("chat_id")
    filename = data.get("file")

    if not chat_id or not filename:
        return jsonify({"error": "Missing data"}), 400

    path = os.path.join(GENERATED_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404

    with open(path, "rb") as f:
        bot.send_sticker(chat_id, InputFile(f))

    return jsonify({"ok": True})

# =======================
# STATIC
# =======================
@app.route("/static/generated/<path:filename>")
def static_generated(filename):
    return send_from_directory(GENERATED_DIR, filename)

# =======================
# TELEGRAM COMMAND
# =======================
@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(
        msg.chat.id,
        "🎨 Открой мини-апп и создай стикер 👇",
        reply_markup={
            "inline_keyboard": [[
                {
                    "text": "🚀 Открыть мини-апп",
                    "web_app": {
                        "url": "https://telegram-ai-bot-production-5a64.up.railway.app"
                    }
                }
            ]]
        }
    )

# =======================
# START BOT POLLING
# =======================
def start_bot():
    bot.infinity_polling(skip_pending=True)

# =======================
# ENTRYPOINT
# =======================
import threading
threading.Thread(target=start_bot, daemon=True).start()
