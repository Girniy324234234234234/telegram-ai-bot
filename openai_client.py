import os
from openai import OpenAI
from prompts import build_prompt

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing")

client = OpenAI(api_key=OPENAI_API_KEY)


def ask_openai(profile, user_message, mode="friend", history=None, lang="ru"):
    styles = {
        "friend": "Отвечай дружелюбно и понятно.",
        "expert": "Отвечай как эксперт, чётко и по делу.",
        "short": "Отвечай кратко и по существу."
    }

    system_prompt = (
        build_prompt(profile)
        + "\n"
        + styles.get(mode, "")
        + "\n"
        + "ЖЁСТКОЕ ПРАВИЛО:\n"
        + "Отвечай ИСКЛЮЧИТЕЛЬНО на русском языке.\n"
        + "Не используй английские слова.\n"
        + "Даже если пользователь пишет на другом языке — отвечай по-русски."
    )

    messages = [{"role": "system", "content": system_prompt}]

    if history:
        for h in history[-5:]:
            messages.append({"role": "user", "content": h})

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    return response.choices[0].message.content
