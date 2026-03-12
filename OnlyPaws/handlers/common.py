import html
from telebot import types
from loader import bot, active_sessions, user_filters
from database import get_db_connection, get_user_role, is_subscribed

# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
def get_logged_user_id(chat_id):
    return active_sessions.get(chat_id)

def create_keyboard(items):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for i in range(0, len(items), 2):
        chunk = items[i:i+2]
        markup.add(*[types.KeyboardButton(text) for text in chunk])
    return markup

def get_menu(role):
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if role == 'user':
        mk.add("🐱 Лента", "💳 Пополнить", "❤️ Мои подписки", "👤 Профиль", "🚪 Выход")

    elif role == 'model':
        mk.add("📸 Мой Кот", "🐱 Лента", "📈 Мой Доход", "💸 Вывести", "📜 История операций", "✏️ Анкету", "✏️ Аватар", "➕ Добавить фото", "🚪 Выход")

    elif role == 'admin':
        mk.add("📊 Статистика", "📈 Доходы Моделей", "🚫 БАН", "🔓 РАЗБАН", "🗑 УДАЛИТЬ ЮЗЕРА", "🚪 Выход")

    return mk

# БАЗОВЫЕ КОМАНДЫ
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Привет в **OnlyPaws**!\n/reg - Регистрация\n/login - Вход\n/logout - Выход\n/me - Профиль")

@bot.message_handler(commands=['logout'])
def logout(message):
    if message.chat.id in active_sessions:
        del active_sessions[message.chat.id]
        # Очищаем фильтры при выходе
        if message.chat.id in user_filters:
            del user_filters[message.chat.id]
        bot.send_message(message.chat.id, "🚪 Вы вышли.", reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "Вы не авторизованы.")

@bot.message_handler(commands=['me'])
def me(message):
    uid = get_logged_user_id(message.chat.id)
    if not uid: return bot.send_message(message.chat.id, "Сначала /login")

    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT login, role, balance FROM users WHERE id = %s", (uid,))
    d = cur.fetchone(); conn.close()

    if d:
        bot.send_message(message.chat.id, f"👤 {html.escape(d[0])} | {d[1]} | 💰 {d[2]}р")

# ОБРАБОТКА МЕНЮ
@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
def menu(message):
    uid = get_logged_user_id(message.chat.id)
    if not uid:
        # Если юзер пишет текст, но не залогинен - отправляем на вход (если это не команды регистрации)
        return bot.send_message(message.chat.id, "Войдите /login")

    txt = message.text

    # ИМПОРТЫ ЛОГИКИ ИЗ ДРУГИХ МОДУЛЕЙ
    from . import admin, models, users, auth

    # ОБЩЕЕ
    if txt == "🚪 Выход":
        logout(message)
    elif txt == "👤 Профиль":
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT balance FROM users WHERE id=%s", (uid,))
        res = cur.fetchone()
        conn.close()
        if res:
            role = get_user_role(uid)
            bot.send_message(message.chat.id, f"💰 Баланс: {res[0]}р", reply_markup=get_menu(role))

    # ДЕЙСТВИЯ МОДЕЛИ
    elif txt == "✏️ Аватар":
       models.change_avatar_start(message)
    elif txt == "✏️ Анкету":
        models.edit_profile_start(message)
    elif txt == "➕ Добавить фото":
        models.add_extra_photo_start(message)
    elif txt == "💸 Вывести":
        models.withdraw_start(message)
    elif txt == "📜 История операций":
        models.show_history(message.chat.id)
    elif txt == "📈 Мой Доход":
        models.show_my_income_graph(message)
    elif txt == "📸 Мой Кот":
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT id, nickname FROM cats WHERE owner_id=%s", (uid,))
        res = cur.fetchone(); conn.close()
        if res:
            users.send_cat_gallery(message.chat.id, res[0], "🏠")
        else:
            bot.send_message(message.chat.id, "Нет кота.")

    # ДЕЙСТВИЯ ПОЛЬЗОВАТЕЛЯ
    elif txt == "💳 Пополнить":
        users.topup_start(message)
    elif txt == "🐱 Лента":
        users.send_filter_menu(message.chat.id)
    elif txt == "❤️ Мои подписки":
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT c.id, c.nickname FROM subscriptions s JOIN cats c ON c.id=s.cat_id WHERE s.user_id=%s", (uid,))
        cats = cur.fetchall(); conn.close()
        if cats:
            for c in cats: users.send_cat_gallery(message.chat.id, c[0], "❤️")
        else:
            bot.send_message(message.chat.id, "У вас нет подписок.")

    # ДЕЙСТВИЯ АДМИНА
    elif txt == "📊 Статистика":
        admin.admin_stats(message)
    elif txt == "🚫 БАН":
        admin.admin_ban_start(message, "ban")
    elif txt == "🔓 РАЗБАН":
        admin.admin_ban_start(message, "unban")
    elif txt == "🗑 УДАЛИТЬ ЮЗЕРА":
        admin.admin_delete_start(message)
    elif txt == "📈 Доходы Моделей":
        admin.admin_income_graph(message)

    else:
        pass
