import os
import telebot, time, re, sqlite3
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from states import SurveyState
from openai_client import ask_openai

# ===== ENV =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

ADMIN_ID = 1987556406
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

THANK_WORDS = ["спасибо", "thanks", "thank you", "thx"]

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
        "/help — Помощь и описание команд\n\n"
        "Если не знаешь с чего начать — нажми /survey"
    ),

    "creator": (
        "👨‍💻 *Создатель проекта*\n\n"
        "Проект разработан энтузиастом @astroanvt\n"
        "в сфере AI и автоматизации.\n\n"
        "Telegram: @astroanvt\n\n"
        "Instagram: @3.morozz.3\n\n"
        "Discord: @sunguys\n\n"
    ),

    "donate": (
        "💖 *Поддержать проект*\n\n"
        "Если бот оказался полезным — ты можешь\n"
        "поддержать его развитие.\n\n"
        "🔧 Новые функции\n"
        "⚡ Улучшение AI\n"
        "📈 Развитие проекта\n\n"
        "Способы поддержки (USDT TRC20) - TR7pwMfXWtT7jcJcnzzpipCXycXAfn3BDQ 🙏"
    ),

    "mood": "🙂 Какое у тебя сейчас настроение?",
    "time": "⏱ Сколько у тебя есть свободного времени?",
    "interests": "🎯 Какие у тебя интересы?",
    "limits": "⚠️ Есть ли ограничения или пожелания?",
    "ask": "✍️ Теперь напиши свой запрос 👇",
    "wait": "⏳ Подожди немного, я думаю…",
    "bye": "🙏 Рад был помочь. Удачи!"
}

    },
"en": {
    "welcome": (
        "👋 Welcome to *Astro AI Bot*\n\n"
        "🤖 I am a smart Telegram bot that helps you:\n"
        "• complete surveys\n"
        "• receive personalized AI responses\n"
        "• generate ideas and solutions\n\n"
        "👇 Use the commands below to get started"
    ),

    "help": (
        "📌 *Available commands:*\n\n"
        "/start — Main menu\n"
        "/survey — Take a survey\n"
        "/creator — About the project creator\n"
        "/donate — Support the project\n"
        "/help — Help and command description\n\n"
        "If you’re not sure where to start — tap /survey"
    ),

    "creator": (
        "👨‍💻 *Project creator*\n\n"
        "This project is developed by an enthusiast @astroanvt\n"
        "in the field of AI and automation.\n\n"
        "Telegram: @astroanvt\n\n"
        "Instagram: @3.morozz.3\n\n"
        "Discord: @sunguys\n\n"
    ),

    "donate": (
        "💖 *Support the project*\n\n"
        "If you found this bot useful, you can\n"
        "support its further development.\n\n"
        "🔧 New features\n"
        "⚡ AI improvements\n"
        "📈 Project growth\n\n"
        "Support options (USDT TRC20) — TR7pwMfXWtT7jcJcnzzpipCXycXAfn3BDQ 🙏"
    ),

    "mood": "🙂 How are you feeling right now?",
    "time": "⏱ How much free time do you have?",
    "interests": "🎯 What are your interests?",
    "limits": "⚠️ Do you have any limitations or preferences?",
    "ask": "✍️ Now write your request 👇",
    "wait": "⏳ Please wait a moment, I’m thinking…",
    "bye": "🙏 Glad I could help. Good luck!"
}


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
    return TEXTS[lang][key]

# ===== KEYBOARDS =====
def start_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("/survey"),
        KeyboardButton("/help")
    )
    kb.add(
        KeyboardButton("/creator"),
        KeyboardButton("/donate")
    )
    return kb

def idea_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("👍", callback_data="like"),
        InlineKeyboardButton("👎", callback_data="dislike"),
        InlineKeyboardButton("🌍 Language", callback_data="language")
    )
    return kb

# ===== COMMANDS =====
@bot.message_handler(commands=["start"])
def start(m):
    lang = get_lang(m.from_user.id, "")
    bot.send_message(m.chat.id, t(lang, "welcome"), reply_markup=start_menu())

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
def survey(m):
    user_state[m.from_user.id] = SurveyState.MOOD
    lang = get_lang(m.from_user.id, "")
    bot.send_message(m.chat.id, t(lang, "mood"))

# ===== MAIN HANDLER =====
@bot.message_handler(func=lambda m: True)
def handler(m):
    uid = m.from_user.id
    text = m.text.strip()

    lang = get_lang(uid, text)
    save_message(uid, text)

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
            bot.send_message(uid, t(lang, "welcome"), reply_markup=start_menu())
            return

        if time.time() - last_request.get(uid, 0) < 5:
            bot.send_message(uid, t(lang, "wait"))
            return

        last_request[uid] = time.time()

        history = get_memory(uid)
        history.append(text)
        save_memory(uid, history)

        answer = ask_openai(profile, text, "friend", history, lang)
        bot.send_message(uid, answer, reply_markup=idea_kb())

# ===== CALLBACKS =====
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data == "language":
        bot.send_message(c.from_user.id, "🌍 Language auto-detect enabled")
    bot.answer_callback_query(c.id)
