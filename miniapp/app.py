import os
import uuid
import base64

from flask import Flask, render_template, request, jsonify
from openai import OpenAI

# ================= CONFIG =================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

GENERATED_DIR = "miniapp/static/generated"
os.makedirs(GENERATED_DIR, exist_ok=True)

# ================= ROUTES =================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "empty text"}), 400

    prompt = f"""
Telegram sticker.
Cute, bold cartoon style.
High contrast.
No text on image.
Subject: {text}
White or transparent background.
"""

    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="512x512"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    filename = f"{uuid.uuid4()}.png"
    path = os.path.join(GENERATED_DIR, filename)

    with open(path, "wb") as f:
        f.write(image_bytes)

    return jsonify({
        "ok": True,
        "url": f"/static/generated/{filename}"
    })
