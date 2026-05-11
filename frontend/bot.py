import telebot
import requests

TELEGRAM_BOT_ACCESS_TOKEN = "8513493118:AAGK9vhZZ1SPAcpKltDP3xHf6ohLIMUGvmI"
BACKEND_API_BASE_URL = "http://127.0.0.1:8000"

user_authentication_tokens_dictionary = {}

# Инициализируем экземпляр бота с развернутым именем
telegram_bot_application_instance = telebot.TeleBot(TELEGRAM_BOT_ACCESS_TOKEN)

@telegram_bot_application_instance.message_handler(commands=['start'])
def handle_start_command_and_register_user(incoming_message_object):
    telegram_user_identifier = str(incoming_message_object.from_user.id)

    static_user_password_string = f"pass_{telegram_user_identifier}"
    
    registration_payload_dictionary = {
        "telegram_user_identifier": telegram_user_identifier,
        "plain_text_user_password": static_user_password_string
    }
    
    try:
        # 1. Отправляем запрос на регистрацию
        registration_response_object = requests.post(
            f"{BACKEND_API_BASE_URL}/authentication/register",
            json=registration_payload_dictionary
        )
        
        # 2. Формируем данные для авторизации
        login_payload_form_data = {
            "username": telegram_user_identifier,
            "password": static_user_password_string
        }
        
        # 3. Запрашиваем JWT-токен доступа
        authentication_response_object = requests.post(
            f"{BACKEND_API_BASE_URL}/authentication/login",
            data=login_payload_form_data
        )
        
        if authentication_response_object.status_code == 200:
            token_data_dictionary = authentication_response_object.json()
            jwt_access_token_string = token_data_dictionary.get("access_token")
            
            user_authentication_tokens_dictionary[telegram_user_identifier] = jwt_access_token_string
            
            welcome_text_message = (
                f"Привет, {incoming_message_object.from_user.first_name}! 👋\n"
                f"Вы успешно авторизованы в системе трекинга привычек.\n\n"
                f"Доступные команды:\n"
                f"➕ /add_habit [название] — создать новую привычку\n"
                f"📋 /habits — показать список ваших привычек"
            )
            telegram_bot_application_instance.reply_to(incoming_message_object, welcome_text_message)
        else:
            server_error_details = authentication_response_object.json().get("detail", "Неизвестная ошибка")
            telegram_bot_application_instance.reply_to(
                incoming_message_object, 
                f"Ошибка авторизации: {server_error_details}"
            )

            
    except requests.exceptions.ConnectionError:
        telegram_bot_application_instance.reply_to(
            incoming_message_object, 
            "Ошибка: Не удалось связаться с сервером бэкенда. Убедитесь, что FastAPI запущен."
        )


@telegram_bot_application_instance.message_handler(commands=['add_habit'])
def handle_habit_creation_command(incoming_message_object):
    # обрабатывает команду добавления привычки и отправляет запрос на FastAPI
    telegram_user_identifier = str(incoming_message_object.from_user.id)
    
    habit_title_name = incoming_message_object.text.replace('/add_habit', '').strip()
    
    if not habit_title_name:
        telegram_bot_application_instance.reply_to(
            incoming_message_object, 
            "Пожалуйста, укажите название привычки. Пример:\n/add_habit Медитация"
        )
        return

    # извлекаем сохраненный JWT-токен пользователя
    user_jwt_token_string = user_authentication_tokens_dictionary.get(telegram_user_identifier)
    
    if not user_jwt_token_string:
        telegram_bot_application_instance.reply_to(
            incoming_message_object, 
            "Вы не авторизованы. Пожалуйста, введите команду /start заново."
        )
        return

    headers_credentials_dictionary = {"Authorization": f"Bearer {user_jwt_token_string}"}
    habit_payload_dictionary = {"habit_title_name": habit_title_name}

    try:
        creation_response_object = requests.post(
            f"{BACKEND_API_BASE_URL}/habits/create",
            json=habit_payload_dictionary,
            headers=headers_credentials_dictionary
        )
        
        if creation_response_object.status_code == 200:
            telegram_bot_application_instance.reply_to(
                incoming_message_object, 
                f"Привычка «{habit_title_name}» успешно добавлена и сохранена в базу данных! ✅"
            )
        else:
            telegram_bot_application_instance.reply_to(
                incoming_message_object, 
                "Не удалось сохранить привычку. Ошибка на стороне сервера бэкенда."
            )
    except requests.exceptions.ConnectionError:
        telegram_bot_application_instance.reply_to(
            incoming_message_object, 
            "Ошибка связи с сервером бэкенда."
        )


@telegram_bot_application_instance.message_handler(commands=['habits'])
def handle_list_habits_command(incoming_message_object):
    # запрашивает список активных привычек пользователя с бэкенда
    telegram_user_identifier = str(incoming_message_object.from_user.id)
    user_jwt_token_string = user_authentication_tokens_dictionary.get(telegram_user_identifier)
    
    if not user_jwt_token_string:
        telegram_bot_application_instance.reply_to(
            incoming_message_object, 
            "Вы не авторизованы. Введите команду /start."
        )
        return

    headers_credentials_dictionary = {"Authorization": f"Bearer {user_jwt_token_string}"}

    try:
        list_response_object = requests.get(
            f"{BACKEND_API_BASE_URL}/habits/list",
            headers=headers_credentials_dictionary
        )
        
        if list_response_object.status_code == 200:
            habits_list_data = list_response_object.json()
            
            if not habits_list_data:
                telegram_bot_application_instance.reply_to(
                    incoming_message_object, 
                    "У вас пока нет активных привычек. Добавьте первую через /add_habit!"
                )
                return
                
            response_text_message = "📋 **Ваши активные привычки:**\n\n"
            for index_counter, habit_item in enumerate(habits_list_data, start=1):
                response_text_message += (
                    f"{index_counter}. *{habit_item['habit_title_name']}*\n"
                    f"   └ Выполнено дней: {habit_item['total_execution_success_count']}/21 ⏳\n\n"
                )
            
            telegram_bot_application_instance.send_message(
                incoming_message_object.chat.id, 
                response_text_message, 
                parse_mode="Markdown"
            )
        else:
            telegram_bot_application_instance.reply_to(
                incoming_message_object, 
                "Не удалось загрузить список с бэкенд-сервера."
            )
    except requests.exceptions.ConnectionError:
        telegram_bot_application_instance.reply_to(
            incoming_message_object, 
            "Ошибка связи с сервером бэкенда."
        )


if __name__ == "__main__":
    print("Telegram-бот успешно запущен в режиме polling и ожидает команд...")
    telegram_bot_application_instance.infinity_polling()
