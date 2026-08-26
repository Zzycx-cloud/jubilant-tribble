import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus
from aiohttp import web

# --- SOZLAMALAR ---
TOKEN = "8783915374:AAFSjTvJTRiNaRgiaHfwTYBjYG4OH2ZQFgA"
LOG_GROUP_ID = -1004384447851  # Siz ko'rsatgan loglar guruhi ID raqami
ADMIN_IDS = [7203210832]  # Adminlar ID raqamlari (o'zingizning Telegram ID'ingizni yozing)

# Statistika uchun o'zgaruvchilar
stats = {
    "deleted_service": 0,
    "deleted_pins": 0,
    "deleted_plus": 0,
    "deleted_commands": 0,
    "total_bans": 0
}

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ADMIN PANEL KEYBOARD ---
def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="show_stats")],
        [InlineKeyboardButton(text="🔄 Statistikani yangilash", callback_data="refresh_stats")]
    ])

# --- LOGLARNI YUBORISH FUNKSIYASI ---
async def send_log(text: str):
    try:
        await bot.send_message(chat_id=LOG_GROUP_ID, text=text)
    except Exception as e:
        logging.error(f"Log guruhiga xabar yuborishda xatolik: {e}")

# --- 1. XIZMAT XABARLARINI O'CHIRISH (Odam qo'shish/chiqish) ---
@dp.message(F.new_chat_members | F.left_chat_member)
async def delete_service_messages(message: Message):
    global stats
    try:
        await message.delete()
        stats["deleted_service"] += 1
    except Exception as e:
        logging.error(f"Xizmat xabari xatosi: {e}")

# --- 2. XABAR PIN QILINGANDA UNI DARHOL O'CHIRISH ---
@dp.message(F.pinned_message)
async def delete_pinned_service_message(message: Message):
    global stats
    try:
        await message.delete()
        stats["deleted_pins"] += 1
    except Exception as e:
        logging.error(f"Pin xabari xatosi: {e}")

# --- 3. '+' BILAN BOSHLANGAN XABARLARNI O'CHIRISH ---
@dp.message(F.text.startswith("+"))
async def delete_plus_messages(message: Message):
    global stats
    try:
        await message.delete()
        stats["deleted_plus"] += 1
    except Exception as e:
        logging.error(f"'+' xabari xatosi: {e}")

# --- 4. MODERATOR BUYRUQLARINI O'CHIRISH ---
@dp.message(F.text.regexp(r"^/(ban|kick|mute|unmute|warn|unban)(\s+@?\w+)?\b"))
async def delete_mod_commands(message: Message):
    global stats
    try:
        command_text = message.text
        group_name = message.chat.title
        group_id = message.chat.id
        
        rayxon = message.from_user.full_name if message.from_user else "Noma'lum"
        
        aziz = "Ko'rsatilmagan"
        target_user_id = None
        if message.reply_to_message and message.reply_to_message.from_user:
            aziz = message.reply_to_message.from_user.full_name
            target_user_id = message.reply_to_message.from_user.id

        await message.delete()
        stats["deleted_commands"] += 1
        
        if "ban" in command_text.lower() and target_user_id:
            stats["total_bans"] += 1
            try:
                await bot.ban_chat_member(chat_id=group_id, user_id=target_user_id)
            except Exception as b_err:
                logging.error(f"Ban qilish xatosi: {b_err}")

        log_text = (
            f"🚨 **Buyruq orqali harakat:**\n"
            f"🏢 Guruh: {group_name}\n"
            f"⚙️ Buyruq: {command_text}\n"
            f"👮 Kim tomonidan: {rayxon}\n"
            f"👤 Kimga (Aziz): {aziz}"
        )
        await send_log(log_text)
    except Exception as e:
        logging.error(f"Buyruqni o'chirishda xatolik: {e}")

# --- 5. GURUHDA KIMDIR BAN QILINGANINI (QO'LDA / NEDAVNIY ORQALI) USHLASH ---
@dp.chat_member()
async def track_user_ban(event: ChatMemberUpdated):
    global stats
    # Agar foydalanuvchi BANNED holatiga o'tgan bo'lsa
    if event.new_chat_member.status == ChatMemberStatus.BANNED:
        stats["total_bans"] += 1
        group_name = event.chat.title
        group_id = event.chat.id
        
        # Ban qilingan odam (Aziz)
        aziz = event.new_chat_member.user.full_name
        aziz_id = event.new_chat_member.user.id
        
        # Kim ban qilgani (Rayxon / Admin)
        # Eslatma: Telegram qoidalari bo'yicha qo'lda qilingan banlarda ba'zan admin ismi to'g'ridan-to'g'ri kelmasligi mumkin, lekin chat ma'lumotidan olinadi
        rayxon = "Noma'lum (Admin)"
        if event.from_user:
            rayxon = event.from_user.full_name

        log_text = (
            f"🚫 **Guruhda Ban berildi!**\n\n"
            f"🏢 Guruh: {group_name} (`{group_id}`)\n"
            f"👤 Kimga (Aziz): {aziz} (`{aziz_id}`)\n"
            f"👮 Kim tomonidan (Rayxon): {rayxon}"
        )
        await send_log(log_text)

# --- 6. ADMIN PANEL VA STATISTIKA ---
@dp.message(Command("admin"), F.from_user.id.in_(ADMIN_IDS))
async def admin_panel(message: Message):
    await message.answer(
        "🎛 **Bot Admin Paneliga xush kelibsiz!**\n\nQuyidagi tugmalar orqali statistikani ko'rishingiz mumkin:",
        reply_markup=get_admin_keyboard()
    )

@dp.callback_query(F.data == "show_stats")
async def callback_stats(callback: CallbackQuery):
    text = (
        f"📊 **Bot Statistikasi:**\n\n"
        f"🧹 O'chirilgan xizmat xabarlari: {stats['deleted_service']}\n"
        f"📌 O'chirilgan pin bildirishnomalari: {stats['deleted_pins']}\n"
        f"➕ O'chirilgan '+' xabarlari: {stats['deleted_plus']}\n"
        f"⚙️ O'chirilgan moderator buyruqlari: {stats['deleted_commands']}\n"
        f"🚫 Jami ban qilinganlar: {stats['total_bans']}"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "refresh_stats")
async def callback_refresh(callback: CallbackQuery):
    await callback.answer("Statistika yangilandi ✅")
    text = (
        f"📊 **Bot Statistikasi (Yangilandi):**\n\n"
        f"🧹 O'chirilgan xizmat xabarlari: {stats['deleted_service']}\n"
        f"📌 O'chirilgan pin bildirishnomalari: {stats['deleted_pins']}\n"
        f"➕ O'chirilgan '+' xabarlari: {stats['deleted_plus']}\n"
        f"⚙️ O'chirilgan moderator buyruqlari: {stats['deleted_commands']}\n"
        f"🚫 Jami ban qilinganlar: {stats['total_bans']}"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())

# --- WEB SERVER (Hostinglar uchun PORT) ---
async def handle(request):
    return web.Response(text="Bot ishlayapti!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server {port}-portda ishga tushdi.")

async def main():
    asyncio.create_task(web_server())
    print("Bot ishga tushdi va polling boshlandi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
