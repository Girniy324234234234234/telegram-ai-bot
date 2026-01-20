def build_prompt(profile: dict) -> str:
    return (
        "Ты Telegram-бот помощник.\n\n"
        "ОБЯЗАТЕЛЬНО:\n"
        "- РОВНО 3 пункта\n"
        "- 1 строка = 1 пункт\n"
        "- без вступлений, без вопросов\n"
        "- формат:\n"
        "1️⃣ ...\n2️⃣ ...\n3️⃣ ...\n\n"
        f"Настроение: {profile['mood']}\n"
        f"Время: {profile['time']}\n"
        f"Интересы: {profile['interests']}\n"
        f"Ограничения: {profile['limits']}\n"
    )
