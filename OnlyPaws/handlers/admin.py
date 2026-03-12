from telebot import types
from loader import bot, admin_action_cache
from database import get_db_connection
from utils.plotting import send_plot

# СТАТИСТИКА ПРОЕКТА
def admin_stats(message):
    conn = get_db_connection()
    cur = conn.cursor()

    # Количество пользователей
    cur.execute("SELECT COUNT(*) FROM users")
    tu = cur.fetchone()[0]

    # Количество котов
    cur.execute("SELECT COUNT(*) FROM cats")
    tc = cur.fetchone()[0]

    # Общая сумма денег
    cur.execute("SELECT SUM(balance) FROM users")
    tm = cur.fetchone()[0] or 0

    # Количество транзакций
    cur.execute("SELECT COUNT(*) FROM transactions")
    tt = cur.fetchone()[0]

    conn.close()

    bot.send_message(
        message.chat.id,
        f"📊 <b>СТАТИСТИКА ONLYPAWS</b>\n\n"
        f"👥 Юзеров: {tu}\n"
        f"🐈 Котов: {tc}\n"
        f"💰 Денег в системе: {tm}р\n"
        f"🔄 Транзакций: {tt}", 
        parse_mode='HTML'
    )

# БАН/РАЗБАН

def admin_ban_start(message, action):
    admin_action_cache[message.chat.id] = action
    text = "БАНА" if action == 'ban' else "РАЗБАНА"
    msg = bot.send_message(message.chat.id, f"Введите ЛОГИН пользователя для {text}:")
    bot.register_next_step_handler(msg, admin_ban_process)

def admin_ban_process(message):
    login = message.text
    action = admin_action_cache.get(message.chat.id)

    conn = get_db_connection()
    cur = conn.cursor()

    # Проверяем, существует ли пользователь
    cur.execute("SELECT id FROM users WHERE login = %s", (login,))
    if not cur.fetchone():
        bot.send_message(message.chat.id, "❌ Пользователь с таким логином не найден.")
        conn.close()
        return

    is_banned = True if action == "ban" else False

    # Обновляем статус
    cur.execute("UPDATE users SET is_banned = %s WHERE login = %s", (is_banned, login))
    conn.commit()
    conn.close()

    status_text = "ЗАБАНЕН 🚫" if is_banned else "РАЗБАНЕН ✅"
    bot.send_message(message.chat.id, f"Пользователь {login} успешно {status_text}!")


# УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ

def admin_delete_start(message):
    msg = bot.send_message(message.chat.id, "🗑 Введите ЛОГИН для удаления (ЭТО НЕОБРАТИМО):")
    bot.register_next_step_handler(msg, admin_delete_process)

def admin_delete_process(message):
    login = message.text
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, role FROM users WHERE login = %s", (login,))
    user = cur.fetchone()

    if not user:
        bot.send_message(message.chat.id, "❌ Пользователь не найден.")
        conn.close()
        return

    user_id, role = user

    # Защита от удаления админа
    if role == 'admin':
        bot.send_message(message.chat.id, "⛔ Администратора удалить нельзя.")
        conn.close()
        return

    try:
        # Сначала удаляем котов пользователя
        cur.execute("DELETE FROM cats WHERE owner_id = %s", (user_id,))
        # Удаляем самого пользователя
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ Пользователь {login} и его анкеты удалены.")
    except Exception as e:
        print(f"Ошибка удаления: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при удалении.")
    finally:
        conn.close()


# ГРАФИК ДОХОДОВ ВСЕХ МОДЕЛЕЙ
def admin_income_graph(message):
    conn = get_db_connection()
    cur = conn.cursor()

    # SQL: Берем дату и сумму, где тип операции 'sub_in' (подписка) или 'don_in' (донат)
    query = """
        SELECT DATE(created_at), SUM(amount) 
        FROM transactions 
        WHERE operation_type IN ('sub_in', 'don_in') 
        GROUP BY DATE(created_at) 
        ORDER BY DATE(created_at)
    """
    cur.execute(query)
    data = cur.fetchall()
    conn.close()

    if not data:
        bot.send_message(message.chat.id, "📉 Нет данных о доходах.")
        return

    # Подготовка данных для графиков
    dates = [row[0].strftime('%d.%m') for row in data]
    values = [row[1] for row in data]

    send_plot(
        message.chat.id,
        dates,
        values,
        title="Общий доход моделей",
        ylabel="Сумма (руб)",
        color="green"
    )
