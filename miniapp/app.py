import os
import base64
from flask import Flask, render_template, request, jsonify
from telebot import TeleBot

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = TeleBot(BOT_TOKEN, threaded=False)

app = Flask(
    name,
    template_folder="templates",
    static_folder="static"
)

# хранение последнего изображения по chat_id
LAST_IMAGE = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)

    prompt = data.get("prompt")
    chat_id = data.get("chat_id")

    if not prompt or not chat_id:
        return jsonify({"error": "prompt or chat_id missing"}), 400

    # ⚠️ ЗДЕСЬ ТВОЯ РЕАЛЬНАЯ AI-ГЕНЕРАЦИЯ
    # сейчас ожидаем base64 PNG
    image_base64 = data.get("image_base64")
    if not image_base64:
        return jsonify({"error": "image generation failed"}), 500

    LAST_IMAGE[chat_id] = image_base64

    return jsonify({
        "ok": True,
        "image_base64": image_base64
    })


@app.route("/send_to_chat", methods=["POST"])
def send_to_chat():
    data = request.get_json(force=True)
    chat_id = data.get("chat_id")

    if not chat_id:
        return jsonify({"error": "chat_id missing"}), 400

    image_base64 = LAST_IMAGE.get(chat_id)
    if not image_base64:
        return jsonify({"error": "no image"}), 400

    image_bytes = base64.b64decode(image_base64)

    bot.send_photo(
        chat_id=chat_id,
        photo=image_bytes,
        caption="🎨 Стикер из Mini App"
    )

    return jsonify({"ok": True})


@app.route("/health")
def health():
    return "OK", 200
