<script>
const tg = window.Telegram.WebApp;
tg.expand();

async function generateSticker() {
    const prompt = document.getElementById("prompt").value;
    const status = document.getElementById("status");
    const img = document.getElementById("result");

    if (!prompt) {
        status.innerText = "❌ Введи описание";
        return;
    }

    status.innerText = "🎨 Генерирую стикер...";
    img.style.display = "none";

    try {
        const res = await fetch("/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: prompt })
        });

        const data = await res.json();

        if (!data.ok) {
            status.innerText = "❌ Ошибка генерации";
            return;
        }

        img.src = data.url + "?t=" + Date.now(); // cache bust
        img.style.display = "block";
        status.innerText = "✅ Стикер готов";

    } catch (e) {
        console.error(e);
        status.innerText = "❌ Сервер недоступен";
    }
}
</script>
