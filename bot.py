import asyncio
import sqlite3
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# --- SOZLAMALAR ---
TOKEN = "8318944066:AAFbXNANLk42CmzWpte4vLXHWW-2AngC0Jk"
ADMIN_ID = 8135296587 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- BAZA BILAN ISHLASH ---
def init_db():
    conn = sqlite3.connect("manecafe.db")
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    cursor.execute('CREATE TABLE IF NOT EXISTS actions (id INTEGER PRIMARY KEY, photo_id TEXT, text TEXT)')
    conn.commit()
    conn.close()

def db_query(query, params=(), commit=False):
    conn = sqlite3.connect("manecafe.db")
    cursor = conn.cursor()
    cursor.execute(query, params)
    if commit:
        conn.commit()
        res = None
    else:
        res = cursor.fetchall()
    conn.close()
    return res

# --- ADMIN HOLATLARI ---
class AdminStates(StatesGroup):
    waiting_reklama = State()
    waiting_action_photo = State()
    waiting_action_text = State()

# --- ASOSIY MENYU ---
def get_main_menu(user_id):
    kb = [
        [KeyboardButton(text='📍 MANE cafe'), KeyboardButton(text='🥐 Pataseri')],
        [KeyboardButton(text='🏦 Aloqa Bank (3-etaj)'), KeyboardButton(text='🚚 Uztelecom (14-etaj)')],
        [KeyboardButton(text='🏢 Toshkent City'), KeyboardButton(text='🎁 Aksiyalar')],
        [KeyboardButton(text='🍴 Menyu (Sayt)'), KeyboardButton(text='🎧 Call Center')]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="⚙️ Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- HANDLERLAR ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db_query("INSERT OR IGNORE INTO users VALUES (?)", (message.from_user.id,), commit=True)
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}!\nMaNe Cafe botiga xush kelibsiz. Kerakli bo'limni tanlang:", 
        reply_markup=get_main_menu(message.from_user.id)
    )

# Filiallar lokatsiyasi (4 ta asosiy filial)
@dp.message(F.text.in_(['📍 MANE cafe', '🥐 Pataseri', '🏦 Aloqa Bank (3-etaj)', '🚚 Uztelecom (14-etaj)']))
async def loc_main(message: types.Message):
    url = "https://yandex.uz/maps/-/av1r0pv5a5tux31bbrfr1wqc6g"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📍 Xaritada ko'rish", url=url)]])
    await message.answer(f"{message.text} filialimiz lokatsiyasi:", reply_markup=kb)

# Toshkent City lokatsiyasi
@dp.message(F.text == '🏢 Toshkent City')
async def loc_city(message: types.Message):
    url = "https://yandex.uz/maps/-/av1r0pv5a5tux31bbrfr1wqc6g" 
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📍 City Filial Lokatsiyasi", url=url)]])
    await message.answer("Toshkent City filialimiz lokatsiyasi:", reply_markup=kb)

# Call Center
@dp.message(F.text == '🎧 Call Center')
async def call_center(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎧 Bog'lanish", url="https://t.me/mane_callcentre")]])
    await message.answer("Savol va takliflar uchun call-centerga murojaat qiling:", reply_markup=kb)

# Aksiyalar (Oxirgi yuklangan aksiyani ko'rsatadi)
@dp.message(F.text == '🎁 Aksiyalar')
async def show_action(message: types.Message):
    res = db_query("SELECT photo_id, text FROM actions ORDER BY id DESC LIMIT 1")
    if res:
        await message.answer_photo(photo=res[0][0], caption=res[0][1])
    else:
        await message.answer("Hozircha faol aksiyalar yo'q. Tez kunda yangi aksiyalar qo'shiladi! ✨")

# Menyu (Sayt)
@dp.message(F.text == '🍴 Menyu (Sayt)')
async def open_site(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🌐 Onlayn Menyu", url="https://manecafe.uz/uz")]])
    await message.answer("Menyuni ko'rish uchun quyidagi tugmani bosing:", reply_markup=kb)

# --- ADMIN PANEL ---
@dp.message(F.text == "⚙️ Admin Panel")
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="adm_reklama")],
            [InlineKeyboardButton(text="🎁 Yangi aksiya qo'shish", callback_data="adm_new_action")]
        ])
        await message.answer("Admin boshqaruv paneli:", reply_markup=kb)

@dp.callback_query(F.data == "adm_new_action")
async def adm_action_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Aksiya uchun rasm (photo) yuboring:")
    await state.set_state(AdminStates.waiting_action_photo)

@dp.message(AdminStates.waiting_action_photo, F.photo)
async def adm_action_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await message.answer("Aksiya matnini yuboring:")
    await state.set_state(AdminStates.waiting_action_text)

@dp.message(AdminStates.waiting_action_text)
async def adm_action_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db_query("INSERT INTO actions (photo_id, text) VALUES (?, ?)", (data['photo_id'], message.text), commit=True)
    await message.answer("✅ Yangi aksiya muvaffaqiyatli yuklandi!")
    await state.clear()

@dp.callback_query(F.data == "adm_reklama")
async def start_ads(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Reklama xabarini yuboring (Rasm, Video yoki Oddiy matn):")
    await state.set_state(AdminStates.waiting_reklama)

@dp.message(AdminStates.waiting_reklama)
async def send_ads(message: types.Message, state: FSMContext):
    users = db_query("SELECT user_id FROM users")
    count = 0
    for u in users:
        try:
            await message.copy_to(u[0])
            count += 1
            await asyncio.sleep(0.05)
        except: pass
    await message.answer(f"✅ Reklama {count} ta foydalanuvchiga yuborildi.")
    await state.clear()

# --- ISHGA TUSHIRISH ---
async def main():
    init_db()
    print("Bot muvaffaqiyatli ishga tushdi (Obuna bo'limisiz)!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())