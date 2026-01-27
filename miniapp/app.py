import os
import uuid
import base64
from flask import Flask, request, jsonify, render_template
from openai import OpenAI

# =========================
# CONFIG
# =========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

GENERATED_DIR = "miniapp/static/generated"
os.makedirs(GENERATED_DIR, exist_ok=True)

# =========================
# ROUTES
# =========================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    prompt = data.get("text", "").strip()

    if not prompt:
        return jsonify({
            "ok": False,
            "error": "Empty text"
        }), 400

    try:
        # 🔥 IMAGE GENERATION
        result = client.images.generate(
            model="gpt-image-1",
            prompt=f"Sticker, simple, flat, transparent background, {prompt}",
            size="auto"
        )

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(GENERATED_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        # ✅ ВАЖНО: ok = True
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


# =========================
# START
# =========================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
