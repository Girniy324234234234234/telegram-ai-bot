import os
from openai import OpenAI
from prompts import build_prompt

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing")

client = OpenAI(api_key=OPENAI_API_KEY)

def ask_openai(profile, user_message, mode="friend", memory=None, language="auto"):
    styles = {
        "friend": "Be friendly.",
        "expert": "Be an expert, clear and helpful.",
        "short": "Be максимально кратким."
    }

    if language == "ru":
        lang_rule = "Answer ONLY in Russian."
    elif language == "en":
        lang_rule = "Answer ONLY in English."
    else:
        lang_rule = "Answer in the same language as the user."

    system_prompt = (
        build_prompt(profile)
        + "\n"
        + styles.get(mode, "")
        + "\n"
        + lang_rule
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.5,
        max_tokens=200
    )

    return response.choices[0].message.content
