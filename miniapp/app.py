from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageDraw
import uuid
import os

app = Flask(__name__)

GENERATED_DIR = "miniapp/static/generated"
os.makedirs(GENERATED_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"error": "empty text"}), 400

    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((40, 230), text[:20], fill="white")

    filename = f"{uuid.uuid4()}.png"
    path = os.path.join(GENERATED_DIR, filename)
    img.save(path)

    return jsonify({
        "ok": True,
        "url": f"/static/generated/{filename}"
    })
