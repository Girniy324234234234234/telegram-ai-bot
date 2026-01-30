import base64
import uuid
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

GENERATED_DIR = "miniapp/static/generated"
os.makedirs(GENERATED_DIR, exist_ok=True)


def generate_sticker(text: str) -> str:
    prompt = f"""
Telegram sticker.
Cute, bold cartoon style.
High contrast.
No text on image.
Subject: {text}
White or transparent background.
"""

    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="512x512"
    )

    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    filename = f"{uuid.uuid4()}.png"
    path = os.path.join(GENERATED_DIR, filename)

    with open(path, "wb") as f:
        f.write(image_bytes)

    return f"/static/generated/{filename}"
