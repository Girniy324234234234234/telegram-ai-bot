import os
import uuid
import requests
from flask import Flask, request, jsonify, send_from_directory
from telebot import TeleBot
from telebot.types import InputFile

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN is not set in Railway Variables")

if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY is not set in Railway Variables")

bot = TeleBot(BOT_TOKEN, threaded=False)

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static", "generated")

os.makedirs(STATIC_DIR, exist_ok=True)

app = Flask(__name__)

# =========================
# AI IMAGE GENERATION
# =========================

def generate_sticker(prompt: str) -> str:
    filename = f"{uuid.uuid4()}.png"
    filepath = os.path.join(STATIC_DIR, filename)

    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-image-1",
            "prompt": f"cute cartoon sticker, white outline, flat style, {prompt}",
            "size": "1024x1024"
        },
        timeout=60
    )

    data = response.json()
    image_url = data["data"][0]["url"]

    img = requests.get(image_url).content
    with open(filepath, "wb") as f:
        f.write(img)

    return f"/static/generated/{filename}"

# =========================
# ROUTES
# =========================

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/generate", methods=["POST"])
def generate():
    text = request.json.get("text")
    if not text:
        return jsonify({"ok": False, "error": "No text provided"})

    url = generate_sticker(text)
    return jsonify({"ok": True, "url": url})

@app.route("/send_to_chat", methods=["POST"])
def send_to_chat():
    data = request.json
    image_url = data.get("image")
    user_id = data.get("user_id")

    if not image_url or not user_id:
        return jsonify({"ok": False, "error": "Missing data"})

    path = image_url.replace("/static/", "")
    file_path = os.path.join(BASE_DIR, "static", path)

    try:
        with open(file_path, "rb") as f:
            bot.send_sticker(
                chat_id=user_id,
                sticker=InputFile(f)
            )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# =========================
# BOT COMMANDS (SAFE)
# =========================

@bot.message_handler(commands=["start", "help"])
def start_handler(message):
    bot.send_message(
        message.chat.id,
        "👋 Открой мини-приложение и создай стикер"
    )

# =========================
# ENTRY POINT
# =========================

if name == "__main__":
    # ❗ ВАЖНО: polling ТОЛЬКО локально
    if os.getenv("RAILWAY_ENVIRONMENT") is None:
        bot.infinity_polling(skip_pending=True)

    app.run(host="0.0.0.0", port=8080)
