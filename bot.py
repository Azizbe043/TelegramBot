import asyncio
import json
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# === CONFIGURATION ===
API_TOKEN = '8000989337:AAFgLYVFammIEgR5Kq553q2OqugZ88IyAxo'
CHANNEL_ID = -1002173910436
ADMIN_ID = 2122907163
BOT_USERNAME = 'filmocbot'

# === FSM STATES ===
class Register(StatesGroup):
    first_name = State()
    last_name = State()

# === INIT BOT & STORAGE ===
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# === JSON STORAGE ===
def load_data():
    try:
        with open("user_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open("user_data.json", "w") as f:
        json.dump(data, f, indent=4)

# === SUBSCRIPTION CHECK ===
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except:
        return False

def get_channel_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Kanalga o'tish", url="https://t.me/FilmoCoder")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])

# === /start (with or without referral) ===
@router.message(CommandStart(deep_link=True))
async def start_with_ref(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = load_data()

    if not await check_subscription(message.from_user.id):
        await message.answer("❗️Botdan foydalanish uchun avval kanalga obuna bo‘ling.", reply_markup=get_channel_button())
        return

    if user_id in data:
        await message.answer("Siz allaqachon ro'yxatdan o'tgansiz.")
        return

    # Bu yerda referrer_id ni qo‘l bilan ajratamiz
    try:
        referrer_id = message.text.split(" ")[1]
    except IndexError:
        referrer_id = None

    if referrer_id and referrer_id != user_id:
        if referrer_id not in data:
            data[referrer_id] = {"friends": 1, "first_name": "", "last_name": ""}
        else:
            data[referrer_id]["friends"] += 1

    data[user_id] = {"friends": 0, "first_name": "", "last_name": ""}
    save_data(data)

    await state.set_state(Register.first_name)
    await message.answer("Ismingizni kiriting:")

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = load_data()

    if not await check_subscription(message.from_user.id):
        await message.answer("❗️Botdan foydalanish uchun avval kanalga obuna bo‘ling.", reply_markup=get_channel_button())
        return

    if user_id in data:
        await message.answer("Siz allaqachon ro'yxatdan o'tgansiz.")
        return

    data[user_id] = {"friends": 0, "first_name": "", "last_name": ""}
    save_data(data)

    await state.set_state(Register.first_name)
    await message.answer("Ismingizni kiriting:")

# === FSM ===
@router.message(Register.first_name)
async def process_first_name(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = load_data()
    data[user_id]["first_name"] = message.text
    save_data(data)

    await state.set_state(Register.last_name)
    await message.answer("Familiyangizni kiriting:")

@router.message(Register.last_name)
async def process_last_name(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = load_data()
    data[user_id]["last_name"] = message.text
    save_data(data)

    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    await message.answer("✅ Ro'yxatdan muvaffaqiyatli o'tdingiz.")
    await message.answer(f"📨 Do‘stlaringizni taklif qilish uchun ushbu havolani ulashing:\n{referral_link}")

    await bot.send_message(
        ADMIN_ID,
        f"👤 Yangi foydalanuvchi ro'yxatdan o'tdi:\nID: {user_id}\nIsm: {data[user_id]['first_name']}\nFamiliya: {data[user_id]['last_name']}"
    )

    await state.clear()

# === /cancel ===
@router.message(Command("cancel"))
async def cancel_registration(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Jarayon bekor qilindi. Yangi boshlash uchun /start ni bosing.")

# === /profile ===
@router.message(Command("profile"))
async def profile_cmd(message: Message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data:
        await message.answer("❗️Siz hali ro'yxatdan o'tmagansiz.")
        return

    user = data[user_id]
    await message.answer(
        f"👤 <b>Profilingiz</b>\n"
        f"Ism: {user['first_name']}\n"
        f"Familiya: {user['last_name']}\n"
        f"Taklif qilgan do‘stlar: {user['friends']}"
    )

# === /myfriend ===
@router.message(Command("myfriend"))
async def myfriend_cmd(message: Message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data:
        await message.answer("❗️Avval ro'yxatdan o'ting.")
        return

    await message.answer(f"👥 Siz {data[user_id]['friends']} do‘stingizni taklif qilgansiz.")

# === /invite ===
@router.message(Command("invite"))
async def invite_cmd(message: Message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data:
        await message.answer("❗️Avval ro'yxatdan o'ting.")
        return

    link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    await message.answer(f"📨 Taklif havolangiz:\n{link}")

# === /top ===
@router.message(Command("top"))
async def top_cmd(message: Message):
    data = load_data()
    top = sorted(data.items(), key=lambda x: x[1]["friends"], reverse=True)[:5]

    if not top:
        await message.answer("Hozircha hech kim ro'yxatdan o'tmagan.")
        return

    text = "🏆 <b>Eng faol foydalanuvchilar:</b>\n"
    for i, (uid, info) in enumerate(top, 1):
        text += f"{i}. {info['first_name']} {info['last_name']} - {info['friends']} do‘st\n"

    await message.answer(text)

# === /help ===
@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "🤖 <b>Yordam</b>\n"
        "/start - Botni boshlash\n"
        "/profile - Profilingiz\n"
        "/myfriend - Taklif qilgan do‘stlar\n"
        "/invite - Taklif havolasi\n"
        "/top - Eng faol foydalanuvchilar\n"
        "/cancel - Bekor qilish\n"
        "/help - Yordam"
    )

# === CALLBACK - Check subscription ===
@router.callback_query(F.data == "check_sub")
async def callback_check(callback: CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.delete()
        await callback.message.answer("✅ Obuna tasdiqlandi. Iltimos, /start buyrug'ini qayta yuboring.")
    else:
        await callback.answer("Hali ham obuna emassiz!", show_alert=True)

# === RUN BOT ===
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
