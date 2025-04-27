import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from dotenv import load_dotenv
import os
import json
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

# Загружаем переменные окружения
load_dotenv()

# Токен и ID владельца
API_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_TELEGRAM_ID'))

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Файл с авторизованными пользователями
AUTHORIZED_USERS_FILE = 'storage/authorized_users.json'

# Функция загрузки авторизованных пользователей
def load_authorized_users():
    if not os.path.exists(AUTHORIZED_USERS_FILE):
        return []
    with open(AUTHORIZED_USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# Функция сохранения авторизованных пользователей
def save_authorized_users(users):
    with open(AUTHORIZED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

# Команда старта
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    authorized_users = load_authorized_users()

    # Проверяем, если пользователь уже авторизован
    if user_id in [user['id'] for user in authorized_users]:
        await message.reply("Добро пожаловать в бот! Для начала работы, выбери нужный филиал.")
        await send_branch_options(message)  # Отправляем кнопки выбора филиала
    else:
        await message.reply("🚨Для работы с ботом необходимо указать вашу Фамилию и Имя")
        # Ожидаем фамилию и имя
        await dp.register_message_handler(handle_name, state="*")

# Класс для состояния пользователя
class UserForm(StatesGroup):
    name = State()

# Обработка фамилии и имени
async def handle_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.text.strip()
    authorized_users = load_authorized_users()

    # Отправляем уведомление владельцу
    owner = await bot.get_chat(OWNER_ID)
    await bot.send_message(OWNER_ID, f"Запрос на доступ от: {user_name} ({user_id})")
    
    # Даем возможность владельцу подтвердить доступ
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Подтвердить✅"), types.KeyboardButton("Отклонить❌"))
    
    await bot.send_message(OWNER_ID, "Пожалуйста, подтвердите доступ к боту", reply_markup=keyboard)

    # Сохраняем данные пользователя в очередь на проверку
    authorized_users.append({
        'id': user_id,
        'name': user_name,
        'status': 'pending'
    })
    save_authorized_users(authorized_users)

    # Переход к следующему состоянию
    await state.finish()

# Обработчик подтверждения владельцем
@dp.message_handler(lambda message: message.text == 'Подтвердить✅')
async def confirm_access(message: types.Message):
    user_id = message.from_user.id
    authorized_users = load_authorized_users()
    for user in authorized_users:
        if user['status'] == 'pending':
            user['status'] = 'approved'
            save_authorized_users(authorized_users)
            await bot.send_message(user_id, "Вы можете работать с ботом!😉")
            await bot.send_message(OWNER_ID, f"Доступ для {user['name']} подтвержден!")
            await send_branch_options(message)  # Отправляем кнопки выбора филиала после подтверждения

# Обработчик отклонения владельцем
@dp.message_handler(lambda message: message.text == 'Отклонить❌')
async def deny_access(message: types.Message):
    user_id = message.from_user.id
    authorized_users = load_authorized_users()
    for user in authorized_users:
        if user['status'] == 'pending':
            user['status'] = 'denied'
            save_authorized_users(authorized_users)
            await bot.send_message(user_id, "Доступ к боту закрыт!⛔")
            await bot.send_message(OWNER_ID, f"Доступ для {user['name']} отклонен!")

# Функция для отправки кнопок выбора филиала
async def send_branch_options(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Филиал 1"), types.KeyboardButton("Филиал 2"))
    keyboard.add(types.KeyboardButton("Филиал 3"))
    
    await message.reply("Выберите филиал для работы с ботом:", reply_markup=keyboard)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
