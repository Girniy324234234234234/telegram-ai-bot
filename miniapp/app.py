import os
import uuid
import base64
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

# ========================
# CONFIG
# ========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

GENERATED_DIR = os.path.join(app.static_folder, "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)

# ========================
# ROUTES
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

    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=f"cute sticker, flat style, transparent background: {text}",
            size="1024x1024"
        )

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(GENERATED_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        image_url = request.host_url.rstrip("/") + f"/static/generated/{filename}"

        return jsonify({
            "ok": True,
            "url": image_url
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/health")
def health():
    return "OK", 200
