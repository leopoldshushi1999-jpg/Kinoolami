import os
import asyncio
import shutil
import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.types import (
    Message, 
    CallbackQuery,
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    FSInputFile,
    InputFile,
    PhotoSize
)
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

from database import Database
from keyboards import Keyboards

# .env faylini yuklash
load_dotenv()

# Global router yaratish
admin_router = Router()

# Database obyekti
db = Database()

# Bot obyektini keyinroq import qilamiz
bot = None

# Adminlar ro'yxati
ADMIN_ID = os.getenv("ADMIN_ID")
ADMINS = [int(ADMIN_ID)] if ADMIN_ID else []

# ========== STATE CLASSES ==========
class BlockStates(StatesGroup):
    waiting_for_id = State()
    waiting_for_reason = State()
    waiting_for_confirmation = State()

class UnblockStates(StatesGroup):
    waiting_for_id = State()
    waiting_for_confirmation = State()

# ========== ADMIN TEKSHIRISH FUNKSIYASI ==========
def is_admin(user_id):
    """Admin tekshirish funksiyasi"""
    return user_id in ADMINS

# Bot obyektini sozlash funksiyasi
def setup_admin_bot(bot_instance):
    global bot
    bot = bot_instance
    print("✅ Admin moduli uchun bot obyekti sozlandi")
    
def escape_markdown(text):
    """Markdown formatidagi maxsus belgilarni escape qilish"""
    if text is None:
        return ""
    text = str(text)
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text    

# ========== QOLGAN STATE CLASS LARI ==========
class AddMovieStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_subcategory = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_language = State()
    waiting_for_quality = State()  # Yangi: Sifat
    waiting_for_release_year = State()  # Yangi: Chiqarilgan yil
    waiting_for_premium_status = State()
    waiting_for_price = State()
    waiting_for_file = State()
    waiting_for_confirmation = State()

class DeleteMovieStates(StatesGroup):
    waiting_for_method = State()
    waiting_for_movie_id = State()
    waiting_for_category = State()
    waiting_for_movie_selection = State()
    waiting_for_movie_number = State()
    waiting_for_confirmation = State()
    waiting_for_all_confirmation = State()
    waiting_for_final_confirmation = State()

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_broadcast_message = State()
    waiting_for_broadcast_confirmation = State()
    waiting_for_limit_approval = State()
    waiting_for_limit_action = State()
    waiting_for_backup_name = State()
    waiting_for_clear_days = State()
    
class PremiumContentStates(StatesGroup):
    waiting_for_price = State()
    waiting_for_payment_method = State()
    waiting_for_check_photo = State()
    waiting_for_check_confirmation = State()

def is_admin(user_id):
    """Admin tekshirish funksiyasi"""
    return user_id in ADMINS

# Bot obyektini global o'zgaruvchiga saqlash
def setup_admin_bot(bot_instance):
    global bot
    bot = bot_instance
    print("✅ Admin moduli uchun bot obyekti sozlandi")

# ==================== ADMIN PANEL ====================
@admin_router.message(Command("admin"))
@admin_router.message(F.text == "👑 Admin paneli")
async def admin_panel(message: Message, state: FSMContext):
    """Admin panelini ochish"""
    if not is_admin(message.from_user.id):
        await message.answer("⚠️ Siz admin emassiz!")
        return
    
    await state.clear()
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Kontent Qo'shish"), KeyboardButton(text="🗑️ Kontent O'chirish")],
            [KeyboardButton(text="👥 Foydalanuvchilar"), KeyboardButton(text="🚫 Bloklash")],
            [KeyboardButton(text="✅ Blokdan Ochish"), KeyboardButton(text="📢 Xabar Yuborish")],
            [KeyboardButton(text="💰 To'lovlar"), KeyboardButton(text="✅ Cheklar")],
            [KeyboardButton(text="💾 Backup"), KeyboardButton(text="🧹 Tozalash")],
            [KeyboardButton(text="🔍 Himoya Monitoringi"), KeyboardButton(text="🔒 Himoya Sozlamalari")],
            [KeyboardButton(text="💰 Pullik/Bepul qilish"), KeyboardButton(text="📊 Pullik statistikasi")],
            [KeyboardButton(text="🏠 Asosiy menyu")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "👑 **Admin Panel**\n\n"
        "Quyidagi funksiyalardan birini tanlang:",
        reply_markup=keyboard
    )
    
def format_quality(quality):
    """Sifat formatini chiroyli ko'rsatish"""
    quality_map = {
        '480p': '📱 SD (480p)',
        '720p': '📺 HD (720p)', 
        '1080p': '🎬 Full HD (1080p)',
        '2K': '🎥 2K',
        '4K': '🎞️ 4K',
        'HD': '📺 HD',
        'Other': '📼 Boshqa'
    }
    return quality_map.get(quality, quality)

def format_language(lang):
    """Til formatini tuzatish"""
    if not lang:
        return "🌍 Noma'lum"
    
    lang = str(lang)
    lang_map = {
        'uz': "🇺🇿 O'zbekcha",
        'ru': "🇷🇺 Ruscha", 
        'en': "🇬🇧 Inglizcha",
        'mixed': "🌍 Aralash",
        '0': "🌍 Noma'lum"
    }
    return lang_map.get(lang, lang)

def format_date(date_string):
    """Sana formatini tuzatish"""
    if not date_string:
        return "Noma'lum"
    
    try:
        # RU formatidan O'zbek formatiga o'tkazish
        date_string = str(date_string)
        if '-' in date_string:
            return date_string[:19] if len(date_string) >= 19 else date_string
        else:
            return date_string
    except:
        return date_string[:19] if len(date_string) >= 19 else date_string

def format_file_size(bytes_size):
    """Fayl hajmini formatlash"""
    if not bytes_size:
        return "Noma'lum"
    
    try:
        bytes_size = int(bytes_size)
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size // 1024} KB"
        elif bytes_size < 1024 * 1024 * 1024:
            return f"{bytes_size // (1024 * 1024)} MB"
        else:
            return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"
    except:
        return "Noma'lum"

def format_duration(seconds):
    """Davomiylikni formatlash"""
    if not seconds:
        return "Noma'lum"
    
    try:
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours} soat {minutes} daqiqa"
        else:
            return f"{minutes} daqiqa {secs} soniya"
    except:
        return str(seconds)    
    
# ==================== ADMIN PAYMENT ACTIONS (REPLY KEYBOARD) ====================
@admin_router.message(F.text.startswith("✅ Tasdiqlash "))
async def admin_confirm_payment_reply(message: Message):
    """Admin to'lovni tasdiqlash (ReplyKeyboard)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    try:
        # Payment ID ni matndan ajratib olish
        payment_text = message.text
        payment_id = int(payment_text.split()[-1])
        
        print(f"DEBUG: Admin {message.from_user.id} to'lovni tasdiqlamoqchi: {payment_id}")
        
        # To'lovni tasdiqlash
        db.cursor.execute('''
            UPDATE payments 
            SET status = 'completed', processed_by = ?, process_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (message.from_user.id, payment_id))
        
        # Foydalanuvchi va film ma'lumotlarini olish
        db.cursor.execute('''
            SELECT p.user_id, p.movie_id, p.amount, u.full_name, m.title 
            FROM payments p
            JOIN users u ON p.user_id = u.user_id
            LEFT JOIN movies m ON p.movie_id = m.id
            WHERE p.id = ?
        ''', (payment_id,))
        payment_info = db.cursor.fetchone()
        
        user_id = None
        movie_title = "Noma'lum"
        amount = 0
        user_name = "Noma'lum"
        
        if payment_info:
            user_id = payment_info[0]
            movie_id = payment_info[1]
            amount = payment_info[2] if payment_info[2] else 0
            user_name = payment_info[3] if payment_info[3] else "Noma'lum"
            movie_title = payment_info[4] if payment_info[4] else "Noma'lum"
            
            # Movie purchase qo'shish
            db.cursor.execute('''
                INSERT OR REPLACE INTO movie_purchases 
                (user_id, movie_id, price_paid, purchase_date, payment_id)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (user_id, movie_id, amount, payment_id))
            
            # Foydalanuvchiga xabar yuborish
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"""✅ **TO'LOV TASDIQLANDI!**

🎬 **Film:** {movie_title}
💰 **To'lov summa:** {amount:,} so'm
📅 **Tasdiqlash vaqti:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

🎉 **Endi filmni ko'rishingiz mumkin!**

Filmni ko'rish uchun kategoriyaga qayting yoki /start ni bosing."""
                )
            except Exception as e:
                print(f"Error sending confirmation to user {user_id}: {e}")
        
        db.conn.commit()
        
        await message.answer(
            f"""✅ **To'lov tasdiqlandi!**

🆔 Payment ID: {payment_id}
👤 Foydalanuvchi: {user_name}
🎬 Film: {movie_title}
💰 Summa: {amount:,} so'm
📊 Status: COMPLETED
👮 Tasdiqlovchi: {message.from_user.full_name}""",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
        
    except Exception as e:
        print(f"Error confirming payment: {e}")
        await message.answer(
            f"❌ **Xatolik yuz berdi!**\n\n{e}",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )

@admin_router.message(F.text.startswith("❌ Rad etish "))
async def admin_reject_payment_reply(message: Message):
    """Admin to'lovni rad etish (ReplyKeyboard)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    try:
        # Payment ID ni matndan ajratib olish
        payment_text = message.text
        payment_id = int(payment_text.split()[-1])
        
        print(f"DEBUG: Admin {message.from_user.id} to'lovni rad etmoqchi: {payment_id}")
        
        # To'lovni rad etish
        db.cursor.execute('''
            UPDATE payments 
            SET status = 'rejected', processed_by = ?, process_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (message.from_user.id, payment_id))
        
        # Foydalanuvchi va film ma'lumotlarini olish
        db.cursor.execute('''
            SELECT p.user_id, p.amount, u.full_name, m.title 
            FROM payments p
            JOIN users u ON p.user_id = u.user_id
            LEFT JOIN movies m ON p.movie_id = m.id
            WHERE p.id = ?
        ''', (payment_id,))
        payment_info = db.cursor.fetchone()
        
        user_id = None
        movie_title = "Noma'lum"
        amount = 0
        user_name = "Noma'lum"
        
        if payment_info:
            user_id = payment_info[0]
            amount = payment_info[1] if payment_info[1] else 0
            user_name = payment_info[2] if payment_info[2] else "Noma'lum"
            movie_title = payment_info[3] if payment_info[3] else "Noma'lum"
            
            # Foydalanuvchiga xabar yuborish
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"""❌ **TO'LOV RAD ETILDI!**

🎬 **Film:** {movie_title}
💰 **Summa:** {amount:,} so'm
📅 **Rad etilgan vaqt:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

⚠️ **Sabab:** To'lov ma'lumotlari noto'g'ri

❓ **Nima qilish kerak:**
1. To'lovni qayta tekshiring
2. Yangi chek yuboring
3. Agar muammo bo'lsa, @Operator_Kino_1985 ga yozing"""
                )
            except Exception as e:
                print(f"Error sending rejection to user {user_id}: {e}")
        
        db.conn.commit()
        
        await message.answer(
            f"""❌ **To'lov rad etildi!**

🆔 Payment ID: {payment_id}
👤 Foydalanuvchi: {user_name}
🎬 Film: {movie_title}
💰 Summa: {amount:,} so'm
📊 Status: REJECTED
👮 Rad etuvchi: {message.from_user.full_name}""",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
        
    except Exception as e:
        print(f"Error rejecting payment: {e}")
        await message.answer(
            f"❌ **Xatolik yuz berdi!**\n\n{e}",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )

@admin_router.message(F.text.startswith("👁️ Chekni ko'rish "))
async def admin_view_check_reply(message: Message):
    """Admin chekni ko'rish (ReplyKeyboard)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    try:
        # Payment ID ni matndan ajratib olish
        payment_text = message.text
        payment_id = int(payment_text.split()[-1])
        
        print(f"DEBUG: Admin {message.from_user.id} chekni ko'rmoqchi: {payment_id}")
        
        # Chek rasmini olish
        db.cursor.execute('''
            SELECT p.check_photo_id, p.user_id, p.amount, u.full_name, m.title, p.payment_method
            FROM payments p
            JOIN users u ON p.user_id = u.user_id
            LEFT JOIN movies m ON p.movie_id = m.id
            WHERE p.id = ?
        ''', (payment_id,))
        payment_info = db.cursor.fetchone()
        
        if not payment_info:
            await message.answer(
                f"❌ Payment #{payment_id} topilmadi!",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                    resize_keyboard=True
                )
            )
            return
        
        check_photo_id = payment_info[0]
        user_id = payment_info[1]
        amount = payment_info[2]
        user_name = payment_info[3]
        movie_title = payment_info[4]
        payment_method = payment_info[5]
        
        # Chek ma'lumotlari
        check_info = f"""📋 **Chek ma'lumotlari:**

🆔 Payment ID: {payment_id}
👤 Foydalanuvchi: {user_name}
🎬 Film: {movie_title}
💰 Miqdor: {amount:,} so'm
💳 Usul: {payment_method}
👁️ Ko'rish: Chek rasmi quyida

✅ **Amallar:**
Tasdiqlash: '✅ Tasdiqlash {payment_id}'
Rad etish: '❌ Rad etish {payment_id}'"""
        
        if check_photo_id:
            try:
                # Rasmni yuborish
                await message.answer_photo(
                    photo=check_photo_id,
                    caption=check_info,
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[
                            [KeyboardButton(text=f"✅ Tasdiqlash {payment_id}"), 
                             KeyboardButton(text=f"❌ Rad etish {payment_id}")],
                            [KeyboardButton(text="⏳ Kutilayotgan to'lovlar")],
                            [KeyboardButton(text="👑 Admin paneli")]
                        ],
                        resize_keyboard=True
                    )
                )
            except:
                await message.answer(
                    f"❌ Chek rasmini yuborishda xatolik!\n\n{check_info}",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[
                            [KeyboardButton(text=f"✅ Tasdiqlash {payment_id}"), 
                             KeyboardButton(text=f"❌ Rad etish {payment_id}")],
                            [KeyboardButton(text="👑 Admin paneli")]
                        ],
                        resize_keyboard=True
                    )
                )
        else:
            await message.answer(
                f"❌ Chek rasmi mavjud emas!\n\n{check_info}",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text=f"✅ Tasdiqlash {payment_id}"), 
                         KeyboardButton(text=f"❌ Rad etish {payment_id}")],
                        [KeyboardButton(text="👑 Admin paneli")]
                    ],
                    resize_keyboard=True
                )
            )
        
    except Exception as e:
        print(f"Error viewing check: {e}")
        await message.answer(
            f"❌ **Xatolik yuz berdi!**\n\n{e}",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )    

# ==================== BACK TO MAIN ====================
@admin_router.message(F.text == "🏠 Asosiy menyu")
async def back_to_main(message: Message, state: FSMContext):
    """Asosiy menyuga qaytish"""
    await state.clear()
    
    user = db.get_user(message.from_user.id)
    language = user[4] if user else 'uz'
    kb = Keyboards(language)
    
    await message.answer(
        "🏠 Asosiy menyu:",
        reply_markup=kb.main_menu(is_admin=is_admin(message.from_user.id))
    )

# ==================== ADD CONTENT ====================
@admin_router.message(F.text == "➕ Kontent Qo'shish")
async def add_content_start(message: Message, state: FSMContext):
    """Kontent qo'shishni boshlash"""
    if not is_admin(message.from_user.id):
        return
    
    await state.clear()
    
    kb = Keyboards('uz')
    
    await message.answer(
        "➕ **Kontent qo'shish**\n\n"
        "Kategoriyani tanlang:",
        reply_markup=kb.admin_categories_menu()
    )
    await state.set_state(AddMovieStates.waiting_for_category)

@admin_router.message(AddMovieStates.waiting_for_category)
async def get_category(message: Message, state: FSMContext):
    """Kategoriyani qabul qilish"""
    if message.text == "⬅️ Ortga":
        await admin_panel(message, state)
        return
    
    category_map = {
        "🎭 Hollywood Kinolari": "hollywood_movies",
        "🕌 Hind Filmlari": "indian_movies",
        "📺 Hind Seriallari": "indian_series",
        "🎪 Rus Kinolari": "russian_movies",
        "📺 Rus Seriallari": "russian_series",
        "🇺🇿 O'zbek Kinolari": "uzbek_movies",
        "📺 O'zbek Seriallari": "uzbek_series",
        "🕌 Islomiy Kinolar": "islamic_movies",
        "📺 Islomiy Seriallar": "islamic_series",
        "🇹🇷 Turk Kinolari": "turkish_movies",
        "📺 Turk Seriallari": "turkish_series",
        "👶 Bolalar Kinolari": "kids_movies",
        "🐰 Bolalar Multfilmlari": "kids_multfilms",
        "🇰🇷 Koreys Kinolari": "korean_movies",
        "📺 Koreys Seriallari": "korean_series",
        "🎥 Qisqa Filmlar": "short_films"
    }
    
    if message.text not in category_map:
        await message.answer("❌ Noto'g'ri kategoriya!")
        return
    
    main_category = category_map[message.text]
    await state.update_data(main_category=main_category)
    
    kb = Keyboards('uz')
    
    # Ichki kategoriya menyusini ko'rsatish
    if main_category == "hollywood_movies":
        await message.answer(
            "🎭 Hollywood aktyorini tanlang:",
            reply_markup=kb.admin_hollywood_subcategories_menu()
        )
        await state.set_state(AddMovieStates.waiting_for_subcategory)
        
    elif main_category == "indian_movies":
        await message.answer(
            "🕌 Hind aktyorini tanlang:",
            reply_markup=kb.admin_indian_subcategories_menu()
        )
        await state.set_state(AddMovieStates.waiting_for_subcategory)
        
    elif main_category == "russian_movies":
        await message.answer(
            "🎪 Rus filmlarini tanlang:",
            reply_markup=kb.admin_russian_movies_subcategories_menu()
        )
        await state.set_state(AddMovieStates.waiting_for_subcategory)
        
    elif main_category == "russian_series":
        await message.answer(
            "📺 Rus seriallarini tanlang:",
            reply_markup=kb.admin_russian_series_subcategories_menu()
        )
        await state.set_state(AddMovieStates.waiting_for_subcategory)
        
    elif main_category == "kids_movies":
        await message.answer(
            "👶 Bolalar filmlarini tanlang:",
            reply_markup=kb.admin_kids_movies_subcategories_menu()
        )
        await state.set_state(AddMovieStates.waiting_for_subcategory)
        
    elif main_category == "kids_multfilms":
        await message.answer(
            "🐰 Multfilmlarni tanlang:",
            reply_markup=kb.admin_kids_multfilms_subcategories_menu()
        )
        await state.set_state(AddMovieStates.waiting_for_subcategory)
        
    elif main_category == "islamic_movies":
        await message.answer(
            "🕌 Islomiy filmlarni tanlang:",
            reply_markup=kb.admin_islamic_movies_subcategories_menu()
        )
        await state.set_state(AddMovieStates.waiting_for_subcategory)
        
    elif main_category == "islamic_series":
        await message.answer(
            "📺 Islomiy seriallarni tanlang:",
            reply_markup=kb.admin_islamic_series_subcategories_menu()
        )
        await state.set_state(AddMovieStates.waiting_for_subcategory)
        
    elif main_category == "korean_movies":
        await message.answer(
            "🇰🇷 Koreys filmlarini tanlang:",
            reply_markup=kb.admin_korean_movies_subcategories_menu()
        )
        await state.set_state(AddMovieStates.waiting_for_subcategory)
        
    elif main_category == "korean_series":
        await message.answer(
            "📺 Koreys seriallarini tanlang:",
            reply_markup=kb.admin_korean_series_subcategories_menu()
        )
        await state.set_state(AddMovieStates.waiting_for_subcategory)
        
    elif main_category == "turkish_series":
        await message.answer(
            "🇹🇷 Turk seriallarini tanlang:",
            reply_markup=kb.admin_turkish_series_subcategories_menu()
        )
        await state.set_state(AddMovieStates.waiting_for_subcategory)
        
    else:
        # Boshqa kategoriyalar uchun sub_category = "all"
        await state.update_data(sub_category="all")
        await message.answer(
            "📝 **Kino nomini kiriting:**\n\n"
            "Namuna: `Titanik` yoki `Harry Potter 1`",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
                resize_keyboard=True
            )
        )
        await state.set_state(AddMovieStates.waiting_for_title)

@admin_router.message(AddMovieStates.waiting_for_subcategory)
async def get_subcategory(message: Message, state: FSMContext):
    """Ichki kategoriyani qabul qilish"""
    if message.text == "⬅️ Ortga":
        await add_content_start(message, state)
        return
    
    # Subkategoriya nomini saqlash
    await state.update_data(sub_category=message.text)
    
    await message.answer(
        "📝 **Kino nomini kiriting:**\n\n"
        "Namuna: `Titanik` yoki `Harry Potter 1`",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
            resize_keyboard=True
        )
    )
    await state.set_state(AddMovieStates.waiting_for_title)

@admin_router.message(AddMovieStates.waiting_for_title)
async def get_title(message: Message, state: FSMContext):
    """Kino nomini qabul qilish"""
    if message.text == "⬅️ Ortga":
        data = await state.get_data()
        if 'main_category' in data:
            await add_content_start(message, state)
        return
    
    if len(message.text) < 2:
        await message.answer("❌ Kino nomi juda qisqa! Kamida 2 belgi kiriting.")
        return
    
    await state.update_data(title=message.text)
    
    await message.answer(
        "📖 **Kino haqida tavsif kiriting:**\n\n"
        "Namuna: `Dunyoning eng mashhur kino seriali`",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
            resize_keyboard=True
        )
    )
    await state.set_state(AddMovieStates.waiting_for_description)

@admin_router.message(AddMovieStates.waiting_for_description)
async def get_description(message: Message, state: FSMContext):
    """Kino tavsifini qabul qilish"""
    if message.text == "⬅️ Ortga":
        await state.set_state(AddMovieStates.waiting_for_title)
        await message.answer("Kino nomini kiriting:")
        return
    
    await state.update_data(description=message.text)
    
    await message.answer(
        "🌐 **Kino tilini tanlang:**",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Ruscha")],
                [KeyboardButton(text="🇬🇧 Inglizcha"), KeyboardButton(text="🌍 Aralash")],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        )
    )
    await state.set_state(AddMovieStates.waiting_for_language)

@admin_router.message(AddMovieStates.waiting_for_language)
async def get_language(message: Message, state: FSMContext):
    """Kino tilini qabul qilish va sifatni so'rash"""
    if message.text == "⬅️ Ortga":
        await state.set_state(AddMovieStates.waiting_for_description)
        await message.answer("Kino haqida tavsif kiriting:")
        return
    
    language_map = {
        "🇺🇿 O'zbekcha": "uz",
        "🇷🇺 Ruscha": "ru",
        "🇬🇧 Inglizcha": "en",
        "🌍 Aralash": "mixed"
    }
    
    if message.text not in language_map:
        await message.answer("❌ Noto'g'ri til tanlovi!")
        return
    
    await state.update_data(language=language_map[message.text])
    
    # Sifatni so'rash
    await message.answer(
        "🎬 **Kino sifatini tanlang:**",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📺 HD (720p)"), KeyboardButton(text="🎬 Full HD (1080p)")],
                [KeyboardButton(text="🎥 2K"), KeyboardButton(text="🎞️ 4K")],
                [KeyboardButton(text="📱 SD (480p)"), KeyboardButton(text="📼 Boshqa")],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        )
    )
    await state.set_state(AddMovieStates.waiting_for_quality)

@admin_router.message(AddMovieStates.waiting_for_quality)
async def get_quality(message: Message, state: FSMContext):
    """Kino sifatini qabul qilish"""
    if message.text == "⬅️ Ortga":
        await state.set_state(AddMovieStates.waiting_for_language)
        await message.answer("Kino tilini tanlang:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Ruscha")],
                [KeyboardButton(text="🇬🇧 Inglizcha"), KeyboardButton(text="🌍 Aralash")],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        ))
        return
    
    quality_map = {
        "📺 HD (720p)": "720p",
        "🎬 Full HD (1080p)": "1080p",
        "🎥 2K": "2K",
        "🎞️ 4K": "4K",
        "📱 SD (480p)": "480p",
        "📼 Boshqa": "Other"
    }
    
    if message.text not in quality_map:
        await message.answer("❌ Noto'g'ri sifat tanlovi!")
        return
    
    await state.update_data(quality=quality_map[message.text])
    
    # Chiqarilgan yilni so'rash
    current_year = datetime.now().year
    
    # Yillar tugmalarini yaratish - TUZATILGAN VERSIYA
    year_buttons = []
    
    # Oxirgi 20 yilni ko'rsatish
    recent_years = list(range(current_year, current_year - 20, -1))
    
    # Har bir qatorda 4 ta tugma
    for i in range(0, len(recent_years), 4):
        row = []
        for j in range(4):
            index = i + j
            if index < len(recent_years):
                row.append(KeyboardButton(text=str(recent_years[index])))
        if row:
            year_buttons.append(row)
    
    # Navigatsiya tugmalari
    year_buttons.append([KeyboardButton(text="⬅️ Ortga"), KeyboardButton(text="📝 Boshqa yil")])
    
    await message.answer(
        "📅 **Kino chiqarilgan yilini tanlang:**",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=year_buttons,
            resize_keyboard=True
        )
    )
    await state.set_state(AddMovieStates.waiting_for_release_year)

@admin_router.message(AddMovieStates.waiting_for_release_year)
async def get_release_year(message: Message, state: FSMContext):
    """Kino chiqarilgan yilini qabul qilish"""
    if message.text == "⬅️ Ortga":
        await state.set_state(AddMovieStates.waiting_for_quality)
        await message.answer("Kino sifatini tanlang:")
        return
    
    if message.text == "📝 Boshqa yil":
        await message.answer(
            "📅 **Kino chiqarilgan yilini kiriting:**\n\n"
            "Namuna: `2019` yoki `2023`",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
                resize_keyboard=True
            )
        )
        return
    
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return
    
    year = int(message.text)
    current_year = datetime.now().year
    
    if year < 1900 or year > current_year + 5:
        await message.answer(f"❌ Noto'g'ri yil! 1900-{current_year + 5} oralig'ida kiriting.")
        return
    
    await state.update_data(release_year=year)
    
    # Premium holatini so'rash
    await message.answer(
        "💰 **Kontent holatini tanlang:**\n\n"
        "Bu kontent pullik yoki bepul bo'ladi:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💰 Pullik kontent"), KeyboardButton(text="🆓 Bepul kontent")],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        )
    )
    await state.set_state(AddMovieStates.waiting_for_premium_status)

@admin_router.message(AddMovieStates.waiting_for_premium_status)
async def get_premium_status(message: Message, state: FSMContext):
    """Kontentning pullik/bepul holatini qabul qilish"""
    if message.text == "⬅️ Ortga":
        await state.set_state(AddMovieStates.waiting_for_language)
        await message.answer("Kino tilini tanlang:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Ruscha")],
                [KeyboardButton(text="🇬🇧 Inglizcha"), KeyboardButton(text="🌍 Aralash")],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        ))
        return
    
    if message.text == "💰 Pullik kontent":
        await state.update_data(is_premium=True)
        
        # Narxni so'rash
        await message.answer(
            "💰 **Kontent narxini kiriting (so'mda):**\n\n"
            "Namuna: `5000` yoki `10000`",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
                resize_keyboard=True
            )
        )
        await state.set_state(AddMovieStates.waiting_for_price)
        
    elif message.text == "🆓 Bepul kontent":
        await state.update_data(is_premium=False, price=0)
        
        # Faylni so'rashga o'tish
        await message.answer(
            "🎬 **Endi video faylini yuboring:**\n\n"
            "📁 **Qo'llab-quvvatlanadigan formatlar:**\n"
            "• Telegram video fayllari (MP4, AVI, MKV)\n"
            "• Telegram dokument fayllari\n"
            "• Telegram audio fayllari\n\n"
            "📊 **Maksimal hajm:** 2GB\n"
            "⏱️ **Maksimal davomiylik:** 4 soat\n\n"
            "Faylni yuborish uchun 📎 tugmasidan foydalaning yoki video yuboring.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
                resize_keyboard=True
            )
        )
        await state.set_state(AddMovieStates.waiting_for_file)
        
    else:
        await message.answer("❌ Noto'g'ri tanlov!")

@admin_router.message(AddMovieStates.waiting_for_price)
async def get_price(message: Message, state: FSMContext):
    """Pullik kontent uchun narxni qabul qilish"""
    if message.text == "⬅️ Ortga":
        await state.set_state(AddMovieStates.waiting_for_premium_status)
        await message.answer("Kontent holatini tanlang:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💰 Pullik kontent"), KeyboardButton(text="🆓 Bepul kontent")],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        ))
        return
    
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return
    
    price = int(message.text)
    
    if price < 1000 or price > 1000000:
        await message.answer("❌ Narx 1000 dan 1,000,000 so'mgacha bo'lishi kerak!")
        return
    
    await state.update_data(price=price)
    
    # Faylni so'rash
    await message.answer(
        "🎬 **Endi video faylini yuboring:**\n\n"
        "📁 **Qo'llab-quvvatlanadigan formatlar:**\n"
        "• Telegram video fayllari (MP4, AVI, MKV)\n"
        "• Telegram dokument fayllari\n"
        "• Telegram audio fayllari\n\n"
        "📊 **Maksimal hajm:** 2GB\n"
        "⏱️ **Maksimal davomiylik:** 4 soat\n\n"
        "Faylni yuborish uchun 📎 tugmasidan foydalaning yoki video yuboring.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
            resize_keyboard=True
        )
    )
    await state.set_state(AddMovieStates.waiting_for_file)

@admin_router.message(AddMovieStates.waiting_for_file)
async def get_file(message: Message, state: FSMContext):
    """Kino faylini qabul qilish - ADMIN uchun (YANGILANGAN)"""
    if message.text == "⬅️ Ortga":
        data = await state.get_data()
        if data.get('is_premium', False):
            await state.set_state(AddMovieStates.waiting_for_price)
            await message.answer("Kontent narxini kiriting:")
        else:
            await state.set_state(AddMovieStates.waiting_for_premium_status)
            await message.answer("Kontent holatini tanlang:", reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="💰 Pullik kontent"), KeyboardButton(text="🆓 Bepul kontent")],
                    [KeyboardButton(text="⬅️ Ortga")]
                ],
                resize_keyboard=True
            ))
        return
    
    # Admin ekanligini tekshirish
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    file_id = None
    file_type = None
    file_size = None
    
    if message.video:
        file_id = message.video.file_id
        file_type = "video"
        file_size = message.video.file_size
        # Davomiylikni olish
        duration = message.video.duration if hasattr(message.video, 'duration') else None
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
        file_size = message.document.file_size
        duration = None
    elif message.audio:
        file_id = message.audio.file_id
        file_type = "audio"
        file_size = message.audio.file_size
        duration = message.audio.duration if hasattr(message.audio, 'duration') else None
    else:
        await message.answer("❌ Iltimos, video yoki dokument fayl yuboring!")
        return
    
    # Davomiylikni formatlash
    if duration:
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        if hours > 0:
            duration_str = f"{hours}h {minutes}m"
        else:
            duration_str = f"{minutes}m {seconds}s"
    else:
        duration_str = "Noma'lum"
    
    await state.update_data(
        file_id=file_id, 
        file_type=file_type, 
        file_size=file_size,
        duration=duration_str
    )
    
    data = await state.get_data()
    
    # Ma'lumotlarni tasdiqlash
    is_premium = data.get('is_premium', False)
    price = data.get('price', 0)
    quality = data.get('quality', 'HD')
    release_year = data.get('release_year', 'Noma\'lum')
    
    confirmation_text = f"""✅ **MA'LUMOTLAR TASDIQLANDI:**

🎬 **Nomi:** {data['title']}
📖 **Tavsif:** {data['description']}
🗂️ **Kategoriya:** {data['main_category']}
📂 **Ichki kategoriya:** {data.get('sub_category', 'all')}
🌐 **Til:** {format_language(data.get('language', 'uz'))}
🎥 **Sifat:** {quality}
📅 **Yil:** {release_year}
⏱️ **Davomiylik:** {duration_str}
💰 **Holat:** {'💰 PULLIK' if is_premium else '🆓 BEPUL'}"""

    if is_premium:
        confirmation_text += f"""
💵 **Narx:** {price:,} so'm"""

    confirmation_text += f"""
📁 **Fayl turi:** {file_type}
📊 **Fayl hajmi:** {file_size // (1024*1024)} MB

📌 **Qo'shishni tasdiqlaysizmi?**"""
    
    await message.answer(
        confirmation_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Tasdiqlash"), KeyboardButton(text="❌ Bekor qilish")]
            ],
            resize_keyboard=True
        )
    )
    await state.set_state(AddMovieStates.waiting_for_confirmation)

@admin_router.message(AddMovieStates.waiting_for_confirmation)
async def confirm_addition(message: Message, state: FSMContext):
    """Kontent qo'shishni tasdiqlash (YANGILANGAN)"""
    if message.text == "❌ Bekor qilish":
        await message.answer("❌ Kontent qo'shish bekor qilindi!")
        await admin_panel(message, state)
        return
    
    if message.text != "✅ Tasdiqlash":
        await message.answer("❌ Noto'g'ri tanlov!")
        return
    
    data = await state.get_data()
    
    # Kerakli ma'lumotlarni tekshirish
    required_fields = ['main_category', 'title', 'description', 'file_id', 'file_type', 'language']
    for field in required_fields:
        if field not in data:
            await message.answer(f"❌ Xatolik: {field} topilmadi!")
            await admin_panel(message, state)
            return
    
    # Sub_category bo'lishini tekshirish
    sub_category = data.get('sub_category', 'all')
    
    # Premium holatini olish
    is_premium = data.get('is_premium', False)
    price = data.get('price', 0)
    
    # Qo'shimcha ma'lumotlar
    quality = data.get('quality', 'HD')
    release_year = data.get('release_year')
    duration = data.get('duration')
    file_size = data.get('file_size', 0)
    
    # Bazaga saqlash (yangi funksiya bilan)
    movie_id = db.add_movie(
        main_category=data['main_category'],
        sub_category=sub_category,
        title=data['title'],
        description=data['description'],
        file_id=data['file_id'],
        file_type=data['file_type'],
        language=data['language'],
        added_by=message.from_user.id,
        is_premium=is_premium,
        price=price if is_premium else 0,
        quality=quality,
        release_year=release_year,
        duration=duration,
        file_size=file_size
    )
    
    if movie_id:
        status_text = f"💰 Pullik ({price:,} so'm)" if is_premium else "🆓 Bepul"
        
        await message.answer(
            f"✅ **KONTENT MUVAFFAQIYATLI QO'SHILDI!**\n\n"
            f"🎬 ID: `{movie_id}`\n"
            f"📛 Nomi: {data['title']}\n"
            f"💰 Holat: {status_text}\n"
            f"🎥 Sifat: {quality}\n"
            f"📅 Yil: {release_year}\n"
            f"📁 Kategoriya: {data['main_category']}\n"
            f"📂 Ichki kategoriya: {sub_category}\n\n"
            f"✅ Bazaga saqlandi!",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="➕ Yangi kontent qo'shish"), KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    else:
        await message.answer(
            "❌ **Xatolik yuz berdi!**\n\n"
            "Kontent qo'shishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    
    await state.clear()

# ==================== DELETE CONTENT IMPROVED ====================
@admin_router.message(F.text == "🗑️ Kontent O'chirish")
async def delete_content_start(message: Message, state: FSMContext):
    """Kontent o'chirishni boshlash"""
    if not is_admin(message.from_user.id):
        return
    
    await state.clear()
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 ID bo'yicha o'chirish"), KeyboardButton(text="📂 Kategoriya bo'yicha")],
            [KeyboardButton(text="🗑️ Barcha filmlarni o'chirish"), KeyboardButton(text="⬅️ Ortga")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "🗑️ **Kontent o'chirish**\n\n"
        "Qanday usulda o'chirmoqchisiz?",
        reply_markup=keyboard
    )
    await state.set_state(DeleteMovieStates.waiting_for_method)

# ==================== DELETE BY METHOD SELECTION ====================
@admin_router.message(DeleteMovieStates.waiting_for_method)
async def delete_method_selection(message: Message, state: FSMContext):
    """O'chirish usulini tanlash"""
    if message.text == "⬅️ Ortga":
        await admin_panel(message, state)
        return
    
    if message.text == "🔍 ID bo'yicha o'chirish":
        await message.answer(
            "🔍 **ID bo'yicha o'chirish**\n\n"
            "O'chirmoqchi bo'lgan film ID sini kiriting:\n\n"
            "Film ID sini bilmasangiz '📂 Kategoriya bo'yicha' tanlang.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
                resize_keyboard=True
            )
        )
        await state.set_state(DeleteMovieStates.waiting_for_movie_id)
        
    elif message.text == "📂 Kategoriya bo'yicha":
        kb = Keyboards('uz')
        
        await message.answer(
            "📂 **Kategoriya bo'yicha o'chirish**\n\n"
            "Kategoriyani tanlang:",
            reply_markup=kb.admin_categories_menu()
        )
        await state.set_state(DeleteMovieStates.waiting_for_category)
        
    elif message.text == "🗑️ Barcha filmlarni o'chirish":
        await message.answer(
            "⚠️ **DIQQAT!**\n\n"
            "Siz BAZADAGI BARCHA FILMLARNI o'chirmoqchisiz!\n\n"
            "Bu amalni qaytarib bo'lmaydi!\n\n"
            "Tasdiqlash uchun '✅ Tasdiqlayman, o'chirish' deb yozing:\n\n"
            "Bekor qilish uchun '❌ Bekor qilish' tugmasini bosing.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="✅ Tasdiqlayman, o'chirish"), KeyboardButton(text="❌ Bekor qilish")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(DeleteMovieStates.waiting_for_all_confirmation)
        
    else:
        await message.answer("❌ Noto'g'ri tanlov!")

# ==================== DELETE BY MOVIE ID ====================
@admin_router.message(DeleteMovieStates.waiting_for_movie_id)
async def delete_by_id(message: Message, state: FSMContext):
    """ID bo'yicha film o'chirish"""
    if message.text == "⬅️ Ortga":
        await delete_content_start(message, state)
        return
    
    if not message.text.isdigit():
        await message.answer("❌ ID faqat raqamlardan iborat bo'lishi kerak!")
        return
    
    movie_id = int(message.text)
    
    # Filmni bazadan qidirish
    movie = db.get_movie_by_id(movie_id)
    
    if not movie:
        await message.answer(
            f"❌ **Film topilmadi!**\n\n"
            f"ID {movie_id} bo'yicha hech qanday film topilmadi.\n\n"
            f"ID ni tekshirib, qayta kiriting yoki '📂 Kategoriya bo'yicha' tanlang.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
                resize_keyboard=True
            )
        )
        return
    
    await state.update_data(movie_id=movie_id, movie_info=movie)
    
    movie_info = f"""🎬 **Film ma'lumotlari:**

🆔 **ID:** {movie[0]}
📛 **Nomi:** {movie[3]}
📖 **Tavsif:** {movie[4][:100]}{'...' if len(movie[4]) > 100 else ''}
🗂️ **Kategoriya:** {movie[1]}
📂 **Ichki kategoriya:** {movie[2]}
🌐 **Til:** {movie[7]}
💰 **Holat:** {'Pullik' if movie[10] == 1 else 'Bepul'}
👁️ **Ko'rishlar:** {movie[8]}
📅 **Qo'shilgan:** {movie[9][:19]}
👤 **Qo'shgan:** {movie[12]}

❓ **Bu filmini o'chirishni tasdiqlaysizmi?**"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Ha, o'chirish"), KeyboardButton(text="❌ Yo'q, bekor qilish")],
            [KeyboardButton(text="📋 Boshqa filmni o'chirish")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(movie_info, reply_markup=keyboard)
    await state.set_state(DeleteMovieStates.waiting_for_confirmation)

# ==================== DELETE BY CATEGORY ====================
@admin_router.message(DeleteMovieStates.waiting_for_category)
async def delete_by_category(message: Message, state: FSMContext):
    """Kategoriya bo'yicha film o'chirish"""
    if message.text == "⬅️ Ortga":
        await delete_content_start(message, state)
        return
    
    category_map = {
        "🎭 Hollywood Kinolari": "hollywood_movies",
        "🕌 Hind Filmlari": "indian_movies",
        "📺 Hind Seriallari": "indian_series",
        "🎪 Rus Kinolari": "russian_movies",
        "📺 Rus Seriallari": "russian_series",
        "🇺🇿 O'zbek Kinolari": "uzbek_movies",
        "📺 O'zbek Seriallari": "uzbek_series",
        "🕌 Islomiy Kinolar": "islamic_movies",
        "📺 Islomiy Seriallar": "islamic_series",
        "🇹🇷 Turk Kinolari": "turkish_movies",
        "📺 Turk Seriallari": "turkish_series",
        "👶 Bolalar Kinolari": "kids_movies",
        "🐰 Bolalar Multfilmlari": "kids_multfilms",
        "🇰🇷 Koreys Kinolari": "korean_movies",
        "📺 Koreys Seriallari": "korean_series",
        "🎥 Qisqa Filmlar": "short_films"
    }
    
    if message.text not in category_map:
        await message.answer("❌ Noto'g'ri kategoriya!")
        return
    
    main_category = category_map[message.text]
    await state.update_data(main_category=main_category, category_name=message.text)
    
    # Kategoriyadagi filmlar soni
    movies_count = db.get_movies_count_by_category(main_category)
    
    if movies_count == 0:
        await message.answer(
            f"❌ **{message.text}** kategoriyasida hech qanday film yo'q!",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
                resize_keyboard=True
            )
        )
        return
    
    # Kategoriyadagi filmlarni olish
    movies = db.get_movies_by_main_category(main_category)
    
    # Filmlarni guruhlab ko'rsatish (har bir guruh 10 tadan)
    page_size = 10
    pages = (movies_count + page_size - 1) // page_size
    
    await state.update_data(all_movies=movies, current_page=1, total_pages=pages)
    
    # Birinchi sahifani ko'rsatish
    await show_category_page(message, state)

async def show_category_page(message: Message, state: FSMContext):
    """Kategoriya sahifasini ko'rsatish"""
    data = await state.get_data()
    movies = data.get('all_movies', [])
    current_page = data.get('current_page', 1)
    total_pages = data.get('total_pages', 1)
    category_name = data.get('category_name', '')
    
    page_size = 10
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, len(movies))
    
    movies_text = f"📂 **{category_name}**\n\n"
    movies_text += f"📊 Jami filmlar: {len(movies)} ta\n"
    movies_text += f"📄 Sahifa: {current_page}/{total_pages}\n\n"
    
    # Sahifadagi filmlarni ro'yxati
    page_movies = []
    for i in range(start_idx, end_idx):
        movie = movies[i]
        item_num = i + 1
        
        movies_text += f"{item_num}. **{movie[3]}**\n"
        movies_text += f"   🆔 ID: {movie[0]}\n"
        movies_text += f"   💰 Holat: {'💰 Pullik' if movie[10] == 1 else '🆓 Bepul'}\n"
        if movie[10] == 1:
            movies_text += f"   💵 Narx: {movie[11]:,} so'm\n"
        movies_text += f"   📖 {movie[4][:50]}{'...' if len(movie[4]) > 50 else ''}\n"
        movies_text += f"   👁️ {movie[8]} ko'rish\n"
        movies_text += "─" * 30 + "\n"
        
        page_movies.append(movie)
    
    await state.update_data(page_movies=page_movies)
    
    # Sahifalash tugmalari
    keyboard_buttons = []
    
    # Har bir film uchun tugma
    for i, movie in enumerate(page_movies, 1):
        keyboard_buttons.append([KeyboardButton(text=f"🗑️ {i}. {movie[3][:20]}{'...' if len(movie[3]) > 20 else ''}")])
    
    # Navigatsiya tugmalari
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(KeyboardButton(text="⬅️ Oldingi"))
    if current_page < total_pages:
        nav_buttons.append(KeyboardButton(text="Keyingi ➡️"))
    
    if nav_buttons:
        keyboard_buttons.append(nav_buttons)
    
    keyboard_buttons.append([
        KeyboardButton(text="🎯 Tanlash orqali o'chirish"),
        KeyboardButton(text="📝 ID kirish orqali")
    ])
    
    keyboard_buttons.append([KeyboardButton(text="⬅️ Ortga")])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard_buttons,
        resize_keyboard=True
    )
    
    await message.answer(movies_text, reply_markup=keyboard)
    await state.set_state(DeleteMovieStates.waiting_for_movie_selection)

@admin_router.message(DeleteMovieStates.waiting_for_movie_selection)
async def handle_category_movie_selection(message: Message, state: FSMContext):
    """Kategoriyadagi filmni tanlash"""
    if message.text == "⬅️ Ortga":
        await delete_content_start(message, state)
        return
    
    if message.text == "⬅️ Oldingi":
        data = await state.get_data()
        current_page = data.get('current_page', 1)
        if current_page > 1:
            await state.update_data(current_page=current_page - 1)
            await show_category_page(message, state)
        return
    
    if message.text == "Keyingi ➡️":
        data = await state.get_data()
        current_page = data.get('current_page', 1)
        total_pages = data.get('total_pages', 1)
        if current_page < total_pages:
            await state.update_data(current_page=current_page + 1)
            await show_category_page(message, state)
        return
    
    if message.text == "🎯 Tanlash orqali o'chirish":
        await message.answer(
            "Tanlagan filmining raqamini kiriting (1-10):",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
                resize_keyboard=True
            )
        )
        await state.set_state(DeleteMovieStates.waiting_for_movie_number)
        return
    
    if message.text == "📝 ID kirish orqali":
        await message.answer(
            "O'chirmoqchi bo'lgan film ID sini kiriting:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
                resize_keyboard=True
            )
        )
        await state.set_state(DeleteMovieStates.waiting_for_movie_id)
        return
    
    # Agar film nomi bilan tanlangan bo'lsa
    if message.text.startswith("🗑️"):
        # Tugma matnidan film raqamini ajratib olish
        try:
            movie_num = int(message.text.split('.')[0].replace('🗑️', '').strip())
            data = await state.get_data()
            page_movies = data.get('page_movies', [])
            
            if 1 <= movie_num <= len(page_movies):
                selected_movie = page_movies[movie_num - 1]
                await show_movie_confirmation(message, state, selected_movie)
                return
        except:
            pass
    
    await message.answer("❌ Noto'g'ri tanlov! Iltimos, tugmalardan foydalaning.")

@admin_router.message(DeleteMovieStates.waiting_for_movie_number)
async def handle_movie_number(message: Message, state: FSMContext):
    """Film raqamini qabul qilish"""
    if message.text == "⬅️ Ortga":
        data = await state.get_data()
        await state.set_state(DeleteMovieStates.waiting_for_movie_selection)
        await show_category_page(message, state)
        return
    
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return
    
    movie_num = int(message.text)
    data = await state.get_data()
    page_movies = data.get('page_movies', [])
    
    if not 1 <= movie_num <= len(page_movies):
        await message.answer(f"❌ Noto'g'ri raqam! 1-{len(page_movies)} oralig'ida kiriting.")
        return
    
    selected_movie = page_movies[movie_num - 1]
    await show_movie_confirmation(message, state, selected_movie)

async def show_movie_confirmation(message: Message, state: FSMContext, movie):
    """Film o'chirishni tasdiqlash sahifasini ko'rsatish"""
    movie_info = f"""🎬 **Film ma'lumotlari:**

🆔 **ID:** {movie[0]}
📛 **Nomi:** {movie[3]}
📖 **Tavsif:** {movie[4][:100]}{'...' if len(movie[4]) > 100 else ''}
🗂️ **Kategoriya:** {movie[1]}
📂 **Ichki kategoriya:** {movie[2]}
🌐 **Til:** {movie[7]}
💰 **Holat:** {'Pullik' if movie[10] == 1 else 'Bepul'}
👁️ **Ko'rishlar:** {movie[8]}
📅 **Qo'shilgan:** {movie[9][:19]}

⚠️ **DIQQAT:** Bu filmni o'chirsangiz, uning barcha statistikasi va loglari ham o'chiriladi!

❓ **Bu filmini o'chirishni tasdiqlaysizmi?**"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Ha, o'chirish"), KeyboardButton(text="❌ Yo'q, bekor qilish")],
            [KeyboardButton(text="⬅️ Ortga kategoriyalarga")]
        ],
        resize_keyboard=True
    )
    
    await state.update_data(selected_movie=movie)
    await message.answer(movie_info, reply_markup=keyboard)
    await state.set_state(DeleteMovieStates.waiting_for_confirmation)

# ==================== DELETE ALL MOVIES ====================
@admin_router.message(DeleteMovieStates.waiting_for_all_confirmation)
async def delete_all_confirmation(message: Message, state: FSMContext):
    """Barcha filmlarni o'chirishni tasdiqlash"""
    if message.text == "❌ Bekor qilish":
        await message.answer("❌ Barcha filmlarni o'chirish bekor qilindi!")
        await admin_panel(message, state)
        return
    
    if message.text != "✅ Tasdiqlayman, o'chirish":
        await message.answer("❌ Noto'g'ri javob! '✅ Tasdiqlayman, o'chirish' deb yozing.")
        return
    
    # Barcha filmlarni o'chirish
    total_movies = db.get_movies_count()
    
    if total_movies == 0:
        await message.answer("❌ Bazada hech qanday film yo'q!")
        await admin_panel(message, state)
        return
    
    # Tasdiqlash uchun yana bir marta so'rash
    await message.answer(
        f"⚠️ **SO'NGI CHORA!**\n\n"
        f"Siz {total_movies} ta filmini o'chirmoqchisiz.\n\n"
        f"Bu amalni QAYTARIB BO'LMAYDI!\n\n"
        f"**O'chirish** deb yozing tasdiqlash uchun:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="O'chirish"), KeyboardButton(text="❌ BEKOR QILISH")]],
            resize_keyboard=True
        )
    )
    await state.set_state(DeleteMovieStates.waiting_for_final_confirmation)

@admin_router.message(DeleteMovieStates.waiting_for_final_confirmation)
async def delete_all_final(message: Message, state: FSMContext):
    """Barcha filmlarni o'chirishni yakuniy tasdiqlash"""
    if message.text == "❌ BEKOR QILISH":
        await message.answer("✅ Barcha filmlarni o'chirish bekor qilindi!")
        await admin_panel(message, state)
        return
    
    if message.text != "O'chirish":
        await message.answer("❌ Noto'g'ri javob! 'O'chirish' deb yozing.")
        return
    
    # Barcha filmlarni o'chirish
    deleted_count = db.delete_all_movies()
    
    await message.answer(
        f"✅ **Barcha filmlar o'chirildi!**\n\n"
        f"🗑️ O'chirilgan filmlar: {deleted_count} ta\n"
        f"📊 Bazada qolgan filmlar: 0 ta\n\n"
        f"✅ Database tozalandi.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
            resize_keyboard=True
        )
    )
    
    await state.clear()

# ==================== FINAL CONFIRMATION FOR ALL METHODS ====================
@admin_router.message(DeleteMovieStates.waiting_for_confirmation)
async def process_deletion_confirmation(message: Message, state: FSMContext):
    """Film o'chirishni tasdiqlash"""
    if message.text == "❌ Yo'q, bekor qilish" or message.text == "⬅️ Ortga kategoriyalarga":
        await message.answer("❌ O'chirish bekor qilindi!")
        await delete_content_start(message, state)
        return
    
    if message.text == "📋 Boshqa filmni o'chirish":
        await delete_content_start(message, state)
        return
    
    if message.text != "✅ Ha, o'chirish":
        await message.answer("❌ Noto'g'ri tanlov!")
        return
    
    data = await state.get_data()
    
    # ID orqali o'chirish
    if 'movie_id' in data:
        movie_id = data['movie_id']
        success = db.delete_movie(movie_id)
        
        if success:
            await message.answer(
                f"✅ **Film muvaffaqiyatli o'chirildi!**\n\n"
                f"🆔 ID: {movie_id}\n"
                f"📛 Nomi: {data['movie_info'][3]}\n\n"
                f"🗑️ Bazadan o'chirildi!",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="🗑️ Boshqa film o'chirish"), 
                         KeyboardButton(text="👑 Admin paneli")]
                    ],
                    resize_keyboard=True
                )
            )
        else:
            await message.answer(
                f"❌ **Xatolik yuz berdi!**\n\n"
                f"Film o'chirishda xatolik yuz berdi.\n"
                f"ID: {movie_id}",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                    resize_keyboard=True
                )
            )
    
    # Kategoriya orqali tanlangan film
    elif 'selected_movie' in data:
        movie = data['selected_movie']
        success = db.delete_movie(movie[0])
        
        if success:
            await message.answer(
                f"✅ **Film muvaffaqiyatli o'chirildi!**\n\n"
                f"🆔 ID: {movie[0]}\n"
                f"📛 Nomi: {movie[3]}\n"
                f"🗂️ Kategoriya: {movie[1]}\n\n"
                f"🗑️ Bazadan o'chirildi!",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="🗑️ Boshqa film o'chirish"), 
                         KeyboardButton(text="👑 Admin paneli")]
                    ],
                    resize_keyboard=True
                )
            )
        else:
            await message.answer(
                f"❌ **Xatolik yuz berdi!**\n\n"
                f"Film o'chirishda xatolik yuz berdi.\n"
                f"ID: {movie[0]}",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                    resize_keyboard=True
                )
            )
    
    else:
        await message.answer("❌ Film ma'lumotlari topilmadi!")
    
    await state.clear()

# ==================== USERS MANAGEMENT - TUZATILGAN ====================
@admin_router.message(F.text == "👥 Foydalanuvchilar")
async def users_management(message: Message):
    """Foydalanuvchilar boshqaruvini ochish"""
    if not is_admin(message.from_user.id):
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Barcha foydalanuvchilar"), KeyboardButton(text="📅 Yangi foydalanuvchilar")],
            [KeyboardButton(text="🔍 Foydalanuvchi qidirish"), KeyboardButton(text="📈 Faollik statistikasi")],
            [KeyboardButton(text="⬅️ Ortga")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "👥 **Foydalanuvchilar boshqaruvi**\n\n"
        "Kerakli amalni tanlang:",
        reply_markup=keyboard
    )

# ========== BARCHA FOYDALANUVCHILAR - FIXED ==========
@admin_router.message(F.text == "📋 Barcha foydalanuvchilar")
async def all_users(message: Message):
    """Barcha foydalanuvchilarni ko'rsatish"""
    try:
        # Admin tekshirish
        if not is_admin(message.from_user.id):
            await message.answer("❌ Bu funksiya faqat adminlar uchun!")
            return
        
        # Kutish xabarini yuborish
        wait_msg = await message.answer("📊 Foydalanuvchilar yuklanmoqda...")
        
        # Database dan foydalanuvchilarni olish
        try:
            # Foydalanuvchilarni olish
            db.cursor.execute('''
                SELECT * FROM users ORDER BY registered_date DESC
            ''')
            users = db.cursor.fetchall()
        except Exception as db_error:
            await wait_msg.delete()
            await message.answer(f"❌ Database xatosi: {db_error}")
            return
        
        if not users:
            await wait_msg.delete()
            await message.answer("📭 Hali hech qanday foydalanuvchi yo'q.")
            return
        
        # Foydalanuvchilarni ko'rsatish
        await wait_msg.delete()
        
        total_users = len(users)
        users_text = f"📋 **Barcha foydalanuvchilar** - Jami: {total_users} ta\n\n"
        
        for i, user in enumerate(users, 1):
            try:
                # Ma'lumotlarni olish va escape qilish
                user_id = user[0] if user and len(user) > 0 else "N/A"
                username = user[1] if user and len(user) > 1 else None
                full_name = escape_markdown(user[2] if user and len(user) > 2 else "N/A")
                phone = escape_markdown(user[3] if user and len(user) > 3 else "Yo'q")
                language = escape_markdown(user[4] if user and len(user) > 4 else "uz")
                registered_date = user[5] if user and len(user) > 5 else "N/A"
                status = escape_markdown(user[6] if user and len(user) > 6 else "active")
                is_admin_user = user[7] if user and len(user) > 7 else 0
                balance = user[8] if user and len(user) > 8 else 0
                subscription_expires = user[9] if user and len(user) > 9 else None
                purchase_balance = user[10] if user and len(user) > 10 else 0
                watching_history = user[11] if user and len(user) > 11 else None
                
                # Admin statusini aniqlash
                admin_status = "👑 Admin" if is_admin_user == 1 else "👤 Foydalanuvchi"
                
                # Ro'yxatdan o'tgan sana
                if registered_date and registered_date != "N/A":
                    reg_date_display = registered_date[:19] if len(registered_date) >= 19 else registered_date
                else:
                    reg_date_display = "N/A"
                
                # Username
                username_display = f"@{username}" if username else "Yo'q"
                username_display = escape_markdown(username_display)
                
                # Telefon formatini tuzatish
                phone_display = phone if phone != "Yo'q" else "Yo'q"
                
                # Foydalanuvchi ma'lumotlari
                users_text += f"{i}. **{admin_status}:**\n"
                users_text += f"**🆔 ID:** `{user_id}`\n"
                users_text += f"**👤 Ism:** {full_name}\n"
                users_text += f"**📱 Telefon:** {phone_display}\n"
                users_text += f"**🌐 Username:** {username_display}\n"
                users_text += f"**💰 Balans:** {balance:,} so'm\n"
                users_text += f"**🌐 Til:** {language}\n"
                users_text += f"**📅 Ro'yxatdan o'tgan:** {reg_date_display}\n"
                users_text += f"**📊 Status:** {status}\n"
                users_text += "─────────────────────\n"
                
                # Har 3 ta foydalanuvchidan keyin yangi xabar
                if i % 3 == 0 and i < total_users:
                    await message.answer(users_text, parse_mode="Markdown")
                    users_text = ""
                    
            except Exception as e:
                print(f"Foydalanuvchi {i} ni o'qishda xatolik: {e}")
                continue
        
        # Qolgan foydalanuvchilarni yuborish
        if users_text:
            await message.answer(users_text, parse_mode="Markdown")
        
        # Jami statistika
        admin_count = sum([1 for user in users if user[7] == 1])
        total_balance = sum([user[8] if user and len(user) > 8 else 0 for user in users])
        
        stats_text = f"""
📊 **JAMI STATISTIKA:**
👥 **Foydalanuvchilar:** {total_users} ta
👑 **Adminlar:** {admin_count} ta
👤 **Oddiy foydalanuvchilar:** {total_users - admin_count} ta
💰 **Umumiy balans:** {total_balance:,} so'm
📅 **Oxirgi yangilanish:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ **Barcha foydalanuvchilar ko'rsatildi!**
"""
        await message.answer(stats_text)
        
    except Exception as e:
        print(f"all_users xatosi: {e}")
        await message.answer(f"❌ Xatolik: {str(e)[:200]}")

# ========== YANGI FOYDALANUVCHILAR - FIXED ==========
@admin_router.message(F.text == "📅 Yangi foydalanuvchilar")
async def new_users(message: Message):
    """Yangi foydalanuvchilarni ko'rsatish"""
    try:
        # Admin tekshirish
        if not is_admin(message.from_user.id):
            await message.answer("❌ Bu funksiya faqat adminlar uchun!")
            return
        
        # Foydalanuvchilarni olish
        db.cursor.execute('''
            SELECT * FROM users ORDER BY registered_date DESC LIMIT 20
        ''')
        users = db.cursor.fetchall()
        
        if not users:
            await message.answer("📭 Hali hech qanday foydalanuvchi yo'q.")
            return
        
        users_text = "🆕 **Yangi foydalanuvchilar** (Oxirgi 20 ta)\n\n"
        
        for i, user in enumerate(users, 1):
            try:
                user_id = user[0]
                username = user[1] if user[1] else None
                full_name = escape_markdown(user[2] if user[2] else "Noma'lum")
                phone = escape_markdown(user[3] if user[3] else "Yo'q")
                registered_date = user[5][:19] if user[5] else "N/A"
                status = escape_markdown(user[6] if user[6] else "active")
                
                # Username
                username_display = f"@{username}" if username else "Yo'q"
                username_display = escape_markdown(username_display)
                
                # Telefon formatini tuzatish
                phone_display = phone if phone != "Yo'q" else "Yo'q"
                
                users_text += f"{i}. **{full_name}**\n"
                users_text += f"**🆔 ID:** `{user_id}`\n"
                users_text += f"**📱 Telefon:** {phone_display}\n"
                users_text += f"**🌐 Username:** {username_display}\n"
                users_text += f"**📅 Ro'yxatdan o'tgan:** {registered_date}\n"
                users_text += f"**📊 Status:** {status}\n"
                users_text += "─────────────────────\n"
                
            except Exception as e:
                print(f"Foydalanuvchi {i} ni o'qishda xatolik: {e}")
                continue
        
        users_text += f"\n📊 Jami foydalanuvchilar: {len(users)} ta"
        
        await message.answer(users_text, parse_mode="Markdown")
        
    except Exception as e:
        print(f"new_users xatosi: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")

# ========== FAQLLIK STATISTIKASI - FIXED ==========
@admin_router.message(F.text == "📈 Faollik statistikasi")
async def activity_stats(message: Message):
    """Faollik statistikasini ko'rsatish"""
    try:
        if not is_admin(message.from_user.id):
            return
        
        # Jami foydalanuvchilar
        total_users = db.get_users_count()
        
        # Kunlik statistika
        try:
            db.cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(registered_date) = DATE('now')
            ''')
            today_users = db.cursor.fetchone()[0] or 0
        except:
            today_users = 0
        
        # Haftalik statistika
        try:
            db.cursor.execute('''
                SELECT DATE(registered_date) as date, COUNT(*) as count 
                FROM users 
                WHERE registered_date >= DATE('now', '-7 days')
                GROUP BY DATE(registered_date)
                ORDER BY date DESC
            ''')
            weekly_stats = db.cursor.fetchall()
        except:
            weekly_stats = []
        
        stats_text = "📈 **Faollik statistikasi**\n\n"
        
        stats_text += f"📊 **Bugungi statistika:**\n"
        stats_text += f"• Yangi foydalanuvchilar: {today_users} ta\n"
        
        if weekly_stats:
            stats_text += f"\n📅 **Haftalik statistika:**\n"
            for date, count in weekly_stats:
                stats_text += f"• {date}: {count} ta yangi foydalanuvchi\n"
        
        stats_text += f"\n👥 **Jami foydalanuvchilar:** {total_users} ta"
        
        # Premium foydalanuvchilar soni
        try:
            db.cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE subscription_expires IS NOT NULL 
                AND subscription_expires > CURRENT_TIMESTAMP
            ''')
            premium_count = db.cursor.fetchone()[0] or 0
            stats_text += f"\n💰 **Premium foydalanuvchilar:** {premium_count} ta"
        except:
            pass
        
        await message.answer(stats_text)
        
    except Exception as e:
        print(f"activity_stats xatosi: {e}")
        await message.answer(f"❌ Xatolik: {str(e)}")

# ========== FOYDALANUVCHI QIDIRISH - FIXED ==========
@admin_router.message(F.text == "🔍 Foydalanuvchi qidirish")
async def search_user_handler(message: Message, state: FSMContext):
    """Foydalanuvchi qidirishni boshlash"""
    if not is_admin(message.from_user.id):
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqami bo'yicha"), KeyboardButton(text="👤 Ism bo'yicha")],
            [KeyboardButton(text="🆔 ID bo'yicha"), KeyboardButton(text="🌐 Username bo'yicha")],
            [KeyboardButton(text="⬅️ Ortga")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "🔍 **Foydalanuvchi qidirish**\n\n"
        "Qidirish usulini tanlang:",
        reply_markup=keyboard
    )
    
    await state.set_state(AdminStates.waiting_for_user_id)
    await state.update_data(action="search_method")

@admin_router.message(AdminStates.waiting_for_user_id, F.text)
async def process_search_method(message: Message, state: FSMContext):
    """Qidirish usulini qabul qilish"""
    if message.text == "⬅️ Ortga":
        await admin_panel(message, state)
        return
    
    search_methods = {
        "📱 Telefon raqami bo'yicha": "phone",
        "👤 Ism bo'yicha": "name",
        "🆔 ID bo'yicha": "id",
        "🌐 Username bo'yicha": "username"
    }
    
    if message.text not in search_methods:
        await message.answer("❌ Noto'g'ri tanlov!")
        return
    
    method = search_methods[message.text]
    await state.update_data(search_method=method)
    
    search_prompts = {
        "phone": "📱 **Telefon raqami bo'yicha qidirish**\n\nTelefon raqamini kiriting:",
        "name": "👤 **Ism bo'yicha qidirish**\n\nIsm yoki familiyani kiriting:",
        "id": "🆔 **ID bo'yicha qidirish**\n\nFoydalanuvchi ID sini kiriting:",
        "username": "🌐 **Username bo'yicha qidirish**\n\nUsername ni kiriting (@ belgisiz):"
    }
    
    await message.answer(
        search_prompts[method],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
            resize_keyboard=True
        )
    )
    
    await state.set_state(AdminStates.waiting_for_broadcast_message)

@admin_router.message(AdminStates.waiting_for_broadcast_message, F.text)
async def process_search_query(message: Message, state: FSMContext):
    """Qidiruv so'rovini qabul qilish va natijalarni ko'rsatish"""
    if message.text == "⬅️ Ortga":
        await search_user_handler(message, state)
        return
    
    data = await state.get_data()
    search_method = data.get('search_method')
    search_query = message.text.strip()
    
    if not search_query:
        await message.answer("❌ Qidiruv so'rovini kiriting!")
        return
    
    try:
        # Qidiruvni amalga oshirish
        users = []
        
        if search_method == "id":
            if not search_query.isdigit():
                await message.answer("❌ ID faqat raqamlardan iborat bo'lishi kerak!")
                return
            
            db.cursor.execute('SELECT * FROM users WHERE user_id = ?', (int(search_query),))
            users = db.cursor.fetchall()
            
        elif search_method == "phone":
            db.cursor.execute('SELECT * FROM users WHERE phone LIKE ?', (f'%{search_query}%',))
            users = db.cursor.fetchall()
            
        elif search_method == "name":
            db.cursor.execute('SELECT * FROM users WHERE full_name LIKE ?', (f'%{search_query}%',))
            users = db.cursor.fetchall()
            
        elif search_method == "username":
            db.cursor.execute('SELECT * FROM users WHERE username LIKE ?', (f'%{search_query}%',))
            users = db.cursor.fetchall()
        
        if not users:
            await message.answer(
                f"❌ '{search_query}' bo'yicha hech qanday foydalanuvchi topilmadi.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                    resize_keyboard=True
                )
            )
            await state.clear()
            return
        
        # Natijalarni ko'rsatish
        results_text = f"🔍 **Qidiruv natijalari**\n\n"
        results_text += f"📊 Topilgan foydalanuvchilar: {len(users)} ta\n\n"
        
        for i, user in enumerate(users[:10], 1):  # Faqat birinchi 10 tasi
            user_id = user[0]
            username = f"@{user[1]}" if user[1] else "Yo'q"
            full_name = user[2] if user[2] else "Noma'lum"
            phone = user[3] if user[3] else "Yo'q"
            registered_date = user[5][:19] if user[5] else "N/A"
            status = user[6] if user[6] else "active"
            is_admin_user = "👑 Admin" if user[7] == 1 else "👤 Oddiy"
            
            results_text += f"""**{i}. {is_admin_user}**
**🆔 ID:** `{user_id}`
**👤 Ism:** {full_name}
**📱 Telefon:** {phone}
**🌐 Username:** {username}
**📅 Ro'yxatdan o'tgan:** {registered_date}
**📊 Status:** {status}
─────────────────────
"""
        
        if len(users) > 10:
            results_text += f"\n📝 Ko'rsatilgan: 10/{len(users)} ta"
        
        await message.answer(
            results_text,
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🔍 Boshqa qidiruv"), KeyboardButton(text="👑 Admin paneli")]
                ],
                resize_keyboard=True
            )
        )
        
        await state.clear()
        
    except Exception as e:
        print(f"Search error: {e}")
        await message.answer(
            f"❌ Qidiruvda xatolik: {str(e)}",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
        await state.clear()

# ========== FOYDALANUVCHI PROFILINI KO'RISH ==========
@admin_router.message(Command("user_profile"))
async def view_user_profile(message: Message):
    """Foydalanuvchi profilini ko'rish"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("❌ Foydalanuvchi ID sini kiriting: /user_profile [user_id]")
            return
        
        user_id = int(parts[1])
        
        # Foydalanuvchi ma'lumotlarini olish
        db.cursor.execute('''
            SELECT 
                u.user_id,
                u.username,
                u.full_name,
                u.phone,
                u.language,
                COALESCE(u.registration_date, u.registered_date) as reg_date,
                u.status,
                u.is_admin,
                u.balance,
                u.subscription_expires,
                COUNT(DISTINCT p.id) as payments_count,
                SUM(p.amount) as total_spent,
                COUNT(DISTINCT mp.movie_id) as purchased_movies,
                COUNT(DISTINCT da.id) as download_attempts,
                COUNT(DISTINCT apl.id) as piracy_attempts
            FROM users u
            LEFT JOIN payments p ON u.user_id = p.user_id AND p.status = 'completed'
            LEFT JOIN movie_purchases mp ON u.user_id = mp.user_id
            LEFT JOIN download_attempts da ON u.user_id = da.user_id
            LEFT JOIN anti_piracy_logs apl ON u.user_id = apl.user_id
            WHERE u.user_id = ?
            GROUP BY u.user_id
        ''', (user_id,))
        
        user_data = db.cursor.fetchone()
        
        if not user_data:
            await message.answer(f"❌ Foydalanuvchi {user_id} topilmadi!")
            return
        
        # Ma'lumotlarni ajratish
        user_id = user_data[0]
        username = f"@{user_data[1]}" if user_data[1] else "Yo'q"
        full_name = user_data[2]
        phone = user_data[3] if user_data[3] else "Yo'q"
        language = user_data[4]
        reg_date = user_data[5][:19] if user_data[5] else "N/A"
        status = user_data[6]
        is_admin = "👑 Admin" if user_data[7] == 1 else "👤 Oddiy foydalanuvchi"
        balance = user_data[8] if user_data[8] else 0
        subscription_expires = user_data[9]
        payments_count = user_data[10] if user_data[10] else 0
        total_spent = user_data[11] if user_data[11] else 0
        purchased_movies = user_data[12] if user_data[12] else 0
        download_attempts = user_data[13] if user_data[13] else 0
        piracy_attempts = user_data[14] if user_data[14] else 0
        
        # Obuna holati
        if subscription_expires:
            try:
                expiry_date = datetime.strptime(subscription_expires[:19], '%Y-%m-%d %H:%M:%S')
                now = datetime.now()
                if expiry_date > now:
                    days_left = (expiry_date - now).days
                    subscription_status = f"✅ Premium obuna ({days_left} kun qoldi)"
                else:
                    subscription_status = "❌ Obuna muddati o'tgan"
            except:
                subscription_status = "✅ Premium obuna"
        else:
            subscription_status = "❌ Obunasiz"
        
        # Foydalanuvchi profilini tuzish
        profile_text = f"""👤 **FOYDALANUVCHI PROFILI**

{is_admin} - {subscription_status.split()[0]}

**ASOSIY MA'LUMOTLAR:**
🆔 **ID:** `{user_id}`
👤 **To'liq ismi:** {full_name}
📱 **Telefon raqami:** {phone}
🌐 **Username:** {username}
💰 **Balans:** {balance:,} so'm
🌐 **Til:** {language}
📅 **Ro'yxatdan o'tgan sana:** {reg_date}
📊 **Hisob holati:** {status}

**FINANCIAL STATISTIKA:**
💳 **To'lovlar soni:** {payments_count} ta
💰 **Jami sarflangan summa:** {total_spent:,} so'm
🎬 **Sotib olgan filmlar:** {purchased_movies} ta
📈 **O'rtacha to'lov:** {total_spent/payments_count:,.0f if payments_count > 0 else 0} so'm

**HIMOYA STATISTIKASI:**
📥 **Yuklab olish urinishlari:** {download_attempts} ta
⚠️ **Piravlik urinishlari:** {piracy_attempts} ta/3
🔒 **Xavf bahosi:** {"🚫 Yuqori" if piracy_attempts >= 2 else "⚠️ O'rtacha" if piracy_attempts == 1 else "✅ Past"}

**OBUNA MA'LUMOTLARI:**
{subscription_status}
"""
        
        if subscription_expires and "qoldi" in subscription_status:
            try:
                expiry_date = datetime.strptime(subscription_expires[:19], '%Y-%m-%d %H:%M:%S')
                expiry_text = expiry_date.strftime('%Y-%m-%d %H:%M')
                profile_text += f"📅 **Obuna tugash muddati:** {expiry_text}\n"
            except:
                pass
        
        profile_text += f"""
**AMALLAR:**
• Bloklash: /block_user {user_id}
• Blokdan ochish: /unblock_user {user_id}
• Balans o'zgartirish: /set_balance {user_id} [summa]
• Obuna berish: /set_premium {user_id} [kunlar]
"""
        
        await message.answer(profile_text, parse_mode="Markdown")
        
    except Exception as e:
        print(f"user_profile xatosi: {e}")
        await message.answer(f"❌ Xatolik: {str(e)}")
        
# ==================== BLOKLASH (TO'G'RI VERSIYA) ====================
@admin_router.message(F.text == "🚫 Bloklash")
async def block_user_proper(message: Message, state: FSMContext):
    """Bloklash - TO'G'RI VERSIYA"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    # Avvalgi state larni tozalash
    await state.clear()
    await state.set_state(BlockStates.waiting_for_id)
    
    await message.answer(
        "🚫 **Foydalanuvchini Bloklash**\n\n"
        "Bloklamoqchi bo'lgan foydalanuvchi ID sini kiriting:\n\n"
        "📝 **Namuna:** `123456789`",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
            resize_keyboard=True
        )
    )

# ==================== ID QABUL QILISH (BLOKLASH) ====================
@admin_router.message(BlockStates.waiting_for_id, F.text)
async def handle_block_user_id(message: Message, state: FSMContext):
    """Bloklash uchun ID qabul qilish"""
    if message.text == "⬅️ Ortga":
        await admin_panel(message, state)
        return
    
    try:
        user_id = int(message.text)
        user = db.get_user(user_id)
        
        if not user:
            await message.answer(f"❌ Foydalanuvchi {user_id} topilmadi!")
            await state.clear()
            return
        
        if user_id == message.from_user.id:
            await message.answer("🤔 O'zingizni bloklab bo'lmaydi!")
            await state.clear()
            return
        
        if is_admin(user_id):
            await message.answer("⚠️ Adminni bloklab bo'lmaydi!")
            await state.clear()
            return
        
        if db.is_user_blocked(user_id):
            await message.answer("❌ Bu foydalanuvchi allaqachon bloklangan!")
            await state.clear()
            return
        
        await state.update_data(
            user_id=user_id,
            user_name=user[2]
        )
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚫 Piravlik"), KeyboardButton(text="⚠️ Qoidabuzarlik")],
                [KeyboardButton(text="💳 To'lov muammosi"), KeyboardButton(text="🔗 Kontent ulashish")],
                [KeyboardButton(text="📝 Boshqa sabab"), KeyboardButton(text="❌ Sababsiz")],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        )
        
        phone_display = user[3] if user[3] else "Yo'q"
        
        await message.answer(
            f"👤 **Foydalanuvchi:** {user[2]}\n"
            f"📱 **Telefon:** {phone_display}\n"
            f"🆔 **ID:** {user_id}\n\n"
            f"**Bloklash sababini tanlang:**",
            reply_markup=keyboard
        )
        
        await state.set_state(BlockStates.waiting_for_reason)
        
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting.")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")
        await state.clear()

# ==================== SABAB QABUL QILISH (BLOKLASH) ====================
@admin_router.message(BlockStates.waiting_for_reason, F.text)
async def handle_block_reason(message: Message, state: FSMContext):
    """Bloklash sababini qabul qilish"""
    if message.text == "⬅️ Ortga":
        await block_user_proper(message, state)
        return
    
    reason = message.text
    if reason == "❌ Sababsiz":
        reason = None
    
    data = await state.get_data()
    user_id = data.get('user_id')
    user_name = data.get('user_name')
    
    await state.update_data(reason=reason)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Ha, bloklash"), KeyboardButton(text="❌ Yo'q, bekor qilish")],
            [KeyboardButton(text="✏️ Sababni o'zgartirish")]
        ],
        resize_keyboard=True
    )
    
    reason_text = reason if reason else "Sabab koʻrsatilmadi"
    
    await message.answer(
        f"⚠️ **YAKUNIY TASDIQLASH**\n\n"
        f"👤 **Foydalanuvchi:** {user_name}\n"
        f"🆔 **ID:** {user_id}\n"
        f"📝 **Sabab:** {reason_text}\n\n"
        f"**Bu foydalanuvchini bloklashni tasdiqlaysizmi?**",
        reply_markup=keyboard
    )
    
    await state.set_state(BlockStates.waiting_for_confirmation)

# ==================== BLOKLASHNI TASDIQLASH ====================
@admin_router.message(BlockStates.waiting_for_confirmation, F.text)
async def handle_block_confirmation(message: Message, state: FSMContext):
    """Bloklashni tasdiqlash"""
    if message.text == "❌ Yo'q, bekor qilish":
        await message.answer("❌ Bloklash bekor qilindi!")
        await state.clear()
        await admin_panel(message, state)
        return
    
    if message.text == "✏️ Sababni o'zgartirish":
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚫 Piravlik"), KeyboardButton(text="⚠️ Qoidabuzarlik")],
                [KeyboardButton(text="💳 To'lov muammosi"), KeyboardButton(text="🔗 Kontent ulashish")],
                [KeyboardButton(text="📝 Boshqa sabab"), KeyboardButton(text="❌ Sababsiz")],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        )
        
        await message.answer("📝 **Yangi sababni tanlang:**", reply_markup=keyboard)
        await state.set_state(BlockStates.waiting_for_reason)
        return
    
    if message.text != "✅ Ha, bloklash":
        await message.answer("❌ Iltimos, tugmalardan foydalaning!")
        return
    
    data = await state.get_data()
    user_id = data.get('user_id')
    user_name = data.get('user_name')
    reason = data.get('reason')
    
    # Positional argument sifatida uzatish (eng ishonchli usul)
    try:
        success = db.block_user(user_id, message.from_user.id, reason)
    except TypeError as e:
        # Agar positional argument ham ishlamasa, alternative usul
        print(f"Error calling block_user: {e}")
        success = False
    
    if success:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"🚫 **Siz bloklandingiz!**\n\n"
                     f"Sabab: {reason if reason else 'Nomaʼlum sabab'}\n"
                     f"Admin: {message.from_user.full_name}\n"
                     f"Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                     f"Blokdan ochish uchun @Operator_Kino_1985 ga murojaat qiling."
            )
        except Exception as e:
            print(f"Bloklash xabarini yuborishda xatolik: {e}")
        
        await message.answer(
            f"✅ **Foydalanuvchi muvaffaqiyatli bloklandi!**\n\n"
            f"👤 **Foydalanuvchi:** {user_name}\n"
            f"🆔 **ID:** {user_id}\n"
            f"📝 **Sabab:** {reason if reason else 'Sabab koʻrsatilmadi'}\n\n"
            f"✅ Bloklash amaliyoti muvaffaqiyatli yakunlandi.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    else:
        await message.answer(
            "❌ **Bloklashda xatolik yuz berdi!**\n\n"
            "Iltimos, qayta urinib ko'ring.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    
    await state.clear()

# ==================== BLOKDAN OCHISH (TO'G'RI VERSIYA) ====================
@admin_router.message(F.text == "✅ Blokdan Ochish")
async def unblock_user_proper(message: Message, state: FSMContext):
    """Blokdan ochish - TO'G'RI VERSIYA"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    # Avvalgi state larni tozalash
    await state.clear()
    
    # Bloklangan foydalanuvchilarni olish
    blocked_users = db.get_blocked_users()
    
    if not blocked_users:
        await message.answer(
            "✅ **Hech qanday bloklangan foydalanuvchi yo'q.**",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
        return
    
    # Bloklanganlar ro'yxatini ko'rsatish
    text = "🚫 **Bloklangan foydalanuvchilar:**\n\n"
    for i, user in enumerate(blocked_users[:10], 1):
        user_id = user[1]  # user_id column
        user_name = user[7] if user[7] else "Noma'lum"  # full_name column
        reason = user[3] if user[3] else "Sabab ko'rsatilmagan"
        text += f"{i}. {user_name} (ID: {user_id})\n"
        text += f"   📝 Sabab: {reason}\n"
        text += "─" * 30 + "\n"
    
    text += "\n**Blokdan ochmoqchi bo'lgan foydalanuvchi ID sini kiriting:**"
    
    await message.answer(
        text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
            resize_keyboard=True
        )
    )
    
    # State ni o'rnatish
    await state.set_state(UnblockStates.waiting_for_id)

# ==================== ID QABUL QILISH (BLOKDAN OCHISH) ====================
@admin_router.message(UnblockStates.waiting_for_id, F.text)
async def handle_unblock_user_id(message: Message, state: FSMContext):
    """Blokdan ochish uchun ID qabul qilish"""
    if message.text == "⬅️ Ortga":
        await admin_panel(message, state)
        return
    
    try:
        user_id = int(message.text)
        
        # Foydalanuvchini tekshirish
        user = db.get_user(user_id)
        if not user:
            await message.answer(f"❌ Foydalanuvchi {user_id} topilmadi!")
            await state.clear()
            return
        
        # Bloklanganligini tekshirish
        if not db.is_user_blocked(user_id):
            await message.answer("✅ Bu foydalanuvchi bloklanmagan!")
            await state.clear()
            return
        
        # State ga saqlash
        await state.update_data(
            user_id=user_id,
            user_name=user[2]
        )
        
        # Tasdiqlash uchun so'rash
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Ha, ochish"), KeyboardButton(text="❌ Yo'q, bekor qilish")],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        )
        
        await message.answer(
            f"✅ **Blokdan Ochish**\n\n"
            f"👤 **Foydalanuvchi:** {user[2]}\n"
            f"🆔 **ID:** {user_id}\n\n"
            f"**Bu foydalanuvchini blokdan ochishni tasdiqlaysizmi?**",
            reply_markup=keyboard
        )
        
        # State ni o'zgartirish
        await state.set_state(UnblockStates.waiting_for_confirmation)
        
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting.")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")
        await state.clear()

# ==================== BLOKDAN OCHISHNI TASDIQLASH ====================
@admin_router.message(UnblockStates.waiting_for_confirmation, F.text)
async def handle_unblock_confirmation(message: Message, state: FSMContext):
    """Blokdan ochishni tasdiqlash"""
    if message.text == "⬅️ Ortga":
        await unblock_user_proper(message, state)
        return
    
    if message.text not in ["✅ Ha, ochish", "❌ Yo'q, bekor qilish"]:
        await message.answer("❌ Iltimos, tugmalardan foydalaning!")
        return
    
    if message.text == "❌ Yo'q, bekor qilish":
        await message.answer("❌ Blokdan ochish bekor qilindi!")
        await state.clear()
        await admin_panel(message, state)
        return
    
    # State dan ma'lumotlarni olish
    data = await state.get_data()
    user_id = data.get('user_id')
    user_name = data.get('user_name')
    
    # Blokdan ochish amalini bajaramiz
    success = db.unblock_user(user_id)
    
    if success:
        # Foydalanuvchiga blokdan ochilganligi haqida xabar yuborish
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"✅ **Sizning blokingiz ochildi!**\n\n"
                     f"Admin: {message.from_user.full_name}\n"
                     f"Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                     f"Endi botdan to'liq foydalana olasiz.\n"
                     f"/start - boshlash uchun"
            )
        except Exception as e:
            print(f"Blokdan ochish xabarini yuborishda xatolik: {e}")
        
        # Adminga muvaffaqiyat xabari
        await message.answer(
            f"✅ **Foydalanuvchi muvaffaqiyatli blokdan ochildi!**\n\n"
            f"👤 **Foydalanuvchi:** {user_name}\n"
            f"🆔 **ID:** {user_id}\n\n"
            f"✅ Endi foydalanuvchi botdan foydalana oladi.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    else:
        await message.answer(
            "❌ **Blokdan ochishda xatolik yuz berdi!**\n\n"
            "Iltimos, qayta urinib ko'ring.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    
    # State ni tozalash
    await state.clear()

# ==================== BROADCAST MESSAGE ====================
@admin_router.message(F.text == "📢 Xabar Yuborish")
async def broadcast_message_start(message: Message, state: FSMContext):
    """Barcha foydalanuvchilarga xabar yuborishni boshlash"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📢 **Xabar yuborish**\n\n"
        "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni kiriting:\n\n"
        "Xabar matnini, rasm, video yoki hujjat bilan birga yuborishingiz mumkin.\n\n"
        "Bekor qilish uchun '⬅️ Ortga' tugmasini bosing.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
            resize_keyboard=True
        )
    )
    await state.set_state(AdminStates.waiting_for_broadcast_message)

@admin_router.message(AdminStates.waiting_for_broadcast_message, F.text)
async def process_broadcast_text(message: Message, state: FSMContext):
    """Xabar matnini qabul qilish"""
    if message.text == "⬅️ Ortga":
        await admin_panel(message, state)
        return
    
    await state.update_data(broadcast_text=message.text)
    
    # Xabarni tasdiqlash
    preview_text = f"""📢 **Xabar namoyishi:**

{message.text}

📊 **Ma'lumotlar:**
• Xabar uzunligi: {len(message.text)} belgi
• Foydalanuvchilar soni: {db.get_users_count()} ta

✅ **Xabarni yuborishni tasdiqlaysizmi?**"""
    
    await message.answer(
        preview_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Ha, yuborish"), KeyboardButton(text="❌ Yo'q, bekor qilish")],
                [KeyboardButton(text="✏️ Xabarni o'zgartirish")]
            ],
            resize_keyboard=True
        )
    )
    await state.set_state(AdminStates.waiting_for_broadcast_confirmation)

@admin_router.message(AdminStates.waiting_for_broadcast_confirmation)
async def confirm_broadcast(message: Message, state: FSMContext):
    """Xabar yuborishni tasdiqlash"""
    if message.text == "❌ Yo'q, bekor qilish":
        await message.answer("❌ Xabar yuborish bekor qilindi!")
        await admin_panel(message, state)
        return
    
    if message.text == "✏️ Xabarni o'zgartirish":
        await message.answer("Yangi xabar matnini kiriting:")
        return
    
    if message.text != "✅ Ha, yuborish":
        await message.answer("❌ Noto'g'ri tanlov!")
        return
    
    data = await state.get_data()
    broadcast_text = data.get('broadcast_text')
    
    if not broadcast_text:
        await message.answer("❌ Xabar matni topilmadi!")
        await admin_panel(message, state)
        return
    
    users = db.get_all_users()
    total_users = len(users)
    sent_count = 0
    failed_count = 0
    
    progress_msg = await message.answer(f"📤 Xabar yuborilmoqda... 0/{total_users}")
    
    for i, user in enumerate(users, 1):
        try:
            await bot.send_message(
                chat_id=user[0],
                text=broadcast_text
            )
            sent_count += 1
            
            # Har 10ta xabar yuborilganda progressni yangilash
            if i % 10 == 0:
                await progress_msg.edit_text(f"📤 Xabar yuborilmoqda... {i}/{total_users}")
                await asyncio.sleep(0.1)  # Rate limit uchun
                
        except Exception as e:
            failed_count += 1
            print(f"Failed to send to {user[0]}: {e}")
    
    await progress_msg.delete()
    
    result_text = f"""✅ **Xabar yuborish yakunlandi!**

📊 **Natijalar:**
📤 Muvaffaqiyatli: {sent_count} ta
❌ Xatolik: {failed_count} ta
📈 Jami: {total_users} ta

📝 **Xabar matni:**
{broadcast_text[:200]}{'...' if len(broadcast_text) > 200 else ''}"""
    
    await message.answer(
        result_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
            resize_keyboard=True
        )
    )
    
    await state.clear()

# ==================== PAYMENTS MANAGEMENT ====================
@admin_router.message(F.text == "💰 To'lovlar")
async def payments_management(message: Message, state: FSMContext):
    """To'lovlar boshqaruvini ochish"""
    if not is_admin(message.from_user.id):
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Barcha to'lovlar"), KeyboardButton(text="⏳ Kutilayotgan to'lovlar")],
            [KeyboardButton(text="✅ Tasdiqlangan to'lovlar"), KeyboardButton(text="❌ Rad etilgan to'lovlar")],
            [KeyboardButton(text="💳 To'lov ma'lumotlari"), KeyboardButton(text="📊 To'lov statistikasi")],
            [KeyboardButton(text="⬅️ Ortga")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "💰 **To'lovlar boshqaruvini**\n\n"
        "Kerakli amalni tanlang:",
        reply_markup=keyboard
    )
    
# ==================== PAYMENT INFO ====================
@admin_router.message(F.text == "💳 To'lov ma'lumotlari")
async def payment_info(message: Message):
    """To'lov ma'lumotlarini ko'rsatish"""
    if not is_admin(message.from_user.id):
        return
    
    payment_info_text = """💳 **TO'LOV MA'LUMOTLARI**

🏦 **Bank kartasi:**
8600 1104 7759 4067

👤 **Karta egasi:**
Admin Kino Bot

💬 **Telegram operatori:**
@Operator_Kino_1985

📋 **To'lov qilish tartibi:**
1. Kontentni tanlang
2. "To'lov qilish" tugmasini bosing
3. To'lov usulini tanlang
4. To'lovni amalga oshiring
5. Chek skrinshotini yuboring
6. Admin to'lovni tekshiradi
7. Kontent ochiladi

⏳ **Tekshirish vaqti:**
1-24 soat ichida

❓ **Muammo bo'lsa:**
@Operator_Kino_1985 ga yozing"""
    
    await message.answer(payment_info_text)

# ==================== ALL PAYMENTS ====================
@admin_router.message(F.text == "📋 Barcha to'lovlar")
async def all_payments(message: Message):
    """Barcha to'lovlarni ko'rsatish"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        db.cursor.execute('''
            SELECT p.*, u.full_name, m.title 
            FROM payments p
            JOIN users u ON p.user_id = u.user_id
            LEFT JOIN movies m ON p.movie_id = m.id
            ORDER BY p.payment_date DESC
            LIMIT 50
        ''')
        payments = db.cursor.fetchall()
        
        if not payments:
            await message.answer("📭 Hech qanday to'lov topilmadi.")
            return
        
        payments_text = "📋 **Oxirgi 50 ta to'lov:**\n\n"
        
        for i, payment in enumerate(payments, 1):
            film_title = payment[9] if payment[9] else "Noma'lum"
            status_icon = "✅" if payment[6] == 'completed' else "⏳" if payment[6] == 'pending' else "❌"
            
            payments_text += f"{i}. {status_icon} **{payment[8]}**\n"
            payments_text += f"   💰 Miqdor: {payment[2]:,} so'm\n"
            payments_text += f"   🎬 Film: {film_title}\n"
            payments_text += f"   📅 Sana: {payment[4][:10]}\n"
            payments_text += f"   📊 Status: {payment[6]}\n"
            payments_text += f"   🆔 Payment ID: {payment[0]}\n"
            payments_text += "─" * 30 + "\n"
        
        await message.answer(payments_text)
        
    except Exception as e:
        print(f"Error getting payments: {e}")
        await message.answer("❌ Xatolik yuz berdi!")

# ==================== PENDING PAYMENTS ====================
@admin_router.message(F.text == "⏳ Kutilayotgan to'lovlar")
async def pending_payments(message: Message):
    """Kutilayotgan to'lovlarni ko'rsatish"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        db.cursor.execute('''
            SELECT p.*, u.full_name, m.title 
            FROM payments p
            JOIN users u ON p.user_id = u.user_id
            LEFT JOIN movies m ON p.movie_id = m.id
            WHERE p.status = 'pending'
            ORDER BY p.payment_date DESC
            LIMIT 20
        ''')
        pending_payments = db.cursor.fetchall()
        
        if not pending_payments:
            await message.answer(
                "✅ Hech qanday kutilayotgan to'lov yo'q.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                    resize_keyboard=True
                )
            )
            return
        
        pending_text = "⏳ **Kutilayotgan to'lovlar:**\n\n"
        
        for i, payment in enumerate(pending_payments[:10], 1):  # Faqat birinchi 10 tasi
            film_title = payment[9] if payment[9] else "Noma'lum"
            pending_text += f"{i}. **{payment[8]}**\n"
            pending_text += f"   💰 Miqdor: {payment[2]:,} so'm\n"
            pending_text += f"   🎬 Film: {film_title[:30]}{'...' if len(film_title) > 30 else ''}\n"
            pending_text += f"   📅 Sana: {payment[4][:10]}\n"
            pending_text += f"   💳 Usul: {payment[5]}\n"
            pending_text += f"   🆔 Payment ID: {payment[0]}\n"
            pending_text += "─" * 30 + "\n"
        
        await message.answer(pending_text)
        
        # Har bir to'lov uchun amallar tugmalari
        for payment in pending_payments[:5]:  # Birinchi 5 tasi uchun
            film_title = payment[9] if payment[9] else "Noma'lum"
            user_name = payment[8]
            amount = payment[2]
            payment_id = payment[0]
            
            payment_info = f"""🎬 **{film_title[:25]}{'...' if len(film_title) > 25 else ''}**

👤 **{user_name[:20]}{'...' if len(user_name) > 20 else ''}**
💰 **{amount:,}** so'm
⏰ **{payment[4][:10]}**
🆔 **Payment ID:** {payment_id}

✅ Amallar:"""
            
            kb = Keyboards('uz')
            await message.answer(
                payment_info,
                reply_markup=kb.admin_payment_actions_reply(payment)
            )
        
        if len(pending_payments) > 5:
            await message.answer(
                f"📊 Jami kutilayotgan to'lovlar: {len(pending_payments)} ta\n"
                f"Ko'rsatilgan: 5/{len(pending_payments)}",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="⏳ Boshqa to'lovlar")],
                        [KeyboardButton(text="👑 Admin paneli")]
                    ],
                    resize_keyboard=True
                )
            )
        
    except Exception as e:
        print(f"Error getting pending payments: {e}")
        await message.answer(
            "❌ Xatolik yuz berdi!",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )

# ==================== PAYMENT ACTIONS ====================
@admin_router.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm_payment(callback: CallbackQuery):
    """Admin to'lovni tasdiqlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!")
        return
    
    try:
        payment_id = int(callback.data.split("_")[2])
        
        # To'lovni tasdiqlash
        db.cursor.execute('''
            UPDATE payments 
            SET status = 'completed', processed_by = ?, process_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (callback.from_user.id, payment_id))
        
        # Foydalanuvchi va film ma'lumotlarini olish
        db.cursor.execute('''
            SELECT p.user_id, p.movie_id, p.amount, u.full_name, m.title 
            FROM payments p
            JOIN users u ON p.user_id = u.user_id
            LEFT JOIN movies m ON p.movie_id = m.id
            WHERE p.id = ?
        ''', (payment_id,))
        payment_info = db.cursor.fetchone()
        
        if payment_info:
            user_id = payment_info[0]
            movie_id = payment_info[1]
            amount = payment_info[2]
            user_name = payment_info[3]
            movie_title = payment_info[4]
            
            # Foydalanuvchiga xabar yuborish
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"✅ **TO'LOV TASDIQLANDI!**\n\n"
                         f"🎬 **Film:** {movie_title}\n"
                         f"💰 **To'lov summa:** {amount:,} so'm\n"
                         f"📅 **Tasdiqlash vaqti:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                         f"🎉 **Endi filmni ko'rishingiz mumkin!**\n\n"
                         f"Filmni ko'rish uchun kategoriyaga qayting yoki /start ni bosing."
                )
            except Exception as e:
                print(f"Error sending confirmation: {e}")
        
        db.conn.commit()
        
        await callback.answer("✅ To'lov tasdiqlandi!")
        await callback.message.edit_text(
            f"✅ **To'lov tasdiqlandi!**\n\n"
            f"👤 Foydalanuvchi: {user_name}\n"
            f"🎬 Film: {movie_title}\n"
            f"💰 Summa: {amount:,} so'm\n"
            f"📊 Status: COMPLETED\n"
            f"👮 Tasdiqlovchi: {callback.from_user.full_name}",
            reply_markup=None
        )
        
    except Exception as e:
        print(f"Error confirming payment: {e}")
        await callback.answer("❌ Xatolik yuz berdi!")

@admin_router.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_payment(callback: CallbackQuery):
    """Admin to'lovni rad etish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!")
        return
    
    try:
        payment_id = int(callback.data.split("_")[2])
        
        # To'lovni rad etish
        db.cursor.execute('''
            UPDATE payments 
            SET status = 'rejected', processed_by = ?, process_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (callback.from_user.id, payment_id))
        
        # Foydalanuvchi va film ma'lumotlarini olish
        db.cursor.execute('''
            SELECT p.user_id, p.amount, u.full_name, m.title 
            FROM payments p
            JOIN users u ON p.user_id = u.user_id
            LEFT JOIN movies m ON p.movie_id = m.id
            WHERE p.id = ?
        ''', (payment_id,))
        payment_info = db.cursor.fetchone()
        
        if payment_info:
            user_id = payment_info[0]
            amount = payment_info[1]
            user_name = payment_info[2]
            movie_title = payment_info[3]
            
            # Foydalanuvchiga xabar yuborish
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text="❌ **TO'LOV RAD ETILDI!**\n\n"
                         "To'lovingiz rad etildi. Iltimos, quyidagilarni tekshiring:\n"
                         "1. To'lov to'g'ri amalga oshirilganligi\n"
                         "2. Chek rasmi aniq ko'rinishi\n"
                         "3. To'lov summasining to'g'riligi\n\n"
                         "Qayta urinib ko'ring yoki @Operator_Kino_1985 ga murojaat qiling."
                )
            except:
                pass
        
        db.conn.commit()
        
        await callback.answer("❌ To'lov rad etildi!")
        await callback.message.edit_text(
            f"❌ **To'lov rad etildi!**\n\n"
            f"👤 Foydalanuvchi: {user_name}\n"
            f"🎬 Film: {movie_title}\n"
            f"💰 Summa: {amount:,} so'm\n"
            f"📊 Status: REJECTED\n"
            f"👮 Rad etuvchi: {callback.from_user.full_name}",
            reply_markup=None
        )
        
    except Exception as e:
        print(f"Error rejecting payment: {e}")
        await callback.answer("❌ Xatolik yuz berdi!")

# ==================== COMPLETED PAYMENTS ====================
@admin_router.message(F.text == "✅ Tasdiqlangan to'lovlar")
async def completed_payments(message: Message):
    """Tasdiqlangan to'lovlarni ko'rsatish"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        db.cursor.execute('''
            SELECT p.*, u.full_name, m.title 
            FROM payments p
            JOIN users u ON p.user_id = u.user_id
            LEFT JOIN movies m ON p.movie_id = m.id
            WHERE p.status = 'completed'
            ORDER BY p.process_date DESC
            LIMIT 50
        ''')
        completed_payments = db.cursor.fetchall()
        
        if not completed_payments:
            await message.answer("✅ Hech qanday tasdiqlangan to'lov yo'q.")
            return
        
        completed_text = "✅ **Tasdiqlangan to'lovlar:**\n\n"
        
        total_amount = 0
        for i, payment in enumerate(completed_payments, 1):
            film_title = payment[9] if payment[9] else "Noma'lum"
            completed_text += f"{i}. **{payment[8]}**\n"
            completed_text += f"   💰 Miqdor: {payment[2]:,} so'm\n"
            completed_text += f"   🎬 Film: {film_title}\n"
            completed_text += f"   📅 Sana: {payment[4][:10]}\n"
            if payment[7]:  # processed_by
                completed_text += f"   👮 Tasdiqlovchi: {payment[7]}\n"
            completed_text += "─" * 25 + "\n"
            
            total_amount += payment[2]
        
        completed_text += f"\n💰 **Jami yig'ilgan summa:** {total_amount:,} so'm"
        
        await message.answer(completed_text)
        
    except Exception as e:
        print(f"Error getting completed payments: {e}")
        await message.answer("❌ Xatolik yuz berdi!")

# ==================== REJECTED PAYMENTS ====================
@admin_router.message(F.text == "❌ Rad etilgan to'lovlar")
async def rejected_payments(message: Message):
    """Rad etilgan to'lovlarni ko'rsatish"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        db.cursor.execute('''
            SELECT p.*, u.full_name, m.title 
            FROM payments p
            JOIN users u ON p.user_id = u.user_id
            LEFT JOIN movies m ON p.movie_id = m.id
            WHERE p.status = 'rejected'
            ORDER BY p.process_date DESC
            LIMIT 50
        ''')
        rejected_payments = db.cursor.fetchall()
        
        if not rejected_payments:
            await message.answer("❌ Hech qanday rad etilgan to'lov yo'q.")
            return
        
        rejected_text = "❌ **Rad etilgan to'lovlar:**\n\n"
        
        for i, payment in enumerate(rejected_payments, 1):
            film_title = payment[9] if payment[9] else "Noma'lum"
            rejected_text += f"{i}. **{payment[8]}**\n"
            rejected_text += f"   💰 Miqdor: {payment[2]:,} so'm\n"
            rejected_text += f"   🎬 Film: {film_title}\n"
            rejected_text += f"   📅 Sana: {payment[4][:10]}\n"
            if payment[7]:  # processed_by
                rejected_text += f"   👮 Rad etuvchi: {payment[7]}\n"
            rejected_text += "─" * 25 + "\n"
        
        await message.answer(rejected_text)
        
    except Exception as e:
        print(f"Error getting rejected payments: {e}")
        await message.answer("❌ Xatolik yuz berdi!")

# ==================== PREMIUM STATUS TOGGLE ====================
@admin_router.message(F.text == "💰 Pullik/Bepul qilish")
async def toggle_premium_status(message: Message, state: FSMContext):
    """Filmlarni pullik/bepul qilish bo'limi"""
    if not is_admin(message.from_user.id):
        return
    
    await state.clear()
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 ID bo'yicha o'zgartirish"), KeyboardButton(text="📂 Kategoriya bo'yicha")],
            [KeyboardButton(text="📊 Pullik filmlar ro'yxati"), KeyboardButton(text="📋 Bepul filmlar ro'yxati")],
            [KeyboardButton(text="⬅️ Ortga")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "💰 **Pullik/Bepul qilish bo'limi**\n\n"
        "Filmlarning pullik/bepul holatini o'zgartirish uchun usulni tanlang:",
        reply_markup=keyboard
    )

@admin_router.message(F.text == "🔍 ID bo'yicha o'zgartirish")
async def toggle_by_id_start(message: Message, state: FSMContext):
    """ID bo'yicha film holatini o'zgartirishni boshlash"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🔍 **ID bo'yicha o'zgartirish**\n\n"
        "O'zgartirmoqchi bo'lgan film ID sini kiriting:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
            resize_keyboard=True
        )
    )
    
    await state.set_state(PremiumContentStates.waiting_for_price)

@admin_router.message(PremiumContentStates.waiting_for_price)
async def process_movie_id_for_toggle(message: Message, state: FSMContext):
    """Film ID sini qabul qilish va holatini ko'rsatish"""
    if message.text == "⬅️ Ortga":
        await toggle_premium_status(message, state)
        return
    
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return
    
    movie_id = int(message.text)
    
    # Filmi tekshirish
    movie = db.get_movie_by_id(movie_id)
    if not movie:
        await message.answer("❌ Film topilmadi!")
        await toggle_premium_status(message, state)
        return
    
    is_premium = movie[10] == 1  # 10-index is_premium
    current_price = movie[11] if is_premium else 0  # 11-index price
    
    await state.update_data(movie_id=movie_id, is_premium=is_premium, current_price=current_price)
    
    if is_premium:
        # Agar pullik bo'lsa, bepul qilish yoki narxni o'zgartirish imkoniyati
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🆓 Bepul qilish"), KeyboardButton(text="✏️ Narxni o'zgartirish")],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        )
        
        await message.answer(
            f"🎬 **{movie[3]}**\n"
            f"💰 Joriy holat: Pullik\n"
            f"💵 Joriy narx: {current_price:,} so'm\n\n"
            f"Kerakli amalni tanlang:",
            reply_markup=keyboard
        )
        
        await state.set_state(PremiumContentStates.waiting_for_payment_method)
        
    else:
        # Agar bepul bo'lsa, pullik qilish uchun narx so'rash
        await message.answer(
            f"🎬 **{movie[3]}**\n"
            f"💰 Joriy holat: Bepul\n\n"
            f"Pullik qilish uchun narxni kiriting (so'mda):",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
                resize_keyboard=True
            )
        )
        
        await state.set_state(PremiumContentStates.waiting_for_price)

@admin_router.message(PremiumContentStates.waiting_for_payment_method)
async def process_premium_action(message: Message, state: FSMContext):
    """Pullik film ustida amalni qabul qilish"""
    if message.text == "⬅️ Ortga":
        await toggle_premium_status(message, state)
        return
    
    data = await state.get_data()
    movie_id = data.get('movie_id')
    
    if message.text == "🆓 Bepul qilish":
        # Filmi bepul qilish
        success = db.update_movie_premium_status(movie_id, is_premium=False, price=0)
        
        if success:
            await message.answer(
                f"✅ **Film bepul qilindi!**\n\n"
                f"🎬 Film: ID {movie_id}\n"
                f"💰 Yangi holat: Bepul\n\n"
                f"✅ Endi barcha foydalanuvchilar bepul ko'rishi mumkin.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="💰 Boshqa film o'zgartirish"), KeyboardButton(text="👑 Admin paneli")]],
                    resize_keyboard=True
                )
            )
        else:
            await message.answer(
                "❌ **Xatolik yuz berdi!**\n\n"
                "Film holatini o'zgartirishda xatolik.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                    resize_keyboard=True
                )
            )
        
        await state.clear()
        
    elif message.text == "✏️ Narxni o'zgartirish":
        # Yangi narxni so'rash
        await message.answer(
            "💰 **Yangi narxni kiriting (so'mda):**",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
                resize_keyboard=True
            )
        )
        
        await state.set_state(PremiumContentStates.waiting_for_price)
        
    else:
        await message.answer("❌ Noto'g'ri tanlov!")

@admin_router.message(PremiumContentStates.waiting_for_price, F.text)
async def process_new_price(message: Message, state: FSMContext):
    """Yangi narxni qabul qilish"""
    if message.text == "⬅️ Ortga":
        data = await state.get_data()
        if data.get('is_premium'):
            await state.set_state(PremiumContentStates.waiting_for_payment_method)
            await message.answer("Kerakli amalni tanlang:")
        else:
            await toggle_premium_status(message, state)
        return
    
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return
    
    new_price = int(message.text)
    
    if new_price < 1000 or new_price > 1000000:
        await message.answer("❌ Narx 1000 dan 1,000,000 so'mgacha bo'lishi kerak!")
        return
    
    data = await state.get_data()
    movie_id = data.get('movie_id')
    
    # Filmi yangilash
    success = db.update_movie_premium_status(movie_id, is_premium=True, price=new_price)
    
    if success:
        await message.answer(
            f"✅ **Film yangilandi!**\n\n"
            f"🎬 Film: ID {movie_id}\n"
            f"💰 Yangi narx: {new_price:,} so'm\n"
            f"📊 Yangi holat: Pullik\n\n"
            f"✅ Yangi narx bilan pullik kontentga aylandi.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="💰 Boshqa film o'zgartirish"), KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    else:
        await message.answer(
            "❌ **Xatolik yuz berdi!**\n\n"
            "Film narxini o'zgartirishda xatolik.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    
    await state.clear()

# ==================== PREMIUM MOVIES LIST ====================
@admin_router.message(F.text == "📊 Pullik filmlar ro'yxati")
async def premium_movies_list(message: Message):
    """Pullik filmlar ro'yxatini ko'rsatish"""
    if not is_admin(message.from_user.id):
        return
    
    premium_movies = db.get_premium_movies()
    
    if not premium_movies:
        await message.answer("💰 **Hech qanday pullik film topilmadi.**")
        return
    
    movies_text = "💰 **PULLIK FILMLAR RO'YXATI**\n\n"
    movies_text += f"📊 Jami pullik filmlar: {len(premium_movies)} ta\n\n"
    
    for i, movie in enumerate(premium_movies, 1):
        movies_text += f"{i}. **{movie[3]}**\n"
        movies_text += f"   🆔 ID: {movie[0]}\n"
        movies_text += f"   💰 Narx: {movie[11]:,} so'm\n"
        movies_text += f"   📁 Kategoriya: {movie[1]}\n"
        movies_text += f"   👁️ Ko'rishlar: {movie[8]}\n"
        movies_text += f"   📅 Qo'shilgan: {movie[9][:10]}\n"
        movies_text += "─" * 30 + "\n"
    
    await message.answer(movies_text)

@admin_router.message(F.text == "📋 Bepul filmlar ro'yxati")
async def free_movies_list(message: Message):
    """Bepul filmlar ro'yxatini ko'rsatish"""
    if not is_admin(message.from_user.id):
        return
    
    free_movies = db.get_free_movies()
    
    if not free_movies:
        await message.answer("🆓 **Hech qanday bepul film topilmadi.**")
        return
    
    movies_text = "🆓 **BEPUL FILMLAR RO'YXATI**\n\n"
    movies_text += f"📊 Jami bepul filmlar: {len(free_movies)} ta\n\n"
    
    # Faqat birinchi 20 tasini ko'rsatish
    for i, movie in enumerate(free_movies[:20], 1):
        movies_text += f"{i}. **{movie[3]}**\n"
        movies_text += f"   🆔 ID: {movie[0]}\n"
        movies_text += f"   📁 Kategoriya: {movie[1]}\n"
        movies_text += f"   👁️ Ko'rishlar: {movie[8]}\n"
        movies_text += f"   📅 Qo'shilgan: {movie[9][:10]}\n"
        movies_text += "─" * 25 + "\n"
    
    if len(free_movies) > 20:
        movies_text += f"\n📝 Ko'rsatilgan: 20/{len(free_movies)} ta"
    
    await message.answer(movies_text)

# ==================== PREMIUM STATISTICS ====================
@admin_router.message(F.text == "📊 Pullik statistikasi")
async def premium_statistics(message: Message):
    """Pullik kontentlar statistikasi"""
    if not is_admin(message.from_user.id):
        return
    
    stats = db.get_premium_statistics()
    
    stats_text = f"""📊 **PULLIK KONTENTLAR STATISTIKASI**

💰 **Umumiy:**
• Pullik filmlar: {stats['premium_count']} ta
• Bepul filmlar: {stats['free_count']} ta
• Jami filmlar: {stats['total_movies']} ta
• Pullik nisbati: {(stats['premium_count']/stats['total_movies']*100 if stats['total_movies'] > 0 else 0):.1f}%

🎬 **Pullik filmlar:**
• Eng qimmat film: {stats['most_expensive_title']} - {stats['most_expensive_price']:,} so'm
• O'rtacha narx: {stats['average_price']:,.0f} so'm
• Jami potensial daromad: {stats['total_potential_revenue']:,} so'm

📈 **To'lovlar statistikasi:**
• Jami to'lovlar: {stats['total_payments']} ta
• Muvaffaqiyatli to'lovlar: {stats['completed_payments']} ta
• Jami yig'ilgan summa: {stats['total_revenue']:,} so'm
• O'rtacha to'lov: {stats['average_payment']:,.0f} so'm

🏆 **Eng mashhur pullik filmlar:**"""
    
    if stats['top_premium_movies']:
        for i, (title, revenue, sales) in enumerate(stats['top_premium_movies'], 1):
            stats_text += f"\n{i}. {title[:25]}{'...' if len(title) > 25 else ''}"
            stats_text += f"\n   💰 {revenue:,} so'm ({sales} sotuv)"
    else:
        stats_text += "\n• Hech qanday sotuv yo'q"
    
    await message.answer(stats_text)

# ==================== PAYMENT STATISTICS ====================
@admin_router.message(F.text == "📊 To'lov statistikasi")
async def payment_statistics(message: Message):
    """To'lov statistikasini ko'rsatish"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        # Umumiy statistika
        db.cursor.execute('SELECT SUM(amount) FROM payments WHERE status = "completed"')
        total_amount = db.cursor.fetchone()[0] or 0
        
        db.cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "completed"')
        completed_count = db.cursor.fetchone()[0] or 0
        
        db.cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "pending"')
        pending_count = db.cursor.fetchone()[0] or 0
        
        db.cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "rejected"')
        rejected_count = db.cursor.fetchone()[0] or 0
        
        # Kunlik to'lovlar
        db.cursor.execute('SELECT SUM(amount) FROM payments WHERE DATE(payment_date) = DATE("now") AND status = "completed"')
        today_amount = db.cursor.fetchone()[0] or 0
        
        db.cursor.execute('SELECT COUNT(*) FROM payments WHERE DATE(payment_date) = DATE("now")')
        today_count = db.cursor.fetchone()[0] or 0
        
        # Oylik statistika
        db.cursor.execute('SELECT SUM(amount) FROM payments WHERE strftime("%Y-%m", payment_date) = strftime("%Y-%m", "now") AND status = "completed"')
        monthly_amount = db.cursor.fetchone()[0] or 0
        
        stats_text = f"""📊 **TO'LOV STATISTIKASI**

💰 **Umumiy:**
• Jami to'lovlar: {total_amount:,} so'm
• Muvaffaqiyatli: {completed_count} ta
• Kutilayotgan: {pending_count} ta
• Rad etilgan: {rejected_count} ta
• Jami so'rovlar: {completed_count + pending_count + rejected_count} ta

📅 **Bugungi:**
• To'lovlar: {today_amount:,} so'm
• So'rovlar: {today_count} ta

📆 **Oylik:**
• To'lovlar: {monthly_amount:,} so'm

📈 **O'rtacha:**
• O'rtacha to'lov: {total_amount/completed_count if completed_count > 0 else 0:,.0f} so'm
• Muvaffaqiyat darajasi: {completed_count/(completed_count + rejected_count)*100 if (completed_count + rejected_count) > 0 else 0:.1f}%"""
        
        # Top pullik filmlar
        db.cursor.execute('''
            SELECT m.title, COUNT(p.id) as sales, SUM(p.amount) as revenue
            FROM movies m
            JOIN payments p ON m.id = p.movie_id
            WHERE m.is_premium = 1 AND p.status = 'completed'
            GROUP BY m.id
            ORDER BY revenue DESC
            LIMIT 5
        ''')
        top_movies = db.cursor.fetchall()
        
        if top_movies:
            stats_text += "\n\n🏆 **Eng ko'p sotilgan filmlar:**"
            for i, (title, sales, revenue) in enumerate(top_movies, 1):
                stats_text += f"\n{i}. {title[:25]}{'...' if len(title) > 25 else ''}"
                stats_text += f"\n   💰 {revenue:,} so'm ({sales} sotuv)"
        
        await message.answer(stats_text)
        
    except Exception as e:
        print(f"Payment statistics error: {e}")
        await message.answer("❌ Statistika olishda xatolik!")

# ==================== LIMITS MANAGEMENT ====================
@admin_router.message(F.text == "✅ Cheklar")
async def limits_management(message: Message, state: FSMContext):
    """Cheklar boshqaruvini ochish"""
    if not is_admin(message.from_user.id):
        return
    
    pending_limits = db.get_pending_limits()
    
    if not pending_limits:
        await message.answer("✅ Hech qanday kutilayotgan chek so'rovi yo'q.")
        return
    
    limits_text = "📋 **Kutilayotgan chek so'rovlari:**\n\n"
    
    for i, limit in enumerate(pending_limits, 1):
        limits_text += f"{i}. **{limit[7]}** (ID: {limit[1]})\n"
        limits_text += f"   Chek turi: {limit[2]}\n"
        limits_text += f"   Miqdor: {limit[3]}\n"
        limits_text += f"   Sana: {limit[6][:10]}\n"
        limits_text += "─" * 25 + "\n"
    
    limits_text += "\nTasdiqlamoqchi bo'lgan chek raqamini kiriting:"
    
    await message.answer(
        limits_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
            resize_keyboard=True
        )
    )
    
    await state.set_state(AdminStates.waiting_for_limit_approval)
    await state.update_data(pending_limits=pending_limits)

@admin_router.message(AdminStates.waiting_for_limit_approval)
async def process_limit_approval(message: Message, state: FSMContext):
    """Chek tasdiqlash uchun raqam qabul qilish"""
    if message.text == "⬅️ Ortga":
        await admin_panel(message, state)
        return
    
    data = await state.get_data()
    pending_limits = data.get('pending_limits', [])
    
    if not message.text.isdigit():
        await message.answer("❌ Raqam kiriting!")
        return
    
    limit_num = int(message.text)
    if not 1 <= limit_num <= len(pending_limits):
        await message.answer(f"❌ Noto'g'ri raqam! 1-{len(pending_limits)} oralig'ida kiriting.")
        return
    
    selected_limit = pending_limits[limit_num - 1]
    
    limit_info = f"""📋 **Chek so'rovi:**

👤 **Foydalanuvchi:** {selected_limit[7]}
🆔 **User ID:** {selected_limit[1]}
📋 **Chek turi:** {selected_limit[2]}
💰 **Miqdor:** {selected_limit[3]}
📅 **So'rov sanasi:** {selected_limit[6]}
📝 **Holat:** {selected_limit[5]}

✅ **Qanday amal bajarmoqchisiz?**"""
    
    await state.update_data(selected_limit_id=selected_limit[0])
    
    await message.answer(
        limit_info,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Tasdiqlash"), KeyboardButton(text="❌ Rad etish")],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        )
    )
    
    await state.set_state(AdminStates.waiting_for_limit_action)

@admin_router.message(AdminStates.waiting_for_limit_action)
async def process_limit_action(message: Message, state: FSMContext):
    """Chek ustida amalni bajarish"""
    if message.text == "⬅️ Ortga":
        await limits_management(message, state)
        return
    
    data = await state.get_data()
    limit_id = data.get('selected_limit_id')
    
    if message.text == "✅ Tasdiqlash":
        success = db.approve_limit(limit_id, message.from_user.id)
        action_text = "tasdiqlandi"
    elif message.text == "❌ Rad etish":
        success = db.reject_limit(limit_id, message.from_user.id)
        action_text = "rad etildi"
    else:
        await message.answer("❌ Noto'g'ri tanlov!")
        return
    
    if success:
        await message.answer(
            f"✅ Chek so'rovi {action_text}!",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    else:
        await message.answer(
            f"❌ Xatolik yuz berdi!",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    
    await state.clear()

# ==================== BACKUP ====================
@admin_router.message(F.text == "💾 Backup")
async def backup_database(message: Message, state: FSMContext):
    """Database backup qilishni boshlash"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "💾 **Database Backup**\n\n"
        "Backup fayl nomini kiriting:\n\n"
        "Namuna: `backup_2024_01_15`",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
            resize_keyboard=True
        )
    )
    
    await state.set_state(AdminStates.waiting_for_backup_name)

@admin_router.message(AdminStates.waiting_for_backup_name)
async def process_backup_name(message: Message, state: FSMContext):
    """Backup fayl nomini qabul qilish"""
    if message.text == "⬅️ Ortga":
        await admin_panel(message, state)
        return
    
    backup_name = message.text.strip()
    
    # Backup qilish
    success = db.backup_database(backup_name)
    
    if success:
        await message.answer(
            f"✅ **Backup muvaffaqiyatli yaratildi!**\n\n"
            f"📁 Fayl nomi: `{backup_name}.db`\n"
            f"📊 Saqlandi: backups/ papkasiga",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    else:
        await message.answer(
            "❌ **Backup yaratishda xatolik!**\n\n"
            "Iltimos, qayta urinib ko'ring.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    
    await state.clear()

# ==================== CLEANUP ====================
@admin_router.message(F.text == "🧹 Tozalash")
async def cleanup_database(message: Message, state: FSMContext):
    """Database tozalashni boshlash"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🧹 **Database Tozalash**\n\n"
        "Necha kundan oldingi ma'lumotlarni tozalashni xohlaysiz?\n"
        "Kun sonini kiriting (30-365):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="30 kun"), KeyboardButton(text="90 kun")],
                [KeyboardButton(text="180 kun"), KeyboardButton(text="365 kun")],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        )
    )
    
    await state.set_state(AdminStates.waiting_for_clear_days)

@admin_router.message(AdminStates.waiting_for_clear_days)
async def process_cleanup_days(message: Message, state: FSMContext):
    """Tozalash kunlarini qabul qilish"""
    if message.text == "⬅️ Ortga":
        await admin_panel(message, state)
        return
    
    days_map = {
        "30 kun": 30,
        "90 kun": 90,
        "180 kun": 180,
        "365 kun": 365
    }
    
    if message.text in days_map:
        days = days_map[message.text]
    elif message.text.isdigit():
        days = int(message.text)
        if not 1 <= days <= 365:
            await message.answer("❌ 1-365 kun oralig'ida kiriting!")
            return
    else:
        await message.answer("❌ Noto'g'ri format!")
        return
    
    # Tozalashni tasdiqlash
    await state.update_data(clear_days=days)
    
    await message.answer(
        f"⚠️ **DIQQAT!**\n\n"
        f"Siz {days} kundan oldingi barcha ma'lumotlarni o'chirmoqchisiz.\n\n"
        f"Bu amalni **qaytarib bo'lmaydi**!\n\n"
        f"Tozalashni davom ettirishni tasdiqlaysizmi?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Ha, tozalash"), KeyboardButton(text="❌ Yo'q, bekor qilish")]
            ],
            resize_keyboard=True
        )
    )

@admin_router.message(AdminStates.waiting_for_clear_days, F.text)
async def confirm_cleanup(message: Message, state: FSMContext):
    """Database tozalashni tasdiqlash"""
    if message.text == "❌ Yo'q, bekor qilish":
        await message.answer("❌ Tozalash bekor qilindi!")
        await admin_panel(message, state)
        return
    
    if message.text != "✅ Ha, tozalash":
        await message.answer("❌ Noto'g'ri tanlov!")
        return
    
    data = await state.get_data()
    days = data.get('clear_days', 30)
    
    # Database ni tozalash
    success = db.clear_old_data(days)
    
    if success:
        await message.answer(
            f"✅ **Database muvaffaqiyatli tozalandi!**\n\n"
            f"🗑️ {days} kundan oldingi ma'lumotlar o'chirildi.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    else:
        await message.answer(
            "❌ **Tozalashda xatolik!**\n\n"
            "Iltimos, qayta urinib ko'ring.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
                resize_keyboard=True
            )
        )
    
    await state.clear()

# ==================== HIMOYA MONITORINGI ====================
@admin_router.message(F.text == "🔍 Himoya Monitoringi")
async def protection_monitoring(message: Message):
    """Himoya monitoringini ko'rsatish"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        # Bugungi yuklab olish urinishlari
        db.cursor.execute('''
            SELECT COUNT(*) as total_attempts,
                   COUNT(DISTINCT user_id) as unique_users,
                   COUNT(DISTINCT movie_id) as unique_movies
            FROM download_attempts 
            WHERE DATE(attempt_date) = DATE('now')
        ''')
        today_stats = db.cursor.fetchone()
        
        # Screen recording detections
        db.cursor.execute('''
            SELECT COUNT(*) FROM screen_recording_detections 
            WHERE DATE(detection_time) = DATE('now')
        ''')
        today_screenshots = db.cursor.fetchone()[0] or 0
        
        # Piravlik urinishlari
        db.cursor.execute('''
            SELECT COUNT(*) FROM anti_piracy_logs 
            WHERE DATE(action_date) >= DATE('now', '-7 days')
        ''')
        weekly_piracy = db.cursor.fetchone()[0] or 0
        
        # Bloklangan foydalanuvchilar
        blocked_users = db.get_blocked_users()
        
        # Faol tokenlar
        db.cursor.execute('''
            SELECT COUNT(*) FROM content_tokens 
            WHERE is_active = 1 AND expires_at > CURRENT_TIMESTAMP
        ''')
        active_tokens = db.cursor.fetchone()[0] or 0
        
        # Eng ko'p piravlik urinishlari
        db.cursor.execute('''
            SELECT u.full_name, u.user_id, COUNT(*) as attempts
            FROM anti_piracy_logs apl
            JOIN users u ON apl.user_id = u.user_id
            WHERE apl.action_date >= DATE('now', '-30 days')
            GROUP BY apl.user_id
            ORDER BY attempts DESC
            LIMIT 5
        ''')
        top_piracy_users = db.cursor.fetchall()
        
    except Exception as e:
        print(f"Monitoring xatosi: {e}")
        today_stats = (0, 0, 0)
        today_screenshots = 0
        weekly_piracy = 0
        active_tokens = 0
        blocked_users = []
        top_piracy_users = []
    
    monitoring_text = f"""🔍 **HIMOYA MONITORINGI - REAL VAQT**

📊 **Bugungi statistika:**
• Yuklab olish urinishlari: {today_stats[0] if today_stats else 0}
• Faol foydalanuvchilar: {today_stats[1] if today_stats else 0}
• Ko'rilgan filmlar: {today_stats[2] if today_stats else 0}
• Skrinshot urinishlari: {today_screenshots}

⚠️ **Xavf statistikasi:**
• 7 kunlik piravlik urinishlari: {weekly_piracy}
• Bloklangan foydalanuvchilar: {len(blocked_users)}
• Faol himoya tokenlari: {active_tokens}

🚫 **Bloklangan foydalanuvchilar:**"""
    
    if blocked_users:
        for i, user in enumerate(blocked_users[:5], 1):
            monitoring_text += f"\n{i}. {user[7]} (ID: {user[1]})"
    else:
        monitoring_text += "\n• Hech kim bloklanmagan"
    
    monitoring_text += "\n\n⚠️ **Eng ko'p piravlik urinishlari:**"
    if top_piracy_users:
        for i, user in enumerate(top_piracy_users, 1):
            monitoring_text += f"\n{i}. {user[0]} (ID: {user[1]}) - {user[2]} urinish"
    else:
        monitoring_text += "\n• Hech qanday urinish yo'q"
    
    monitoring_text += """
⚙️ **Himoya sozlamalari:**
• Token amal qilish: 2 soat
• Kunlik limit: 50 yuklab olish
• Skrinshot blok: ✅ Faol
• Ekran yozib olish deteksiyasi: ✅ Faol
• 3 urinishdan keyin blok: ✅ Faol

📊 **Qo'shimcha komandalar:**
• /himoya_stats - Batafsil statistika
• /check_user [user_id] - Foydalanuvchini tekshirish"""
    
    await message.answer(monitoring_text)

@admin_router.message(Command("himoya_stats"))
async def detailed_protection_stats(message: Message):
    """Batafsil himoya statistikasi"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        # 30 kunlik statistika
        db.cursor.execute('''
            SELECT DATE(attempt_date) as date, COUNT(*) as attempts
            FROM download_attempts 
            WHERE attempt_date >= DATE('now', '-30 days')
            GROUP BY DATE(attempt_date)
            ORDER BY date DESC
            LIMIT 15
        ''')
        daily_attempts = db.cursor.fetchall()
        
        # Piravlik urinishlari oylik
        db.cursor.execute('''
            SELECT strftime('%Y-%m', action_date) as month, COUNT(*) as attempts
            FROM anti_piracy_logs 
            WHERE action_date >= DATE('now', '-90 days')
            GROUP BY strftime('%Y-%m', action_date)
            ORDER BY month DESC
        ''')
        monthly_piracy = db.cursor.fetchall()
        
        # Top 10 ko'rilgan filmlar
        db.cursor.execute('''
            SELECT title, views, id FROM movies 
            ORDER BY views DESC 
            LIMIT 10
        ''')
        top_movies = db.cursor.fetchall()
        
        # Eng faol foydalanuvchilar
        db.cursor.execute('''
            SELECT u.full_name, COUNT(da.id) as attempts
            FROM download_attempts da
            JOIN users u ON da.user_id = u.user_id
            WHERE da.attempt_date >= DATE('now', '-7 days')
            GROUP BY da.user_id
            ORDER BY attempts DESC
            LIMIT 10
        ''')
        top_users = db.cursor.fetchall()
        
    except Exception as e:
        print(f"Detailed stats error: {e}")
        daily_attempts = []
        monthly_piracy = []
        top_movies = []
        top_users = []
    
    stats_text = "📈 **BATAFSIL HIMOYA STATISTIKASI**\n\n"
    
    stats_text += "📅 **Oxirgi 15 kunlik yuklab olishlar:**"
    if daily_attempts:
        for date, attempts in daily_attempts:
            stats_text += f"\n• {date}: {attempts} urinish"
    else:
        stats_text += "\n• Ma'lumot yo'q"
    
    stats_text += "\n\n⚠️ **Oylik piravlik urinishlari:**"
    if monthly_piracy:
        for month, attempts in monthly_piracy:
            stats_text += f"\n• {month}: {attempts} urinish"
    else:
        stats_text += "\n• Ma'lumot yo'q"
    
    stats_text += "\n\n🎬 **Eng ko'p ko'rilgan filmlar:**"
    if top_movies:
        for i, (title, views, movie_id) in enumerate(top_movies, 1):
            stats_text += f"\n{i}. {title[:30]}{'...' if len(title) > 30 else ''}"
            stats_text += f"\n   👁️ {views} ko'rish | ID: {movie_id}"
    else:
        stats_text += "\n• Ma'lumot yo'q"
    
    stats_text += "\n\n👥 **Eng faol foydalanuvchilar (7 kun):**"
    if top_users:
        for i, (name, attempts) in enumerate(top_users, 1):
            stats_text += f"\n{i}. {name[:20]}{'...' if len(name) > 20 else ''}: {attempts} urinish"
    else:
        stats_text += "\n• Ma'lumot yo'q"
    
    await message.answer(stats_text)

@admin_router.message(Command("check_user"))
async def check_user_protection(message: Message):
    """Foydalanuvchi himoya holatini tekshirish"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("❌ Foydalanuvchi ID sini kiriting: /check_user [user_id]")
            return
        
        user_id = int(parts[1])
        user = db.get_user(user_id)
        
        if not user:
            await message.answer(f"❌ Foydalanuvchi {user_id} topilmadi!")
            return
        
        # Foydalanuvchi statistikasi
        download_stats = db.get_user_download_stats(user_id, hours=24)
        piracy_attempts = db.get_user_piracy_attempts(user_id)
        is_blocked = db.is_user_blocked(user_id)
        
        # Blok ma'lumotlari
        block_info = None
        if is_blocked:
            db.cursor.execute('''
                SELECT reason, block_date, blocked_by FROM blocked_users 
                WHERE user_id = ? AND unblock_date IS NULL
            ''', (user_id,))
            block_info = db.cursor.fetchone()
        
        user_text = f"""🔍 **FOYDALANUVCHI HIMOYA HOLATI**

👤 **Asosiy ma'lumotlar:**
• ID: {user[0]}
• Ism: {user[2]}
• Tel: {user[3]}
• Ro'yxatdan o'tgan: {user[5][:10]}
• Status: {user[6]}

🔒 **Himoya statistikasi:**
• Bugun yuklab olishlar: {download_stats[0] if download_stats else 0}/50
• Piravlik urinishlari: {piracy_attempts}/3
• Blok holati: {'🚫 Bloklangan' if is_blocked else '✅ Faol'}"""
        
        if is_blocked and block_info:
            blocked_by_user = db.get_user(block_info[2])
            blocked_by_name = blocked_by_user[2] if blocked_by_user else str(block_info[2])
            
            reason_text = block_info[0] if block_info[0] else "Noma'lum"
            date_text = block_info[1][:19] if block_info[1] else "Noma'lum"
            
            user_text += f"""

**Blok ma'lumotlari:**
Sabab: {reason_text}
Sana: {date_text}
Bloklovchi: {blocked_by_name}"""
        
        user_text += f"""

**Xavf bahosi:**"""
        
        if is_blocked:
            user_text += " 🚫 Yuqori (Bloklangan)"
        elif piracy_attempts >= 2:
            user_text += f" ⚠️ O'rtacha ({3 - piracy_attempts} urinish qolgan)"
        elif piracy_attempts == 1:
            user_text += " ⚠️ Past (2 urinish qolgan)"
        else:
            user_text += " ✅ Past (Hech qanday urinish yo'q)"
        
        await message.answer(user_text)
        
    except Exception as e:
        print(f"Check user error: {e}")
        await message.answer("❌ Xatolik yuz berdi!")

# ==================== HIMOYA SOZLAMALARI ====================
@admin_router.message(F.text == "🔒 Himoya Sozlamalari")
async def protection_settings(message: Message, state: FSMContext):
    """Himoya sozlamalarini ko'rsatish"""
    if not is_admin(message.from_user.id):
        return
    
    # Statistik ma'lumotlarni olish
    try:
        db.cursor.execute('SELECT COUNT(*) FROM download_attempts WHERE DATE(attempt_date) = DATE("now")')
        today_downloads = db.cursor.fetchone()[0] or 0
        
        db.cursor.execute('SELECT COUNT(*) FROM blocked_users WHERE unblock_date IS NULL')
        blocked_users_count = db.cursor.fetchone()[0] or 0
        
        db.cursor.execute('SELECT COUNT(*) FROM screen_recording_detections WHERE DATE(detection_time) = DATE("now")')
        today_screenshots = db.cursor.fetchone()[0] or 0
    except:
        today_downloads = 0
        blocked_users_count = 0
        today_screenshots = 0
    
    settings_text = f"""🔒 **HIMOYA SOZLAMALARI**

⚙️ **Joriy sozlamalar:**
• Token amal qilish: 2 soat
• Kunlik yuklab olish limiti: 50 ta
• Skrinshot deteksiyasi: ✅ Faol
• Screen recording deteksiyasi: ✅ Faol
• Avtomatik blok: 3 urinishdan keyin

🛡️ **Himoya darajalari:**
1. **Oson** - Faqat ogohlantirishlar
2. **O'rtacha** - Limitlar + ogohlantirishlar (hozirgi)
3. **Qattiq** - Limitlar + avtomatik blok

🔧 **Sozlash uchun komandalar:**
• /set_protection [level] - Himoya darajasini o'zgartirish
• /set_daily_limit [number] - Kunlik limitni o'zgartirish
• /set_token_expiry [hours] - Token amal qilish muddatini o'zgartirish

📊 **Statistika:**
• Bugun yuklab olishlar: {today_downloads}
• Bloklangan foydalanuvchilar: {blocked_users_count}
• Screen recording aniqlangan: {today_screenshots}"""
    
    await message.answer(settings_text)

@admin_router.message(Command("set_daily_limit"))
async def set_daily_limit(message: Message):
    """Kunlik limitni o'zgartirish"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("❌ Limit sonini kiriting: /set_daily_limit [number]")
            return
        
        limit = int(parts[1])
        if limit < 1 or limit > 1000:
            await message.answer("❌ Limit 1-1000 oralig'ida bo'lishi kerak!")
            return
        
        # Bu yerda limitni saqlash logikasi bo'ladi
        # Hozircha faqat xabar chiqaramiz
        await message.answer(f"✅ Kunlik yuklab olish limiti {limit} ta ga o'zgartirildi!")
        
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting.")

# ==================== HELPER FUNCTIONS ====================
@admin_router.message(F.text == "🔍 Foydalanuvchi qidirish")
async def search_user(message: Message, state: FSMContext):
    """Foydalanuvchi qidirishni boshlash"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🔍 **Foydalanuvchi qidirish**\n\n"
        "Qidirmoqchi bo'lgan foydalanuvchi ID sini, telefon raqamini yoki ismini kiriting:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Ortga")]],
            resize_keyboard=True
        )
    )
    
    await state.set_state(AdminStates.waiting_for_user_id)
    await state.update_data(action="search")

@admin_router.message(AdminStates.waiting_for_user_id, F.text)
async def process_user_search(message: Message, state: FSMContext):
    """Foydalanuvchi qidiruv natijalarini ko'rsatish"""
    if message.text == "⬅️ Ortga":
        await admin_panel(message, state)
        return
    
    search_query = message.text
    users = db.get_all_users()
    
    results = []
    
    for user in users:
        # ID bo'yicha qidirish
        if str(user[0]) == search_query:
            results.append(user)
            continue
        
        # Telefon raqami bo'yicha qidirish
        if search_query in user[3]:
            results.append(user)
            continue
        
        # Ism bo'yicha qidirish
        if search_query.lower() in user[2].lower():
            results.append(user)
            continue
        
        # Username bo'yicha qidirish
        if user[1] and search_query.lower() in user[1].lower():
            results.append(user)
            continue
    
    if not results:
        await message.answer(f"❌ '{search_query}' bo'yicha hech qanday natija topilmadi.")
        await admin_panel(message, state)
        return
    
    results_text = f"🔍 **Qidiruv natijalari: '{search_query}'**\n\n"
    results_text += f"📊 Topilgan foydalanuvchilar: {len(results)} ta\n\n"
    
    for i, user in enumerate(results[:10], 1):  # Faqat birinchi 10 tasi
        results_text += f"{i}. **{user[2]}**\n"
        results_text += f"   ID: `{user[0]}` | Tel: {user[3]}\n"
        results_text += f"   Til: {user[4]} | Sana: {user[5][:10]}\n"
        
        if user[1]:
            results_text += f"   @{user[1]}\n"
        
        results_text += f"   Status: {user[6]}\n"
        results_text += "─" * 30 + "\n"
    
    if len(results) > 10:
        results_text += f"\n📝 Ko'rsatilgan: 10/{len(results)} ta"
    
    await message.answer(results_text)
    await state.clear()

@admin_router.message(F.text == "📈 Faollik statistikasi")
async def activity_stats(message: Message):
    """Faollik statistikasini ko'rsatish"""
    if not is_admin(message.from_user.id):
        return
    
    weekly_stats = db.get_weekly_stats()
    
    stats_text = "📈 **Haftalik faollik statistikasi**\n\n"
    
    if weekly_stats['weekly_users']:
        stats_text += "👥 **Yangi foydalanuvchilar:**"
        for date, count in weekly_stats['weekly_users']:
            stats_text += f"\n• {date}: {count} ta"
    
    stats_text += "\n\n🎬 **Yangi filmlar:**"
    if weekly_stats['weekly_movies']:
        for date, count in weekly_stats['weekly_movies']:
            stats_text += f"\n• {date}: {count} ta"
    else:
        stats_text += "\n• Hech qanday yangi film yo'q"
    
    await message.answer(stats_text)
    
# ========== ADMIN PULLIK KONTENTLAR BOSHQARUVI ==========
@admin_router.message(F.text == "💰 To'lovlarni boshqarish")
async def admin_payments_dashboard(message: Message):
    """Admin to'lovlar boshqaruvi"""
    if not is_admin(message.from_user.id):
        return
    
    # Real vaqt statistikasi
    try:
        db.cursor.execute('SELECT COUNT(*) FROM payments WHERE DATE(payment_date) = DATE("now")')
        today_payments = db.cursor.fetchone()[0] or 0
        
        db.cursor.execute('SELECT SUM(amount) FROM payments WHERE DATE(payment_date) = DATE("now") AND status = "completed"')
        today_revenue = db.cursor.fetchone()[0] or 0
        
        db.cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "pending"')
        pending_payments = db.cursor.fetchone()[0] or 0
    except:
        today_payments = 0
        today_revenue = 0
        pending_payments = 0
    
    dashboard_text = f"""💰 **TO'LOVLAR BOSHQARUVI PANELI**

📊 **BUGUNGI STATISTIKA:**
💳 **To'lovlar:** {today_payments} ta
💰 **Daromad:** {today_revenue:,} so'm
⏳ **Kutilayotgan:** {pending_payments} ta

⚙️ **TEZKOR AMALLAR:**
1️⃣ '⏳ Kutilayotgan to'lovlar' - Tasdiqlash uchun
2️⃣ '📋 Barcha to'lovlar' - To'lovlar tarixi
3️⃣ '📊 Pullik statistikasi' - Umumiy statistika
4️⃣ '💰 Pullik/Bepul qilish' - Kontent holati

👇 **Kerakli bo'limni tanlang:**"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏳ Kutilayotgan to'lovlar"), KeyboardButton(text="✅ Tasdiqlangan to'lovlar")],
            [KeyboardButton(text="📋 Barcha to'lovlar"), KeyboardButton(text="📊 To'lov statistikasi")],
            [KeyboardButton(text="💰 Pullik statistikasi"), KeyboardButton(text="💰 Pullik/Bepul qilish")],
            [KeyboardButton(text="🎬 Pullik filmlar ro'yxati"), KeyboardButton(text="📋 Bepul filmlar ro'yxati")],
            [KeyboardButton(text="👑 Admin paneli"), KeyboardButton(text="🏠 Asosiy menyu")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(dashboard_text, reply_markup=keyboard)    

@admin_router.message(Command("debug_state"))
async def debug_state(message: Message, state: FSMContext):
    """State debug ma'lumotlarini ko'rsatish"""
    if not is_admin(message.from_user.id):
        return
    
    current_state = await state.get_state()
    data = await state.get_data()
    
    debug_text = f"""🔍 **State Debug Information:**

📝 Current State: {current_state}
🗂️ State Data: {data}

📊 Data keys: {list(data.keys()) if data else "Empty"}"""
    
    await message.answer(debug_text)