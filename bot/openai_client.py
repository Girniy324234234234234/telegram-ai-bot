import openai
from config import OPENAI_API_KEY
from prompts import build_prompt
import json

openai.api_key = OPENAI_API_KEY

def generate_ideas(profile: dict):
    prompt = build_prompt(profile)

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Ты полезный ассистент."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8
    )

    content = response['choices'][0]['message']['content']
    return json.loads(content)

