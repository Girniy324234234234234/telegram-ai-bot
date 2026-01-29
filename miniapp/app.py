import os
import base64
import requests
from flask import Flask, request, jsonify, send_from_directory
import telebot

# ================== CONFIG ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("HF_MODEL", "stabilityai/sdxl-turbo")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

if not HF_API_KEY:
    raise RuntimeError("HF_API_KEY is not set")

bot = telebot.TeleBot(BOT_TOKEN)

# MiniApp лежит в папке miniapp/
app = Flask(
    name,
    static_folder="miniapp",
    static_url_path=""
)

# Храним последнее изображение для чата
LAST_IMAGE = {}

# ================== MINI APP ==================

@app.route("/")
def index():
    # ❗️ВАЖНО — отдаём HTML, а не "OK"
    return send_from_directory("miniapp", "index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)

    prompt = data.get("text", "").strip()
    chat_id = data.get("chat_id")

    if not prompt or not chat_id:
        return jsonify({"error": "prompt or chat_id missing"}), 400

    # ===== HuggingFace generation =====
    hf_url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Accept": "image/png"
    }

    payload = {
        "inputs": f"cute telegram sticker, flat illustration, white outline, {prompt}"
    }

    resp = requests.post(hf_url, headers=headers, json=payload, timeout=60)

    if resp.status_code != 200:
        return jsonify({
            "error": "HF generation failed",
            "details": resp.text
        }), 500

    image_bytes = resp.content
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    LAST_IMAGE[str(chat_id)] = image_base64

    return jsonify({
        "ok": True,
        "image": image_base64
    })


@app.route("/send", methods=["POST"])
def send_to_chat():
    data = request.get_json(force=True)
    chat_id = str(data.get("chat_id"))

    image_base64 = LAST_IMAGE.get(chat_id)
    if not image_base64:
        return jsonify({"error": "no image"}), 400

    image_bytes = base64.b64decode(image_base64)

    bot.send_photo(
        chat_id=int(chat_id),
        photo=image_bytes,
        caption="🎨 Стикер из Mini App"
    )

    return jsonify({"ok": True})


# ================== HEALTH ==================

@app.route("/health")
def health():
    return "OK", 200
