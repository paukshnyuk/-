import time
from requests.exceptions import ReadTimeout
from loader import bot
import handlers

if __name__ == '__main__':
    print("🚀 OnlyPaws Запущен!")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)
