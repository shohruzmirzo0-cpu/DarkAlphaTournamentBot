import asyncio
import threading

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from flask import Flask

from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ----- Soxta veb-server (Render "port ochilgan" deb bilishi uchun) -----
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot ishlab turibdi!"


def run_flask():
    app.run(host="0.0.0.0", port=10000)
# -------------------------------------------------------------------


@dp.message(CommandStart())
async def start_handler(message: Message):

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Kontakt yuborish", request_contact=True)]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "🏆 eFootball Champions League botiga xush kelibsiz!\n\nRo'yxatdan o'tish uchun telefon raqamingizni yuboring.",
        reply_markup=keyboard
    )


@dp.message(F.contact)
async def contact_handler(message: Message):
    await message.answer(
        "✅ Telefon raqamingiz qabul qilindi!"
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Flask serverni alohida oqimda (thread) ishga tushiramiz
    threading.Thread(target=run_flask, daemon=True).start()

    # Botni asosiy oqimda ishga tushiramiz
    asyncio.run(main())
