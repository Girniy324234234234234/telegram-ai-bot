import os
from openai import OpenAI
from prompts import build_prompt

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing")

client = OpenAI(api_key=OPENAI_API_KEY)


def ask_openai(profile, user_message, mode="friend", history=None, language="auto"):
    styles = {
        "friend": "Be friendly and helpful.",
        "expert": "Be an expert, clear and helpful.",
        "short": "Answer briefly and to the point."
    }

    if language == "ru":
        lang_rule = (
            "Answer ONLY in Russian. "
            "Do NOT use English words, phrases, or sentences."
        )
    elif language == "en":
        lang_rule = (
            "Answer ONLY in English. "
            "Do NOT use Russian words, phrases, or sentences."
        )
    else:
        lang_rule = (
            "Answer strictly in the same language as the user's last message."
        )

    system_prompt = (
        build_prompt(profile)
        + "\n"
        + styles.get(mode, "")
        + "\n"
        + lang_rule
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    return response.choices[0].message.content
