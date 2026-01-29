import os
import base64
import requests
from flask import Flask, request, jsonify, render_template

# ---------------- CONFIG ----------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")

HF_MODEL = "stabilityai/stable-diffusion-2-1"
HF_URL = f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}"

# ---------------------------------------

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json(force=True)
        prompt = data.get("text", "").strip()

        if not prompt:
            return jsonify({"ok": False, "error": "empty prompt"}), 400

        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": prompt
        }

        hf_response = requests.post(
            HF_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        if hf_response.status_code != 200:
            print("HF ERROR:", hf_response.text)
            return jsonify({"ok": False, "error": "hf_error"}), 500

        image_bytes = hf_response.content
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        return jsonify({
            "ok": True,
            "image": image_base64
        })

    except Exception as e:
        print("SERVER ERROR:", str(e))
        return jsonify({"ok": False, "error": "server_error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
