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

# ===== TEXTS =====
TEXTS = {
    "ru": {
        "welcome": (
            "👋 Добро пожаловать в *Astro AI Bot*\n\n"
            "🤖 Я умный Telegram-бот.\n"
            "Помогаю с анкетированием и AI-ответами.\n\n"
            "👇 Используй команды ниже"
        ),

        "help": (
            "📌 *Доступные команды:*\n\n"
            "/start — Главное меню\n"
            "/survey — Пройти анкетирование\n"
            "/creator — О создателе\n"
            "/donate — Поддержать проект\n"
            "/affiliate — Партнёрская программа\n"
            "/status — Статус использования\n"
            "/help — Помощь"
        ),

        "creator": (
            "👨‍💻 *Создатель проекта*\n\n"
            "Проект разработан @astroanvt\n"
            "AI и автоматизация"
        ),

        "donate": (
            "💖 *Поддержка проекта*\n\n"
            "USDT TRC20:\n"
            "`TR7pwMfXWtT7jcJcnzzpipCXycXAfn3BDQ`"
        ),

        "affiliate": (
            "🤝 *Партнёрская программа*\n\n"
            "Приглашай друзей и получай бонусы.\n"
            "Реферальная система будет добавлена позже."
        ),

        "status": (
            "📊 *Статус использования*\n\n"
            "Статус: бесплатно\n"
            "Лимиты: без ограничений"
        ),

        "mood": "🙂 Какое у тебя сейчас настроение?",
        "time": "⏱ Сколько у тебя есть свободного времени?",
        "interests": "🎯 Какие у тебя интересы?",
        "limits": "⚠️ Есть ли ограничения или пожелания?",
        "ask": "✍️ Теперь напиши свой запрос 👇",
        "wait": "⏳ Подожди немного, я думаю…",
        "bye": "🙏 Рад был помочь!"
    }
}

# ===== HELPERS =====
def detect_language(text: str) -> str:
    return "ru"

def get_lang(uid, text):
    cursor.execute("SELECT language FROM users WHERE telegram_id=?", (uid,))
    row = cursor.fetchone()
    if row:
        return row[0]
    lang = "ru"
    cursor.execute(
        "INSERT OR REPLACE INTO users VALUES (?, ?, ?)",
        (uid, None, lang)
    )
    conn.commit()
    return lang

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
    return TEXTS["ru"].get(key, "")

# ===== COMMANDS =====
@bot.message_handler(commands=["start"])
def cmd_start(m):
    bot.send_message(m.chat.id, t("ru", "welcome"), parse_mode="Markdown")

@bot.message_handler(commands=["help"])
def cmd_help(m):
    bot.send_message(m.chat.id, t("ru", "help"), parse_mode="Markdown")

@bot.message_handler(commands=["creator"])
def cmd_creator(m):
    bot.send_message(m.chat.id, t("ru", "creator"), parse_mode="Markdown")

@bot.message_handler(commands=["donate"])
def cmd_donate(m):
    bot.send_message(m.chat.id, t("ru", "donate"), parse_mode="Markdown")

@bot.message_handler(commands=["affiliate"])
def cmd_affiliate(m):
    bot.send_message(m.chat.id, t("ru", "affiliate"), parse_mode="Markdown")

@bot.message_handler(commands=["status"])
def cmd_status(m):
    bot.send_message(m.chat.id, t("ru", "status"), parse_mode="Markdown")

@bot.message_handler(commands=["survey"])
def cmd_survey(m):
    user_state[m.from_user.id] = SurveyState.MOOD
    bot.send_message(m.chat.id, t("ru", "mood"))

# ===== MAIN HANDLER =====
@bot.message_handler(func=lambda m: True)
def main_handler(m):
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
            bot.send_message(uid, t("ru", "welcome"), parse_mode="Markdown")
            return

        if time.time() - last_request.get(uid, 0) < 5:
            bot.send_message(uid, t("ru", "wait"))
            return

        last_request[uid] = time.time()

        history = get_memory(uid)
        history.append(text)
        save_memory(uid, history)

        answer = ask_openai(profile, text, "friend", history)
        bot.send_message(uid, answer)
        @bot.message_handler(content_types=["web_app_data"])
def web_app_handler(m):
    uid = m.from_user.id
    prompt = m.web_app_data.data

    bot.send_message(
        uid,
        f"🎨 Запрос на стикер принят:\n\n{prompt}\n\n⏳ Генерирую..."
    )

    # позже сюда добавим генерацию картинки

