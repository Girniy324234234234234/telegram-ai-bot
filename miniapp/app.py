import os
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

HF_API_KEY = os.getenv("HF_API_KEY")

MODEL_ID = "stabilityai/stable-diffusion-2-1"
HF_URL = f"https://router.huggingface.co/hf-inference/models/{MODEL_ID}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("text")

    if not prompt:
        return jsonify({"ok": False, "error": "empty prompt"}), 400

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": prompt
    }

    try:
        r = requests.post(HF_URL, headers=headers, json=payload, timeout=60)

        if r.status_code != 200:
            print("HF ERROR:", r.text)
            return jsonify({"ok": False, "error": "hf error"}), 500

        image_bytes = r.content
        image_base64 = image_bytes.encode("base64").decode("utf-8")

        return jsonify({
            "ok": True,
            "image": image_base64
        })

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"ok": False, "error": "server error"}), 500


if name == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
