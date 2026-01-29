import os
import uuid
from flask import Flask, render_template, request, jsonify
from telebot import TeleBot

# ========================
# ENV
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN is not set")

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

# ========================
# FLASK APP
# ========================
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

# ========================
# ROUTES
# ========================

# 🔹 Mini App entry point
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


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
