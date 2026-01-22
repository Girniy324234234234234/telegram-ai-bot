from flask import Flask, render_template, request, jsonify

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    data = request.json

    # то, что придёт из Telegram WebApp
    prompt = data.get("prompt")
    photo = data.get("photo")  # base64 или null
    user_id = data.get("user_id")

    print("📥 MINIAPP DATA:", data)

    # ⚠️ пока просто возвращаем OK
    # дальше ты отправишь это в бота
    return jsonify({"status": "ok"})
