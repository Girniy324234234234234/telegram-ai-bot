import os
import uuid
import base64

from flask import Flask, render_template, request, jsonify
from telebot import TeleBot, types

# ========================
# CONFIG
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
MINIAPP_URL = os.getenv("MINIAPP_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = TeleBot(BOT_TOKEN, threaded=False)

app = Flask(
    name,
    template_folder="templates",
    static_folder="static"
)

# image_id -> base64
IMAGES = {}

# ========================
# MINI APP
# ========================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"ok": False, "error": "Empty prompt"}), 400

    # 🔴 ЗАГЛУШКА (вместо AI)
    fake_png = base64.b64encode(b"fake-image-bytes").decode()

    image_id = str(uuid.uuid4())
    IMAGES[image_id] = fake_png

    return jsonify({
        "ok": True,
        "url": f"/image/{image_id}"
    })


@app.route("/image/<image_id>")
def image(image_id):
    img = IMAGES.get(image_id)
    if not img:
        return "Not found", 404

    return base64.b64decode(img), 200, {
        "Content-Type": "image/png",
        "Cache-Control": "no-store"
    }


# ========================
# BOT
# ========================

@bot.message_handler(commands=["start"])
def start(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            text="🎨 Открыть Mini App",
            web_app=types.WebAppInfo(url=MINIAPP_URL)
        )
    )

    bot.send_message(
        message.chat.id,
        "👋 Открой Mini App и сгенерируй стикер",
        reply_markup=kb
    )


@bot.message_handler(content_types=["web_app_data"])
def webapp_data(message):
    try:
        payload = eval(message.web_app_data.data)
        image_url = payload.get("url")

        if not image_url:
            bot.send_message(message.chat.id, "❌ Нет изображения")
            return

        full_url = request.host_url.rstrip("/") + image_url

        bot.send_photo(
            chat_id=message.chat.id,
            photo=full_url,
            caption="🎨 Стикер из Mini App"
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")


# ========================
# HEALTHCHECK
# ========================

@app.route("/health")
def health():
    return "OK", 200
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200
