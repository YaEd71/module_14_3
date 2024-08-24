import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '--'

# Создаем экземпляр бота
bot = Bot(token=API_TOKEN)

# Создаем диспетчер с хранилищем состояний в памяти
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Определяем группу состояний
class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()


# Создаем обычную клавиатуру
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton('Рассчитать'), KeyboardButton('Информация'))
keyboard.add(KeyboardButton('Купить'))

# Создаем Inline клавиатуру для основного меню
inline_kb = InlineKeyboardMarkup(row_width=1)
inline_kb.add(InlineKeyboardButton(text='Рассчитать норму калорий', callback_data='calories'))
inline_kb.add(InlineKeyboardButton(text='Формулы расчёта', callback_data='formulas'))

# Создаем Inline клавиатуру для покупки продуктов
buying_kb = InlineKeyboardMarkup(row_width=2)
buying_kb.add(
    InlineKeyboardButton(text="Product1", callback_data="product_buying"),
    InlineKeyboardButton(text="Product2", callback_data="product_buying"),
    InlineKeyboardButton(text="Product3", callback_data="product_buying"),
    InlineKeyboardButton(text="Product4", callback_data="product_buying")
)


# Функция, обрабатывающая команду /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply(
        'Привет! Я бот, помогающий твоему здоровью.\nНажмите "Рассчитать", чтобы начать расчет нормы калорий.\n'
        'Нажмите "Купить", чтобы купить витамины',
        reply_markup=keyboard
    )


# Функция для отображения Inline меню
@dp.message_handler(lambda message: message.text == 'Рассчитать')
async def main_menu(message: types.Message):
    await message.reply('Выберите опцию:', reply_markup=inline_kb)


# Функция для отображения формул
@dp.callback_query_handler(lambda c: c.data == 'formulas')
async def get_formulas(call: types.CallbackQuery):
    formula_text = ("Формула Миффлина-Сан Жеора для расчета нормы калорий:\n\n"
                    "Для мужчин: (10 * вес (кг)) + (6.25 * рост (см)) - (5 * возраст) + 5\n"
                    "Для женщин: (10 * вес (кг)) + (6.25 * рост (см)) - (5 * возраст) - 161")
    await call.message.answer(formula_text)
    await call.answer()


# Функция для установки возраста
@dp.callback_query_handler(lambda c: c.data == 'calories', state=None)
async def set_age(call: types.CallbackQuery):
    await call.message.answer('Введите свой возраст:')
    await UserState.age.set()
    await call.answer()


# Функция для установки роста
@dp.message_handler(state=UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.reply('Введите свой рост (в см):')
    await UserState.growth.set()


# Функция для установки веса
@dp.message_handler(state=UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    await state.update_data(growth=message.text)
    await message.reply('Введите свой вес (в кг):')
    await UserState.weight.set()


# Функция для расчета и отправки нормы калорий
@dp.message_handler(state=UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)

    data = await state.get_data()

    try:
        age = int(data['age'])
        growth = int(data['growth'])
        weight = int(data['weight'])

        calories = int(10 * weight + 6.25 * growth - 5 * age + 5)

        await message.reply(f"Ваша норма калорий: {calories} ккал в день", reply_markup=keyboard)
    except ValueError:
        await message.reply("Ошибка в введенных данных. Пожалуйста, убедитесь, что вы ввели числовые значения.",
                            reply_markup=keyboard)

    await state.finish()


# Новая функция для отображения списка продуктов
@dp.message_handler(lambda message: message.text == 'Купить')
async def get_buying_list(message: types.Message):
    products = [
        {"name": "Витамины 1", "description": "Описание витаминов 1", "price": 100, "photo": "Фото_1.png"},
        {"name": "Витамины 2", "description": "Описание витаминов 2", "price": 200, "photo": "Фото_2.png"},
        {"name": "Витамины 3", "description": "Описание витаминов 3", "price": 300, "photo": "Фото_3.png"},
        {"name": "Витамины 4", "description": "Описание витаминов 4", "price": 400, "photo": "Фото_4.png"}
    ]

    for product in products:
        await message.answer(
            f"Название: {product['name']} | Описание: {product['description']} | Цена: {product['price']}")
        with open(f"files/{product['photo']}", 'rb') as photo:
            await message.answer_photo(photo)

    await message.answer("Выберите продукт для покупки:", reply_markup=buying_kb)


# Новая функция для подтверждения покупки
@dp.callback_query_handler(lambda c: c.data == 'product_buying')
async def send_confirm_message(call: types.CallbackQuery):
    await call.message.answer("Вы успешно приобрели продукт!")
    await call.answer()


# Функция, обрабатывающая все остальные сообщения
@dp.message_handler()
async def all_messages(message: types.Message):
    if message.text == 'Информация':
        await message.reply('Этот бот поможет вам рассчитать норму калорий. Нажмите "Рассчитать", чтобы начать.',
                            reply_markup=keyboard)
    else:
        await message.reply(
            'Введите команду /start, чтобы начать общение или нажмите "Рассчитать" для расчета нормы калорий.',
            reply_markup=keyboard)


if __name__ == '__main__':
    # Запуск бота
    executor.start_polling(dp, skip_updates=True)