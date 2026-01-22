const tg = window.Telegram.WebApp;
tg.expand();

async function sendData() {
    const prompt = document.getElementById("prompt").value;
    const fileInput = document.getElementById("photo");
    const status = document.getElementById("status");

    let photoBase64 = null;

    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        photoBase64 = await toBase64(file);
    }

    const payload = {
        user_id: tg.initDataUnsafe?.user?.id || null,
        prompt: prompt,
        photo: photoBase64
    };

    status.innerText = "⏳ Отправка...";

    await fetch("/submit", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
    });

    // 🔥 Отправляем данные боту
    tg.sendData(JSON.stringify(payload));
    status.innerText = "✅ Отправлено в бота";
}

function toBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}
