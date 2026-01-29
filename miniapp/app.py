import os
import base64
import requests
from threading import Thread
from flask import Flask, request, jsonify, Response
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

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

LAST_IMAGE = {}

# ================== TELEGRAM BOT ==================

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет!\n\n🎨 Открой Mini App и сгенерируй стикер."
    )

@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(message.chat.id, "ℹ️ Используй Mini App для генерации.")

def run_bot():
    bot.infinity_polling(skip_pending=True)

# ================== MINI APP UI ==================

@app.route("/", methods=["GET"])
def index():
    html = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sticker Generator</title>
<style>
body {
  margin:0;
  background:#0f0f1a;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  color:white;
  display:flex;
  justify-content:center;
  align-items:center;
  height:100vh;
}
.container {
  width:90%;
  max-width:420px;
}
input {
  width:100%;
  padding:14px;
  border-radius:12px;
  border:none;
  margin-bottom:12px;
  font-size:16px;
}
button {
  width:100%;
  padding:14px;
  border-radius:12px;
  border:none;
  background:#6c63ff;
  color:white;
  font-size:16px;
}
</style>
</head>
<body>
<div class="container">
  <h2>🎨 Генерация стикера</h2>
  <input id="prompt" placeholder="Например: бобёр в худи">
  <button onclick="generate()">Сгенерировать</button>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.expand();

async function generate() {
  const prompt = document.getElementById("prompt").value;
  if (!prompt) {
    alert("Введите описание");
    return;
  }

  const res = await fetch("/generate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      prompt: prompt,
      chat_id: tg.initDataUnsafe.user.id
    })
  });

  const data = await res.json();
  if (!data.ok) {
    alert("Ошибка генерации");
    return;
  }

  await fetch("/send_to_chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      chat_id: tg.initDataUnsafe.user.id
    })
  });

  tg.close();
}
</script>
</body>
</html>
"""
    return Response(html, mimetype="text/html")

# ================== API ==================

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)

    prompt = data.get("prompt", "").strip()
    chat_id = str(data.get("chat_id"))

    if not prompt or not chat_id:
        return jsonify({"ok": False, "error": "missing data"}), 400

    hf_url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Accept": "image/png"
    }

    payload = {
        "inputs": f"cute sticker, flat illustration, white outline, {prompt}"
    }

    r = requests.post(hf_url, headers=headers, json=payload, timeout=90)

    if r.status_code != 200:
        return jsonify({"ok": False, "error": "hf failed"}), 500

    image_b64 = base64.b64encode(r.content).decode()
    LAST_IMAGE[chat_id] = image_b64

    return jsonify({"ok": True})

@app.route("/send_to_chat", methods=["POST"])
def send_to_chat():
    data = request.get_json(force=True)
    chat_id = str(data.get("chat_id"))

    image_b64 = LAST_IMAGE.get(chat_id)
    if not image_b64:
        return jsonify({"ok": False}), 400

    image_bytes = base64.b64decode(image_b64)

    bot.send_photo(
        chat_id=int(chat_id),
        photo=image_bytes,caption="🎨 Стикер из Mini App"
    )

    return jsonify({"ok": True})

# ================== MAIN ==================

if name == "__main__":
    Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
