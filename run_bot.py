import os
import time
import re
import sqlite3
import telebot
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from states import SurveyState
from openai_client import ask_openai

# ===== ENV =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

ADMIN_ID = 1987556406
DB_FILE = "bot.db"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
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

# ===== TEXTS =====
TEXTS = {
    "ru": {
        "welcome": (
            "👋 Добро пожаловать в *Astro AI Bot*\n\n"
            "🤖 Я — умный Telegram-бот, который помогает:\n"
            "• проходить анкетирование\n"
            "• получать персональные AI-ответы\n"
            "• создавать идеи и решения\n\n"
            "👇 Используй команды ниже, чтобы начать"
        ),
        "help": (
            "📌 *Доступные команды:*\n\n"
            "/start — Главное меню\n"
            "/survey — Пройти анкетирование\n"
            "/creator — О создателе проекта\n"
            "/donate — Поддержать проект\n"
            "/help — Помощь\n"
        ),
        "creator": (
            "👨‍💻 *Создатель проекта*\n\n"
            "Проект разработан @astroanvt\n"
            "в сфере AI и автоматизации."
        ),
        "donate": (
            "💖 *Поддержать проект*\n\n"
            "USDT TRC20:\n"
            "`TR7pwMfXWtT7jcJcnzzpipCXycXAfn3BDQ`"
        ),
        "mood": "🙂 Какое у тебя настроение?",
        "time": "⏱ Сколько у тебя есть времени?",
        "interests": "🎯 Какие у тебя интересы?",
        "limits": "⚠️ Есть ли ограничения?",
        "ask": "✍️ Напиши свой запрос",
        "wait": "⏳ Думаю...",
        "bye": "🙏 Рад был помочь!"
    },

    "en": {
        "welcome": (
            "👋 Welcome to *Astro AI Bot*\n\n"
            "🤖 I am a smart Telegram bot that helps you:\n"
            "• complete surveys\n"
            "• get AI-powered answers\n"
            "• generate ideas and solutions\n\n"
            "👇 Use the commands below to get started"
        ),
        "help": (
            "📌 *Available commands:*\n\n"
            "/start — Main menu\n"
            "/survey — Take a survey\n"
            "/creator — About the creator\n"
            "/donate — Support the project\n"
            "/help — Help\n"
        ),
        "creator": (
            "👨‍💻 *Project creator*\n\n"
            "Created by @astroanvt\n"
            "AI & automation enthusiast."
        ),
        "donate": (
            "💖 *Support the project*\n\n"
            "USDT TRC20:\n"
            "`TR7pwMfXWtT7jcJcnzzpipCXycXAfn3BDQ`"
        ),
        "mood": "🙂 How do you feel?",
        "time": "⏱ How much time do you have?",
        "interests": "🎯 Your interests?",
        "limits": "⚠️ Any limitations?",
        "ask": "✍️ Type your request",
        "wait": "⏳ Thinking...",
        "bye": "🙏 Glad to help!"
    }
}

THANK_WORDS = ["спасибо", "thanks", "thank you", "thx"]

# ===== HELPERS =====
def detect_language(text):
    return "ru" if re.search(r"[а-яА-Я]", text) else "en"

def get_lang(uid, text):
    cursor.execute("SELECT language FROM users WHERE telegram_id=?", (uid,))
    row = cursor.fetchone()
    if row:
        return row[0]
    lang = detect_language(text)
    cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (uid, None, lang))
    conn.commit()
    return lang

def t(lang, key):
    return TEXTS.get(lang, TEXTS["en"]).get(key, "")

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

# ===== COMMANDS =====
@bot.message_handler(commands=["start"])
def start_cmd(m):
    lang = get_lang(m.from_user.id, "")
    bot.send_message(m.chat.id, t(lang, "welcome"))

@bot.message_handler(commands=["help"])
def help_cmd(m):
    lang = get_lang(m.from_user.id, "")
    bot.send_message(m.chat.id, t(lang, "help"))

@bot.message_handler(commands=["creator"])
def creator_cmd(m):
    lang = get_lang(m.from_user.id, "")
    bot.send_message(m.chat.id, t(lang, "creator"))

@bot.message_handler(commands=["donate"])
def donate_cmd(m):
    lang = get_lang(m.from_user.id, "")
    bot.send_message(m.chat.id, t(lang, "donate"))

@bot.message_handler(commands=["survey"])
def survey_cmd(m):
    user_state[m.from_user.id] = SurveyState.MOOD
    lang = get_lang(m.from_user.id, "")
    bot.send_message(m.chat.id, t(lang, "mood"))

# ===== STATE =====
user_state = {}
user_data = {}
last_request = {}

# ===== MAIN HANDLER =====
@bot.message_handler(func=lambda m: True)
def handler(m):
    uid = m.from_user.id
    text = m.text.strip()
    lang = get_lang(uid, text)

    if any(w in text.lower() for w in THANK_WORDS):
        bot.send_message(uid, t(lang, "bye"))
        return

    state = user_state.get(uid)

    if state == SurveyState.MOOD:
        user_data.setdefault(uid, {})["mood"] = text
        user_state[uid] = SurveyState.TIME
        bot.send_message(uid, t(lang, "time"))

    elif state == SurveyState.TIME:
        user_data[uid]["time"] = text
        user_state[uid] = SurveyState.INTERESTS
        bot.send_message(uid, t(lang, "interests"))

    elif state == SurveyState.INTERESTS:
        user_data[uid]["interests"] = text
        user_state[uid] = SurveyState.LIMITS
        bot.send_message(uid, t(lang, "limits"))

    elif state == SurveyState.LIMITS:
        user_data[uid]["limits"] = text
        user_state[uid] = None
        bot.send_message(uid, t(lang, "ask"))

    else:
        profile = user_data.get(uid)
        if not profile:
            bot.send_message(uid, t(lang, "welcome"))
            return

        if time.time() - last_request.get(uid, 0) < 5:
            bot.send_message(uid, t(lang, "wait"))
            return

        last_request[uid] = time.time()
        history = get_memory(uid)
        history.append(text)
        save_memory(uid, history)

        answer = ask_openai(profile, text, "friend", history, lang)
        bot.send_message(uid, answer)

# ===== RUN =====
if __name__ == "__main__":
    print("🚀 Polling started")
    bot.infinity_polling(skip_pending=True)
