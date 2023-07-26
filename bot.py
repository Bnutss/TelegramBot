import logging
from settings import keep_alive
import re
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

BOT_TOKEN = ""

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

users_data = {}


class OrderState(StatesGroup):
    FULL_NAME = State()
    PHONE_NUMBER = State()
    CAR_NUMBER = State()
    CAR_BRAND = State()


def get_main_menu():
    buttons = ["Записаться", "Геолокация", "Контакты"]
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(*(types.KeyboardButton(text) for text in buttons))
    return menu


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    await message.answer(
        f"🇷🇺 Привет, {user_name}! Я Автомойка OLTIN бот, и готов помочь вам. \n Выберите действие из меню \n \n🇺🇿 Salom, {user_name}! men OLTIN Автомойка botiman va men sizga yordam berishga tayyorman.\n Menyudan amalni tanlang",
        reply_markup=get_main_menu(),
    )


@dp.message_handler(lambda message: message.text == "Записаться")
async def btn_order_wash(message: types.Message):
    user_id = message.from_user.id
    users_data[user_id] = {}
    await message.answer(
        "🇷🇺 Пожалуйста, введите своё Имя и Фамилию 👨 \n \n🇺🇿 Iltimos, ismingiz va familiyangizni kiriting 👨"
    )
    await OrderState.FULL_NAME.set()


@dp.message_handler(state=OrderState.FULL_NAME)
async def get_full_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    full_name = message.text.strip()
    pattern = r"^[A-Za-zА-Яа-яЁё\s]+$"
    if not re.match(pattern, full_name):
        await message.answer(
            "🇷🇺 Пожалуйста, введите своё Имя и Фамилию только буквами 👨 \n \n🇺🇿 Iltimos, ismingiz va familiyangizni faqat harflar bilan kiriting 👨"
        )
        return
    users_data[user_id]["full_name"] = full_name
    await state.update_data(full_name=full_name)
    await message.answer(
        "🇷🇺 Пожалуйста, введите свой мобильный номер 📱 \n \n 🇺🇿 Iltimos, mobil raqamingizni kiriting 📱"
    )
    await OrderState.PHONE_NUMBER.set()


@dp.message_handler(state=OrderState.PHONE_NUMBER)
async def get_phone_number(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    phone_number = message.text
    pattern = r"^\+998\d{9}$"
    if not re.match(pattern, phone_number):
        await message.answer(
            "🇷🇺 Неправильный формат номера! Пожалуйста, введите номер в формате +998XXXXXXXXX \n \n🇺🇿 Raqam formati noto'g'ri! Iltimos, raqamni +998XXXXXXXXX formatida kiriting"
        )
        return
    users_data[user_id]["phone_number"] = phone_number
    await state.update_data(phone_number=phone_number)
    await message.answer(
        "🇷🇺 Пожалуйста, введите номер вашего авто в таком формате Х000ХХ 🚘 \n \n🇺🇿 Iltimos, X000XX formatida avtomobil raqamingizni kiriting 🚘"
    )
    await OrderState.CAR_NUMBER.set()


@dp.message_handler(state=OrderState.CAR_NUMBER)
async def get_car_number(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    car_number = message.text.upper()
    pattern = r"^(?:[A-Z]\d{3}[A-Z]{2}|[0-9]{3}[A-Z]{3})$"
    if not re.match(pattern, car_number):
        await message.answer(
            "🇷🇺 Неправильный формат номера автомобиля! Пожалуйста, введите номер в формате X000XX или XXX000 \n \n🇺🇿 Avtomobil raqami formati noto'g'ri! Raqamni X000XX yoki XXX000 formatida kiriting"
        )
        return
    users_data[user_id]["car_number"] = car_number
    await state.update_data(car_number=car_number)
    await message.answer(
        "🇷🇺 Пожалуйста, введите марку вашего авто 🚗 \n \n 🇺🇿 Iltimos, mashinangiz markasini kiriting 🚗"
    )
    await OrderState.CAR_BRAND.set()


@dp.message_handler(state=OrderState.CAR_BRAND)
async def get_car_brand(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    users_data[user_id]["car_brand"] = message.text
    user_data = users_data[user_id]
    order_text = (
        f"НОВАЯ ЗАЯВКА НА МОЙКУ:\n"
        f"Имя Фамилия 👨: {user_data['full_name']}\n"
        f"Мобильный номер 📱: {user_data['phone_number']}\n"
        f"Номер авто 🚘: {user_data['car_number']}\n"
        f"Марка авто 🚗: {user_data['car_brand']}"
    )

    try:
        await bot.send_message(chat_id="", text=order_text)
        await state.finish()
        await message.answer(
            "🇷🇺 Ваша заявка на мойку успешно отправлена администратору. Мы скоро сважемся с вами! \n \n🇺🇿 Avtomobil yuvish so‘rovingiz administratorga muvaffaqiyatli yuborildi. Tez orada siz bilan bog'lanamiz!"
        )
    except Exception as e:
        logging.exception(e)
        await message.answer(
            "🇷🇺 Произошла ошибка при отправке заявки. Попробуйте позже или свяжитесь с администратором автомойки. \n \n🇺🇿 Arizani yuborishda xatolik yuz berdi. Keyinroq qayta urinib ko'ring yoki avtomobil yuvish administratoriga murojaat qiling."
        )

    await message.answer(
        "🇷🇺 Выберите действие из меню: \n \n🇺🇿 Menyudan amalni tanlang:",
        reply_markup=get_main_menu(),
    )


@dp.message_handler(lambda message: message.text == "Геолокация")
async def btn_location(message: types.Message):
    latitude = 41.447221
    longitude = 69.560973
    await message.answer_location(latitude=latitude, longitude=longitude)


@dp.message_handler(lambda message: message.text == "Контакты")
async def btn_contact_us(message: types.Message):
    await message.answer(
        "🇷🇺 Вы можете связаться с нами по номеру телефона: +998 97-707-82-88 \n \n🇺🇿 Biz bilan quyidagi telefon raqami orqali bogʻlanishingiz mumkin: +998 97-707-82-88"
    )


keep_alive()
if __name__ == "__main__":
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
