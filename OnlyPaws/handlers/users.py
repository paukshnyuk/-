from telebot import types
from telebot.types import InputMediaPhoto
import html

from loader import bot, user_filters, payment_cache, donation_cache
from database import get_db_connection, get_user_role, is_subscribed, get_likes_count
from config import CATS_BREEDS, CATS_COLORS, CATS_EYES, CATS_AGES
from handlers.common import get_logged_user_id, get_menu

# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
def toggle_like(user_id, cat_id):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT 1 FROM likes WHERE user_id=%s AND cat_id=%s", (user_id, cat_id))
    if cur.fetchone():
        cur.execute("DELETE FROM likes WHERE user_id=%s AND cat_id=%s", (user_id, cat_id))
        result = False # Лайк убран
    else:
        cur.execute("INSERT INTO likes (user_id, cat_id) VALUES (%s, %s)", (user_id, cat_id))
        result = True # Лайк поставлен
    conn.commit(); conn.close()
    return result

# ГАЛЕРЕЯ И ЛЕНТА
def send_cat_gallery(chat_id, cat_id, title_prefix=""):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("""SELECT nickname, breed, subscription_price, avatar_url, gender, fur_color, eye_color, age_category, bio
                   FROM cats WHERE id = %s""", (cat_id,))
    res = cur.fetchone()

    if not res:
        conn.close()
        bot.send_message(chat_id, "Кот не найден.")
        return

    name, breed, price, avatar, gender, fur, eyes, age, bio = res
    likes_count = get_likes_count(cat_id)

    cur.execute("SELECT file_id FROM cat_photos WHERE cat_id = %s", (cat_id,))
    extra_photos = [row[0] for row in cur.fetchall()]
    conn.close()

    bio_text = f"📝 <i>{html.escape(bio)}</i>\n\n" if bio else ""

    caption = (f"{title_prefix} 👑 <b>{html.escape(name)}</b>\n"
               f"{bio_text}"
               f"💰 Подписка: {price} руб\n❤️ Лайков: {likes_count}\n\n"
               f"📋 <b>Анкета:</b>\n🧬 {html.escape(breed or '?')}\n🚻 {html.escape(gender or '?')}\n"
               f"🎂 {html.escape(age or '?')}\n🎨 {html.escape(fur or '?')}\n👁 {html.escape(eyes or '?')}")

    all_photos = []
    if avatar: all_photos.append(avatar)
    all_photos.extend(extra_photos)

    if not all_photos:
        bot.send_message(chat_id, caption, parse_mode='HTML')
        return

    media_group = []
    for i, photo_id in enumerate(all_photos):
        if i == 0:
            media_group.append(InputMediaPhoto(photo_id, caption=caption, parse_mode='HTML'))
        else:
            media_group.append(InputMediaPhoto(photo_id))

    try:
        bot.send_media_group(chat_id, media_group[:10])
    except:
        bot.send_message(chat_id, caption, parse_mode='HTML')

def show_cats_by_query(chat_id, query_sql, params=None):
    uid = get_logged_user_id(chat_id)
    role = get_user_role(uid)

    conn = get_db_connection(); cur = conn.cursor()
    cur.execute(query_sql, params or ())
    cats = cur.fetchall()
    conn.close()

    if not cats:
        bot.send_message(chat_id, "😿 Никого не найдено.")
        send_filter_menu(chat_id)
        return

    for c in cats:
        cid, name, breed, price, photo, gender, fur, eyes, age, bio = c
        likes = get_likes_count(cid)
        bio_text = f"📝 <i>{html.escape(bio)}</i>\n\n" if bio else ""

        caption = (f"👑 <b>{html.escape(name)}</b>\n"
                   f"{bio_text}"
                   f"💰 Подписка: {price} руб\n❤️ Лайков: {likes}\n\n📋 <b>Анкета:</b>\n"
                   f"🧬 {html.escape(breed or '?')}\n🚻 {html.escape(gender or '?')}\n"
                   f"🎂 {html.escape(age or '?')}\n🎨 {html.escape(fur or '?')}\n👁 {html.escape(eyes or '?')}")

        mk = types.InlineKeyboardMarkup()
        if role == 'user':
            mk.add(types.InlineKeyboardButton(f"❤️ {likes}", callback_data=f"like_{cid}"))
            if is_subscribed(uid, cid):
                mk.add(types.InlineKeyboardButton("🖼 Альбом", callback_data=f"gallery_{cid}"),
                       types.InlineKeyboardButton("🎁 Донат", callback_data=f"donate_{cid}"))
                mk.add(types.InlineKeyboardButton("💔 Отписаться", callback_data=f"unsub_{cid}"))
            else:
                mk.add(types.InlineKeyboardButton(f"💸 Подписаться ({price}р)", callback_data=f"buy_{cid}_{price}"),
                       types.InlineKeyboardButton("🎁 Донат", callback_data=f"donate_{cid}"))
        else:
            mk.add(types.InlineKeyboardButton(f"❤️ Лайков: {likes}", callback_data="dummy_like"))

        if photo:
            try: bot.send_photo(chat_id, photo, caption=caption, parse_mode='HTML', reply_markup=mk)
            except: bot.send_message(chat_id, caption, parse_mode='HTML', reply_markup=mk)
        else:
            bot.send_message(chat_id, caption, parse_mode='HTML', reply_markup=mk)

def send_filter_menu(chat_id):
    filters = user_filters.get(chat_id, {})
    titles = {
        "breed": "Порода",
        "fur": "Окрас",
        "eyes": "Глаза",
        "age": "Возраст",
        "gender": "Пол"
    }

    status_text = "<b>⚙️ Фильтры OnlyPaws:</b>\n"
    if filters:
        # Переводим ключи (breed -> Порода)
        status_text += "\n".join([f"🔹 {titles.get(k, k)}: {', '.join(v)}" for k,v in filters.items()])
    else:
        status_text += "Все коты (без фильтров)"

    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("🧬 Порода", callback_data="f_menu_breed"),
           types.InlineKeyboardButton("🚻 Пол", callback_data="f_menu_gender"))
    mk.add(types.InlineKeyboardButton("🎨 Шерсть", callback_data="f_menu_fur"),
           types.InlineKeyboardButton("👁 Глаза", callback_data="f_menu_eyes"))
    mk.add(types.InlineKeyboardButton("🎂 Возраст", callback_data="f_menu_age"),
           types.InlineKeyboardButton("🔄 Сброс", callback_data="f_reset"))
    mk.add(types.InlineKeyboardButton("🔍 ИСКАТЬ", callback_data="f_search_run"))

    bot.send_message(chat_id, status_text, parse_mode='HTML', reply_markup=mk)

# ПЛАТЕЖИ И ДОНАТЫ
def topup_start(message):
    bot.send_message(message.chat.id, "Введите сумму пополнения (руб):")
    bot.register_next_step_handler(message, topup_method)

def topup_method(message):
    try:
        amt = float(message.text)
        if amt <= 0: raise ValueError
        payment_cache[message.chat.id] = {'amount': amt, 'type': 'deposit'}

        mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        mk.add("Карта", "СБП")
        bot.send_message(message.chat.id, "Выберите способ оплаты:", reply_markup=mk)
        bot.register_next_step_handler(message, topup_confirm)
    except:
        bot.send_message(message.chat.id, "Ошибка. Введите число.")

def topup_confirm(message):
    data = payment_cache.get(message.chat.id)
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(f"Оплатить {data['amount']}р", callback_data="pay_confirm"))
    bot.send_message(message.chat.id, f"Подтверждение пополнения на {data['amount']}р через {message.text}.", reply_markup=mk)

def donate_start(chat_id, cat_id):
    donation_cache[chat_id] = cat_id
    bot.send_message(chat_id, "Введите сумму доната:")
    bot.register_next_step_handler_by_chat_id(chat_id, donate_process)

def donate_process(message):
    try:
        amt = float(message.text)
        if amt <= 0: raise ValueError

        cat_id = donation_cache.get(message.chat.id)
        uid = get_logged_user_id(message.chat.id)

        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT balance FROM users WHERE id=%s", (uid,))
        balance = cur.fetchone()[0]

        if balance < amt:
            bot.send_message(message.chat.id, "❌ Недостаточно средств на балансе.")
            conn.close()
            return

        cur.execute("UPDATE users SET balance=balance-%s WHERE id=%s", (amt, uid))
        cur.execute("UPDATE users SET balance=balance+%s WHERE id=(SELECT owner_id FROM cats WHERE id=%s)", (amt, cat_id))
        cur.execute("INSERT INTO transactions (user_id, amount, operation_type, description) VALUES (%s, %s, 'don_out', 'Донат')", (uid, amt))
        cur.execute("INSERT INTO transactions (user_id, amount, operation_type, description) VALUES ((SELECT owner_id FROM cats WHERE id=%s), %s, 'don_in', 'Донат')", (cat_id, amt))
        conn.commit(); conn.close()
        bot.send_message(message.chat.id, f"✅ Донат {amt}р успешно отправлен!")
    except:
        bot.send_message(message.chat.id, "Ошибка ввода суммы.")

# ОБРАБОТЧИК КНОПОК
@bot.callback_query_handler(func=lambda call: True)
def callback_master(call):
    uid = get_logged_user_id(call.message.chat.id)
    if not uid: return

    if call.data == "pay_confirm":
        data = payment_cache.get(call.message.chat.id)
        if not data: return
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("UPDATE users SET balance=balance+%s WHERE id=%s", (data['amount'], uid))
        cur.execute("INSERT INTO transactions (user_id, amount, operation_type, description) VALUES (%s, %s, 'deposit', 'Пополнение')", (uid, data['amount']))
        conn.commit(); conn.close()
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ Баланс пополнен!", reply_markup=get_menu('user'))

    elif call.data.startswith('like_'):
        role = get_user_role(uid)
        if role == 'model':
            return bot.answer_callback_query(call.id, "Модели не могут ставить лайки.")
        cat_id = call.data.split('_')[1]
        liked = toggle_like(uid, cat_id)
        text = "❤️ Лайк!" if liked else "💔 Лайк убран"
        bot.answer_callback_query(call.id, text)

    elif call.data == "dummy_like":
        bot.answer_callback_query(call.id, "Это счетчик лайков")

    elif call.data.startswith('donate_'):
        donate_start(call.message.chat.id, call.data.split('_')[1])
        bot.answer_callback_query(call.id)

    elif call.data.startswith('buy_'):
        role = get_user_role(uid)
        if role == 'model':
            return bot.answer_callback_query(call.id, "Модели не могут подписываться.")
        cat_id = call.data.split('_')[1]
        price = float(call.data.split('_')[2])
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT balance FROM users WHERE id=%s", (uid,))
        user_balance = cur.fetchone()[0]
        if user_balance < price:
            bot.answer_callback_query(call.id, "Недостаточно средств!", show_alert=True)
            conn.close()
            return
        cur.execute("SELECT owner_id, nickname FROM cats WHERE id=%s", (cat_id,))
        res = cur.fetchone()
        owner_id, cat_name = res
        cur.execute("UPDATE users SET balance=balance-%s WHERE id=%s", (price, uid))
        cur.execute("UPDATE users SET balance=balance+%s WHERE id=%s", (price, owner_id))
        cur.execute("INSERT INTO subscriptions (user_id, cat_id) VALUES (%s, %s)", (uid, cat_id))
        cur.execute("INSERT INTO transactions (user_id, amount, operation_type, description) VALUES (%s, %s, 'sub_out', %s)", (uid, price, f"Подписка: {cat_name}"))
        cur.execute("INSERT INTO transactions (user_id, amount, operation_type, description) VALUES (%s, %s, 'sub_in', %s)", (owner_id, price, f"Новый подписчик"))
        conn.commit(); conn.close()
        bot.answer_callback_query(call.id, "Вы успешно подписались!", show_alert=True)
        send_cat_gallery(call.message.chat.id, cat_id, "🎉")

    elif call.data.startswith('unsub_'):
        cat_id = call.data.split('_')[1]
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM subscriptions WHERE user_id=%s AND cat_id=%s", (uid, cat_id))
        conn.commit(); conn.close()
        bot.answer_callback_query(call.id, "Вы отписались.")
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data.startswith('gallery_'):
        send_cat_gallery(call.message.chat.id, call.data.split('_')[1], "🖼")

    # МЕНЮ ФИЛЬТРОВ
    elif call.data.startswith("f_menu_"):
        cat_type = call.data.split("_")[2]

        titles = {
            "breed": "породу",
            "fur": "окрас",
            "eyes": "цвет глаз",
            "age": "возраст",
            "gender": "пол"
        }
        title_ru = titles.get(cat_type, cat_type)

        mk = types.InlineKeyboardMarkup()
        if cat_type == "breed": items = CATS_BREEDS
        elif cat_type == "fur": items = CATS_COLORS
        elif cat_type == "eyes": items = CATS_EYES
        elif cat_type == "age": items = CATS_AGES
        elif cat_type == "gender": items = ["Кот ♂️", "Кошечка ♀️"]
        else: items = []

        for i in items:
            mk.add(types.InlineKeyboardButton(i, callback_data=f"set_{cat_type}_{i[:20]}"))
        mk.add(types.InlineKeyboardButton("🔙 Назад", callback_data="f_reset"))
        bot.edit_message_text(f"Выберите {title_ru}:", call.message.chat.id, call.message.message_id, reply_markup=mk)

    elif call.data.startswith("set_"):
        ft = call.data.split("_")[1]
        fv = call.data.split("_")[2]
        if call.message.chat.id not in user_filters: user_filters[call.message.chat.id] = {}
        if ft not in user_filters[call.message.chat.id]: user_filters[call.message.chat.id][ft] = []
        user_filters[call.message.chat.id][ft].append(fv)
        bot.answer_callback_query(call.id, f"Добавлено: {fv}")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_filter_menu(call.message.chat.id)

    elif call.data == "f_reset":
        if call.message.chat.id in user_filters: del user_filters[call.message.chat.id]
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_filter_menu(call.message.chat.id)

    elif call.data == "f_search_run":
        filters = user_filters.get(call.message.chat.id, {})
        sql = "SELECT id, nickname, breed, subscription_price, avatar_url, gender, fur_color, eye_color, age_category, bio FROM cats WHERE 1=1"
        params = []
        col_map = {"breed": "breed", "gender": "gender", "fur": "fur_color", "eyes": "eye_color", "age": "age_category"}
        for k, v in filters.items():
            db_col = col_map.get(k)
            if db_col and v:
                sql += f" AND ({' OR '.join([f'{db_col} LIKE %s' for _ in v])})"
                for val in v: params.append(f"{val}%")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_cats_by_query(call.message.chat.id, sql, tuple(params))
