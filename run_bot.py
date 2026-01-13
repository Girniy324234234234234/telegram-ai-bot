import os
import time
import re
import sqlite3
from datetime import datetime

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from states import SurveyState
from openai_client import ask_openai

# ===== ENV =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

DB_FILE = "bot.db"

bot = telebot.TeleBot(BOT_TOKEN)
print("🚀 Bot started")

# ===== DATABASE =====
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    language TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    text TEXT,
    created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS memory (
    telegram_id INTEGER PRIMARY KEY,
    history TEXT
)
""")

conn.commit()

# ===== STATE =====
user_state = {}
user_data = {}
last_request = {}

THANK_WORDS = ["спасибо"]

TEXTS = {
    "ru": {
        "welcome": (
            "👋 Добро пожаловать в *Astro AI Bot*\n\n"
            "🤖 Я умный Telegram-бот.\n\n"
            "👇 Используй команды:\n"
            "/survey — пройти анкету\n"
            "/help — помощь"
        ),
        "help": (
            "📌 *Команды:*\n\n"
            "/start — главное меню\n"
            "/survey — анкетирование\n"
            "/creator — о создателе\n"
            "/donate — поддержка\n"
            "/help — помощь"
        ),
        "creator": "👨‍💻 Создатель: @astroanvt",
        "donate": "💖 Поддержка проекта: USDT TRC20\nTR7pwMfXWtT7jcJcnzzpipCXycXAfn3BDQ",
        "mood": "🙂 Какое у тебя настроение?",
        "time": "⏱ Сколько у тебя есть свободного времени?",
        "interests": "🎯 Какие у тебя интересы?",
        "limits": "⚠️ Есть ли ограничения?",
        "ask": "✍️ Напиши свой запрос 👇",
        "wait": "⏳ Думаю...",
        "bye": "🙏 Рад был помочь!"
    }
}

# ===== HELPERS =====
def get_lang(uid, text):
    cursor.execute("SELECT language FROM users WHERE telegram_id=?", (uid,))
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute(
        "INSERT INTO users VALUES (?, ?, ?)",
        (uid, None, "ru")
    )
    conn.commit()
    return "ru"


def save_message(uid, text):
    cursor.execute(
        "INSERT INTO messages (telegram_id, text, created_at) VALUES (?, ?, ?)",
        (uid, text, datetime.now().isoformat())
    )
    conn.commit()


def get_memory(uid):
    cursor.execute("SELECT history FROM memory WHERE telegram_id=?", (uid,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO memory VALUES (?, ?)", (uid, ""))
        conn.commit()
        return []
    return row[0].split("|") if row[0] else []


def save_memory(uid, history):
    cursor.execute(
        "UPDATE memory SET history=? WHERE telegram_id=?",
        ("|".join(history), uid)
    )
    conn.commit()


def t(lang, key):
    return TEXTS["ru"][key]


# ===== COMMANDS =====
@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.chat.id, t("ru", "welcome"), parse_mode="Markdown")


@bot.message_handler(commands=["help"])
def help_cmd(m):
    bot.send_message(m.chat.id, t("ru", "help"), parse_mode="Markdown")


@bot.message_handler(commands=["creator"])
def creator_cmd(m):
    bot.send_message(m.chat.id, t("ru", "creator"))


@bot.message_handler(commands=["donate"])
def donate_cmd(m):
    bot.send_message(m.chat.id, t("ru", "donate"))


@bot.message_handler(commands=["survey"])
def survey(m):
    user_state[m.from_user.id] = SurveyState.MOOD
    bot.send_message(m.chat.id, t("ru", "mood"))


# ===== MAIN HANDLER =====
@bot.message_handler(func=lambda m: True)
def handler(m):
    if m.text.startswith("/"):
        return

    uid = m.from_user.id
    text = m.text.strip()

    save_message(uid, text)

    if any(w in text.lower() for w in THANK_WORDS):
        bot.send_message(uid, t("ru", "bye"))
        return

    state = user_state.get(uid)

    if state == SurveyState.MOOD:
        user_data.setdefault(uid, {})["mood"] = text
        user_state[uid] = SurveyState.TIME
        bot.send_message(uid, t("ru", "time"))

    elif state == SurveyState.TIME:
        user_data[uid]["time"] = text
        user_state[uid] = SurveyState.INTERESTS
        bot.send_message(uid, t("ru", "interests"))

    elif state == SurveyState.INTERESTS:
        user_data[uid]["interests"] = text
        user_state[uid] = SurveyState.LIMITS
        bot.send_message(uid, t("ru", "limits"))

    elif state == SurveyState.LIMITS:
        user_data[uid]["limits"] = text
        user_state[uid] = None
        bot.send_message(uid, t("ru", "ask"))

    else:
        profile = user_data.get(uid)
        if not profile:
            bot.send_message(uid, t("ru", "welcome"))
            return

        if time.time() - last_request.get(uid, 0) < 5:
            bot.send_message(uid, t("ru", "wait"))
            return

        last_request[uid] = time.time()

        history = get_memory(uid)
        history.append(text)
        save_memory(uid, history)

        answer = ask_openai(profile, text, "friend", history, "ru")
        bot.send_message(uid, answer)


# ===== RUN =====
if __name__ == "__main__":
    bot.infinity_polling(skip_pending=True)
