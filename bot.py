import telebot

# Вставь сюда токен, который дал BotFather
TOKEN = "8561521206:AAEipzpPNEwC_Xba8MmEEcFI_6n9MRRVHF8"

bot = telebot.TeleBot(TOKEN)

# Сообщение при старте /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Бот запущен 🚀 Привет!")

# Эхо: бот будет повторять любое сообщение
@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.send_message(message.chat.id, f"Ты написал: {message.text}")

# Вывод в терминал, чтобы понимать, что бот стартовал
print("Бот запускается...")

# Запуск бота
bot.polling()
