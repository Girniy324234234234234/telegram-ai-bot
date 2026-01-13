from flask import Flask, request, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Astro Sticker Generator</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            background: #0f0f0f;
            color: white;
            font-family: Arial;
            padding: 20px;
        }
        textarea {
            width: 100%;
            height: 100px;
            border-radius: 10px;
            padding: 10px;
        }
        button {
            margin-top: 15px;
            padding: 15px;
            width: 100%;
            border-radius: 10px;
            border: none;
            background: #6c5ce7;
            color: white;
            font-size: 16px;
        }
    </style>
</head>
<body>

<h2>🎨 Генерация стикера</h2>

<p>Опиши стикер:</p>
<textarea id="prompt" placeholder="Кот в космосе, стиль мультфильма"></textarea>

<button onclick="send()">✨ Сгенерировать</button>

<script>
const tg = window.Telegram.WebApp;
tg.expand();

function send() {
    const text = document.getElementById("prompt").value;
    tg.sendData(text);
}
</script>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)
