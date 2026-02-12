import asyncio
import sqlite3
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# --- ASOSIY SOZLAMALAR ---
TOKEN = os.getenv("TOKEN", "8318944066:AAFhjLk4HT3F5eCuzD-4dp-MN7-jDlROMZM")
ADMIN_ID = 8135296587

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- BAZA BILAN ISHLASH ---
def init_db():
    conn = sqlite3.connect("manecafe.db")
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    
    defaults = [
        ('sayt_url', 'https://manecafe.uz/uz'),
        ('wolt_url', 'https://wolt.com/uz/uzb/tashkent/restaurant/mane-cafe-tash'),
        ('tg_admin', 'https://t.me/mane_callcentre'),
        ('maps_url', 'https://yandex.uz/maps/org/174532732165?si=av1r0pv5a5tux31bbrfr1wqc6g'),
        ('b1', '📍 Bizning manzillar'), 
        ('b2', '📞 Aloqa / Bron'),
        ('b3', '📸 MaNe Cafe (Video Menyu)'), 
        ('b4', '🎁 Aksiyalar'),
        ('b5', '✍️ Fikr qoldirish'), 
        ('b6', 'Mane Cafe Menu 🍴')
    ]
    for k, v in defaults:
        cursor.execute("INSERT OR IGNORE INTO settings VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()

def get_conf(key):
    try:
        conn = sqlite3.connect("manecafe.db")
        res = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        conn.close()
        return res[0] if res else ""
    except:
        return ""

def set_conf(key, value):
    conn = sqlite3.connect("manecafe.db")
    conn.execute("UPDATE settings SET value=? WHERE key=?", (value, key))
    conn.commit()
    conn.close()

class AdminStates(StatesGroup):
    waiting_reklama = State()
    waiting_config_val = State()

def get_main_menu(user_id):
    kb = [
        [KeyboardButton(text=get_conf('b1')), KeyboardButton(text=get_conf('b2'))],
        [KeyboardButton(text=get_conf('b3')), KeyboardButton(text=get_conf('b4'))],
        [KeyboardButton(text=get_conf('b5')), KeyboardButton(text=get_conf('b6'))]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="⚙️ Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- HANDLERLAR ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    conn = sqlite3.connect("manecafe.db")
    conn.execute("INSERT OR IGNORE INTO users VALUES (?)", (message.from_user.id,))
    conn.commit()
    conn.close()
    await message.answer(
        f"Xush kelibsiz, {message.from_user.full_name}!\nMane Cafe botidan foydalanishingiz mumkin.", 
        reply_markup=get_main_menu(message.from_user.id)
    )

@dp.message(lambda message: message.text == get_conf('b1'))
async def show_location(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Xaritada ko'rish", url=get_conf('maps_url'))]
    ])
    await message.answer("📍 Bizning manzillarimiz va ish vaqtimiz:\n\nDu-Yak: 08:00 - 22:00", reply_markup=kb)

@dp.message(lambda message: message.text == get_conf('b2'))
async def contact_us(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Admin bilan bog'lanish", url=get_conf('tg_admin'))]
    ])
    await message.answer("Stol buyurtma qilish yoki savollaringiz bo'lsa, yozing:", reply_markup=kb)

@dp.message(lambda message: message.text == get_conf('b3'))
async def open_mane_site(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Saytni ochish (Video & Menu)", url=get_conf('sayt_url'))]
    ])
    await message.answer("MaNe Cafe atmosferasi va video-menyusi bilan tanishing:", reply_markup=kb)

@dp.message(lambda message: message.text == get_conf('b4'))
async def offers(message: types.Message):
    await message.answer("🎁 Hozirgi aksiyalarimiz:\n\n- Har seshanba barcha kofelar uchun 10% chegirma!")

@dp.message(lambda message: message.text == get_conf('b5'))
async def feedback(message: types.Message):
    await message.answer("Sizning fikringiz biz uchun muhim! Iltimos, takliflaringizni yozib qoldiring.")

@dp.message(lambda message: message.text == get_conf('b6'))
async def open_menu_options(message: types.Message):
    url_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Wolt orqali buyurtma", url=get_conf('wolt_url'))],
        [InlineKeyboardButton(text="🌐 Rasmiy sayt", url=get_conf('sayt_url'))]
    ])
    await message.answer(
        "Mane Cafe menyusi va yetkazib berish:\n\n*(Wolt ilovasi bo'lsa, avtomatik ilovada ochiladi)*", 
        reply_markup=url_kb,
        parse_mode="Markdown"
    )

@dp.message(F.text == "⚙️ Admin Panel")
@dp.message(Command("admin"))
async def admin_main(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Reklama", callback_data="adm_reklama")],
        [InlineKeyboardButton(text="🛍 Wolt linki", callback_data="conf_wolt_url")],
        [InlineKeyboardButton(text="🌐 Sayt linki", callback_data="conf_sayt_url")],
        [InlineKeyboardButton(text="✏️ Tugmalar", callback_data="adm_edit_btns")]
    ])
    await message.answer("Admin paneli:", reply_markup=kb)

@dp.callback_query(F.data.startswith("conf_"))
async def edit_config(call: types.CallbackQuery, state: FSMContext):
    key = call.data.replace("conf_", "")
    await state.update_data(key=key)
    await call.message.answer(f"Yangi qiymatni yuboring:")
    await state.set_state(AdminStates.waiting_config_val)

@dp.callback_query(F.data == "adm_edit_btns")
async def list_btns(call: types.CallbackQuery):
    btns = [[InlineKeyboardButton(text=get_conf(f"b{i}"), callback_data=f"conf_b{i}")] for i in range(1, 7)]
    await call.message.edit_text("Tugmani tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@dp.message(AdminStates.waiting_config_val)
async def update_config(message: types.Message, state: FSMContext):
    data = await state.get_data()
    set_conf(data['key'], message.text)
    await message.answer("✅ Saqlandi!")
    await state.clear()

@dp.callback_query(F.data == "adm_reklama")
async def start_ads(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Reklama xabarini yuboring:")
    await state.set_state(AdminStates.waiting_reklama)

@dp.message(AdminStates.waiting_reklama)
async def send_ads(message: types.Message, state: FSMContext):
    conn = sqlite3.connect("manecafe.db")
    users = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    for u in users:
        try: await message.copy_to(u[0])
        except: pass
    await message.answer("Reklama yuborildi.")
    await state.clear()

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
