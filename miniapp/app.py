import os
import uuid
import base64

from flask import Flask, request, jsonify, render_template
from openai import OpenAI

# ================= CONFIG =================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_DIR = os.path.join(BASE_DIR, "static", "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)

# ================= ROUTES =================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    prompt = data.get("text", "").strip()

    if not prompt:
        return jsonify({"ok": False, "error": "Empty prompt"}), 400

    try:
        # 🔥 Генерация изображения
        result = client.images.generate(
            model="gpt-image-1",
            prompt=f"Sticker, simple, flat, vector style, transparent background. {prompt}",
            size="1024x1024"
        )

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(GENERATED_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        # ✅ ВАЖНО: полный HTTPS URL для Telegram Mini App
        base_url = request.host_url.rstrip("/")

        return jsonify({
            "ok": True,
            "url": f"{base_url}/static/generated/{filename}"
        })

    except Exception as e:
        print("IMAGE ERROR:", e)
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


# ================= START =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
