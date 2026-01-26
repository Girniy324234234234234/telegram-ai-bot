import os
import uuid
import base64

from flask import Flask, request, jsonify, render_template
from openai import OpenAI

# ================== CONFIG ==================

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

GENERATED_DIR = "miniapp/static/generated"
os.makedirs(GENERATED_DIR, exist_ok=True)

# ================== ROUTES ==================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    prompt_text = data.get("text", "").strip()

    if not prompt_text:
        return jsonify({"ok": False, "error": "empty text"}), 400

    try:
        # === IMAGE GENERATION ===
        result = client.images.generate(
            model="gpt-image-1",
            prompt=f"Telegram sticker, simple, flat, cartoon style, "
                   f"high contrast, transparent background. Subject: {prompt_text}",
            size="auto"
        )

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(GENERATED_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        # === VERY IMPORTANT PART ===
        return jsonify({
            "ok": True,
            "url": f"/static/generated/{filename}"
        })

    except Exception as e:
        print("IMAGE ERROR:", e)
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


# ================== RUN ==================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        debug=False
    )
