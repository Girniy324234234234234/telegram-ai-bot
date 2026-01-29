import os
import uuid
import requests
from flask import Flask, request, jsonify, send_from_directory
from telebot import TeleBot
from telebot.types import InputFile

# =====================
# ENV
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in environment variables")

# =====================
# APP + BOT
# =====================
app = Flask(__name__)
bot = TeleBot(BOT_TOKEN, threaded=False)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_DIR = os.path.join(BASE_DIR, "static", "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)

# =====================
# TELEGRAM COMMANDS
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет!\n\nНажми кнопку ниже и создай стикер 👇",
        reply_markup={
            "inline_keyboard": [[
                {
                    "text": "🎨 Открыть генератор",
                    "web_app": {"url": os.getenv("WEBAPP_URL", "")}
                }
            ]]
        }
    )

# =====================
# IMAGE GENERATION
# =====================
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
            "prompt": f"Sticker, cartoon style, thick outline, telegram sticker, {prompt}",
            "size": "1024x1024",
        },
        timeout=60
    )

    image_url = response.json()["data"][0]["url"]
    image_data = requests.get(image_url).content

    with open(filepath, "wb") as f:
        f.write(image_data)

    return filename

# =====================
# API — GENERATE
# =====================
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt")

    if not prompt:
        return jsonify({"error": "No prompt"}), 400

    filename = generate_image(prompt)

    return jsonify({
        "image": f"/static/generated/{filename}",
        "file": filename
    })

# =====================
# API — SEND TO CHAT
# =====================
@app.route("/send_to_chat", methods=["POST"])
def send_to_chat():
    data = request.json
    chat_id = data.get("chat_id")
    filename = data.get("file")

    if not chat_id or not filename:
        return jsonify({"error": "chat_id or file missing"}), 400

    path = os.path.join(GENERATED_DIR, filename)

    with open(path, "rb") as f:
        bot.send_sticker(chat_id, InputFile(f))

    return jsonify({"status": "ok"})

# =====================
# STATIC
# =====================
@app.route("/static/generated/<path:filename>")
def static_files(filename):
    return send_from_directory(GENERATED_DIR, filename)

# =====================
# BOT POLLING (ОДИН РАЗ!)
# =====================
def run_bot():
    bot.infinity_polling(skip_pending=True)

if os.getenv("RUN_BOT") == "1":
    run_bot()
