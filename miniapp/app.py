import os
import base64
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__, template_folder="templates")

HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = "stabilityai/stable-diffusion-2-1"
HF_URL = f"https://api-inference.hf.co/models/{HF_MODEL}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    prompt = data.get("text")

    if not prompt:
        return jsonify({"ok": False, "error": "no prompt"}), 400

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Accept": "image/png"
    }

    payload = {
        "inputs": prompt
    }

    try:
        r = requests.post(HF_URL, headers=headers, json=payload, timeout=60)

        if r.status_code != 200:
            print("HF ERROR:", r.text)
            return jsonify({"ok": False}), 500

        image_base64 = base64.b64encode(r.content).decode("utf-8")
        return jsonify({
            "ok": True,
            "image": image_base64
        })

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"ok": False}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
