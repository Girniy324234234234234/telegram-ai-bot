import os
from openai import OpenAI
from prompts import build_prompt

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_openai(profile, user_message, mode="friend", memory=None, language="auto"):
    styles = {
        "friend": "Be friendly.",
        "expert": "Be an expert, clear and helpful.",
        "short": "Be максимально кратким."
    }

    lang_rule = ""
    if language == "ru":
        lang_rule = "Answer ONLY in Russian."
    elif language == "en":
        lang_rule = "Answer ONLY in English."
    else:
        lang_rule = "Answer in the same language as the user."

    memory_block = ""
    if memory:
        if memory["likes"]:
            memory_block += f"\nUser likes: {', '.join(memory['likes'][-3:])}"
        if memory["dislikes"]:
            memory_block += f"\nUser dislikes: {', '.join(memory['dislikes'][-3:])}"

    system_prompt = (
        build_prompt(profile)
        + "\n"
        + styles.get(mode, "")
        + "\n"
        + lang_rule
        + memory_block
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
