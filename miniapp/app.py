import os
import base64
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

HF_API_KEY = os.getenv("HF_API_KEY")

HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        text = data.get("text")

        if not text:
            return jsonify({"ok": False, "error": "no text"}), 400

        payload = {
            "inputs": f"sticker, cute, simple, vector style, {text}"
        }

        r = requests.post(
            HF_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        if r.status_code != 200:
            print("HF ERROR:", r.text)
            return jsonify({"ok": False}), 500

        image_bytes = r.content
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        return jsonify({
            "ok": True,
            "image": image_base64
        })

    except Exception as e:
        print("GEN ERROR:", e)
        return jsonify({"ok": False}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
