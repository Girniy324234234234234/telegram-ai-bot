import os
import uuid
import requests

from flask import Flask, request, jsonify, render_template

# =========================
# CONFIG
# =========================

HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("HF_MODEL", "stabilityai/sdxl-turbo")

if not HF_API_KEY:
    raise RuntimeError("HF_API_KEY is not set")

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
GENERATED_DIR = os.path.join(STATIC_DIR, "generated")

os.makedirs(GENERATED_DIR, exist_ok=True)

app = Flask(
    name,
    template_folder="templates",
    static_folder="static"
)

# =========================
# ROUTES
# =========================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"ok": False, "error": "empty prompt"}), 400

    # -------- HF REQUEST --------
    hf_url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Accept": "image/png"
    }

    payload = {
        "inputs": f"sticker style, flat illustration, white outline, {text}"
    }

    try:
        resp = requests.post(
            hf_url,
            headers=headers,
            json=payload,
            timeout=60
        )
    except Exception as e:
        print("HF REQUEST ERROR:", e)
        return jsonify({"ok": False, "error": "hf request failed"}), 500

    if resp.status_code != 200:
        print("HF ERROR:", resp.text)
        return jsonify({"ok": False, "error": "hf generation error"}), 500

    # -------- SAVE IMAGE --------
    filename = f"{uuid.uuid4()}.png"
    filepath = os.path.join(GENERATED_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(resp.content)

    image_url = f"/static/generated/{filename}"

    return jsonify({
        "ok": True,
        "url": image_url
    })


@app.route("/health")
def health():
    return "OK", 200
