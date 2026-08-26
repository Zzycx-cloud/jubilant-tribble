import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

TOKEN = "8783915374:AAFSjTvJTRiNaRgiaHfwTYBjYG4OH2ZQFgA"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 1. Guruhga odam qo'shilganda yoki chiqib ketganda chiqadigan xabarlarni o'chirish
@dp.message(F.new_chat_members | F.left_chat_member)
async def delete_service_messages(message: Message):
    try:
        await message.delete()
    except Exception as e:
        logging.error(f"Xizmat xabarini o'chirishda xatolik: {e}")

# 2. Xabar pin qilinganda chiqadigan bildirishnomani o'chirish
@dp.message(F.pinned_message)
async def delete_pinned_service_message(message: Message):
    try:
        await message.delete()
    except Exception as e:
        logging.error(f"Pin xabarini o'chirishda xatolik: {e}")

# 3. '+' bilan boshlangan xabarlarni o'chirish
@dp.message(F.text.startswith("+"))
async def delete_plus_messages(message: Message):
    try:
        await message.delete()
    except Exception as e:
        logging.error(f"'+' xabarini o'chirishda xatolik: {e}")

# 4. Faqat maxsus moderator buyruqlarini (/ban, /kick va hokazo) o'chirish
# /start yoki boshqa oddiy buyruqlarga tegmaydi
@dp.message(F.text.regexp(r"^/(ban|kick|mute|unmute|warn|unban)\b"))
async def delete_mod_commands(message: Message):
    try:
        await message.delete()
    except Exception as e:
        logging.error(f"Buyruqni o'chirishda xatolik: {e}")

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())