import os
import uuid
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

# ================== INIT ==================
app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing")

client = OpenAI(api_key=OPENAI_API_KEY)

GENERATED_DIR = "miniapp/static/generated"
os.makedirs(GENERATED_DIR, exist_ok=True)

# ================== ROUTES ==================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    prompt = data.get("text", "").strip()

    if not prompt:
        return jsonify({"error": "empty text"}), 400

    try:
        # 🔥 ГЕНЕРАЦИЯ ЧЕРЕЗ OPENAI
        result = client.images.generate(
            model="gpt-image-1",
            prompt=f"Sticker, simple, flat, transparent background, {prompt}",
            size="512x512"
        )

        image_base64 = result.data[0].b64_json
        image_bytes = __import__("base64").b64decode(image_base64)

        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(GENERATED_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        return jsonify({
            "ok": True,
            "url": f"/static/generated/{filename}"
        })

    except Exception as e:
        print("IMAGE ERROR:", e)
        return jsonify({"error": "generation failed"}), 500


# ================== RUN ==================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
