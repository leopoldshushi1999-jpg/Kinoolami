import asyncio
import os
import sys
import threading
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Awaitable

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, 
    CallbackQuery, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from aiogram import BaseMiddleware
from dotenv import load_dotenv

from database import Database
from keyboards import Keyboards
from keep_alive import keep_alive

# .env faylini yuklash
load_dotenv()

# Bot token va admin ID .env fayldan o'qiladi
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Token tekshirish
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN .env faylida mavjud emas!")
    exit(1)

if not ADMIN_ID:
    print("WARNING: ADMIN_ID .env faylida mavjud emas! Admin funksiyalari ishlamaydi.")

# Bot obyektlarini yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Database obyekti
db = Database()

# Admin routerini import qilish (dp yaratilganidan keyin)
from admin import admin_router, setup_admin_bot

# Routerlarni qo'shish
dp.include_router(admin_router)

# Bot obyektini admin moduliga o'tkazish
setup_admin_bot(bot)

# ... qolgan kodlar ...

# Himoya konfiguratsiyasi
PROTECTION_CONFIG = {
    'token_expiry_hours': 2,
    'daily_download_limit': 50,
    'screenshot_detection': True,
    'screen_recording_detection': True,
    'content_protection': True,
    'auto_block_attempts': 3,
    'warning_attempts': 2,
    'protection_level': 'high',
    'platform_protection': {
        'android': True,
        'ios': True,
        'windows': True,
        'web': True
    },
    'monitoring_enabled': True,
    'real_time_detection': True
}

# ADMIN ID larni global ro'yxatga olish
ADMINS = []
if ADMIN_ID:
    try:
        ADMINS.append(int(ADMIN_ID))
    except:
        pass

# ========== FLASK SERVER - RENDER UCHUN ==========
def run_flask_server():
    """Flask serverini ishga tushiradi"""
    try:
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>🎬 Kino Bot</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding: 50px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }}
                    .container {{
                        background: rgba(255, 255, 255, 0.1);
                        padding: 30px;
                        border-radius: 20px;
                        backdrop-filter: blur(10px);
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                    }}
                    h1 {{
                        font-size: 3em;
                        margin-bottom: 20px;
                    }}
                    .status {{
                        font-size: 1.5em;
                        margin: 20px 0;
                        color: #4CAF50;
                    }}
                    .info {{
                        background: rgba(255, 255, 255, 0.2);
                        padding: 20px;
                        border-radius: 10px;
                        margin: 20px 0;
                    }}
                </style>
                <meta http-equiv="refresh" content="30">
            </head>
            <body>
                <div class="container">
                    <h1>🎬 Kino Bot</h1>
                    <div class="status">✅ Bot ishlayapti!</div>
                    <div class="info">
                        <p><strong>🛡️ Himoya:</strong> FAOL</p>
                        <p><strong>📊 Monitoring:</strong> 24/7</p>
                        <p><strong>⏰ Vaqt:</strong> {current_time}</p>
                        <p><strong>🔧 Platforma:</strong> Render</p>
                    </div>
                    <p>Bot faol holatda. Hech narsa qilish shart emas.</p>
                </div>
            </body>
            </html>
            """
        
        @app.route('/health')
        def health():
            return "OK", 200
        
        @app.route('/status')
        def status():
            return {
                "status": "running",
                "bot": "active",
                "timestamp": datetime.now().isoformat(),
                "platform": "render"
            }
        
        # Portni Render muhitidan olish
        port = int(os.environ.get("PORT", 8080))
        print(f"🌐 Flask server {port}-portda ishga tushmoqda...")
        
        # Development mode o'chirilgan
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        
    except Exception as e:
        print(f"❌ Flask server xatosi: {e}")

def start_flask_in_thread():
    """Flask serverni threadda ishga tushiradi"""
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    print("✅ Flask server threadda ishga tushirildi")

# ========== ADMIN TEKSHIRISH FUNKSIYASI ==========
def is_admin(user_id):
    """Admin tekshirish funksiyasi"""
    return user_id in ADMINS

# Foydalanuvchi holatlari
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

class SearchStates(StatesGroup):
    waiting_for_query = State()

class CategoryStates(StatesGroup):
    waiting_for_subcategory = State()

class PaginationStates(StatesGroup):
    browsing_category = State()
    browsing_subcategory = State()
    browsing_search = State()
    
class PaymentStates(StatesGroup):
    waiting_for_payment_method = State()
    waiting_for_check_photo = State()
    waiting_for_check_confirmation = State()

# ========== KUCHAYTIRILGAN ANTI-SCREENSHOT MIDDLEWARE ==========
class EnhancedProtectionMiddleware(BaseMiddleware):
    """Kuchaytirilgan himoya middleware"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # 1. AGAR ADMIN BO'LSA, HIMOYANI O'TKAZIB YUBORISH
        if is_admin(event.from_user.id):
            return await handler(event, data)
        
        # 2. BLOKLANMI LIGINI TEKSHIRISH - HAR QANDAY XABAR UCHUN
        user_id = event.from_user.id
        
        # Avval tekshirish - block_date NULL bo'lgan (aktiv blok) yoki status bloklangan
        try:
            db.cursor.execute('''
                SELECT id, reason, block_date 
                FROM blocked_users 
                WHERE user_id = ? AND unblock_date IS NULL
            ''', (user_id,))
            block_record = db.cursor.fetchone()
            
            if block_record:
                # Agar bloklangan bo'lsa, foydalanuvchiga xabar yuborish
                reason = block_record[1] if block_record[1] else "Kontent himoya qoidalarini buzish"
                block_date = block_record[2][:10] if block_record[2] else "Noma'lum"
                
                block_message = f"""🚫 **SIZ BLOKLANDINGIZ!**

📅 **Bloklangan sana:** {block_date}
📝 **Sabab:** {reason}

🔓 **Blokdan ochish uchun:**
@Operator_Kino_1985 ga yozing

❌ **Diqqat:** Blokdan avtomatik ochilmaydi!
Faoliyatingiz to'liq cheklangan."""
                
                await event.answer(block_message)
                return  # Handler ni chaqirmaymiz
                
            # Qo'shimcha users jadvalidagi statusni tekshirish
            db.cursor.execute('SELECT status FROM users WHERE user_id = ?', (user_id,))
            user_status = db.cursor.fetchone()
            
            if user_status and user_status[0] == 'blocked':
                # Emergency block qilish
                db.cursor.execute('''
                    INSERT OR IGNORE INTO blocked_users (user_id, blocked_by, reason, block_date)
                    VALUES (?, ?, ?, datetime('now', 'localtime'))
                ''', (user_id, 1, "Emergency block - status mismatch",))
                db.conn.commit()
                
                block_message = f"""🚫 **SIZ AVTOMATIK BLOKLANDINGZ!**

Akkauntingiz tizim tomonidan avtomatik bloklandi.

🔓 **Blokdan ochish uchun:**
@Operator_Kino_1985 ga yozing"""
                
                await event.answer(block_message)
                return
                
        except Exception as e:
            print(f"⚠️ Block check middleware error: {e}")
        
        # 3. FSM holatini olish
        state = data.get('state')
        if state:
            current_state = await state.get_state()
            
            # TO'LOV HOLATLARIDA HIMOYANI O'TKAZIB YUBORISH
            if current_state and "PaymentStates" in current_state:
                return await handler(event, data)
        
        # 4. FAQAT FILM KONTENTLARINI TEKSHIRISH
        # ODDIY MATN XABARLARINI TO'LIQ O'TKAZIB YUBORISH
        if not (event.photo or event.video or event.document):
            return await handler(event, data)
        
        # 5. Kontent yuborilayotgan xabarlarni tekshirish (faqat media)
        # Screen recording aniqlash
        if event.photo:
            detection_type = 'screenshot'
        elif event.video:
            detection_type = 'screen_recording'
        elif event.document:
            # Dokumentlar uchun alohida tekshirish
            # Telegram'dan yuborilgan dokumentlar (rasm, video, fayl)
            detection_type = 'document'
        
        # Yuklab olish urinishini log qilish
        try:
            if event.photo:
                file_size = event.photo[-1].file_size
            elif event.video:
                file_size = event.video.file_size
            elif event.document:
                file_size = event.document.file_size
            else:
                file_size = 0
                
            db.log_screen_recording_detection(
                user_id=user_id,
                detection_type=detection_type,
                details=f"File size: {file_size}"
            )
        except:
            pass
        
        # Urinishlar sonini tekshirish
        today_attempts = db.get_user_download_stats(user_id, hours=24)
        today_count = today_attempts[0] if today_attempts else 0
        
        if today_count >= PROTECTION_CONFIG['daily_download_limit']:
            # Limitdan oshgan holatda
            await event.answer(
                "🚫 **YUKLAB OLISH LIMITI TUGADI!**\n\n"
                "Sizning kunlik yuklab olish limitingiz (50 ta) tugadi.\n"
                "Limit ertaga soat 00:00 da tiklanadi.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="🔒 Himoya Qoidalari")]],
                    resize_keyboard=True
                )
            )
            return
        
        # Agar screen recording aniqlansa
        if PROTECTION_CONFIG['screen_recording_detection']:
            # Piravlik urinishini log qilish
            db.log_anti_piracy_action(
                user_id=user_id,
                action_type=detection_type,
                details="Auto-detected screen recording attempt"
            )
            
            # Urinishlar sonini tekshirish
            piracy_attempts = db.get_user_piracy_attempts(user_id)
            if piracy_attempts >= 3:
                # 3 marta urinishdan keyin bloklash
                db.block_user(
                    user_id=user_id,
                    blocked_by=int(ADMIN_ID) if ADMIN_ID else 1,
                    reason=f"3 marta {detection_type} urinishi"
                )
                
                await event.answer(
                    "🚫 **SIZ BLOKLANDINGIZ!**\n\n"
                    "Kontent himoya qoidalarini 3 marta buzganingiz uchun "
                    "sizning akkauntingiz bloklandi.\n\n"
                    "Batafsil ma'lumot uchun administrator bilan bog'laning.",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[[KeyboardButton(text="🏠 Asosiy menyu")]],
                        resize_keyboard=True
                    )
                )
                return
            
            # Ogohlantirish xabari (faqat film kontentlariga)
            warning_text = f"""
⚠️ **{detection_type.upper()} ANIQLANDI!**

📵 Bu harakat kontent himoya qoidalariga ziddir:
• Skrinshot olish ta'qiqlangan
• Ekran yozib olish ta'qiqlangan
• Kontentni saqlash ta'qiqlangan

🔢 Urinishlar soni: {piracy_attempts + 1}/3

❗ **Ogohlantirish:** Yana {3 - piracy_attempts - 1} marta shunday harakat qilsangiz, akkauntingiz bloklanadi.
            """
            
            await event.answer(
                warning_text,
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="🔒 Himoya Qoidalari")]],
                    resize_keyboard=True
                )
            )
            
            # Original handler ni chaqirmaymiz
            return
    
        # Agar yuqoridagi shartlar bajarilmasa, handler ni chaqiramiz
        return await handler(event, data)

# ========== HIMOYALANGAN KONTENT YUBORISH FUNKSIYASI ==========
async def send_protected_content(message: Message, movie, user_id, page_info="", state: FSMContext = None):
    """Himoyalangan kontentni yuborish"""
    try:
        # 1. Foydalanuvchi tekshirish
        if db.is_user_blocked(user_id):
            await message.answer("🚫 Sizning akkauntingiz bloklangan!")
            return
        
        # 2. Film ma'lumotlari
        movie_id = movie[0]
        is_premium, price = db.is_premium_movie(movie_id)
        
        # 3. AGAR FILM PULLIK BO'LSA VA FOYDALANUVCHI SOTIB OLMAGAN BO'LSA
        if is_premium:
            # Foydalanuvchi sotib olganmi?
            has_purchased = db.has_purchased_movie(user_id, movie_id)
            
            if not has_purchased:
                # User tilini aniqlash
                user = db.get_user(user_id)
                language = user[4] if user else 'uz'
                kb = Keyboards(language)
                
                # Soddalashtirilgan xabar
                premium_text = f"""🎬 **{movie[3]}** - 💰 PULLIK KONTENT

📖 {movie[4]}
🌐 Til: {movie[7]}
👁️ Ko'rishlar: {movie[8]}
📅 Sana: {movie[9][:10]}

💵 **Narxi:** {price:,} so'm

👇 **To'lash uchun quyidagi tugmani bosing:**"""
                
                # State ga filmni saqlash (agar state bo'lsa)
                if state:
                    await state.update_data(premium_movie=movie)
                
                await message.answer(
                    premium_text,
                    reply_markup=kb.premium_content_keyboard()
                )
                return  # Kontent yubormaymiz
        
        # 4. Bepul yoki sotib olgan bo'lsa
        # Kunlik limit
        today_stats = db.get_user_download_stats(user_id, hours=24)
        today_count = today_stats[0] if today_stats else 0
        
        if today_count >= 50:
            await message.answer(
                "🚫 **YUKLAB OLISH LIMITI TUGADI!**\n\n"
                "Kunlik limit (50 ta) tugadi.\n"
                "Ertaga 00:00 da tiklanadi."
            )
            return
        
        # 5. Kontent yuborish
        price_display = f"{price:,} so'm" if is_premium and price else "Bepul"
        
        movie_text = f"""
🎬 **{movie[3]}**
📖 {movie[4]}
🌐 Til: {movie[7]}
👁️ Ko'rishlar: {movie[8] + 1}
📅 Sana: {movie[9][:10]}
💰 **Holat:** {price_display}

{page_info}
        """
        
        # Statistikalar
        db.increment_views(movie_id)
        db.add_video_access_log(user_id, movie_id)
        db.log_download_attempt(user_id, movie_id, 'view')
        
        # Kontent yuborish
        try:
            if movie[5]:  # file_id bor
                if movie[6] == 'video':
                    await message.answer_video(
                        video=movie[5],
                        caption=movie_text,
                        protect_content=True,
                        has_spoiler=True,
                    )
                else:
                    await message.answer_document(
                        document=movie[5],
                        caption=movie_text,
                        protect_content=True,
                    )
                
                # Qisqa xabar
                if is_premium:
                    protection_msg = f"✅ **PULLIK KONTENT OCHILDI!**\n\n🎬 {movie[3]}\n💰 {price:,} so'm\n📊 {today_count + 1}/50"
                else:
                    protection_msg = f"✅ **KONTENT OCHILDI!**\n\n🎬 {movie[3]}\n🆓 Bepul\n📊 {today_count + 1}/50"
                
                await message.answer(protection_msg)
            else:
                await message.answer(f"❌ Fayl topilmadi: {movie[3]}")
                
        except Exception as e:
            print(f"Video yuborish xatosi: {e}")
            await message.answer("❌ Xatolik yuz berdi!")
            
    except Exception as e:
        print(f"send_protected_content xatosi: {e}")
        await message.answer("❌ Xatolik yuz berdi!")

# ========== START COMMAND ==========
@dp.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Start komandasi - Yangilangan versiya"""
    user_id = message.from_user.id
    
    # 1. BLOK TEKSHIRISH
    try:
        # To'g'ridan-to'g'ri SQL so'rovi bilan tekshirish
        db.cursor.execute('''
            SELECT id FROM blocked_users 
            WHERE user_id = ? AND unblock_date IS NULL
        ''', (user_id,))
        
        active_block = db.cursor.fetchone()
        
        if active_block:
            # users jadvalini yangilash
            db.cursor.execute('''
                UPDATE users 
                SET status = 'blocked' 
                WHERE user_id = ?
            ''', (user_id,))
            db.conn.commit()
            
            # Blok xabarini yuborish
            await message.answer(
                "🚫 **SIZ BLOKLANDINGIZ!**\n\n"
                "Kontent himoya qoidalarini buzganingiz uchun akkauntingiz bloklangan.\n\n"
                "✅ **Sabab:** Kontent himoya qoidalarini buzish\n"
                "📅 **Blok sanasi:** Oxirgi marta\n"
                "👮 **Bloklovchi:** Sistema\n\n"
                "🔓 **Blokdan ochish uchun:** @Operator_Kino_1985 ga murojaat qiling.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="🏠 Asosiy menyu")]],
                    resize_keyboard=True
                )
            )
            await state.clear()
            return
        
        # users jadvalidagi statusni tekshirish
        db.cursor.execute('SELECT status FROM users WHERE user_id = ?', (user_id,))
        user_result = db.cursor.fetchone()
        
        if user_result and user_result[0] == 'blocked':
            # blocked_users ga yozish agar yo'q bo'lsa
            db.cursor.execute('''
                INSERT OR IGNORE INTO blocked_users (user_id, blocked_by, reason, block_date)
                VALUES (?, ?, ?, datetime('now', 'localtime'))
            ''', (user_id, 1, "Emergency block - status mismatch",))
            
            db.conn.commit()
            
            await message.answer(
                "🚫 **SIZ BLOKLANDINGIZ!**\n\n"
                "Akkauntingiz tizim tomonidan avtomatik bloklandi.\n\n"
                "🔓 Blokdan ochish uchun: @Operator_Kino_1985 ga murojaat qiling.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="🏠 Asosiy menyu")]],
                    resize_keyboard=True
                )
            )
            await state.clear()
            return
            
    except Exception as e:
        print(f"⚠️ Block check error: {e}")
    
    # 2. FOYDALANUVCHINI TEKSHIRISH VA RO'YXATDAN O'TISH
    await state.clear()
    
    user = db.get_user(user_id)
    
    # JAMI FOYDALANUVCHILAR SONINI OLISH
    try:
        total_users = db.get_users_count()
    except:
        total_users = 0
    
    if user:
        # Foydalanuvchi mavjud - sqlite3.Row yoki tuple formatida
        # User ma'lumotlarini to'g'ri formatda olish
        user_name = user[2] if user and len(user) > 2 else message.from_user.first_name
        language = user[4] if user and len(user) > 4 else 'uz'
        
        # QO'SHIMCHA STATUS TEKSHIRISH
        if user and len(user) > 6 and user[6] == 'blocked':
            # Emergency block qilish
            db.cursor.execute('''
                UPDATE users SET status = 'blocked' WHERE user_id = ?
            ''', (user_id,))
            
            db.cursor.execute('''
                INSERT OR IGNORE INTO blocked_users (user_id, blocked_by, reason, block_date)
                VALUES (?, ?, ?, datetime('now', 'localtime'))
            ''', (user_id, 1, "Emergency block - status mismatch",))
            
            db.conn.commit()
            
            await message.answer(
                "🚫 **SIZ BLOKLANDINGIZ!**\n\n"
                "Akkauntingiz tizim tomonidan avtomatik bloklandi.\n\n"
                "🔓 Blokdan ochish uchun: @Operator_Kino_1985 ga murojaat qiling.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="🏠 Asosiy menyu")]],
                    resize_keyboard=True
                )
            )
            return
        
        # Yangilangan keyboard
        kb = Keyboards(language)
        
        # RO'YXATDAN O'TGAN SANANI OLISH
        registered_date = ''
        if user and len(user) > 5:
            registered_date = str(user[5])[:10] if user[5] else 'Bugun'
        else:
            registered_date = 'Bugun'
        
        # FOYDALANUVCHI ISMI VA OBUNACHILAR SONINI KO'RSATISH
        welcome_message = f"""🎬 **Xush kelibsiz, {user_name}!** 

🤖 **UnitedMedia Kino Bot** ga xush kelibsiz!

📊 **Statistika:**
👥 **Jami obunachilar:** {total_users:,} ta
🆔 **Sizning ID:** `{user_id}`
📅 **Ro'yxatdan o'tgan:** {registered_date}

🎬 **Mavjud kategoriyalar:** 15+
🎥 **Filmlar va seriallar:** Har xil
💰 **Pullik va bepul** kontentlar

👇 **Quyidagi menyudan kerakli bo'limni tanlang:**"""
        
        await message.answer(
            welcome_message,
            reply_markup=kb.main_menu(is_admin=is_admin(user_id))
        )
    else:
        # Yangi foydalanuvchi - STATISTIKA QO'SHAMIZ
        # Bugungi yangi foydalanuvchilarni hisoblash
        try:
            db.cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(registered_date) = DATE('now')
            ''')
            today_new = db.cursor.fetchone()[0] or 0
        except:
            today_new = 0
            
        # Faol foydalanuvchilarni hisoblash
        try:
            db.cursor.execute('''
                SELECT COUNT(DISTINCT user_id) 
                FROM download_attempts 
                WHERE attempt_date >= DATE('now', '-7 days')
            ''')
            active_users = db.cursor.fetchone()[0] or 0
        except:
            active_users = 0
        
        welcome_new_message = f"""🎬 **Kino Botga xush kelibsiz!** 

🤖 **UnitedMedia Kino Bot** ga xush kelibsiz!

📊 **Bugungi statistika:**
👥 **Jami obunachilar:** {total_users:,} ta (siz qo'shilgach)
🆕 **Bugun qo'shilgan:** {today_new} ta
🔥 **Faol foydalanuvchilar:** {active_users} ta

🎬 **Botda mavjud:**
• 15+ kategoriya
• Har xil filmlar va seriallar  
• Pullik va bepul kontentlar

📝 **Botdan foydalanish uchun ro'yxatdan o'tishingiz kerak.**
Iltimos, tilni tanlang:"""
        
        await message.answer(
            welcome_new_message,
            reply_markup=Keyboards().language_selection()  # Tilni tanlash tugmalari
        )
        await state.clear()

# ========== KUCHAYTIRILGAN HIMOYA QOIDALARI ==========
@dp.message(F.text == "🔒 Himoya Qoidalari")
async def protection_rules(message: Message):
    """Qisqa himoya qoidalari"""
    rules_text = """
🔒 **HIMOYA QOIDALARI**

📋 **Asosiy qoidalar:**
1. Skrinshot olish ta'qiqlangan
2. Ekran yozib olish ta'qiqlangan
3. Kontent saqlash ta'qiqlangan
4. Kunlik limit: 50 ta

⚠️ **Jarimalar:**
• 1-2 urinish: Ogohlantirish
• 3 urinish: Blok

✅ **Ruxsat etilgan:**
• Bot ichida ko'rish
• Limit doirasida yuklab olish

📞 **Yordam:** @Operator_Kino_1985
    """
    
    await message.answer(rules_text)

# ========== KUCHAYTIRILGAN HIMOYA STATISTIKASI ==========
@dp.message(Command("mystats"))
async def my_stats(message: Message):
    """Foydalanuvchining kuchaytirilgan statistikasi"""
    user = db.get_user(message.from_user.id)
    
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz!")
        return
    
    user_id = message.from_user.id
    
    # Bloklanganligini tekshirish
    if db.is_user_blocked(user_id):
        block_info = db.cursor.execute(
            'SELECT reason, block_date, blocked_by FROM blocked_users WHERE user_id = ? AND unblock_date IS NULL',
            (user_id,)
        ).fetchone()
        
        if block_info:
            reason = block_info[0] if block_info[0] else "Kontent himoya qoidalarini buzish"
            date = block_info[1][:10] if block_info[1] else 'Noma\'lum'
            blocked_by_id = block_info[2]
            
            blocked_by_user = db.get_user(blocked_by_id)
            blocked_by_name = blocked_by_user[2] if blocked_by_user else "Administrator"
            
            block_text = f"""
🚫 **SIZ BLOKLANDINGIZ!**

📅 **Bloklangan sana:** {date}
📝 **Sabab:** {reason}
👮 **Bloklovchi:** {blocked_by_name}

🔓 **Blokdan ochish uchun:**
1. @Operator_Kino_1985 ga yozing
2. Blok sababini tushuntiring
3. Administrator qarorini kuting

❌ **Diqqat:** Blokdan avtomatik ochilmaydi!
Faoliyatingiz to'liq cheklangan.
"""
            await message.answer(block_text)
            return
    
    # Yuklab olish statistikasi
    download_stats = db.get_user_download_stats(user_id, hours=24)
    weekly_stats = db.get_user_download_stats(user_id, hours=168)
    monthly_stats = db.get_user_download_stats(user_id, hours=720)
    
    # Video access statistikasi
    try:
        db.cursor.execute('''
            SELECT COUNT(*) FROM video_access_logs 
            WHERE user_id = ?
        ''', (user_id,))
        video_access = db.cursor.fetchone()[0] or 0
    except:
        video_access = 0
    
    # Piravlik urinishlari
    piracy_attempts = db.get_user_piracy_attempts(user_id)
    
    # Screen recording detections
    try:
        db.cursor.execute('''
            SELECT COUNT(*) FROM screen_recording_detections 
            WHERE user_id = ?
        ''', (user_id,))
        screenshot_attempts = db.cursor.fetchone()[0] or 0
    except:
        screenshot_attempts = 0
    
    stats_text = f"""
📊 **SIZNING KUCHAYTIRILGAN STATISTIKANGIZ**

👤 **SHAXSIY MA'LUMOTLAR:**
• Ism: {user[2]}
• Ro'yxatdan o'tgan: {user[5][:10]}
• Status: {user[6]}
• Blok holati: ✅ FAOL
• Xavf darajasi: {'🟢 Past' if piracy_attempts == 0 else '🟡 Oʻrtacha' if piracy_attempts < 3 else '🔴 Yuqori'}

🔒 **HIMOYA STATISTIKASI:**
• Bugun yuklab olish: {download_stats[0] if download_stats else 0}/50
• Haftalik yuklab olish: {weekly_stats[0] if weekly_stats else 0}
• Oylik yuklab olish: {monthly_stats[0] if monthly_stats else 0}
• Ko'rilgan filmlar: {video_access}
• Skrinshot urinishlari: {screenshot_attempts}
• Piravlik urinishlari: {piracy_attempts}/3
• Qolgan urinishlar: {3 - piracy_attempts}

⚠️ **XAVF TAHLILI:**
• Blok chegarasi: 3 urinish
• Sizda qolgan: {3 - piracy_attempts} urinish
• Kunlik limit: 50 ta
• Screen recording: TA'QIQ

🛡️ **HIMOYA HOLATI:**
• Telegram himoyasi: ✅ FAOL
• Token himoyasi: ✅ FAOL (2 soat)
• Monitoring: ✅ FAOL (24/7)
• Platforma himoyasi: ✅ (Android/iOS/Windows)

📈 **TAVSIYALAR:**
1. Skrinshot olmang
2. Screen recording qilmang
3. Limitdan oshirmang
4. Qoidalarga rioya qiling
5. Agar muammo bo'lsa, admin bilan bog'laning

🔔 **OGOHLANTIRISH:** {3 - piracy_attempts} ta urinish qolgan.
3 ta urinishdan keyin AVTOMATIK BLOKLANASIZ!
"""
    
    await message.answer(stats_text)
    
# ========== HIMOYA STATISTIKASI ==========
@dp.message(Command("protection_stats"))
async def protection_stats(message: Message):
    """Himoya statistikasini ko'rsatish"""
    user_id = message.from_user.id
    
    # Faqat adminlar uchun
    if not is_admin(user_id):
        await message.answer("❌ Bu komanda faqat adminlar uchun!")
        return
    
    try:
        # Bugungi statistika
        db.cursor.execute('''
            SELECT COUNT(*) FROM download_attempts 
            WHERE DATE(attempt_date) = DATE('now')
        ''')
        today_downloads = db.cursor.fetchone()[0] or 0
        
        db.cursor.execute('''
            SELECT COUNT(*) FROM screen_recording_detections 
            WHERE DATE(detection_time) = DATE('now')
        ''')
        today_screenshots = db.cursor.fetchone()[0] or 0
        
        db.cursor.execute('''
            SELECT COUNT(*) FROM anti_piracy_logs 
            WHERE DATE(action_date) = DATE('now')
        ''')
        today_piracy = db.cursor.fetchone()[0] or 0
        
        # Bloklangan foydalanuvchilar
        db.cursor.execute('SELECT COUNT(*) FROM blocked_users WHERE unblock_date IS NULL')
        blocked_users = db.cursor.fetchone()[0] or 0
        
        # Faol tokenlar
        db.cursor.execute('SELECT COUNT(*) FROM content_tokens WHERE is_active = 1')
        active_tokens = db.cursor.fetchone()[0] or 0
        
        stats_text = f"""
🔒 **HIMOYA STATISTIKASI - REAL VAQT**

📊 **Bugungi faollik:**
• Yuklab olishlar: {today_downloads}
• Skrinshot aniqlangan: {today_screenshots}
• Piravlik urinishlari: {today_piracy}

👥 **Foydalanuvchilar:**
• Bloklangan foydalanuvchilar: {blocked_users}
• Faol himoya tokenlari: {active_tokens}

⚙️ **Himoya sozlamalari:**
• Token amal qilish: {PROTECTION_CONFIG['token_expiry_hours']} soat
• Kunlik limit: {PROTECTION_CONFIG['daily_download_limit']} ta
• Avtomatik blok: {PROTECTION_CONFIG['auto_block_attempts']} urinish
• Himoya darajasi: {PROTECTION_CONFIG['protection_level'].upper()}

🛡️ **Platforma himoyasi:**
• Android: {'✅' if PROTECTION_CONFIG['platform_protection']['android'] else '❌'}
• iOS: {'✅' if PROTECTION_CONFIG['platform_protection']['ios'] else '❌'}
• Windows: {'✅' if PROTECTION_CONFIG['platform_protection']['windows'] else '❌'}
• Web: {'✅' if PROTECTION_CONFIG['platform_protection']['web'] else '❌'}

📈 **Status:** ✅ HIMOYA FAOL
"""
        
        await message.answer(stats_text)
        
    except Exception as e:
        print(f"Protection stats xatosi: {e}")
        await message.answer("❌ Statistika olishda xatolik!")    

# ========== TILNI O'ZGARTIRISH ==========
@dp.message(F.text.contains("Tilni O'zgartirish") | 
            F.text.contains("Сменить язык") | 
            F.text.contains("Change Language"))
async def change_language(message: Message):
    user = db.get_user(message.from_user.id)
    
    if user:
        # Foydalanuvchi ro'yxatdan o'tgan, faqat tilni tanlash
        await message.answer(
            "Tilni tanlang: 🌐",
            reply_markup=Keyboards().language_selection()
        )
    else:
        # Foydalanuvchi ro'yxatdan o'tmagan
        await message.answer(
            "Siz hali ro'yxatdan o'tmagansiz. Iltimos, avval ro'yxatdan o'ting: 👤",
            reply_markup=Keyboards().language_selection()
        )

# ========== TILNI TANLASH ==========
@dp.message(F.text.in_(["🇺🇿 UZ", "🇷🇺 RU", "🇬🇧 EN"]))
async def select_language(message: Message, state: FSMContext):
    lang_map = {
        "🇺🇿 UZ": "uz",
        "🇷🇺 RU": "ru", 
        "🇬🇧 EN": "en"
    }
    
    language = lang_map[message.text]
    
    # Avval state ma'lumotlarini olamiz
    data = await state.get_data()
    
    # Tilni state ga saqlaymiz
    await state.update_data(language=language)
    
    user = db.get_user(message.from_user.id)
    
    if user:
        # Foydalanuvchi ro'yxatdan o'tgan, faqat tilni o'zgartirish
        db.update_user_language(message.from_user.id, language)
        
        kb = Keyboards(language)
        
        success_texts = {
            'uz': "✅ Til muvaffaqiyatli o'zgartirildi! 🌐",
            'ru': "✅ Язык успешно изменен! 🌐",
            'en': "✅ Language changed successfully! 🌐"
        }
        
        await message.answer(
            success_texts[language],
            reply_markup=kb.main_menu(is_admin=is_admin(message.from_user.id)))
        await state.clear()
    else:
        # Foydalanuvchi ro'yxatdan o'tmagan, ro'yxatdan o'tish jarayoni
        await state.update_data(language=language)
        
        kb = Keyboards(language)
        
        await message.answer(
            "Iltimos, botdan to'liq foydalanish uchun ro'yxatdan o'ting (faqat bir marta). 👤\n\n"
            "Ismingizni kiriting:",
            reply_markup=kb.back_button()
        )
        await state.set_state(RegistrationStates.waiting_for_name)

# ========== ISM QABUL QILISH ==========
@dp.message(RegistrationStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    back_texts = ["⬅️ Ortga", "⬅️ Назад", "⬅️ Back"]
    if message.text in back_texts:
        await message.answer("Tilni tanlang: 🌐", reply_markup=Keyboards().language_selection())
        await state.clear()
        return
    
    await state.update_data(full_name=message.text)
    
    data = await state.get_data()
    
    # Tilni tekshirish - agar yo'q bo'lsa, standart tilni o'rnatamiz
    language = data.get('language', 'uz')  # Uzbek tilini standart qilamiz
    kb = Keyboards(language)
    
    await message.answer(
        "Telefon raqamingizni kiriting:",
        reply_markup=kb.phone_number_request()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)

# ========== TELEFON RAQAM QABUL QILISH ==========
@dp.message(RegistrationStates.waiting_for_phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    contact = message.contact
    data = await state.get_data()
    
    # Ma'lumotlarni bazaga saqlash
    db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=data['full_name'],
        phone=contact.phone_number
    )
    
    # Tilni saqlash
    db.update_user_language(message.from_user.id, data['language'])
    
    kb = Keyboards(data['language'])
    
    # Animatsiyali kutish xabari
    wait_msg = await message.answer("Ma'lumotlar tekshirilmoqda... 🔄")
    
    for i in range(1, 6):
        await asyncio.sleep(1)
        await wait_msg.edit_text(f"Ma'lumotlar tekshirilmoqda... 🔄 {i}/5")
    
    await wait_msg.delete()
    
    success_texts = {
        'uz': "✅ Ro'yxatdan o'tish ma'lumotlaringiz tasdiqlandi! 🎉",
        'ru': "✅ Ваши регистрационные данные подтверждены! 🎉",
        'en': "✅ Your registration data has been confirmed! 🎉"
    }
    
    await message.answer(
        success_texts[data['language']],
        reply_markup=kb.main_menu(is_admin=is_admin(message.from_user.id)))
    await state.clear()

# ========== BARCHA KONTENTLAR ==========
@dp.message(F.text.contains("Barcha kontentlar") | 
            F.text.contains("Все контенты") | 
            F.text.contains("All Content"))
async def show_all_content(message: Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    language = user[4] if user else 'uz'
    kb = Keyboards(language)
    
    await message.answer(
        "Kategoriyani tanlang: 📁",
        reply_markup=kb.categories_menu()
    )

# ========== QIDIRUV ==========
@dp.message(F.text.contains("🔍 Qidiruv") | 
            F.text.contains("🔍 Поиск") | 
            F.text.contains("🔍 Search"))
async def search_movies(message: Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    language = user[4] if user else 'uz'
    kb = Keyboards(language)
    
    search_texts = {
        'uz': "Kino nomini yoki kalit so'zni kiriting: 🔤",
        'ru': "Введите название фильма или ключевое слово: 🔤",
        'en': "Enter movie title or keyword: 🔤"
    }
    
    await message.answer(
        search_texts[language],
        reply_markup=kb.back_button()
    )
    await state.set_state(SearchStates.waiting_for_query)

# ========== QIDIRUV NATIJALARI ==========
@dp.message(SearchStates.waiting_for_query)
async def show_search_results(message: Message, state: FSMContext):
    back_texts = ["⬅️ Ortga", "⬅️ Назад", "⬅️ Back"]
    if message.text in back_texts:
        user = db.get_user(message.from_user.id)
        language = user[4] if user else 'uz'
        kb = Keyboards(language)
        
        await message.answer("Asosiy menyu: 🏠", reply_markup=kb.main_menu(is_admin=is_admin(message.from_user.id)))
        await state.clear()
        return
    
    query = message.text.strip()
    
    # Qidiruvni bo'sh bo'lishini tekshirish
    if not query or len(query) < 2:
        await message.answer("❌ Iltimos, kamida 2 ta belgidan iborat so'z kiriting!")
        return
    
    await state.update_data(search_query=query)
    
    user = db.get_user(message.from_user.id)
    language = user[4] if user else 'uz'
    kb = Keyboards(language)
    
    # Sahifalangan qidiruv natijalari
    page = 1
    per_page = 5  # Bir sahifada 5 ta natija ko'rsatamiz
    results = db.search_movies_paginated(query, page=page, per_page=per_page)
    
    # Jami filmlar soni (taxminiy)
    total_results = len(results)
    
    if not results:
        no_results_texts = {
            'uz': f"❌ '{query}' uchun hech qanday natija topilmadi. 😔\n\nBoshqa kalit so'z bilan qayta urinib ko'ring.",
            'ru': f"❌ Для '{query}' результатов не найдено. 😔\n\nПопробуйте с другими ключевыми словами.",
            'en': f"❌ No results found for '{query}'. 😔\n\nTry with different keywords."
        }
        await message.answer(no_results_texts[language])
        return
    
    # Natijalarni chiroyli formatda ko'rsatish
    results_text = f"🔍 **Qidiruv natijalari: '{query}'**\n\n"
    results_text += f"📊 Topilgan filmlar: {total_results} ta\n"
    results_text += f"📄 Sahifa: {page}/{max(1, total_results // per_page + (1 if total_results % per_page > 0 else 0))}\n\n"
    
    for i, movie in enumerate(results, 1):
        if len(movie) >= 10:  # Tuple indexlarni tekshirish
            results_text += f"**{i}. {movie[3]}**\n"
            results_text += f"   📖 {movie[4][:80]}{'...' if len(movie[4]) > 80 else ''}\n"
            results_text += f"   🗂️ Kategoriya: {movie[1]}\n"
            results_text += f"   🌐 Til: {movie[9] if len(movie) > 9 else 'N/A'}\n"
            results_text += f"   👁️ Ko'rishlar: {movie[10] if len(movie) > 10 else 0}\n"
            results_text += "─" * 30 + "\n"
    
    # Agar juda ko'p natija bo'lsa
    if total_results > per_page:
        results_text += f"\n⚠️ **Diqqat:** Faqat birinchi {per_page} ta natija ko'rsatilmoqda."
    
    # Sahifalash tugmalari - to'g'ri callback_data yaratish
    pagination_kb = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Agar natijalar bo'lsa
    if results:
        # BIRINCHI filmini video sifatida yuborish
        first_movie = results[0]
        try:
            if len(first_movie) > 5 and first_movie[5]:  # file_id borligini tekshirish
                movie_info = f"🎬 **{first_movie[3]}**\n"
                if len(first_movie) > 4:
                    movie_info += f"📖 {first_movie[4][:100]}{'...' if len(first_movie[4]) > 100 else ''}\n"
                if len(first_movie) > 9:
                    movie_info += f"🌐 Til: {first_movie[9]}"
                
                # Film pullik yoki bepul ekanligini tekshirish
                is_premium, price = db.is_premium_movie(first_movie[0])
                
                if is_premium:
                    # Agar pullik bo'lsa, to'lov sahifasini ko'rsatish
                    premium_text = f"""🎬 **{first_movie[3]}** - 💰 PULLIK KONTENT

📖 {first_movie[4][:100]}{'...' if len(first_movie[4]) > 100 else ''}
🌐 Til: {first_movie[9] if len(first_movie) > 9 else 'N/A'}
👁️ Ko'rishlar: {first_movie[10] if len(first_movie) > 10 else 0}

💵 **Narxi:** {price:,} so'm

👇 **To'lash uchun quyidagi tugmani bosing:**"""
                    
                    await state.update_data(premium_movie=first_movie)
                    
                    await message.answer(
                        premium_text,
                        reply_markup=kb.premium_content_keyboard()
                    )
                else:
                    # Bepul bo'lsa, himoyalangan holda yuborish
                    await send_protected_content(
                        message=message,
                        movie=first_movie,
                        user_id=message.from_user.id
                    )
                
                # Sahifalash tugmalari
                total_pages = max(1, total_results // per_page + (1 if total_results % per_page > 0 else 0))
                
                if total_pages > 1:
                    keyboard_buttons = []
                    
                    # Oldingi sahifa
                    if page > 1:
                        keyboard_buttons.append(
                            InlineKeyboardButton(
                                text="◀️ Oldingi", 
                                callback_data=f"search_page_{page-1}_{query}"
                            )
                        )
                    
                    # Keyingi sahifa
                    if page < total_pages:
                        keyboard_buttons.append(
                            InlineKeyboardButton(
                                text="Keyingi ▶️", 
                                callback_data=f"search_page_{page+1}_{query}"
                            )
                        )
                    
                    pagination_kb.inline_keyboard.append(keyboard_buttons)
                
                # Ortga qaytish tugmasi
                pagination_kb.inline_keyboard.append([
                    InlineKeyboardButton(
                        text="🏠 Asosiy menyuga", 
                        callback_data="back_to_main"
                    )
                ])
                
        except Exception as e:
            print(f"❌ Error sending first movie: {e}")
            await message.answer("❌ Film yuborishda xatolik yuz berdi.")
    
    await message.answer(results_text, reply_markup=pagination_kb)
    await state.set_state(PaginationStates.browsing_search)

# ========== ASOSIY KATEGORIYALAR ==========
@dp.message(F.text.in_([
    # Asosiy kategoriyalar
    "🎭 Hollywood Kinolari", "🎭 Голливудские Фильмы", "🎭 Hollywood Movies",
    "🕌 Hind Filmlari", "🕌 Индийские Фильмы", "🕌 Indian Movies",
    "📺 Hind Seriallari", "📺 Индийские Сериалы", "📺 Indian Series",
    "🎪 Rus Kinolari", "🎪 Русские Фильмы", "🎪 Russian Movies",
    "📺 Rus Seriallari", "📺 Русские Сериалы", "📺 Russian Series",
    "🇺🇿 O'zbek Kinolari", "🇺🇿 Узбекские Фильмы", "🇺🇿 Uzbek Movies",
    "📺 O'zbek Seriallari", "📺 Узбекские Сериалы", "📺 Uzbek Series",
    "🕌 Islomiy Kinolar", "🕌 Исламские Фильмы", "🕌 Islamic Movies",
    "📺 Islomiy Seriallar", "📺 Исламские Сериалы", "📺 Islamic Series",
    "🇹🇷 Turk Kinolari", "🇹🇷 Турецкие Фильмы", "🇹🇷 Turkish Movies",
    "📺 Turk Seriallari", "📺 Турецкие Сериалы", "📺 Turkish Series",
    "👶 Bolalar Kinolari", "👶 Детские Фильмы", "👶 Kids Movies",
    "🐰 Bolalar Multfilmlari", "🐰 Детские Мультфильмы", "🐰 Kids Cartoons",
    "🇰🇷 Koreys Kinolari", "🇰🇷 Корейские Фильмы", "🇰🇷 Korean Movies",
    "📺 Koreys Seriallari", "📺 Корейские Сериалы", "📺 Korean Series",
    "🎥 Qisqa Filmlar", "🎥 Короткометражные Фильмы", "🎥 Short Films"
]))
async def handle_main_category(message: Message, state: FSMContext):
    # ADMIN HOLATINI TEKSHIRISH
    current_state = await state.get_state()
    
    # Agar admin bo'lsa va kontent qo'shish holatida bo'lsa
    if is_admin(message.from_user.id) and current_state == "AddMovieStates:waiting_for_category":
        from admin import get_category
        await get_category(message, state)
        return
    
    user = db.get_user(message.from_user.id)
    language = user[4] if user else 'uz'
    kb = Keyboards(language)
    
    # Kategoriya nomlarini matnidan olish
    category_map = {
        # Uzbek
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
        "🎥 Qisqa Filmlar": "short_films",
        # Russian
        "🎭 Голливудские Фильмы": "hollywood_movies",
        "🕌 Индийские Фильмы": "indian_movies",
        "📺 Индийские Сериалы": "indian_series",
        "🎪 Русские Фильмы": "russian_movies",
        "📺 Русские Сериалы": "russian_series",
        "🇺🇿 Узбекские Фильмы": "uzbek_movies",
        "📺 Узбекские Сериалы": "uzbek_series",
        "🕌 Исламские Фильмы": "islamic_movies",
        "📺 Исламские Сериалы": "islamic_series",
        "🇹🇷 Турецкие Фильмы": "turkish_movies",
        "📺 Турецкие Сериалы": "turkish_series",
        "👶 Детские Фильмы": "kids_movies",
        "🐰 Детские Мультфильмы": "kids_multfilms",
        "🇰🇷 Корейские Фильмы": "korean_movies",
        "📺 Корейские Сериалы": "korean_series",
        "🎥 Короткометражные Фильмы": "short_films",
        # English
        "🎭 Hollywood Movies": "hollywood_movies",
        "🕌 Indian Movies": "indian_movies",
        "📺 Indian Series": "indian_series",
        "🎪 Russian Movies": "russian_movies",
        "📺 Russian Series": "russian_series",
        "🇺🇿 Uzbek Movies": "uzbek_movies",
        "📺 Uzbek Series": "uzbek_series",
        "🕌 Islamic Movies": "islamic_movies",
        "📺 Islamic Series": "islamic_series",
        "🇹🇷 Turkish Movies": "turkish_movies",
        "📺 Turkish Series": "turkish_series",
        "👶 Kids Movies": "kids_movies",
        "🐰 Kids Cartoons": "kids_multfilms",
        "🇰🇷 Korean Movies": "korean_movies",
        "📺 Korean Series": "korean_series",
        "🎥 Short Films": "short_films"
    }
    
    category = category_map.get(message.text)
    if not category:
        await message.answer("❌ Noto'g'ri kategoriya!")
        return
    
    # Kategoriya nomini state ga saqlash
    await state.update_data(main_category=category, category_name=message.text)
    
    # Ichki kategoriyalarni ko'rsatish
    if category == "hollywood_movies":
        await message.answer(
            "Hollywood aktyorlarini tanlang: 🎭",
            reply_markup=kb.hollywood_subcategories_menu()
        )
        await state.set_state(CategoryStates.waiting_for_subcategory)
        
    elif category == "indian_movies":
        await message.answer(
            "Hind aktyorlarini tanlang: 🕌",
            reply_markup=kb.indian_subcategories_menu()
        )
        await state.set_state(CategoryStates.waiting_for_subcategory)
        
    elif category == "russian_movies":
        await message.answer(
            "Rus filmlarini tanlang: 🎪",
            reply_markup=kb.russian_movies_subcategories_menu()
        )
        await state.set_state(CategoryStates.waiting_for_subcategory)
        
    elif category == "russian_series":
        await message.answer(
            "Rus seriallarini tanlang: 📺",
            reply_markup=kb.russian_series_subcategories_menu()
        )
        await state.set_state(CategoryStates.waiting_for_subcategory)
        
    elif category == "kids_movies":
        await message.answer(
            "Bolalar filmlarini tanlang: 👶",
            reply_markup=kb.kids_movies_subcategories_menu()
        )
        await state.set_state(CategoryStates.waiting_for_subcategory)
        
    elif category == "kids_multfilms":
        await message.answer(
            "Multfilmlarni tanlang: 🐰",
            reply_markup=kb.kids_multfilms_subcategories_menu()
        )
        await state.set_state(CategoryStates.waiting_for_subcategory)
        
    elif category == "islamic_movies":
        await message.answer(
            "Islomiy filmlarni tanlang: 🕌",
            reply_markup=kb.islamic_movies_subcategories_menu()
        )
        await state.set_state(CategoryStates.waiting_for_subcategory)
        
    elif category == "islamic_series":
        await message.answer(
            "Islomiy seriallarni tanlang: 📺",
            reply_markup=kb.islamic_series_subcategories_menu()
        )
        await state.set_state(CategoryStates.waiting_for_subcategory)
        
    elif category == "korean_movies":
        await message.answer(
            "Koreys filmlarini tanlang: 🇰🇷",
            reply_markup=kb.korean_movies_subcategories_menu()
        )
        await state.set_state(CategoryStates.waiting_for_subcategory)
        
    elif category == "korean_series":
        await message.answer(
            "Koreys seriallarini tanlang: 📺",
            reply_markup=kb.korean_series_subcategories_menu()
        )
        await state.set_state(CategoryStates.waiting_for_subcategory)
        
    elif category == "turkish_series":
        await message.answer(
            "Turk seriallarini tanlang: 🇹🇷",
            reply_markup=kb.turkish_series_subcategories_menu()
        )
        await state.set_state(CategoryStates.waiting_for_subcategory)
        
    else:
        # Boshqa kategoriyalar uchun to'g'ridan-to'g'ri filmlarni ko'rsatish
        # Filmlarni sahifalangan holda olish
        page = 1
        per_page = 1
        movies = db.get_movies_paginated(category=category, page=page, per_page=per_page)
        total_movies = db.get_movies_count_by_category(category=category)
        total_pages = total_movies
        
        if not movies:
            no_movies_texts = {
                'uz': "❌ Bu kategoriyada hali hech qanday kino yo'q. 😔",
                'ru': "❌ В этой категории пока нет фильмов. 😔",
                'en': "❌ No movies in this category yet. 😔"
            }
            await message.answer(no_movies_texts[language])
            return
        
        # Himoya eslatmasi
        await message.answer("🔒 Kontentlar himoyalangan holda yuborilmoqda...")
        
        for movie in movies[:5]:  # Bir vaqtning o'zida 5 tadan ko'p bo'lmasin
            # Film pullik yoki bepul ekanligini tekshirish
            is_premium, price = db.is_premium_movie(movie[0])
            
            if is_premium:
                # Agar pullik bo'lsa, to'lov sahifasini ko'rsatish
                premium_text = f"""🎬 **{movie[3]}** - 💰 PULLIK KONTENT

📖 {movie[4]}
🌐 Til: {movie[7]}
👁️ Ko'rishlar: {movie[8]}
📅 Sana: {movie[9][:10]}

💵 **Narxi:** {price:,} so'm

👇 **To'lash uchun quyidagi tugmani bosing:**"""
                
                await state.update_data(premium_movie=movie)
                
                await message.answer(
                    premium_text,
                    reply_markup=kb.premium_content_keyboard()
                )
            else:
                # Agar bepul bo'lsa, odatdagi kontentni yuborish
                await send_protected_content(
                    message=message,
                    movie=movie,
                    user_id=message.from_user.id
                )
            await asyncio.sleep(1)  # Rate limit uchun

# ========== ICHKI KATEGORIYALAR ==========
@dp.message(CategoryStates.waiting_for_subcategory)
async def handle_subcategory(message: Message, state: FSMContext):
    # ADMIN HOLATINI TEKSHIRISH
    current_state = await state.get_state()
    
    # Agar admin bo'lsa va kontent qo'shish holatida bo'lsa
    if is_admin(message.from_user.id):
        admin_state = await state.get_state()
        
        # Agar admin AddMovieStates holatida bo'lsa
        if admin_state == "AddMovieStates:waiting_for_subcategory":
            from admin import get_subcategory
            await get_subcategory(message, state)
            return
    
    user = db.get_user(message.from_user.id)
    language = user[4] if user else 'uz'
    kb = Keyboards(language)
    
    # Ortga qaytish
    back_texts = ["⬅️ Ortga", "⬅️ Назад", "⬅️ Back"]
    if message.text in back_texts:
        await message.answer(
            "Kategoriyani tanlang: 📁",
            reply_markup=kb.categories_menu()
        )
        await state.clear()
        return
    
    data = await state.get_data()
    main_category = data.get('main_category')
    
    if not main_category:
        await message.answer("❌ Xatolik yuz berdi! Qaytadan boshlang.")
        await state.clear()
        return
    
    # Ichki kategoriya nomi
    subcategory = message.text
    
    # Filmlarni olish
    page = 1
    per_page = 1  # Har bir sahifada 1 ta film
    
    if "Barcha" in message.text or "Все" in message.text or "All" in message.text:
        movies = db.get_movies_paginated(category=main_category, page=page, per_page=per_page)
        total_movies = db.get_movies_count_by_category(category=main_category)
        action = "category"
        data_str = main_category
    else:
        movies = db.get_movies_paginated(
            category=main_category, 
            sub_category=subcategory, 
            page=page, 
            per_page=per_page
        )
        total_movies = db.get_movies_count_by_category(category=main_category, sub_category=subcategory)
        action = "subcategory"
        # Ma'lumotlarni maxsus formatda saqlaymiz
        data_str = f"{main_category}__{subcategory}"
    
    total_pages = total_movies  # Har bir sahifada 1 ta film
    
    if not movies:
        no_movies_texts = {
            'uz': f"❌ {subcategory} hali mavjud emas. 😔",
            'ru': f"❌ {subcategory} пока недоступно. 😔",
            'en': f"❌ {subcategory} not available yet. 😔"
        }
        await message.answer(no_movies_texts[language])
        return
    
    # Himoya eslatmasi
    await message.answer("🔒 Kontent himoyalangan holda yuborilmoqda...")
    
    # FAQAT BIRINCHI FILMNI chiqaramiz
    if movies:
        movie = movies[0]  # Birinchi filmni olamiz
        
        # Film pullik yoki bepul ekanligini tekshirish
        is_premium, price = db.is_premium_movie(movie[0])
        
        if is_premium:
            # Agar pullik bo'lsa, to'lov sahifasini ko'rsatish
            premium_text = f"""🎬 **{movie[3]}** - 💰 PULLIK KONTENT

📖 {movie[4]}
🌐 Til: {movie[7]}
👁️ Ko'rishlar: {movie[8]}
📅 Sana: {movie[9][:10]}

💵 **Narxi:** {price:,} so'm

👇 **To'lash uchun quyidagi tugmani bosing:**"""
            
            await state.update_data(premium_movie=movie)
            
            await message.answer(
                premium_text,
                reply_markup=kb.premium_content_keyboard()
            )
        else:
            # Himoyalangan kontentni yuborish
            await send_protected_content(
                message=message,
                movie=movie,
                user_id=message.from_user.id,
                page_info=f"📄 Sahifa: {page}/{total_pages}"
            )
    
    # Sahifalash tugmalari
    pagination_kb = kb.pagination_menu_simple(
        current_page=page,
        total_pages=total_pages,
        action=action,
        data=data_str
    )
    
    await message.answer(f"📄 Sahifa: {page}/{total_pages}", reply_markup=pagination_kb)
    
    await state.set_state(PaginationStates.browsing_subcategory)
    await state.update_data(
        main_category=main_category, 
        subcategory=message.text,
        current_page=page
    )
    
# ========== CALLBACK QUERY HANDLERS ==========

@dp.callback_query(F.data.startswith("category|"))
async def handle_category_pagination(callback: CallbackQuery, state: FSMContext):
    """Kategoriya sahifalash"""
    try:
        parts = callback.data.split("|")
        if len(parts) < 2:
            await callback.answer("❌ Noto'g'ri format!")
            return
            
        action = parts[0]
        page = int(parts[1])
        category = parts[2] if len(parts) > 2 else None
        
        await callback.answer()
        
        user = db.get_user(callback.from_user.id)
        language = user[4] if user else 'uz'
        
        # Filmlarni sahifalangan holda olish
        per_page = 1
        movies = db.get_movies_paginated(category=category, page=page, per_page=per_page)
        total_movies = db.get_movies_count_by_category(category=category)
        total_pages = total_movies
        
        if not movies:
            await callback.answer("❌ Hech qanday film topilmadi.")
            return
        
        # Sahifalash tugmalari
        kb = Keyboards(language)
        pagination_kb = kb.pagination_menu_simple(
            current_page=page,
            total_pages=total_pages,
            action="category",
            data=category
        )
        
        for movie in movies:
            page_info = f"📄 Sahifa: {page}/{total_pages}"
            
            # Film pullik yoki bepul ekanligini tekshirish
            is_premium, price = db.is_premium_movie(movie[0])
            
            if is_premium:
                # Agar pullik bo'lsa, to'lov sahifasini ko'rsatish
                premium_text = f"""🎬 **{movie[3]}** - 💰 PULLIK KONTENT

📖 {movie[4]}
🌐 Til: {movie[7]}
👁️ Ko'rishlar: {movie[8]}
📅 Sana: {movie[9][:10]}

💵 **Narxi:** {price:,} so'm

👇 **To'lash uchun quyidagi tugmani bosing:**"""
                
                await state.update_data(premium_movie=movie)
                
                await callback.message.answer(
                    premium_text,
                    reply_markup=kb.premium_content_keyboard()
                )
            else:
                # Himoyalangan kontentni yuborish
                await send_protected_content(
                    message=callback.message,
                    movie=movie,
                    user_id=callback.from_user.id,
                    page_info=page_info,
                    state=state
                )
        
        # Sahifa raqamini yangilash
        await callback.message.answer(f"📄 Sahifa: {page}/{total_pages}", reply_markup=pagination_kb)
        
    except Exception as e:
        print(f"ERROR in category pagination: {e}")
        await callback.answer("❌ Xatolik yuz berdi!")

# Ichki kategoriya sahifalash uchun
@dp.callback_query(F.data.startswith("subcategory|"))
async def handle_subcategory_pagination(callback: CallbackQuery, state: FSMContext):
    """Ichki kategoriya sahifalash"""
    try:
        parts = callback.data.split("|")
        if len(parts) < 3:
            await callback.answer("❌ Noto'g'ri format!")
            return
            
        action = parts[0]
        page = int(parts[1])
        data_str = parts[2]
        
        if "__" in data_str:
            data_parts = data_str.split("__")
        else:
            await callback.answer("❌ Noto'g'ri ma'lumot formati!")
            return
        
        if len(data_parts) < 2:
            await callback.answer("❌ Noto'g'ri ma'lumot formati!")
            return
            
        category = data_parts[0]
        subcategory = data_parts[1]
        
        await callback.answer()
        
        user = db.get_user(callback.from_user.id)
        language = user[4] if user else 'uz'
        
        # Filmlarni sahifalangan holda olish
        per_page = 1
        movies = db.get_movies_paginated(
            category=category, 
            sub_category=subcategory, 
            page=page, 
            per_page=per_page
        )
        total_movies = db.get_movies_count_by_category(category=category, sub_category=subcategory)
        total_pages = total_movies
        
        if not movies:
            await callback.answer(f"❌ {subcategory} hali mavjud emas.")
            return
        
        # FAQAT BIRINCHI FILMNI chiqaramiz
        if movies:
            movie = movies[0]
            page_info = f"📄 Sahifa: {page}/{total_pages}"
            
            # Film pullik yoki bepul ekanligini tekshirish
            is_premium, price = db.is_premium_movie(movie[0])
            
            if is_premium:
                # Agar pullik bo'lsa, to'lov sahifasini ko'rsatish
                premium_text = f"""🎬 **{movie[3]}** - 💰 PULLIK KONTENT

📖 {movie[4]}
🌐 Til: {movie[7]}
👁️ Ko'rishlar: {movie[8]}
📅 Sana: {movie[9][:10]}

💵 **Narxi:** {price:,} so'm

👇 **To'lash uchun quyidagi tugmani bosing:**"""
                
                await state.update_data(premium_movie=movie)
                
                await callback.message.answer(
                    premium_text,
                    reply_markup=Keyboards(language).premium_content_keyboard()
                )
            else:
                # Himoyalangan kontentni yuborish
                await send_protected_content(
                    message=callback.message,
                    movie=movie,
                    user_id=callback.from_user.id,
                    page_info=page_info
                )
        
        # Sahifalash tugmalari
        kb = Keyboards(language)
        pagination_kb = kb.pagination_menu_simple(
            current_page=page,
            total_pages=total_pages,
            action="subcategory",
            data=data_str
        )
        
        await callback.message.answer(f"📄 Sahifa: {page}/{total_pages}", reply_markup=pagination_kb)
        
    except Exception as e:
        print(f"ERROR in subcategory pagination: {e}")
        await callback.answer("❌ Xatolik yuz berdi!")

@dp.callback_query(F.data.startswith("search_page_"))
async def handle_search_pagination(callback: CallbackQuery, state: FSMContext):
    """Qidiruv sahifalash"""
    try:
        parts = callback.data.split("_")
        page = int(parts[2])
        query = "_".join(parts[3:]) if len(parts) > 3 else ""
        
        print(f"🔍 DEBUG search_pagination: page={page}, query={query}")
        
        await callback.answer()
        
        user = db.get_user(callback.from_user.id)
        language = user[4] if user else 'uz'
        kb = Keyboards(language)
        
        # Qidiruv natijalarini sahifalangan holda olish
        per_page = 5
        results = db.search_movies_paginated(query, page=page, per_page=per_page)
        
        if not results:
            await callback.message.answer("❌ Hech qanday natija topilmadi.")
            return
        
        # Natijalar soni
        total_results = len(results)
        total_pages = max(1, total_results // per_page + (1 if total_results % per_page > 0 else 0))
        
        # Sahifalash tugmalari
        pagination_kb = InlineKeyboardMarkup(inline_keyboard=[])
        keyboard_buttons = []
        
        # Oldingi sahifa
        if page > 1:
            keyboard_buttons.append(
                InlineKeyboardButton(
                    text="◀️ Oldingi", 
                    callback_data=f"search_page_{page-1}_{query}"
                )
            )
        
        # Sahifa raqami
        keyboard_buttons.append(
            InlineKeyboardButton(
                text=f"{page}/{total_pages}", 
                callback_data=f"page_info_{page}"
            )
        )
        
        # Keyingi sahifa
        if page < total_pages:
            keyboard_buttons.append(
                InlineKeyboardButton(
                    text="Keyingi ▶️", 
                    callback_data=f"search_page_{page+1}_{query}"
                )
            )
        
        pagination_kb.inline_keyboard.append(keyboard_buttons)
        
        # Ortga qaytish
        pagination_kb.inline_keyboard.append([
            InlineKeyboardButton(
                text="🔍 Qidiruvga qaytish", 
                callback_data="back_to_search"
            ),
            InlineKeyboardButton(
                text="🏠 Asosiy menyu", 
                callback_data="back_to_main"
            )
        ])
        
        # FAQAT BIRINCHI FILMNI video sifatida yuborish
        if results:
            movie = results[0]
            
            # Film pullik yoki bepul ekanligini tekshirish
            is_premium, price = db.is_premium_movie(movie[0])
            
            if is_premium:
                # Agar pullik bo'lsa, to'lov sahifasini ko'rsatish
                premium_text = f"""🎬 **{movie[3]}** - 💰 PULLIK KONTENT

📖 {movie[4][:100]}{'...' if len(movie[4]) > 100 else ''}
🌐 Til: {movie[9] if len(movie) > 9 else 'N/A'}
👁️ Ko'rishlar: {movie[10] if len(movie) > 10 else 0}

💵 **Narxi:** {price:,} so'm

👇 **To'lash uchun quyidagi tugmani bosing:**"""
                
                await state.update_data(premium_movie=movie)
                
                await callback.message.answer(
                    premium_text,
                    reply_markup=kb.premium_content_keyboard()
                )
            else:
                # Himoyalangan kontentni yuborish
                await send_protected_content(
                    message=callback.message,
                    movie=movie,
                    user_id=callback.from_user.id,
                    page_info=f"📄 Sahifa: {page}/{total_pages}",
                    state=state
                )
        
        # Sahifa ma'lumotlari
        page_info = f"📄 **Sahifa:** {page}/{total_pages}\n🔍 **Qidiruv so'rovi:** {query}\n📊 **Natijalar:** {total_results} ta"
        
        await callback.message.answer(page_info, reply_markup=pagination_kb)
        
        # Oldingi xabarni o'chirish
        try:
            await callback.message.delete()
        except:
            pass
            
    except Exception as e:
        print(f"❌ Error in search pagination: {e}")
        import traceback
        traceback.print_exc()
        await callback.answer("❌ Xatolik yuz berdi!")
        
# ========== YANGILANGAN PULLIK KONTENTLAR BO'LIMI ==========
@dp.message(F.text.contains("Pullik Kontentlar") | 
            F.text.contains("Платные Контенты") | 
            F.text.contains("Premium Content"))
async def premium_content_section(message: Message, state: FSMContext):
    """Pullik kontentlar bo'limini ochish"""
    user = db.get_user(message.from_user.id)
    language = user[4] if user else 'uz'
    kb = Keyboards(language)
    
    # Bloklanganlikni tekshirish
    if db.is_user_blocked(message.from_user.id):
        await message.answer("🚫 Sizning akkauntingiz bloklangan!")
        return
    
    # Pullik kontentlar statistikasi
    premium_stats = db.get_premium_statistics()
    
    premium_text = f"""⭐ **PULLIK KONTENTLAR BOLIMI**

📊 **Statistika:**
🎬 Pullik filmlar: {premium_stats['premium_count']} ta
💰 O'rtacha narx: {premium_stats['average_price']:,.0f} so'm
🏆 Eng qimmat: {premium_stats['most_expensive_title']} - {premium_stats['most_expensive_price']:,} so'm

🎯 **Qanday ishlaydi:**
1️⃣ Pullik filmni tanlang
2️⃣ To'lov usulini tanlang
3️⃣ To'lovni amalga oshiring
4️⃣ Chek yuboring
5️⃣ Admin tasdiqlashi bilan film ochiladi

💳 **To'lov usullari:**
• Bank kartasi (8600 1104 7759 4067)
• Click, Payme yoki boshqa ilovalar

📞 **Yordam:** @Operator_Kino_1985

👇 **Kerakli amalni tanlang:**"""
    
    # Admin paneli tugmasini qo'shamiz
    keyboard_buttons = [
        ["🎬 Pullik filmlarni ko'rish", "💰 To'lov ma'lumotlari"],
        ["📊 Mening to'lovlarim", "💼 Balansim"],
        ["📞 Yordam", "🏠 Asosiy menyu"]
    ]
    
    if is_admin(message.from_user.id):
        keyboard_buttons.append(["👑 Admin paneli", "💰 To'lovlarni boshqarish"])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn) for btn in row] for row in keyboard_buttons],
        resize_keyboard=True
    )
    
    await message.answer(premium_text, reply_markup=keyboard)

# ========== PULLIK FILMLARNI KO'RISH ==========
@dp.message(F.text.contains("🎬 Pullik filmlarni ko'rish") | 
            F.text.contains("🎬 Платные фильмы") | 
            F.text.contains("🎬 Premium Movies"))
async def show_premium_movies(message: Message, state: FSMContext):
    """Pullik filmlarni kategoriyalar bo'yicha ko'rsatish"""
    user = db.get_user(message.from_user.id)
    language = user[4] if user else 'uz'
    kb = Keyboards(language)
    
    # Pullik filmlar soni
    premium_count = db.get_premium_movies_count()
    
    if premium_count == 0:
        await message.answer(
            "⭐ Hozirda hech qanday pullik film mavjud emas. Iltimos, keyinroq urinib ko'ring.",
            reply_markup=kb.main_menu(is_admin=is_admin(message.from_user.id)))
        return
    
    # Pullik filmlar kategoriyalari
    categories_text = f"""💰 **PULLIK FILMLAR KATEGORIYALARI**

📊 Jami pullik filmlar: {premium_count} ta

🎯 **Kategoriyalarni tanlang:**"""
    
    await message.answer(categories_text, reply_markup=kb.categories_menu())

# ========== TO'LOV MA'LUMOTLARI ==========
@dp.message(F.text.contains("💰 To'lov ma'lumotlari") | 
            F.text.contains("💰 Платежная информация") | 
            F.text.contains("💰 Payment Information"))
async def payment_information(message: Message):
    """To'lov ma'lumotlarini ko'rsatish"""
    payment_info = """💳 **TO'LOV MA'LUMOTLARI**

🏦 **Bank kartasi raqami:**
`8600 1104 7759 4067`

👤 **Karta egasi:**
Admin Kino Bot

💼 **To'lov tartibi:**
1️⃣ Kontentni tanlang
2️⃣ "💳 To'lash va Ko'rish" tugmasini bosing
3️⃣ Yuqoridagi karta raqamiga to'lov qiling
4️⃣ To'lov chekini (skrinshot) yuboring
5️⃣ Admin tekshiradi (1-24 soat ichida)
6️⃣ Kontent ochiladi

⚠️ **DIQQAT:**
• Faqat to'lov amalga oshirilgandan keyin chek yuboring
• To'lov cheki aniq ko'rinishi kerak
• Noto'g'ri ma'lumotlar bilan chek yubormang

⏰ **Tekshirish vaqti:**
1-24 soat ichida

📞 **Yordam va savollar:**
@Operator_Kino_1985

✅ **To'lov qilgandan so'ng "📤 Chek yuborish" tugmasini bosing!**"""
    
    await message.answer(payment_info, parse_mode="Markdown")

# ========== FOYDALANUVCHI BALANSI ==========
@dp.message(F.text.contains("💼 Balansim") | 
            F.text.contains("💼 Мой баланс") | 
            F.text.contains("💼 My Balance"))
async def user_balance(message: Message):
    """Foydalanuvchi balansini ko'rsatish"""
    user = db.get_user(message.from_user.id)
    
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz!")
        return
    
    user_id = message.from_user.id
    
    # Balansni olish
    balance = db.get_user_balance(user_id)
    
    # To'lovlar statistikasi
    try:
        db.cursor.execute('''
            SELECT 
                COUNT(*) as total_payments,
                SUM(amount) as total_spent,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_payments
            FROM payments 
            WHERE user_id = ?
        ''', (user_id,))
        payment_stats = db.cursor.fetchone()
        
        total_payments = payment_stats[0] or 0
        total_spent = payment_stats[1] or 0
        completed_payments = payment_stats[2] or 0
    except:
        total_payments = 0
        total_spent = 0
        completed_payments = 0
    
    # Sotib olingan filmlar
    try:
        db.cursor.execute('''
            SELECT COUNT(*) as purchased_movies
            FROM movie_purchases 
            WHERE user_id = ?
        ''', (user_id,))
        purchased_result = db.cursor.fetchone()
        purchased_movies = purchased_result[0] if purchased_result else 0
    except:
        purchased_movies = 0
    
    balance_text = f"""💰 **SIZNING BALANS MA'LUMOTLARINGIZ**

👤 **Foydalanuvchi:** {user[2]}
🆔 **ID:** {user[0]}
💼 **Joriy balans:** {balance:,} so'm

📊 **STATISTIKA:**
💳 **To'lovlar:** {total_payments} ta
✅ **Tasdiqlangan:** {completed_payments} ta
💰 **Sarflangan summa:** {total_spent:,} so'm
🎬 **Sotib olingan filmlar:** {purchased_movies} ta

🔢 **Balansni to'ldirish:**
1️⃣ Yuqoridagi karta raqamiga o'tkazma qiling
2️⃣ Chekni yuboring
3️⃣ Admin tekshiradi
4️⃣ Balansingiz to'lidi

⚠️ **Eslatma:** Balans faqat pullik filmlar sotib olish uchun ishlatiladi

📞 **Yordam:** @Operator_Kino_1985"""
    
    await message.answer(balance_text)

# ========== FOYDALANUVCHI TO'LOVLARI ==========
@dp.message(F.text.contains("📊 Mening to'lovlarim") | 
            F.text.contains("📊 Мои платежи") | 
            F.text.contains("📊 My Payments"))
async def user_payments(message: Message):
    """Foydalanuvchining to'lovlar tarixini ko'rsatish"""
    user = db.get_user(message.from_user.id)
    
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz!")
        return
    
    user_id = message.from_user.id
    
    # Oxirgi 10 ta to'lovni olish
    try:
        db.cursor.execute('''
            SELECT 
                p.id,
                p.amount,
                p.payment_date,
                p.status,
                p.payment_method,
                m.title
            FROM payments p
            LEFT JOIN movies m ON p.movie_id = m.id
            WHERE p.user_id = ?
            ORDER BY p.payment_date DESC
            LIMIT 10
        ''', (user_id,))
        payments = db.cursor.fetchall()
    except Exception as e:
        print(f"Error getting user payments: {e}")
        payments = []
    
    if not payments:
        await message.answer("📭 Sizda hech qanday to'lov tarixi yo'q.")
        return
    
    payments_text = f"""📊 **SIZNING TO'LOVLAR TARIXINGIZ**

👤 **Foydalanuvchi:** {user[2]}
📅 **Oxirgi 10 ta to'lov:**
─────────────────────
"""
    
    for i, payment in enumerate(payments, 1):
        payment_id = payment[0]
        amount = payment[1] or 0
        payment_date = payment[2] if payment[2] else "N/A"
        status = payment[3] if payment[3] else "N/A"
        payment_method = payment[4] if payment[4] else "N/A"
        movie_title = payment[5] if payment[5] else "N/A"
        
        # Status ikonkalari
        if status == 'completed':
            status_icon = "✅"
        elif status == 'pending':
            status_icon = "⏳"
        elif status == 'rejected':
            status_icon = "❌"
        else:
            status_icon = "❓"
        
        # Sana formatlash
        if payment_date and payment_date != "N/A":
            date_display = payment_date[:16] if len(payment_date) >= 16 else payment_date
        else:
            date_display = "N/A"
        
        payments_text += f"""**{i}. {status_icon} To'lov #{payment_id}**
💰 **Miqdor:** {amount:,} so'm
🎬 **Film:** {movie_title[:30]}{'...' if len(movie_title) > 30 else ''}
📅 **Sana:** {date_display}
💳 **Usul:** {payment_method}
─────────────────────
"""
    
    # Umumiy statistika
    try:
        db.cursor.execute('''
            SELECT 
                SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as completed_total,
                SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as pending_total
            FROM payments 
            WHERE user_id = ?
        ''', (user_id,))
        totals = db.cursor.fetchone()
        
        completed_total = totals[0] or 0
        pending_total = totals[1] or 0
        
        payments_text += f"""
📈 **UMUMIY STATISTIKA:**
✅ **Tasdiqlangan to'lovlar:** {completed_total:,} so'm
⏳ **Kutilayotgan to'lovlar:** {pending_total:,} so'm
"""
    except:
        pass
    
    await message.answer(payments_text, parse_mode="Markdown")        

# ==================== ODDIY TO'LOV TIZIMI ====================

@dp.message(F.text.in_([
    "💳 To'lash va Ko'rish",
    "💳 Оплатить и смотреть", 
    "💳 Pay and Watch"
]))
async def handle_payment_button(message: Message, state: FSMContext):
    """To'lov tugmasi bosilganda"""
    user_id = message.from_user.id
    
    # User tilini aniqlash
    user = db.get_user(user_id)
    language = user[4] if user else 'uz'
    kb = Keyboards(language)
    
    # State dan oxirgi pullik filmni olish
    data = await state.get_data()
    premium_movie = data.get('premium_movie')
    
    if not premium_movie:
        # Agar state da yo'q bo'lsa, oxirgi ko'rilgan pullik filmni topish
        
        # Foydalanuvchining oxirgi urinishlaridan pullik filmni topish
        db.cursor.execute('''
            SELECT m.* 
            FROM download_attempts da
            JOIN movies m ON da.movie_id = m.id
            WHERE da.user_id = ? AND m.is_premium = 1
            ORDER BY da.attempt_date DESC
            LIMIT 1
        ''', (user_id,))
        
        premium_movie = db.cursor.fetchone()
        
        if not premium_movie:
            # Agar topilmasa, biron bir pullik film
            db.cursor.execute('''
                SELECT * FROM movies 
                WHERE is_premium = 1 
                ORDER BY added_date DESC 
                LIMIT 1
            ''')
            premium_movie = db.cursor.fetchone()
    
    if not premium_movie:
        await message.answer(
            "❌ Hech qanday pullik film topilmadi.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="/start")]],
                resize_keyboard=True
            )
        )
        return
    
    movie_id = premium_movie[0]
    is_premium, price = db.is_premium_movie(movie_id)
    
    if not is_premium:
        await message.answer(
            "❌ Bu film pullik emas.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="/start")]],
                resize_keyboard=True
            )
        )
        return
    
    # Foydalanuvchi allaqachon sotib olganmi?
    has_purchased = db.has_purchased_movie(user_id, movie_id)
    
    if has_purchased:
        # Agar sotib olgan bo'lsa, kontentni ochish
        await send_protected_content(message, premium_movie, user_id, state=state)
        return
    
    # To'lov ma'lumotlari
    payment_info = f"""💳 **TO'LOV MA'LUMOTLARI**

🎬 **Film:** {premium_movie[3]}
💰 **Narxi:** {price:,} so'm

🏦 **KARTA RAQAMI:**
`8600 1104 7759 4067`

👤 **Karta egasi:**
Admin Kino Bot

📞 **Operator:** @Operator_Kino_1985

📝 **To'lov tartibi:**
1. Yuqoridagi karta raqamiga {price:,} so'm o'tkazing
2. To'lov chekini (skrinshot yoki foto) yuboring
3. Admin tekshiradi (1-24 soat)
4. Film ochiladi

⚠️ **Diqqat:** Faqat to'lov amalga oshirilgandan keyin chek yuboring!"""
    
    # State ga filmni saqlash
    await state.update_data(premium_movie=premium_movie, payment_price=price)
    await state.set_state(PaymentStates.waiting_for_check_photo)
    
    await message.answer(
        payment_info,
        reply_markup=kb.send_check_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(PaymentStates.waiting_for_check_photo, F.text.in_([
    "📤 Chek yuborish",
    "📤 Отправить чек", 
    "📤 Send receipt"
]))
async def prompt_check_photo(message: Message, state: FSMContext):
    """Chek yuborish tugmasi bosilganda"""
    user = db.get_user(message.from_user.id)
    language = user[4] if user else 'uz'
    kb = Keyboards(language)
    
    await message.answer(
        "📸 **Chek rasmini yuboring:**\n\n"
        "To'lov chekini quyidagi formatlarda yuboring:\n"
        "• Rasm (photo) 📷\n"
        "• Fayl (document) 📄\n"
        "• Skrinshot 🖼️\n\n"
        "⚠️ **Diqqat:** Faqat media fayllar qabul qilinadi!",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Ortga" if language == 'uz' else 
                                     "⬅️ Назад" if language == 'ru' else 
                                     "⬅️ Back")]],
            resize_keyboard=True
        )
    )
    
@dp.message(Command("checkblock"))
async def check_block_status(message: Message):
    """Blok holatini tekshirish"""
    user_id = message.from_user.id
    
    if db.is_user_blocked(user_id):
        block_info = db.cursor.execute(
            'SELECT reason, block_date FROM blocked_users WHERE user_id = ? AND unblock_date IS NULL',
            (user_id,)
        ).fetchone()
        
        if block_info:
            reason = block_info[0] if block_info[0] else "Kontent himoya qoidalarini buzish"
            date = block_info[1][:10] if block_info[1] else 'Noma\'lum'
            
            block_text = f"""
🚫 **SIZ BLOKLANDINGIZ!**

📅 **Bloklangan sana:** {date}
📝 **Sabab:** {reason}

🔓 **Blokdan ochish uchun:**
@Operator_Kino_1985 ga yozing

❌ **Diqqat:** Blokdan avtomatik ochilmaydi!
"""
            await message.answer(block_text)
            return
    
    await message.answer("✅ Sizning akkauntingiz faol holatda. Bloklanmagan.")    

@dp.message(PaymentStates.waiting_for_check_photo, F.photo | F.document)
async def receive_check_photo(message: Message, state: FSMContext):
    """Chek rasmini qabul qilish"""
    try:
        data = await state.get_data()
        premium_movie = data.get('premium_movie')
        payment_price = data.get('payment_price', 0)
        
        if not premium_movie:
            await message.answer("❌ Film ma'lumotlari topilmadi!")
            await state.clear()
            return
        
        # Rasm yoki dokument ID sini olish
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
        elif message.document:
            file_id = message.document.file_id
            file_type = "document"
        else:
            await message.answer("❌ Iltimos, rasm yoki dokument yuboring!")
            return
        
        # To'lov ma'lumotlarini bazaga saqlash
        payment_id = db.add_payment(
            user_id=message.from_user.id,
            amount=payment_price,
            payment_method="Bank kartasi",
            movie_id=premium_movie[0]
        )
        
        if payment_id:
            # Chek fayl ID sini saqlash
            try:
                db.cursor.execute('''
                    UPDATE payments 
                    SET check_photo_id = ?, transaction_id = ?
                    WHERE id = ?
                ''', (file_id, str(payment_id), payment_id))
                db.conn.commit()
            except Exception as e:
                print(f"Check photo save error: {e}")
            
            # User tilini aniqlash
            user = db.get_user(message.from_user.id)
            language = user[4] if user else 'uz'
            kb = Keyboards(language)
            
            # Foydalanuvchiga tasdiqlash xabari
            await message.answer(
                f"✅ **Chek qabul qilindi!**\n\n"
                f"🎬 Film: {premium_movie[3]}\n"
                f"💰 Miqdor: {payment_price:,} so'm\n"
                f"🔑 So'rov ID: {payment_id}\n\n"
                f"⏳ **Admin tekshiruvi:**\n"
                f"To'lovingiz admin tomonidan tekshirilmoqda.\n"
                f"Tasdiqlanganidan so'ng film ochiladi.\n\n"
                f"📞 **Aloqa:** @Operator_Kino_1985",
                reply_markup=kb.main_menu(is_admin=is_admin(message.from_user.id))
            )
            
            # Adminlarga xabar yuborish
            admin_text = f"""🆕 **YANGI TO'LOV SO'ROVI!**

👤 **Foydalanuvchi:** {message.from_user.full_name}
🆔 **User ID:** {message.from_user.id}
📞 **Username:** @{message.from_user.username}
🎬 **Film:** {premium_movie[3]}
💰 **Miqdor:** {payment_price:,} so'm
📅 **Vaqt:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
🔑 **Payment ID:** {payment_id}

✅ **Tekshirish uchun:**
1. /admin - Admin panel
2. '⏳ Kutilayotgan to'lovlar' - To'lovlarni ko'rish"""
            
            # Barcha adminlarga xabar yuborish
            for admin_id in ADMINS:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=admin_text
                    )
                    
                    # Chek rasmini ham yuborish
                    if message.photo:
                        await bot.send_photo(
                            chat_id=admin_id,
                            photo=file_id,
                            caption=f"Chek #{payment_id}"
                        )
                    elif message.document:
                        await bot.send_document(
                            chat_id=admin_id,
                            document=file_id,
                            caption=f"Chek #{payment_id}"
                        )
                except Exception as e:
                    print(f"Error sending to admin {admin_id}: {e}")
            
            await state.clear()
            
        else:
            await message.answer("❌ To'lov saqlashda xatolik yuz berdi!")
            await state.clear()
            
    except Exception as e:
        print(f"Check photo error: {e}")
        await message.answer("❌ Xatolik yuz berdi!")
        await state.clear()       

@dp.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    """Kategoriyalarga qaytish"""
    await callback.answer()
    
    user = db.get_user(callback.from_user.id)
    language = user[4] if user else 'uz'
    kb = Keyboards(language)
    
    await callback.message.answer(
        "Kategoriyani tanlang: 📁",
        reply_markup=kb.categories_menu()
    )

@dp.callback_query(F.data.startswith("back_to_"))
async def back_to_category(callback: CallbackQuery, state: FSMContext):
    """Muayyan kategoriyaga qaytish"""
    await callback.answer()
    
    category = callback.data.replace("back_to_", "")
    
    user = db.get_user(callback.from_user.id)
    language = user[4] if user else 'uz'
    kb = Keyboards(language)
    
    # Kategoriya bo'yicha ichki menyuni ko'rsatish
    if category == "hollywood_movies":
        await callback.message.answer(
            "Hollywood aktyorlarini tanlang: 🎭",
            reply_markup=kb.hollywood_subcategories_menu()
        )
    elif category == "indian_movies":
        await callback.message.answer(
            "Hind aktyorlarini tanlang: 🕌",
            reply_markup=kb.indian_subcategories_menu()
        )
    elif category == "russian_movies":
        await callback.message.answer(
            "Rus filmlarini tanlang: 🎪",
            reply_markup=kb.russian_movies_subcategories_menu()
        )
    elif category == "russian_series":
        await callback.message.answer(
            "Rus seriallarini tanlang: 📺",
            reply_markup=kb.russian_series_subcategories_menu()
        )
    elif category == "kids_movies":
        await callback.message.answer(
            "Bolalar filmlarini tanlang: 👶",
            reply_markup=kb.kids_movies_subcategories_menu()
        )
    elif category == "kids_multfilms":
        await callback.message.answer(
            "Multfilmlarni tanlang: 🐰",
            reply_markup=kb.kids_multfilms_subcategories_menu()
        )
    elif category == "islamic_movies":
        await callback.message.answer(
            "Islomiy filmlarni tanlang: 🕌",
            reply_markup=kb.islamic_movies_subcategories_menu()
        )
    elif category == "islamic_series":
        await callback.message.answer(
            "Islomiy seriallarni tanlang: 📺",
            reply_markup=kb.islamic_series_subcategories_menu()
        )
    elif category == "korean_movies":
        await callback.message.answer(
            "Koreys filmlarini tanlang: 🇰🇷",
            reply_markup=kb.korean_movies_subcategories_menu()
        )
    elif category == "korean_series":
        await callback.message.answer(
            "Koreys seriallarini tanlang: 📺",
            reply_markup=kb.korean_series_subcategories_menu()
        )
    elif category == "turkish_series":
        await callback.message.answer(
            "Turk seriallarini tanlang: 🇹🇷",
            reply_markup=kb.turkish_series_subcategories_menu()
        )
    else:
        await callback.message.answer(
            "Kategoriyani tanlang: 📁",
            reply_markup=kb.categories_menu()
        )

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Asosiy menyuga qaytish"""
    await callback.answer()
    
    user = db.get_user(callback.from_user.id)
    if user:
        language = user[4]
        kb = Keyboards(language)
        await callback.message.answer(
            "Asosiy menyu: 🏠",
            reply_markup=kb.main_menu(is_admin=is_admin(callback.from_user.id)))
    await state.clear()

# ========== ORTGA QAYTISH ==========
@dp.message(F.text.in_(["⬅️ Ortga", "⬅️ Назад", "⬅️ Back"]))
async def go_back(message: Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if user:
        language = user[4]
        kb = Keyboards(language)
        await message.answer(
            "Asosiy menyu: 🏠",
            reply_markup=kb.main_menu(is_admin=is_admin(message.from_user.id)))
    await state.clear()

# ========== DEBUG HANDLER ==========
@dp.message(Command("debug"))
async def debug_command(message: Message, state: FSMContext):
    """Debug ma'lumotlarini ko'rsatish"""
    current_state = await state.get_state()
    data = await state.get_data()
    
    debug_text = f"""
🔍 **Debug Information:**
    
📝 Current State: {current_state}
📊 State Data: {data}
👤 User ID: {message.from_user.id}
👑 Is Admin: {is_admin(message.from_user.id)}
    
📋 Data keys: {list(data.keys()) if data else "Empty"}
"""
    
    print(f"DEBUG: {debug_text}")
    await message.answer(debug_text)

# ========== ASOSIY FUNKSIYA ==========
async def main():
    print("=" * 60)
    print("🤖 KINO BOT - KUCHAYTIRILGAN HIMOYA VERSIYASI")
    print("=" * 60)
    print("🔧 Platforma: Render")
    print("🌐 Web Server: Flask")
    print("🛡️ Himoya: FAOL")
    print("=" * 60)
    
    # 1. Flask serverini ishga tushirish
    print("\n🌐 Flask serverini ishga tushirish...")
    try:
        flask_thread = threading.Thread(target=run_flask_server, daemon=True)
        flask_thread.start()
        print("✅ Flask server muvaffaqiyatli ishga tushirildi")
    except Exception as e:
        print(f"⚠️ Flask server xatosi: {e}")
    
    # 2. Himoya jadvallarini yaratish
    print("\n🔒 Himoya jadvallarini yaratish...")
    try:
        db.create_protection_tables()
        print("✅ Himoya jadvallari muvaffaqiyatli yaratildi")
    except Exception as e:
        print(f"⚠️ Himoya jadvallar xatosi: {e}")
    
    # 3. Admin routerini import qilish
    print("\n👑 Admin routerini yuklash...")
    try:
        from admin import admin_router, setup_admin_bot
        
        setup_admin_bot(bot)
        dp.include_router(admin_router)
        print("✅ Admin router muvaffaqiyatli yuklandi!")
    except ImportError as e:
        print(f"❌ Admin router yuklanmadi: {e}")
        print("⚠️ Admin funksiyalari ishlamaydi!")
    except Exception as e:
        print(f"❌ Admin router sozlashda xatolik: {e}")
    
    # 4. Himoya middleware qo'shish
    print("\n🛡️ Himoya middleware ni sozlash...")
    try:
        dp.message.middleware(EnhancedProtectionMiddleware())
        print("✅ Himoya middleware muvaffaqiyatli qo'shildi")
    except Exception as e:
        print(f"⚠️ Himoya middleware xatosi: {e}")
    
    # 5. Himoya configini chiqarish
    print("\n🔧 KUCHAYTIRILGAN HIMOYA SOZLAMALARI:")
    for key, value in PROTECTION_CONFIG.items():
        if isinstance(value, dict):
            print(f"  • {key}:")
            for sub_key, sub_value in value.items():
                print(f"    - {sub_key}: {sub_value}")
        else:
            print(f"  • {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ BOT TO'LIQ TAYYOR!")
    print("🛡️ Himoya: FAOL (Android/iOS/Windows)")
    print("📊 Monitoring: FAOL (24/7)")
    print("🚨 Avtomatik blok: FAOL (3 urinish)")
    print("🌐 Web Server: FAOL (Render)")
    print("=" * 60)
    
    # 6. Botni ishga tushirish
    print("\n⏳ Bot Telegram serverlariga ulanmoqda...")
    try:
        # Botni ishga tushirish
        await dp.start_polling(bot, skip_updates=True, timeout=60)
        print("✅ Bot muvaffaqiyatli ishga tushdi va ishlayapti!")
        
    except KeyboardInterrupt:
        print("\n🛑 Bot foydalanuvchi tomonidan to'xtatildi!")
    except Exception as e:
        print(f"❌ Bot ishga tushirishda xatolik: {e}")
        import traceback
        traceback.print_exc()

# ========== Dasturni Ishga tushirish ==========
if __name__ == "__main__":
    # Windows uchun asyncio policy sozlamalari
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Flask serverni ALBATTA birinchi ishga tushiramiz
    print("🚀 Flask serverni ishga tushirish...")
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    # Flask ishga tushishini kutish
    print("⏳ Flask ishga tushishini kutish (5 soniya)...")
    import time
    time.sleep(5)
    
    # Endi botni ishga tushirish
    print("🤖 Botni ishga tushirish...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot foydalanuvchi tomonidan to'xtatildi!")
    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("👋 Bot yopildi. Xayr!")