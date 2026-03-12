import matplotlib.pyplot as plt
import io
from loader import bot

# Настраиваем matplotlib для работы на сервере (без экрана)
plt.switch_backend('Agg')

def send_plot(chat_id, dates, values, title, ylabel, color='blue'):
    # Проверка: если данных нет, график не строим
    if not dates:
        bot.send_message(chat_id, "📉 Нет данных для построения графика.")
        return

    # Создаем фигуру
    plt.figure(figsize=(10, 6))

    # Рисуем линию
    plt.plot(dates, values, marker='o', linestyle='-', color=color, linewidth=2)

    # Дизайн
    plt.title(title, fontsize=16)
    plt.xlabel('Дата', fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Сохраняем график в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    # Отправляем фото в Telegram
    try:
        bot.send_photo(chat_id, buf, caption=f"📊 {title}")
    except Exception as e:
        print(f"Ошибка отправки графика: {e}")
        bot.send_message(chat_id, "❌ Не удалось отправить график.")
