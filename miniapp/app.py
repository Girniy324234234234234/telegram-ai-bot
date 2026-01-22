import os
import uuid
import base64
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

# ===== CONFIG =====
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


# ===== ROUTES =====
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
Sticker for Telegram.
Style: cute, bold, cartoon, high contrast.
No text on image.
Idea: {text}
White or transparent background.
"""

result = client.responses.create(
    model="gpt-4.1",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": prompt},
            {"type": "output_image", "size": "512x512"}
        ]
    }]
)

image_base64 = result.output[0].content[0].image_base64


    filename = f"{uuid.uuid4()}.png"
    path = os.path.join(GENERATED_DIR, filename)

    with open(path, "wb") as f:
        f.write(image_bytes)

    return jsonify({
        "ok": True,
        "url": f"/static/generated/{filename}"
    })
