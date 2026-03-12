from huggingface_hub import InferenceClient
from config import HF_TOKEN, BOT_TOKEN
from loader import bot

# ПРОВЕРКА ФОТО
def is_cat_ai(file_id):
    try:
        # Получаем ссылку на файл в Telegram
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        # Подключаемся к Hugging Face
        client = InferenceClient(token=HF_TOKEN)

        # Используем модель для классификации изображений
        result = client.image_classification(file_url, model="google/vit-base-patch16-224")

        # Слова-маркеры
        cat_words = ['cat', 'tabby', 'tiger', 'kitten', 'siamese', 'persian', 'lynx', 'leopard', 'lion']
        dog_words = ['dog', 'retriever', 'terrier', 'pug', 'chihuahua', 'beagle', 'shepherd', 'husky', 'corgi', 'bulldog', 'wolf']

        for item in result:
            label = item.label.lower()
            score = item.score

            # Если уверенность больше 30%
            if score > 0.3:
                # Сначала ищем собак
                for dw in dog_words:
                    if dw in label:
                        return False
                # Потом ищем котов
                for cw in cat_words:
                    if cw in label:
                        return True

        return False

    except Exception as e:
        print(f"⚠️ Ошибка Vision AI: {e}")
        return True # Если ИИ сломался, пускаем всех

# ГЕНЕРАЦИЯ ТЕКСТА
def generate_ai_bio(data, user_text):
    print(f"🤖 Запрос к ИИ (Bio) для кота {data.get('cat_name')}...")

    try:
        client = InferenceClient(token=HF_TOKEN)

        # Системный промпт
        system_prompt = (
            "Ты — остроумный и креативный помощник, который пишет анкеты для котов на сайте знакомств. "
            "Твоя задача: взять скучные факты и превратить их в веселое, милое описание от ПЕРВОГО ЛИЦА (от имени кота). "
            "НЕ копируй текст пользователя слово в слово! Перефразируй его литературно. "
            "Обязательно используй эмодзи. "
            "Пиши коротко (максимум 3 предложения)."
        )

        # Промпт юзера
        user_content = (
            f"Имя: {data.get('cat_name')}\n"
            f"Порода: {data.get('breed')}\n"
            f"Пол: {data.get('gender')}\n"
            f"Окрас: {data.get('fur')}\n"
            f"Факты от хозяина: '{user_text}'\n\n"
            "Напиши классное био!"
        )

        # Формируем диалог
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        # Выполняем запрос
        response = client.chat_completion(
            messages=messages,
            model="Qwen/Qwen2.5-72B-Instruct",
            max_tokens=250,
            temperature=0.8
        )

        # Получаем результат
        result = response.choices[0].message.content.strip()

        # Чистим от кавычек, если они есть
        if result.startswith('"') and result.endswith('"'):
            result = result[1:-1]

        return result

    except Exception as e:
        print(f"❌ ОШИБКА AI (Bio): {e}")
        # Запасной вариант, если ИИ недоступен
        return f"Всем мяу! Я {data.get('cat_name')}. {user_text} 🐾"
