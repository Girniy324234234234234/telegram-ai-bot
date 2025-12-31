import telebot
import openai
from config import BOT_TOKEN, OPENAI_API_KEY
import time

# Инициализация бота и OpenAI
bot = telebot.TeleBot(BOT_TOKEN)
openai.api_key = OPENAI_API_KEY  # Установи свой OpenAI API ключ

# Словарь для хранения состояния анкеты и ответов пользователей
user_state = {}

# Функции для изменения состояния
def set_state(user_id, state):
    if user_id not in user_state:
        user_state[user_id] = {}  # Инициализация пустого словаря, если его нет
    user_state[user_id]['state'] = state

def get_state(user_id):
    return user_state.get(user_id, {}).get('state', "START")

# Функция для общения с OpenAI (для предложений досуга)
def get_openai_response(prompt):
    try:
        response = openai.completions.create(  # Новый метод для OpenAI API версии 1.0.0
            model="gpt-3.5-turbo",  # Используем gpt-3.5, или gpt-4, если доступно
            prompt=prompt,           # Простой текстовый запрос
            max_tokens=250,
            temperature=0.7
        )
        return response.choices[0].text.strip()  # Получаем ответ от модели
    except openai.error.RateLimitError:
        print("Ошибка: Превышена квота на использование API OpenAI. Попробуй снова позже.")
        bot.send_message(user_id, "Ошибка: Превышена квота на использование API OpenAI. Попробуй снова позже.")
        time.sleep(60)  # Подождать минуту перед повторной попыткой
        return None  # Возвращаем None, чтобы не отправлять запрос

# Функция для предложений по досугу с учетом интересов
def suggest_activity(user_id, interests):
    prompt = f"Пользователь интересуется {interests}. Порекомендуй ему интересные способы провести время, учитывая эти интересы."
    # Используем OpenAI для создания предложений
    ai_suggestion = get_openai_response(prompt)
    if ai_suggestion:
        bot.send_message(user_id, ai_suggestion)  # Отправляем сгенерированное сообщение от ШИ

# Обработчик команды /start
@bot.message_handler(commands=["start"])
def start(message):
    print("Команда /start получена.")
    bot.send_message(message.chat.id, "👋 Привет! Напиши /survey чтобы начать анкетирование.")

# Обработчик команды /survey — старт анкеты
@bot.message_handler(commands=["survey"])
def survey(message):
    set_state(message.from_user.id, "MOOD")  # Начинаем с вопроса про настроение
    bot.send_message(message.chat.id, "Какое у тебя настроение?")

# Обработчик всех сообщений, чтобы продолжить анкету
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    state = get_state(user_id)

    # Логика обработки анкеты в зависимости от состояния
    if state == "MOOD":
        mood = message.text
        bot.send_message(user_id, f"Твое настроение: {mood}. Сколько у тебя времени?")
        set_state(user_id, "TIME")

    elif state == "TIME":
        time = message.text
        bot.send_message(user_id, f"Ты сказал, что у тебя время: {time}. Какие у тебя интересы?")
        set_state(user_id, "INTERESTS")

    elif state == "INTERESTS":
        interests = message.text
        bot.send_message(user_id, f"Твои интересы: {interests}. Есть ли у тебя ограничения?")
        # Сохраняем интересы пользователя в словарь
        user_state[user_id]["interests"] = interests
        set_state(user_id, "LIMITS")

    elif state == "LIMITS":
        limits = message.text
        bot.send_message(user_id, f"Ты сказал, что твои ограничения: {limits}. Спасибо за участие в анкете!")
        set_state(user_id, "FINISHED")
        bot.send_message(user_id, "Теперь давай проведем время вместе! Вот несколько идей от меня:")
        # Получаем интересы из сохраненных данных
        interests = user_state[user_id].get("interests", "")
        suggest_activity(user_id, interests)  # Предлагаем активность с учетом интересов

    # Обработка запроса пользователя на рекомендации
    elif state == "FINISHED":
        if "порекомендуй" in message.text.lower():
            # Получаем интересы из сохраненных данных
            interests = user_state[user_id].get("interests", "")
            bot.send_message(user_id, "Вот что я могу тебе предложить на основе твоих интересов:")
            suggest_activity(user_id, interests)

# Основная функция для запуска бота
if __name__ == "__main__":
    print("Запуск бота...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Ошибка: {e}")
