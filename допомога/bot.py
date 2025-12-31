import telebot
from config import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Бот работает ✅\nНапишите /survey чтобы пройти анкету")

if __name__ == "__main__":
    bot.infinity_polling()
