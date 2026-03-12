import html
from telebot import types
from loader import bot, active_sessions, reg_cache, user_filters
from database import get_db_connection
from utils.security import hash_pass, verify_pass
from utils.ai import is_cat_ai, generate_ai_bio
from config import ADMIN_SECRET_KEY, CATS_BREEDS, CATS_COLORS, CATS_EYES, CATS_AGES
from handlers.common import create_keyboard, get_menu

# РЕГИСТРАЦИЯ: НАЧАЛО

@bot.message_handler(commands=['reg'])
def reg_start(message):
    msg = bot.send_message(message.chat.id, "Придумайте ЛОГИН:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, reg_login)

def reg_login(message):
    reg_cache[message.chat.id] = {'login': message.text}
    msg = bot.send_message(message.chat.id, "Придумайте ПАРОЛЬ:")
    bot.register_next_step_handler(msg, reg_pass)

def reg_pass(message):
    reg_cache[message.chat.id]['password'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👀 Наблюдатель", "📸 Модель", "👑 Администратор")
    msg = bot.send_message(message.chat.id, "Кто вы?", reply_markup=markup)
    bot.register_next_step_handler(msg, reg_role)

def reg_role(message):
    role = message.text
    data = reg_cache[message.chat.id]
    chat_id = message.chat.id

    # АДМИНИСТРАТОР
    if role == "👑 Администратор":
        msg = bot.send_message(message.chat.id, "🔑 Введите секретный код:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, reg_admin_check)
        return

    # НАБЛЮДАТЕЛЬ
    if role == "👀 Наблюдатель":
        conn = get_db_connection(); cur = conn.cursor()
        try:
            # Удаляем старую привязку телеграм ID, если была
            cur.execute("UPDATE users SET telegram_id = NULL WHERE telegram_id = %s", (chat_id,))

            # Создаем нового юзера
            cur.execute("INSERT INTO users (login, password, role, balance, username, email, telegram_id) VALUES (%s, %s, 'user', 5000, %s, 'no_email', %s)", 
                        (data['login'], hash_pass(data['password']), data['login'], chat_id))
            conn.commit()
            bot.send_message(message.chat.id, "✅ Наблюдатель создан! Пиши /login")
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка при регистрации: {e}")
        finally:
            conn.close()

    # МОДЕЛЬ
    elif role == "📸 Модель":
        reg_cache[message.chat.id]['role'] = 'model'
        msg = bot.send_message(message.chat.id, "Как зовут кота?", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, reg_cat_name)

# ПРОВЕРКА АДМИНА
def reg_admin_check(message):
    if message.text == ADMIN_SECRET_KEY:
        data = reg_cache[message.chat.id]
        conn = get_db_connection(); cur = conn.cursor()
        try:
            hashed = hash_pass(data['password'])
            cur.execute("UPDATE users SET telegram_id = NULL WHERE telegram_id = %s", (message.chat.id,))
            cur.execute("INSERT INTO users (login, password, role, balance, username, email, telegram_id) VALUES (%s, %s, 'admin', 0, %s, 'admin', %s)", 
                        (data['login'], hashed, data['login'], message.chat.id))
            conn.commit()
            bot.send_message(message.chat.id, "👑 Админ создан! Используйте /login")
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка: {e}")
        finally:
            conn.close()
    else:
        bot.send_message(message.chat.id, "⛔ Неверный код!")


# АНКЕТА МОДЕЛИ
def reg_cat_name(message):
    reg_cache[message.chat.id]['cat_name'] = message.text
    msg = bot.send_message(message.chat.id, "Цена подписки (число)?")
    bot.register_next_step_handler(msg, reg_cat_price)

def reg_cat_price(message):
    try:
        reg_cache[message.chat.id]['price'] = float(message.text)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True); markup.add("Кот ♂️", "Кошечка ♀️")
        bot.register_next_step_handler(bot.send_message(message.chat.id, "Пол:", reply_markup=markup), reg_cat_gender)
    except:
        bot.send_message(message.chat.id, "Пожалуйста, введите число!")
        bot.register_next_step_handler(message, reg_cat_price)

def reg_cat_gender(message):
    reg_cache[message.chat.id]['gender'] = message.text
    bot.register_next_step_handler(bot.send_message(message.chat.id, "Порода:", reply_markup=create_keyboard(CATS_BREEDS)), reg_cat_breed)

def reg_cat_breed(message):
    reg_cache[message.chat.id]['breed'] = message.text
    bot.register_next_step_handler(bot.send_message(message.chat.id, "Шерсть:", reply_markup=create_keyboard(CATS_COLORS)), reg_cat_fur)

def reg_cat_fur(message):
    reg_cache[message.chat.id]['fur'] = message.text
    bot.register_next_step_handler(bot.send_message(message.chat.id, "Глаза:", reply_markup=create_keyboard(CATS_EYES)), reg_cat_eyes)

def reg_cat_eyes(message):
    reg_cache[message.chat.id]['eyes'] = message.text
    bot.register_next_step_handler(bot.send_message(message.chat.id, "Возраст:", reply_markup=create_keyboard(CATS_AGES)), reg_cat_age)

def reg_cat_age(message):
    reg_cache[message.chat.id]['age'] = message.text
    # Спрашиваем про характер для ИИ
    msg = bot.send_message(
        message.chat.id,
        "✍️ Напиши пару слов о характере кота или его любимых игрушках.\n\n🤖 ИИ составит красивое био!\n\nОтправь «-» (минус), чтобы пропустить.", 
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, reg_cat_bio_process)

def reg_cat_bio_process(message):
    user_text = message.text
    chat_id = message.chat.id

    # Генерация БИО
    if user_text.strip() == "-" or len(user_text) < 3:
        reg_cache[chat_id]['bio'] = "Новая звезда OnlyPaws! 🐾"
        msg = bot.send_message(chat_id, "Окей, будет стандартное описание. Теперь загрузи 📸 ФОТО АВАТАРКИ:")
    else:
        wait_msg = bot.send_message(chat_id, "🤖 ИИ придумывает описание... ⏳")
        ai_bio = generate_ai_bio(reg_cache[chat_id], user_text)
        reg_cache[chat_id]['bio'] = ai_bio

        bot.delete_message(chat_id, wait_msg.message_id)
        bot.send_message(chat_id, f"✨ <b>Био готово:</b>\n\n<i>{html.escape(ai_bio)}</i>\n\nТеперь загрузи 📸 ФОТО АВАТАРКИ:", parse_mode="HTML")
        msg = bot.send_message(chat_id, "Жду фото...", reply_markup=types.ReplyKeyboardRemove())

    bot.register_next_step_handler(msg, reg_cat_photo_finish)

def reg_cat_photo_finish(message):
    if not message.photo:
        bot.send_message(message.chat.id, "Нужно фото! Попробуйте снова.")
        return bot.register_next_step_handler(message, reg_cat_photo_finish)

    file_id = message.photo[-1].file_id

    # Проверка ИИ
    bot.send_message(message.chat.id, "🤖 ИИ проверяет, кот ли это...")
    if not is_cat_ai(file_id):
        bot.send_message(message.chat.id, "⛔ ИИ считает, что это не кот (или это собака). Загрузите другое фото.")
        bot.register_next_step_handler(message, reg_cat_photo_finish)
        return

    # Сохранение в БД
    d = reg_cache[message.chat.id]; chat_id = message.chat.id
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET telegram_id = NULL WHERE telegram_id = %s", (chat_id,))
        cur.execute("INSERT INTO users (login, password, role, balance, username, email, telegram_id) VALUES (%s, %s, 'model', 0, %s, 'no_email', %s) RETURNING id", 
                    (d['login'], hash_pass(d['password']), d['login'], chat_id))
        uid = cur.fetchone()[0]

        final_bio = d.get('bio', 'Новая звезда OnlyPaws!')

        cur.execute("""INSERT INTO cats (owner_id, nickname, breed, subscription_price, bio, avatar_url, gender, fur_color, eye_color, age_category)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                    (uid, d['cat_name'], d['breed'], d['price'], final_bio, file_id, d['gender'], d['fur'], d['eyes'], d['age']))

        conn.commit()
        bot.send_message(message.chat.id, "✅ Модель создана! Пиши /login")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка БД при создании модели.")
        print(e)
    finally:
        conn.close()


# ВХОД В СИСТЕМУ
@bot.message_handler(commands=['login'])
def login_start(message):
    msg = bot.send_message(message.chat.id, "ЛОГИН:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, login_pass)

def login_pass(message):
    reg_cache[message.chat.id] = {'l': message.text}
    msg = bot.send_message(message.chat.id, "ПАРОЛЬ:")
    bot.register_next_step_handler(msg, login_check)

def login_check(message):
    l = reg_cache[message.chat.id]['l']
    p_input = message.text

    conn = get_db_connection(); cur = conn.cursor()
    # Ищем по логину, достаем хеш
    cur.execute("SELECT id, role, is_banned, password FROM users WHERE login=%s", (l,))
    res = cur.fetchone()
    conn.close()

    if res:
        uid, role, is_banned, stored_hash = res

        # Сравниваем пароль с хешем
        if verify_pass(p_input, stored_hash):
            if is_banned:
                bot.send_message(message.chat.id, "⛔ АККАУНТ ЗАБЛОКИРОВАН!")
                return

            # Привязываем Telegram ID
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("UPDATE users SET telegram_id = NULL WHERE telegram_id = %s", (message.chat.id,))
            cur.execute("UPDATE users SET telegram_id = %s WHERE id = %s", (message.chat.id, uid))
            conn.commit(); conn.close()

            # Сохраняем сессию
            active_sessions[message.chat.id] = uid
            if message.chat.id in user_filters: del user_filters[message.chat.id]

            bot.send_message(message.chat.id, f"🔓 Привет, {role}!", reply_markup=get_menu(role))
        else:
            bot.send_message(message.chat.id, "⛔ Неверный логин или пароль.")
    else:
        bot.send_message(message.chat.id, "⛔ Неверный логин или пароль.")
