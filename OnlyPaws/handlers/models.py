from telebot import types
from loader import bot, reg_cache, payment_cache
from database import get_db_connection, get_user_role
from utils.ai import is_cat_ai
from utils.plotting import send_plot
from config import CATS_BREEDS, CATS_COLORS, CATS_EYES, CATS_AGES
from handlers.common import create_keyboard, get_menu, get_logged_user_id

# РАБОТА С ФОТОГРАФИЯМИ

def add_extra_photo_start(message):
    msg = bot.send_message(message.chat.id, "Отправьте фото для добавления в альбом:")
    bot.register_next_step_handler(msg, add_extra_photo_finish)

def add_extra_photo_finish(message):
    if not message.photo:
        bot.send_message(message.chat.id, "Нужно отправить именно фото!")
        return

    # Проверка через ИИ
    bot.send_message(message.chat.id, "🤖 ИИ проверяет фото...")
    if not is_cat_ai(message.photo[-1].file_id):
        bot.send_message(message.chat.id, "⛔ ИИ считает, что это не кот. Фото не добавлено.")
        return

    uid = get_logged_user_id(message.chat.id)
    conn = get_db_connection()
    cur = conn.cursor()

    # Получаем ID кота текущего пользователя
    cur.execute("SELECT id FROM cats WHERE owner_id=%s", (uid,))
    cat = cur.fetchone()

    if cat:
        cur.execute("INSERT INTO cat_photos (cat_id, file_id) VALUES (%s, %s)", (cat[0], message.photo[-1].file_id))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Фото успешно добавлено в альбом!")
    else:
        bot.send_message(message.chat.id, "❌ Ошибка: у вас нет анкеты кота.")

    conn.close()


def change_avatar_start(message):
    msg = bot.send_message(message.chat.id, "Отправьте новое фото для аватарки:")
    bot.register_next_step_handler(msg, change_avatar_finish)

def change_avatar_finish(message):
    if not message.photo:
        bot.send_message(message.chat.id, "Нужно отправить фото!")
        return

    bot.send_message(message.chat.id, "🤖 ИИ проверяет...")
    if not is_cat_ai(message.photo[-1].file_id):
        bot.send_message(message.chat.id, "⛔ Это не кот! Аватарка не изменена.")
        return

    uid = get_logged_user_id(message.chat.id)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE cats SET avatar_url=%s WHERE owner_id=%s", (message.photo[-1].file_id, uid))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, "✅ Аватарка обновлена!")

# РЕДАКТИРОВАНИЕ АНКЕТЫ
def edit_profile_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Кот ♂️", "Кошечка ♀️")
    bot.register_next_step_handler(bot.send_message(message.chat.id, "Выберите пол:", reply_markup=markup), edit_gender)

def edit_gender(message):
    # Используем reg_cache для временного хранения данных редактирования
    reg_cache[message.chat.id] = {'gender': message.text}
    bot.register_next_step_handler(bot.send_message(message.chat.id, "Порода:", reply_markup=create_keyboard(CATS_BREEDS)), edit_breed)

def edit_breed(message):
    reg_cache[message.chat.id]['breed'] = message.text
    bot.register_next_step_handler(bot.send_message(message.chat.id, "Цвет шерсти:", reply_markup=create_keyboard(CATS_COLORS)), edit_fur)

def edit_fur(message):
    reg_cache[message.chat.id]['fur'] = message.text
    bot.register_next_step_handler(bot.send_message(message.chat.id, "Цвет глаз:", reply_markup=create_keyboard(CATS_EYES)), edit_eyes)

def edit_eyes(message):
    reg_cache[message.chat.id]['eyes'] = message.text
    bot.register_next_step_handler(bot.send_message(message.chat.id, "Возраст:", reply_markup=create_keyboard(CATS_AGES)), edit_age)

def edit_age(message):
    d = reg_cache[message.chat.id]
    d['age'] = message.text
    uid = get_logged_user_id(message.chat.id)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE cats SET gender=%s, breed=%s, fur_color=%s, eye_color=%s, age_category=%s WHERE owner_id=%s", 
                (d['gender'], d['breed'], d['fur'], d['eyes'], d['age'], uid))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, "✅ Анкета успешно обновлена!", reply_markup=get_menu('model'))

# ФИНАНСЫ (ВЫВОД СРЕДСТВ)
def withdraw_start(message):
    msg = bot.send_message(message.chat.id, "Введите сумму для вывода (руб):", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, withdraw_card)

def withdraw_card(message):
    try:
        amt = float(message.text)
        if amt <= 0: raise ValueError

        # Проверка баланса
        uid = get_logged_user_id(message.chat.id)
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT balance FROM users WHERE id=%s", (uid,))
        balance = cur.fetchone()[0]
        conn.close()

        if balance < amt:
            bot.send_message(message.chat.id, f"❌ Недостаточно средств. Ваш баланс: {balance}р")
            return

        payment_cache[message.chat.id] = {'amount': amt, 'type': 'withdraw'}
        bot.register_next_step_handler(bot.send_message(message.chat.id, "Введите номер карты/кошелька:"), withdraw_process)
    except:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректное число.")

def withdraw_process(message):
    data = payment_cache.get(message.chat.id)
    uid = get_logged_user_id(message.chat.id)

    conn = get_db_connection()
    cur = conn.cursor()

    # Списание средств
    cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (data['amount'], uid))

    # Запись в историю
    cur.execute("INSERT INTO transactions (user_id, amount, operation_type, description) VALUES (%s, %s, 'withdraw', 'Вывод средств')", 
                (uid, data['amount']))

    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, f"✅ Заявка на вывод {data['amount']}р принята! (Карта: {message.text})", reply_markup=get_menu('model'))

# ГРАФИКИ И ИСТОРИЯ
def show_my_income_graph(message):
    uid = get_logged_user_id(message.chat.id)
    conn = get_db_connection()
    cur = conn.cursor()

    # Берем только поступления
    query = """
        SELECT DATE(created_at), SUM(amount) 
        FROM transactions 
        WHERE user_id=%s AND operation_type IN ('don_in', 'sub_in') 
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """
    cur.execute(query, (uid,))
    data = cur.fetchall()
    conn.close()

    if not data:
        bot.send_message(message.chat.id, "📉 У вас пока нет доходов для графика.")
        return

    dates = [row[0].strftime('%d.%m') for row in data]
    values = [row[1] for row in data]

    send_plot(message.chat.id, dates, values, "Мой Доход", "Сумма (руб)", "purple")

def show_history(chat_id):
    uid = get_logged_user_id(chat_id)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT amount, description, operation_type, created_at FROM transactions WHERE user_id=%s ORDER BY id DESC LIMIT 10", (uid,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        bot.send_message(chat_id, "История операций пуста.")
        return

    text = "<b>📜 Последние операции:</b>\n\n"
    for r in rows:
        am, desc, op, date = r
        d_str = date.strftime('%d.%m %H:%M')

        # Иконки для красоты
        if op == 'deposit': icon = "🟢"
        elif op == 'withdraw': icon = "🔴"
        elif op in ['don_in', 'sub_in']: icon = "📈"
        elif op in ['don_out', 'sub_out']: icon = "💸"
        else: icon = "⚪️"

        text += f"{icon} <code>{d_str}</code>: <b>{am}₽</b>\nℹ️ {desc}\n\n"

    bot.send_message(chat_id, text, parse_mode='HTML')
