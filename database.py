import sqlite3
import logging
from datetime import datetime, timedelta
import os
import shutil
import secrets

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('kino_bot.db', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Logging
        self.logger = logging.getLogger('database')
        
        # Jadvallarni yaratish
        self.create_tables()
        
        # Jadvalni yangilash (agar kerak bo'lsa) - bu funksiyani qo'shamiz
        self.upgrade_movies_table()
        
        # Yangi: Database schema ni to'liq yangilash
        self.update_database_schema()
        
        print("✅ Database initialized successfully!")
    
    def create_tables(self):
        """Barcha kerakli jadvallarni yaratish"""
        try:
            # Users jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    language TEXT DEFAULT 'uz',
                    registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    is_admin INTEGER DEFAULT 0,
                    balance REAL DEFAULT 0,
                    subscription_expires TIMESTAMP,
                    UNIQUE(user_id)
                )
            ''')
            
            # Movies jadvali (TO'G'RILANGAN - discount_price va is_discounted qo'shildi)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    main_category TEXT NOT NULL,
                    sub_category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    file_id TEXT NOT NULL,
                    file_type TEXT,
                    language TEXT DEFAULT 'uz',
                    views INTEGER DEFAULT 0,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    added_by INTEGER,
                    is_premium INTEGER DEFAULT 0,
                    price INTEGER DEFAULT 0,
                    discount_price INTEGER,
                    is_discounted INTEGER DEFAULT 0,
                    quality TEXT DEFAULT 'HD',
                    release_year INTEGER,
                    duration TEXT,
                    file_size INTEGER,
                    rating REAL DEFAULT 0,
                    total_ratings INTEGER DEFAULT 0,
                    FOREIGN KEY (added_by) REFERENCES users(user_id)
                )
            ''')
            
            # Blocked users jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocked_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    blocked_by INTEGER NOT NULL,
                    reason TEXT,
                    block_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    unblock_date TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (blocked_by) REFERENCES users(user_id),
                    CHECK (unblock_date IS NULL OR unblock_date > block_date)
                )
            ''')
            
            # Limits jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    limit_type TEXT NOT NULL,
                    limit_value REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_by INTEGER,
                    approved_date TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (approved_by) REFERENCES users(user_id),
                    CHECK (limit_value >= 0)
                )
            ''')
            
            # Payments jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    movie_id INTEGER,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'UZS',
                    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    payment_method TEXT,
                    status TEXT DEFAULT 'pending',
                    transaction_id TEXT UNIQUE,
                    check_photo_id TEXT,
                    processed_by INTEGER,
                    process_date TIMESTAMP,
                    payment_type TEXT DEFAULT 'movie_purchase',
                    subscription_days INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (movie_id) REFERENCES movies(id),
                    FOREIGN KEY (processed_by) REFERENCES users(user_id),
                    CHECK (amount >= 0)
                )
            ''')
            
            # Subscriptions jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subscription_type TEXT NOT NULL,
                    price REAL NOT NULL,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP NOT NULL,
                    status TEXT DEFAULT 'active',
                    auto_renew INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    CHECK (price >= 0),
                    CHECK (end_date > start_date)
                )
            ''')
            
            # Movie purchases jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS movie_purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    movie_id INTEGER NOT NULL,
                    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    price_paid REAL NOT NULL,
                    payment_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (movie_id) REFERENCES movies(id),
                    FOREIGN KEY (payment_id) REFERENCES payments(id),
                    UNIQUE(user_id, movie_id),
                    CHECK (price_paid >= 0)
                )
            ''')
            
            # Ratings jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    movie_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                    comment TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (movie_id) REFERENCES movies(id),
                    UNIQUE(user_id, movie_id)
                )
            ''')
            
            # Favorites jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    movie_id INTEGER NOT NULL,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (movie_id) REFERENCES movies(id),
                    UNIQUE(user_id, movie_id)
                )
            ''')
            
            # Himoya jadvallarini yaratish
            self.create_protection_tables()
            
            self.conn.commit()
            print("✅ All tables created successfully!")
            
        except Exception as e:
            self.logger.error(f"Jadvallarni yaratishda xatolik: {e}")
            raise
            
    def upgrade_movies_table(self):
        """Movies jadvalini yangi ustunlar bilan yangilash"""
        try:
            # Tekshirish: jadval mavjudmi?
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
            table_exists = self.cursor.fetchone()
            
            if not table_exists:
                print("ℹ️ Movies jadvali mavjud emas, allaqachon yaratilgan")
                return
            
            # Tekshirish: ustunlar mavjudmi?
            self.cursor.execute("PRAGMA table_info(movies)")
            columns = {col[1] for col in self.cursor.fetchall()}
            print(f"📊 Mavjud ustunlar: {columns}")
            
            # Yangi ustunlarni qo'shish (discount_price qo'shildi)
            new_columns = [
                ('quality', 'TEXT DEFAULT "HD"'),
                ('release_year', 'INTEGER'),
                ('duration', 'TEXT'),
                ('file_size', 'INTEGER'),
                ('discount_price', 'INTEGER'),
                ('is_discounted', 'INTEGER DEFAULT 0'),
                ('rating', 'REAL DEFAULT 0'),
                ('total_ratings', 'INTEGER DEFAULT 0')
            ]
            
            for column_name, column_type in new_columns:
                if column_name not in columns:
                    print(f"➕ {column_name} ustunini qo'shish...")
                    self.cursor.execute(f"ALTER TABLE movies ADD COLUMN {column_name} {column_type}")
                    print(f"✅ {column_name} ustuni qo'shildi")
                else:
                    print(f"ℹ️ {column_name} ustuni allaqachon mavjud")
            
            self.conn.commit()
            print("✅ Movies jadvali yangilandi!")
            
        except Exception as e:
            print(f"❌ Jadvalni yangilashda xatolik: {e}")      
        
    def create_protection_tables(self):
        """Kontent himoyasi uchun jadvallarni yaratish"""
        try:
            # Download attempts jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS download_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    movie_id INTEGER,
                    attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    attempt_type TEXT NOT NULL,
                    user_agent TEXT,
                    ip_address TEXT,
                    details TEXT,
                    success BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (movie_id) REFERENCES movies(id)
                )
            ''')
            
            # Screen recording detections jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS screen_recording_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    detection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    detection_type TEXT NOT NULL,
                    details TEXT,
                    file_size INTEGER DEFAULT 0,
                    file_type TEXT,
                    action_taken TEXT DEFAULT 'warning',
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Anti-piracy logs jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS anti_piracy_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    action_type TEXT NOT NULL,
                    details TEXT,
                    severity TEXT DEFAULT 'medium',
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Video access logs jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS video_access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    movie_id INTEGER NOT NULL,
                    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_type TEXT DEFAULT 'view',
                    token_used TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (movie_id) REFERENCES movies(id)
                )
            ''')
            
            # Content tokens jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    movie_id INTEGER NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    views_count INTEGER DEFAULT 0,
                    max_views INTEGER DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (movie_id) REFERENCES movies(id),
                    CHECK (views_count <= max_views),
                    CHECK (expires_at > created_at)
                )
            ''')
            
            # Daily stats jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_date DATE UNIQUE,
                    new_users INTEGER DEFAULT 0,
                    new_movies INTEGER DEFAULT 0,
                    free_movies_added INTEGER DEFAULT 0,
                    premium_movies_added INTEGER DEFAULT 0,
                    total_downloads INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    total_revenue REAL DEFAULT 0,
                    movie_sales_count INTEGER DEFAULT 0,
                    subscription_sales_count INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            print("✅ Himoya jadvallari yaratildi!")
            
        except Exception as e:
            self.logger.error(f"Jadval yaratishda xatolik: {e}")
            raise
    
    def update_database_schema(self):
        """Database schema ni to'liq yangilash"""
        try:
            print("📋 Database schema yangilanmoqda...")
            
            # 1. users jadvali uchun registration_date ustunini qo'shish
            self.cursor.execute("PRAGMA table_info(users)")
            user_columns = [column[1] for column in self.cursor.fetchall()]
            
            # registration_date ustunini qo'shamiz
            if 'registration_date' not in user_columns:
                try:
                    self.cursor.execute('ALTER TABLE users ADD COLUMN registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                    self.logger.info(f"users jadvaliga registration_date ustuni qo'shildi")
                    
                    # Mavjud foydalanuvchilar uchun registered_date ni registration_date ga ko'chiramiz
                    self.cursor.execute('''
                        UPDATE users 
                        SET registration_date = registered_date 
                        WHERE registration_date IS NULL AND registered_date IS NOT NULL
                    ''')
                except Exception as e:
                    self.logger.warning(f"registration_date ustunini qo'shishda xatolik: {e}")
            
            # 2. movies jadvali uchun BARCHA kerakli ustunlar
            self.cursor.execute("PRAGMA table_info(movies)")
            movie_columns = [column[1] for column in self.cursor.fetchall()]
            
            movie_columns_to_add = [
                ('is_premium', 'INTEGER DEFAULT 0'),
                ('price', 'INTEGER DEFAULT 0'),
                ('discount_price', 'INTEGER DEFAULT 0'),
                ('is_discounted', 'INTEGER DEFAULT 0'),
                ('rating', 'REAL DEFAULT 0'),
                ('total_ratings', 'INTEGER DEFAULT 0'),
                ('duration', 'INTEGER DEFAULT 0'),
                ('file_size', 'INTEGER DEFAULT 0')
            ]
            
            for column_name, column_type in movie_columns_to_add:
                if column_name not in movie_columns:
                    try:
                        self.cursor.execute(f'ALTER TABLE movies ADD COLUMN {column_name} {column_type}')
                        self.logger.info(f"movies jadvaliga {column_name} ustuni qo'shildi")
                    except Exception as e:
                        self.logger.warning(f"{column_name} ustunini qo'shishda xatolik: {e}")
            
            # 3. users jadvali uchun qo'shimcha yangi ustunlar
            user_columns_to_add = [
                ('balance', 'REAL DEFAULT 0'),
                ('subscription_expires', 'TIMESTAMP'),
                ('is_admin', 'INTEGER DEFAULT 0')
            ]
            
            for column_name, column_type in user_columns_to_add:
                if column_name not in user_columns:
                    try:
                        self.cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}')
                        self.logger.info(f"users jadvaliga {column_name} ustuni qo'shildi")
                    except Exception as e:
                        self.logger.warning(f"{column_name} ustunini qo'shishda xatolik: {e}")
            
            # 4. payments jadvalini yangilash
            self.cursor.execute("PRAGMA table_info(payments)")
            payment_columns = [column[1] for column in self.cursor.fetchall()]
            
            # check_photo_id ustunini qo'shish
            if 'check_photo_id' not in payment_columns:
                try:
                    self.cursor.execute('ALTER TABLE payments ADD COLUMN check_photo_id TEXT')
                    self.logger.info(f"payments jadvaliga check_photo_id ustuni qo'shildi")
                except Exception as e:
                    self.logger.warning(f"check_photo_id ustunini qo'shishda xatolik: {e}")
            
            # 5. movie_purchases jadvalini yaratish
            try:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS movie_purchases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        movie_id INTEGER NOT NULL,
                        purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        price_paid REAL NOT NULL,
                        payment_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        FOREIGN KEY (movie_id) REFERENCES movies(id),
                        FOREIGN KEY (payment_id) REFERENCES payments(id),
                        UNIQUE(user_id, movie_id),
                        CHECK (price_paid >= 0)
                    )
                ''')
                self.logger.info("movie_purchases jadvali yaratildi/yangilandi")
            except Exception as e:
                self.logger.warning(f"movie_purchases jadvalini yaratishda xatolik: {e}")
            
            # 6. Indekslarni yaratish
            self.create_indexes()
            
            self.conn.commit()
            print("✅ Database schema muvaffaqiyatli yangilandi!")
            return True
            
        except Exception as e:
            self.logger.error(f"Schema yangilashda xatolik: {e}")
            self.conn.rollback()
            return False
    
    def create_indexes(self):
        """Performans uchun indekslarni yaratish"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_movies_category ON movies(main_category, sub_category)",
            "CREATE INDEX IF NOT EXISTS idx_movies_premium ON movies(is_premium)",
            "CREATE INDEX IF NOT EXISTS idx_movies_added_date ON movies(added_date)",
            "CREATE INDEX IF NOT EXISTS idx_payments_user_date ON payments(user_id, payment_date)",
            "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
            "CREATE INDEX IF NOT EXISTS idx_download_attempts_user_date ON download_attempts(user_id, attempt_date)",
            "CREATE INDEX IF NOT EXISTS idx_movie_purchases_user_movie ON movie_purchases(user_id, movie_id)",
            "CREATE INDEX IF NOT EXISTS idx_ratings_movie ON ratings(movie_id)",
            "CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_video_access_logs_user_movie ON video_access_logs(user_id, movie_id)",
            "CREATE INDEX IF NOT EXISTS idx_content_tokens_token ON content_tokens(token)",
            "CREATE INDEX IF NOT EXISTS idx_content_tokens_expires ON content_tokens(expires_at)"
        ]
        
        for index_sql in indexes:
            try:
                self.cursor.execute(index_sql)
            except Exception as e:
                self.logger.warning(f"Indeks yaratishda xatolik: {e}")
    
    # ========== HIMOYA METODLARI ==========
    
    def log_screen_recording_detection(self, user_id, detection_type, details=""):
        """Screen recording/screenshot aniqlanganligini log qilish"""
        try:
            self.cursor.execute('''
                INSERT INTO screen_recording_detections 
                (user_id, detection_type, details) 
                VALUES (?, ?, ?)
            ''', (user_id, detection_type, details))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Screen recording log xatosi: {e}")
            return False
    
    def log_anti_piracy_action(self, user_id, action_type, details=""):
        """Piravlik harakatini log qilish"""
        try:
            self.cursor.execute('''
                INSERT INTO anti_piracy_logs 
                (user_id, action_type, details) 
                VALUES (?, ?, ?)
            ''', (user_id, action_type, details))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Anti-piracy log xatosi: {e}")
            return False
    
    def log_download_attempt(self, user_id, movie_id, attempt_type, user_agent=""):
        """Yuklab olish urinishini log qilish"""
        try:
            success = attempt_type in ["download_success", "view_success"]
            
            self.cursor.execute('''
                INSERT INTO download_attempts 
                (user_id, movie_id, attempt_type, user_agent, success) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, movie_id, attempt_type, user_agent, success))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Download attempt log xatosi: {e}")
            return False
    
    def get_user_download_stats(self, user_id, hours=24):
        """Foydalanuvchining yuklab olish statistikasini olish"""
        try:
            self.cursor.execute('''
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_attempts
                FROM download_attempts 
                WHERE user_id = ? 
                AND attempt_date >= datetime('now', ?)
            ''', (user_id, f'-{hours} hours'))
            result = self.cursor.fetchone()
            return result if result else (0, 0)
        except Exception as e:
            self.logger.error(f"Download stats xatosi: {e}")
            return (0, 0)
    
    def get_user_piracy_attempts(self, user_id):
        """Foydalanuvchining piravlik urinishlari soni"""
        try:
            self.cursor.execute('''
                SELECT COUNT(*) 
                FROM anti_piracy_logs 
                WHERE user_id = ?
            ''', (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Piracy attempts xatosi: {e}")
            return 0

    def is_user_blocked(self, user_id: int):
        """Foydalanuvchi bloklanganligini tekshirish - ISHONCHLI VERSIYA"""
        try:
            # 1. blocked_users jadvalida faol blok borligini tekshirish
            self.cursor.execute('''
                SELECT id FROM blocked_users 
                WHERE user_id = ? AND unblock_date IS NULL
            ''', (user_id,))
            
            if self.cursor.fetchone():
                print(f"✅ DEBUG: User {user_id} has active block in blocked_users")
                return True
            
            # 2. users jadvalidagi statusni tekshirish
            self.cursor.execute('SELECT status FROM users WHERE user_id = ?', (user_id,))
            result = self.cursor.fetchone()
            
            if result:
                # SQLite Row obyektini to'g'ri o'qish
                if hasattr(result, '__getitem__'):
                    status = result[0]  # Birinchi ustun
                else:
                    status = result[0]
                
                print(f"🔍 DEBUG: User {user_id} status = '{status}'")
                
                if status == 'blocked':
                    # Agar users da blocked bo'lsa, lekin blocked_users da yo'q bo'lsa
                    # blocked_users ga yozib qo'yamiz
                    self.cursor.execute('''
                        INSERT OR IGNORE INTO blocked_users 
                        (user_id, blocked_by, reason, block_date)
                        VALUES (?, ?, ?, datetime('now', 'localtime'))
                    ''', (user_id, 1, "Auto-detected blocked status",))
                    self.conn.commit()
                    return True
            
            return False
            
        except Exception as e:
            print(f"🚨 ERROR in is_user_blocked: {e}")
            return False

    def block_user(self, user_id, blocked_by, reason=None):
        """Foydalanuvchini bloklash - TO'G'RILANGAN VERSIYA"""
        try:
            print(f"🛡️ DEBUG: Starting block_user for user_id={user_id}")
            
            # 1. Foydalanuvchi mavjudligini tekshirish
            self.cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
            user_exists = self.cursor.fetchone()
            
            if not user_exists:
                print(f"❌ DEBUG: User {user_id} not found in users table")
                return False
            
            # 2. Allaqachon bloklanganligini tekshirish
            self.cursor.execute('''
                SELECT id FROM blocked_users 
                WHERE user_id = ? AND unblock_date IS NULL
            ''', (user_id,))
            
            if self.cursor.fetchone():
                print(f"⚠️ DEBUG: User {user_id} already has active block, updating status only")
                
                # Allaqachon bloklangan bo'lsa, faqat statusni yangilash
                self.cursor.execute('''
                    UPDATE users 
                    SET status = 'blocked' 
                    WHERE user_id = ?
                ''', (user_id,))
                self.conn.commit()
                return True
            
            # 3. Bloklash amallari
            print(f"🚫 DEBUG: Adding new block for user {user_id}")
            
            # a) blocked_users ga yozish
            self.cursor.execute('''
                INSERT INTO blocked_users (user_id, blocked_by, reason, block_date)
                VALUES (?, ?, ?, datetime('now', 'localtime'))
            ''', (user_id, blocked_by, reason))
            
            # b) users statusini yangilash
            self.cursor.execute('''
                UPDATE users 
                SET status = 'blocked' 
                WHERE user_id = ?
            ''', (user_id,))
            
            # 4. Tekshirish va commit
            self.conn.commit()
            
            # Blok qilinganligini tekshirish
            self.cursor.execute('SELECT status FROM users WHERE user_id = ?', (user_id,))
            updated_status = self.cursor.fetchone()
            
            print(f"✅ DEBUG: Successfully blocked user {user_id}, new status: '{updated_status[0] if updated_status else 'N/A'}'")
            return True
            
        except Exception as e:
            print(f"🚨 ERROR in block_user for {user_id}: {e}")
            self.conn.rollback()
            return False

    def unblock_user(self, user_id):
        """Foydalanuvchini blokdan ochish - TO'G'RILANGAN VERSIYA"""
        try:
            print(f"🔓 DEBUG: Starting unblock_user for user_id={user_id}")
            
            # 1. Bloklanganligini tekshirish
            self.cursor.execute('''
                SELECT id FROM blocked_users 
                WHERE user_id = ? AND unblock_date IS NULL
            ''', (user_id,))
            
            if not self.cursor.fetchone():
                print(f"⚠️ DEBUG: User {user_id} not found in active blocks, but checking users table")
                
                # Agar blocked_users da yo'q bo'lsa, users jadvalidagi statusni tekshirish
                self.cursor.execute('SELECT status FROM users WHERE user_id = ?', (user_id,))
                user_status = self.cursor.fetchone()
                
                if user_status and user_status[0] == 'blocked':
                    print(f"🔄 DEBUG: User {user_id} has status 'blocked' in users, setting to 'active'")
                    self.cursor.execute('''
                        UPDATE users 
                        SET status = 'active' 
                        WHERE user_id = ?
                    ''', (user_id,))
                    self.conn.commit()
                    return True
                
                print(f"❌ DEBUG: User {user_id} is not blocked anywhere")
                return False
            
            # 2. Blokdan ochish amallari
            print(f"🔄 DEBUG: Unblocking user {user_id}")
            
            # a) blocked_users ni yangilash
            self.cursor.execute('''
                UPDATE blocked_users 
                SET unblock_date = datetime('now', 'localtime')
                WHERE user_id = ? AND unblock_date IS NULL
            ''', (user_id,))
            
            # b) users statusini yangilash
            self.cursor.execute('''
                UPDATE users 
                SET status = 'active' 
                WHERE user_id = ?
            ''', (user_id,))
            
            # 3. Tekshirish
            self.conn.commit()
            
            print(f"✅ DEBUG: Successfully unblocked user {user_id}")
            return True
            
        except Exception as e:
            print(f"🚨 ERROR in unblock_user for {user_id}: {e}")
            self.conn.rollback()
            return False

    def get_blocked_users(self):
        """Barcha bloklangan foydalanuvchilarni olish"""
        try:
            self.cursor.execute('''
                SELECT b.*, u.full_name 
                FROM blocked_users b
                LEFT JOIN users u ON b.user_id = u.user_id
                WHERE b.unblock_date IS NULL
                ORDER BY b.block_date DESC
            ''')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting blocked users: {e}")
            return []
    
    def get_blocked_users(self):
        """Bloklangan foydalanuvchilarni olish"""
        try:
            self.cursor.execute('''
                SELECT bu.*, u.full_name, u.username, u.phone
                FROM blocked_users bu
                JOIN users u ON bu.user_id = u.user_id
                WHERE bu.unblock_date IS NULL
                ORDER BY bu.block_date DESC
            ''')
            return self.cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Get blocked users xatosi: {e}")
            return []
            
    def is_user_active(user_id):
        """Foydalanuvchi aktiv (bloklanmagan) holatda ekanligini tekshirish"""
        try:
            cursor.execute('SELECT status FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0] == 'active'
            return True  # Agar foydalanuvchi topilmasa, avtomatik ravishda faol deb hisoblanadi
        except Exception as e:
            print(f"Error checking user status: {e}")
            return True        
    
    def add_video_access_log(self, user_id, movie_id, access_type='view', token_used=None):
        """Video ko'rish logini qo'shish"""
        try:
            self.cursor.execute('''
                INSERT INTO video_access_logs 
                (user_id, movie_id, access_type, token_used) 
                VALUES (?, ?, ?, ?)
            ''', (user_id, movie_id, access_type, token_used))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Video access log xatosi: {e}")
            return False
    
    def increment_views(self, movie_id):
        """Film ko'rishlar sonini oshirish"""
        try:
            self.cursor.execute('''
                UPDATE movies 
                SET views = views + 1 
                WHERE id = ?
            ''', (movie_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Increment views xatosi: {e}")
            return False
    
    def get_pending_limits(self):
        """Kutilayotgan limit so'rovlarini olish"""
        try:
            self.cursor.execute('''
                SELECT l.*, u.full_name, u.username
                FROM limits l
                JOIN users u ON l.user_id = u.user_id
                WHERE l.status = 'pending'
                ORDER BY l.requested_date
            ''')
            return self.cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Pending limits error: {e}")
            return []
    
    def approve_limit(self, limit_id, approved_by):
        """Limit so'rovini tasdiqlash"""
        try:
            self.cursor.execute('''
                UPDATE limits 
                SET status = 'approved', 
                    approved_by = ?, 
                    approved_date = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (approved_by, limit_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Approve limit error: {e}")
            return False
    
    def reject_limit(self, limit_id, rejected_by):
        """Limit so'rovini rad etish"""
        try:
            self.cursor.execute('''
                UPDATE limits 
                SET status = 'rejected', 
                    approved_by = ?, 
                    approved_date = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (rejected_by, limit_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Reject limit error: {e}")
            return False
    
    # ========== USER METHODS ==========
    def add_user(self, user_id, username, full_name, phone):
        """Yangi foydalanuvchi qo'shish"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, full_name, phone)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, full_name, phone))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error adding user: {e}")
            return False
    
    def get_user(self, user_id):
        """Foydalanuvchini ID bo'yicha olish"""
        try:
            self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = self.cursor.fetchone()
            
            if user:
                # DEBUG: Ustunlarni chiqarish
                print(f"🔍 DEBUG User columns for {user_id}: {len(user)} columns")
                for i, value in enumerate(user):
                    print(f"  [{i}] {value}")
            
            return user
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def update_user_language(self, user_id, language):
        """Foydalanuvchi tilini yangilash"""
        try:
            self.cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating user language: {e}")
            return False
    
    def get_all_users(self):
        """Barcha foydalanuvchilarni olish - FIXED VERSION"""
        try:
            self.cursor.execute('''
                SELECT 
                    user_id,
                    username,
                    full_name,
                    phone,
                    language,
                    registration_date,
                    status,
                    is_admin,
                    balance,
                    subscription_expires
                FROM users 
                ORDER BY registration_date DESC
            ''')
            users = self.cursor.fetchall()
            return users  # List of tuples qaytaradi
        except Exception as e:
            self.logger.error(f"Get all users error: {e}")
            return []
    
    def get_users_count(self):
        """Foydalanuvchilar sonini olish"""
        try:
            self.cursor.execute('SELECT COUNT(*) FROM users')
            result = self.cursor.fetchone()
            
            # SQLite Row obyektini to'g'ri o'qish
            if isinstance(result, sqlite3.Row):
                return result[0]
            elif isinstance(result, tuple) or isinstance(result, list):
                return result[0] if result else 0
            else:
                return result if result else 0
                
        except Exception as e:
            self.logger.error(f"Get users count error: {e}")
            return 0
    
    def get_active_users_count(self):
        """Faol foydalanuvchilar sonini olish"""
        try:
            self.cursor.execute('''
                SELECT COUNT(DISTINCT user_id) 
                FROM download_attempts 
                WHERE attempt_date >= datetime('now', '-7 days')
            ''')
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Get active users count error: {e}")
            return 0
    
    def update_user_balance(self, user_id, amount):
        """Foydalanuvchi balansini yangilash"""
        try:
            self.cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating user balance: {e}")
            return False
    
    def get_user_balance(self, user_id):
        """Foydalanuvchi balansini olish"""
        try:
            self.cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Error getting user balance: {e}")
            return 0
    
    def has_active_subscription(self, user_id):
        """Foydalanuvchining faol obunasi borligini tekshirish"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # users jadvalidan tekshirish
            self.cursor.execute('''
                SELECT subscription_expires FROM users 
                WHERE user_id = ? AND subscription_expires > ?
            ''', (user_id, current_time))
            
            if self.cursor.fetchone():
                return True
            
            # subscriptions jadvalidan tekshirish
            self.cursor.execute('''
                SELECT * FROM subscriptions 
                WHERE user_id = ? AND end_date > ? AND status = 'active'
            ''', (user_id, current_time))
            
            return self.cursor.fetchone() is not None
            
        except Exception as e:
            self.logger.error(f"Error checking subscription: {e}")
            return False
    
    def get_user_subscription_info(self, user_id):
        """Foydalanuvchi obuna ma'lumotlarini olish"""
        try:
            self.cursor.execute('''
                SELECT subscription_expires FROM users 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = self.cursor.fetchone()
            if result and result[0]:
                expires = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
                now = datetime.now()
                
                if expires > now:
                    days_left = (expires - now).days
                    return {
                        'has_subscription': True,
                        'expires_date': expires,
                        'days_left': days_left
                    }
            
            return {
                'has_subscription': False,
                'expires_date': None,
                'days_left': 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting subscription info: {e}")
            return {
                'has_subscription': False,
                'expires_date': None,
                'days_left': 0
            }
    
    # ========== MOVIE METHODS ==========
    def add_movie(self, main_category, sub_category, title, description, 
                  file_id, file_type, language, added_by, is_premium=False, price=0, 
                  file_size=0, duration=0, quality='HD', release_year=None, 
                  discount_price=None):
        """Yangi film qo'shish (pullik yoki bepul)"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            is_premium_int = 1 if is_premium else 0
            
            # discount_price NULL bo'lsa is_discounted = 0
            is_discounted = 0
            if discount_price is not None and discount_price < price:
                is_discounted = 1
            else:
                discount_price = None
            
            # Yangilangan SQL so'rovi - discount_price va is_discounted ustunlari bilan
            self.cursor.execute('''
                INSERT INTO movies 
                (main_category, sub_category, title, description, file_id, 
                 file_type, file_size, duration, language, added_by, added_date, 
                 views, is_premium, price, discount_price, is_discounted,
                 quality, release_year) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
            ''', (
                main_category, sub_category, title, description, 
                file_id, file_type, file_size, duration, language, added_by, 
                current_time, is_premium_int, price, discount_price, is_discounted,
                quality, release_year
            ))
            
            movie_id = self.cursor.lastrowid
            
            # Kunlik statistika yangilash
            self.update_daily_stats_movie_added(is_premium)
            
            self.conn.commit()
            
            self.logger.info(f"Film qo'shildi: {title} (ID: {movie_id}, Premium: {is_premium}, Narx: {price}, Quality: {quality}, Year: {release_year})")
            return movie_id
        except Exception as e:
            self.logger.error(f"Film qo'shishda xatolik: {e}")
            self.conn.rollback()
            return None
    
    def update_movie(self, movie_id, **kwargs):
        """Filmini yangilash"""
        try:
            if not kwargs:
                return False
            
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(movie_id)
            
            query = f"UPDATE movies SET {set_clause} WHERE id = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            self.logger.info(f"Film yangilandi: ID {movie_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating movie: {e}")
            return False
    
    def delete_movie(self, movie_id):
        """Filmini bazadan o'chirish"""
        try:
            # Bog'liq yozuvlarni o'chirish
            tables = [
                'movie_purchases',
                'ratings',
                'favorites',
                'download_attempts',
                'video_access_logs'
            ]
            
            for table in tables:
                self.cursor.execute(f'DELETE FROM {table} WHERE movie_id = ?', (movie_id,))
            
            # Filmini o'chirish
            self.cursor.execute('DELETE FROM movies WHERE id = ?', (movie_id,))
            self.conn.commit()
            
            self.logger.info(f"Film o'chirildi: ID {movie_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting movie: {e}")
            self.conn.rollback()
            return False
    
    def delete_all_movies(self):
        """Barcha filmlarni o'chirish"""
        try:
            # Bog'liq jadvallarni tozalash
            tables = [
                'movie_purchases',
                'ratings',
                'favorites',
                'download_attempts',
                'video_access_logs',
                'content_tokens'
            ]
            
            for table in tables:
                self.cursor.execute(f'DELETE FROM {table}')
            
            # Filmlarni o'chirish
            self.cursor.execute('DELETE FROM movies')
            self.conn.commit()
            
            self.logger.info("Barcha filmlar o'chirildi")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting all movies: {e}")
            self.conn.rollback()
            return False
    
    def get_movies_count(self):
        """Filmlar sonini olish"""
        try:
            self.cursor.execute('SELECT COUNT(*) FROM movies')
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Error getting movies count: {e}")
            return 0
    
    def get_movies_count_by_category(self, category=None, sub_category=None):
        """Kategoriya bo'yicha filmlar sonini olish"""
        try:
            if category and sub_category:
                self.cursor.execute('''
                    SELECT COUNT(*) FROM movies 
                    WHERE main_category = ? AND sub_category = ?
                ''', (category, sub_category))
            elif category:
                self.cursor.execute('''
                    SELECT COUNT(*) FROM movies 
                    WHERE main_category = ?
                ''', (category,))
            else:
                self.cursor.execute('SELECT COUNT(*) FROM movies')
            
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Category count error: {e}")
            return 0
    
    def get_movies_paginated(self, category=None, sub_category=None, page=1, per_page=1):
        """Filmlarni sahifalangan holda olish"""
        try:
            offset = (page - 1) * per_page
            
            print(f"🔧 DEBUG get_movies_paginated: category={category}, sub_category={sub_category}, page={page}")
            
            if category and sub_category:
                self.cursor.execute('''
                    SELECT * FROM movies 
                    WHERE main_category = ? AND sub_category = ?
                    ORDER BY added_date DESC
                    LIMIT ? OFFSET ?
                ''', (category, sub_category, per_page, offset))
            elif category:
                self.cursor.execute('''
                    SELECT * FROM movies 
                    WHERE main_category = ?
                    ORDER BY added_date DESC
                    LIMIT ? OFFSET ?
                ''', (category, per_page, offset))
            else:
                self.cursor.execute('''
                    SELECT * FROM movies 
                    ORDER BY added_date DESC
                    LIMIT ? OFFSET ?
                ''', (per_page, offset))
            
            movies = self.cursor.fetchall()
            print(f"🔧 DEBUG: Found {len(movies)} movies")
            
            if movies:
                print(f"🔧 DEBUG: First movie columns: {len(movies[0])}")
            
            return movies
        except Exception as e:
            print(f"❌ Error getting paginated movies: {e}")
            traceback.print_exc()
            return []
    
    def get_movies_by_main_category(self, main_category):
        """Asosiy kategoriya bo'yicha filmlarni olish"""
        try:
            self.cursor.execute('''
                SELECT * FROM movies 
                WHERE main_category = ? 
                ORDER BY added_date DESC
            ''', (main_category,))
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting movies by category: {e}")
            return []
    
    def search_movies_paginated(self, query, page=1, per_page=10):
        """Filmlarni sahifalangan qidirish"""
        try:
            offset = (page - 1) * per_page
            search_pattern = f'%{query}%'
            
            print(f"🔍 DEBUG search_movies_paginated: query={query}, page={page}, per_page={per_page}")
            
            self.cursor.execute('''
                SELECT * FROM movies 
                WHERE title LIKE ? OR description LIKE ?
                ORDER BY views DESC
                LIMIT ? OFFSET ?
            ''', (search_pattern, search_pattern, per_page, offset))
            
            rows = self.cursor.fetchall()
            
            # DEBUG ma'lumotlari
            print(f"🔍 DEBUG: Found {len(rows)} movies for query '{query}'")
            if rows:
                print(f"🔍 DEBUG: First movie title: {rows[0][3]}")
            
            # SQLite Row objectlarini list of tuples ga aylantiramiz
            return [tuple(row) for row in rows]
            
        except Exception as e:
            print(f"❌ Error searching movies: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_top_movies(self, limit=10):
        """Eng ko'p ko'rilgan filmlarni olish"""
        try:
            self.cursor.execute('''
                SELECT * FROM movies 
                ORDER BY views DESC 
                LIMIT ?
            ''', (limit,))
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Top movies error: {e}")
            return []
    
    def get_category_stats(self):
        """Kategoriyalar bo'yicha statistika"""
        try:
            self.cursor.execute('''
                SELECT main_category, COUNT(*) as count
                FROM movies 
                GROUP BY main_category
                ORDER BY count DESC
            ''')
            return self.cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Category stats error: {e}")
            return []
    
    def get_recent_movies(self, limit=5):
        """So'ngi qo'shilgan filmlarni olish"""
        try:
            self.cursor.execute('''
                SELECT * FROM movies 
                ORDER BY added_date DESC 
                LIMIT ?
            ''', (limit,))
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Recent movies error: {e}")
            return []
    
    # ========== PREMIUM CONTENT METHODS ==========
    def is_premium_movie(self, movie_id):
        """Film pullik ekanligini tekshirish"""
        try:
            self.cursor.execute('SELECT is_premium, price, discount_price FROM movies WHERE id = ?', (movie_id,))
            result = self.cursor.fetchone()
            if result:
                is_premium = result[0] == 1
                price = result[1]
                discount_price = result[2]
                current_price = discount_price if discount_price else price
                return is_premium, current_price
            return False, 0
        except Exception as e:
            self.logger.error(f"Error checking premium movie: {e}")
            return False, 0
    
    def get_movie_price(self, movie_id):
        """Film narxini olish"""
        try:
            self.cursor.execute('SELECT price, discount_price FROM movies WHERE id = ?', (movie_id,))
            result = self.cursor.fetchone()
            if result:
                return result[1] if result[1] else result[0]
            return 0
        except Exception as e:
            self.logger.error(f"Error getting movie price: {e}")
            return 0
    
    def has_purchased_movie(self, user_id, movie_id):
        """Foydalanuvchi filmni sotib olganligini tekshirish"""
        try:
            # 1. Admin tekshiruvi
            self.cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
            user_result = self.cursor.fetchone()
            
            if user_result and user_result[0] == 1:
                return True
            
            # 2. To'liq sotib olish
            self.cursor.execute('''
                SELECT * FROM movie_purchases 
                WHERE user_id = ? AND movie_id = ?
            ''', (user_id, movie_id))
            
            if self.cursor.fetchone():
                return True
            
            # 3. Faol obuna
            if self.has_active_subscription(user_id):
                return True
            
            # 4. Bepul film tekshiruvi
            self.cursor.execute('SELECT is_premium FROM movies WHERE id = ?', (movie_id,))
            movie_result = self.cursor.fetchone()
            
            if movie_result and movie_result[0] == 0:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"has_purchased_movie xatosi: {e}")
            return False
    
    def purchase_movie(self, user_id, movie_id, price):
        """Filmini sotib olish"""
        try:
            # Balansni tekshirish
            self.cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            balance_result = self.cursor.fetchone()
            
            if not balance_result or balance_result[0] < price:
                return False, "Balans yetarli emas"
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Balansdan yechish
            self.cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (price, user_id))
            
            # To'lov qo'shish
            payment_id = self.add_payment(
                user_id=user_id,
                movie_id=movie_id,
                amount=price,
                payment_method='balance',
                status='completed'
            )
            
            if not payment_id:
                return False, "To'lov qo'shishda xatolik"
            
            # Sotib olishni qo'shish
            self.cursor.execute('''
                INSERT INTO movie_purchases (user_id, movie_id, price_paid, purchase_date, payment_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, movie_id, price, current_time, payment_id))
            
            self.conn.commit()
            
            self.logger.info(f"Film sotib olindi: User {user_id}, Movie {movie_id}, Price {price}")
            return True, "Muvaffaqiyatli sotib olindi"
            
        except Exception as e:
            self.logger.error(f"Film sotib olishda xatolik: {e}")
            self.conn.rollback()
            return False, f"Xatolik: {str(e)}"
    
    def get_premium_movies(self, limit=None):
        """Barcha pullik filmlarni olish"""
        try:
            if limit:
                self.cursor.execute('''
                    SELECT * FROM movies 
                    WHERE is_premium = 1 
                    ORDER BY added_date DESC
                    LIMIT ?
                ''', (limit,))
            else:
                self.cursor.execute('''
                    SELECT * FROM movies 
                    WHERE is_premium = 1 
                    ORDER BY added_date DESC
                ''')
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting premium movies: {e}")
            return []
    
    def get_free_movies(self, limit=None):
        """Barcha bepul filmlarni olish"""
        try:
            if limit:
                self.cursor.execute('''
                    SELECT * FROM movies 
                    WHERE is_premium = 0 
                    ORDER BY added_date DESC
                    LIMIT ?
                ''', (limit,))
            else:
                self.cursor.execute('''
                    SELECT * FROM movies 
                    WHERE is_premium = 0 
                    ORDER BY added_date DESC
                ''')
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting free movies: {e}")
            return []
    
    def get_premium_movies_count(self):
        """Pullik filmlar sonini olish"""
        try:
            self.cursor.execute('SELECT COUNT(*) FROM movies WHERE is_premium = 1')
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Error getting premium movies count: {e}")
            return 0
    
    def get_free_movies_count(self):
        """Bepul filmlar sonini olish"""
        try:
            self.cursor.execute('SELECT COUNT(*) FROM movies WHERE is_premium = 0')
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Error getting free movies count: {e}")
            return 0
    
    def update_movie_premium_status(self, movie_id, is_premium=True, price=0):
        """Filmning pullik/bepul holatini yangilash"""
        try:
            is_premium_int = 1 if is_premium else 0
            
            if is_premium:
                self.cursor.execute('''
                    UPDATE movies 
                    SET is_premium = ?, price = ? 
                    WHERE id = ?
                ''', (is_premium_int, price, movie_id))
            else:
                self.cursor.execute('''
                    UPDATE movies 
                    SET is_premium = ?, price = 0, discount_price = NULL, is_discounted = 0
                    WHERE id = ?
                ''', (is_premium_int, movie_id))
            
            self.conn.commit()
            
            status_text = "pullik" if is_premium else "bepul"
            self.logger.info(f"Film holati yangilandi: ID {movie_id}, Holat: {status_text}, Narx: {price}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating movie premium status: {e}")
            return False
    
    def set_movie_discount(self, movie_id, discount_price):
        """Filmga chegirma belgilash"""
        try:
            self.cursor.execute('SELECT price FROM movies WHERE id = ?', (movie_id,))
            result = self.cursor.fetchone()
            
            if not result:
                return False, "Film topilmadi"
            
            original_price = result[0]
            
            if discount_price >= original_price:
                return False, "Chegirma narx asl narxdan kichik bo'lishi kerak"
            
            self.cursor.execute('''
                UPDATE movies 
                SET discount_price = ?, is_discounted = 1
                WHERE id = ?
            ''', (discount_price, movie_id))
            
            self.conn.commit()
            return True, "Chegirma muvaffaqiyatli belgilandi"
        except Exception as e:
            self.logger.error(f"Error setting movie discount: {e}")
            return False, f"Xatolik: {str(e)}"
    
    # ========== PAYMENT METHODS ==========
    def add_payment(self, user_id, amount, payment_method, movie_id=None, 
                   transaction_id=None, status='pending', payment_type='movie_purchase',
                   subscription_days=None):
        """Yangi to'lov qo'shish"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.cursor.execute('''
                INSERT INTO payments 
                (user_id, movie_id, amount, payment_method, transaction_id, 
                 payment_date, status, payment_type, subscription_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, movie_id, amount, payment_method, transaction_id, 
                  current_time, status, payment_type, subscription_days))
            
            payment_id = self.cursor.lastrowid
            self.conn.commit()
            
            self.logger.info(f"To'lov qo'shildi: ID {payment_id}, User {user_id}, Amount {amount}")
            return payment_id
        except Exception as e:
            self.logger.error(f"Error adding payment: {e}")
            return None
    
    def update_payment_status(self, payment_id, status, processed_by=None):
        """To'lov holatini yangilash"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if processed_by:
                self.cursor.execute('''
                    UPDATE payments 
                    SET status = ?, processed_by = ?, process_date = ?
                    WHERE id = ?
                ''', (status, processed_by, current_time, payment_id))
            else:
                self.cursor.execute('''
                    UPDATE payments 
                    SET status = ?, process_date = ?
                    WHERE id = ?
                ''', (status, current_time, payment_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating payment status: {e}")
            return False
    
    def get_payments_stats(self):
        """To'lovlar statistikasini olish"""
        try:
            self.cursor.execute('''
                SELECT 
                    SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as total_revenue,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count
                FROM payments
            ''')
            
            result = self.cursor.fetchone()
            
            return {
                'total_revenue': result[0] or 0,
                'completed_count': result[1] or 0,
                'pending_count': result[2] or 0,
                'failed_count': result[3] or 0
            }
        except Exception as e:
            self.logger.error(f"Error getting payment stats: {e}")
            return {
                'total_revenue': 0,
                'completed_count': 0,
                'pending_count': 0,
                'failed_count': 0
            }
    
    def get_premium_statistics(self):
        """Pullik kontentlar statistikasini olish"""
        try:
            total_movies = self.get_movies_count()
            premium_count = self.get_premium_movies_count()
            free_count = total_movies - premium_count
            
            # Eng qimmat film
            self.cursor.execute('SELECT title, price FROM movies WHERE is_premium = 1 ORDER BY price DESC LIMIT 1')
            most_expensive = self.cursor.fetchone()
            
            # O'rtacha narx
            self.cursor.execute('SELECT AVG(price) FROM movies WHERE is_premium = 1 AND price > 0')
            average_price_result = self.cursor.fetchone()
            average_price = average_price_result[0] or 0
            
            # Jami potentsial daromad
            self.cursor.execute('SELECT SUM(price) FROM movies WHERE is_premium = 1')
            total_potential_revenue_result = self.cursor.fetchone()
            total_potential_revenue = total_potential_revenue_result[0] or 0
            
            # To'lov statistikasi
            payment_stats = self.get_payments_stats()
            
            # Top premium filmlar
            self.cursor.execute('''
                SELECT m.title, COUNT(p.id) as sales, SUM(p.amount) as revenue
                FROM movies m
                JOIN payments p ON m.id = p.movie_id
                WHERE m.is_premium = 1 AND p.status = 'completed'
                GROUP BY m.id
                ORDER BY revenue DESC
                LIMIT 5
            ''')
            top_premium_movies = self.cursor.fetchall()
            
            return {
                'total_movies': total_movies,
                'premium_count': premium_count,
                'free_count': free_count,
                'most_expensive_title': most_expensive[0] if most_expensive else "Mavjud emas",
                'most_expensive_price': most_expensive[1] if most_expensive else 0,
                'average_price': round(float(average_price), 2),
                'total_potential_revenue': total_potential_revenue,
                'total_payments': payment_stats['completed_count'] + payment_stats['pending_count'] + payment_stats['failed_count'],
                'completed_payments': payment_stats['completed_count'],
                'pending_payments': payment_stats['pending_count'],
                'failed_payments': payment_stats['failed_count'],
                'total_revenue': payment_stats['total_revenue'],
                'average_payment': payment_stats['total_revenue'] / payment_stats['completed_count'] if payment_stats['completed_count'] > 0 else 0,
                'top_premium_movies': top_premium_movies
            }
        except Exception as e:
            self.logger.error(f"Premium statistics error: {e}")
            return {
                'total_movies': 0,
                'premium_count': 0,
                'free_count': 0,
                'most_expensive_title': "Mavjud emas",
                'most_expensive_price': 0,
                'average_price': 0,
                'total_potential_revenue': 0,
                'total_payments': 0,
                'completed_payments': 0,
                'pending_payments': 0,
                'failed_payments': 0,
                'total_revenue': 0,
                'average_payment': 0,
                'top_premium_movies': []
            }
            
    def get_user_payments_history(self, user_id, limit=20):
        """Foydalanuvchi to'lovlar tarixini olish"""
        try:
            self.cursor.execute('''
                SELECT 
                    p.id,
                    p.amount,
                    p.payment_date,
                    p.status,
                    p.payment_method,
                    m.title,
                    p.transaction_id
                FROM payments p
                LEFT JOIN movies m ON p.movie_id = m.id
                WHERE p.user_id = ?
                ORDER BY p.payment_date DESC
                LIMIT ?
            ''', (user_id, limit))
            rows = self.cursor.fetchall()
            return rows
        except Exception as e:
            self.logger.error(f"Error getting user payments history: {e}")
            return []

    def get_user_payment_stats(self, user_id):
        """Foydalanuvchi to'lov statistikasini olish"""
        try:
            self.cursor.execute('''
                SELECT 
                    COUNT(*) as total_payments,
                    SUM(amount) as total_amount,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count
                FROM payments 
                WHERE user_id = ?
            ''', (user_id,))
            result = self.cursor.fetchone()
            
            return {
                'total_payments': result[0] or 0,
                'total_amount': result[1] or 0,
                'completed_count': result[2] or 0,
                'pending_count': result[3] or 0,
                'rejected_count': result[4] or 0
            }
        except Exception as e:
            self.logger.error(f"Error getting user payment stats: {e}")
            return {
                'total_payments': 0,
                'total_amount': 0,
                'completed_count': 0,
                'pending_count': 0,
                'rejected_count': 0
            }        
    
    # ========== STATISTICS METHODS ==========
    def get_daily_stats(self):
        """Kunlik statistikani olish"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            self.cursor.execute('SELECT * FROM daily_stats WHERE stat_date = ?', (today,))
            stats = self.cursor.fetchone()
            
            if stats:
                return {
                    'stat_date': stats[1],
                    'new_users': stats[2] or 0,
                    'new_movies': stats[3] or 0,
                    'free_movies_added': stats[4] or 0,
                    'premium_movies_added': stats[5] or 0,
                    'total_downloads': stats[6] or 0,
                    'total_views': stats[7] or 0,
                    'total_revenue': stats[8] or 0,
                    'movie_sales_count': stats[9] or 0,
                    'subscription_sales_count': stats[10] or 0,
                    'updated_at': stats[11]
                }
            
            return {
                'stat_date': today,
                'new_users': 0,
                'new_movies': 0,
                'free_movies_added': 0,
                'premium_movies_added': 0,
                'total_downloads': 0,
                'total_views': 0,
                'total_revenue': 0,
                'movie_sales_count': 0,
                'subscription_sales_count': 0,
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            self.logger.error(f"Daily stats error: {e}")
            return {
                'stat_date': datetime.now().strftime('%Y-%m-%d'),
                'new_users': 0,
                'new_movies': 0,
                'free_movies_added': 0,
                'premium_movies_added': 0,
                'total_downloads': 0,
                'total_views': 0,
                'total_revenue': 0,
                'movie_sales_count': 0,
                'subscription_sales_count': 0,
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def update_daily_stats_movie_added(self, is_premium):
        """Kunlik statistikaga film qo'shilganini yozish"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            self.cursor.execute('SELECT id FROM daily_stats WHERE stat_date = ?', (today,))
            stats = self.cursor.fetchone()
            
            if not stats:
                if is_premium:
                    self.cursor.execute('''
                        INSERT INTO daily_stats (stat_date, new_movies, free_movies_added, premium_movies_added)
                        VALUES (?, 1, 0, 1)
                    ''', (today,))
                else:
                    self.cursor.execute('''
                        INSERT INTO daily_stats (stat_date, new_movies, free_movies_added, premium_movies_added)
                        VALUES (?, 1, 1, 0)
                    ''', (today,))
            else:
                if is_premium:
                    self.cursor.execute('''
                        UPDATE daily_stats 
                        SET new_movies = new_movies + 1,
                            premium_movies_added = premium_movies_added + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE stat_date = ?
                    ''', (today,))
                else:
                    self.cursor.execute('''
                        UPDATE daily_stats 
                        SET new_movies = new_movies + 1,
                            free_movies_added = free_movies_added + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE stat_date = ?
                    ''', (today,))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating daily stats for movie: {e}")
            return False
    
    def update_daily_stats_user_added(self):
        """Kunlik statistikaga foydalanuvchi qo'shilganini yozish"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            self.cursor.execute('SELECT id FROM daily_stats WHERE stat_date = ?', (today,))
            stats = self.cursor.fetchone()
            
            if not stats:
                self.cursor.execute('''
                    INSERT INTO daily_stats (stat_date, new_users)
                    VALUES (?, 1)
                ''', (today,))
            else:
                self.cursor.execute('''
                    UPDATE daily_stats 
                    SET new_users = new_users + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE stat_date = ?
                ''', (today,))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating daily stats for user: {e}")
            return False
    
    def get_weekly_stats(self):
        """Haftalik statistikani olish"""
        try:
            self.cursor.execute('''
                SELECT DATE(registered_date) as date, COUNT(*) as count
                FROM users 
                WHERE registered_date >= DATE('now', '-7 days')
                GROUP BY DATE(registered_date)
                ORDER BY date DESC
            ''')
            weekly_users = self.cursor.fetchall()
            
            self.cursor.execute('''
                SELECT DATE(added_date) as date, COUNT(*) as count
                FROM movies 
                WHERE added_date >= DATE('now', '-7 days')
                GROUP BY DATE(added_date)
                ORDER BY date DESC
            ''')
            weekly_movies = self.cursor.fetchall()
            
            self.cursor.execute('''
                SELECT DATE(payment_date) as date, SUM(amount) as revenue
                FROM payments 
                WHERE payment_date >= DATE('now', '-7 days') AND status = 'completed'
                GROUP BY DATE(payment_date)
                ORDER BY date DESC
            ''')
            weekly_revenue = self.cursor.fetchall()
            
            return {
                'weekly_users': weekly_users,
                'weekly_movies': weekly_movies,
                'weekly_revenue': weekly_revenue
            }
        except Exception as e:
            self.logger.error(f"Weekly stats error: {e}")
            return {
                'weekly_users': [],
                'weekly_movies': [],
                'weekly_revenue': []
            }
    
    def get_overall_stats(self):
        """Umumiy statistikani olish"""
        try:
            total_users = self.get_users_count()
            total_movies = self.get_movies_count()
            premium_movies = self.get_premium_movies_count()
            free_movies = self.get_free_movies_count()
            
            payment_stats = self.get_payments_stats()
            
            # Aktiv foydalanuvchilar
            self.cursor.execute('''
                SELECT COUNT(DISTINCT user_id) 
                FROM download_attempts 
                WHERE attempt_date >= datetime('now', '-30 days')
            ''')
            active_users_result = self.cursor.fetchone()
            active_users = active_users_result[0] if active_users_result else 0
            
            # Eng ko'p ko'rilgan film
            self.cursor.execute('SELECT title, views FROM movies ORDER BY views DESC LIMIT 1')
            top_movie = self.cursor.fetchone()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_movies': total_movies,
                'premium_movies': premium_movies,
                'free_movies': free_movies,
                'total_revenue': payment_stats['total_revenue'],
                'total_payments': payment_stats['completed_count'],
                'top_movie_title': top_movie[0] if top_movie else "Mavjud emas",
                'top_movie_views': top_movie[1] if top_movie else 0
            }
        except Exception as e:
            self.logger.error(f"Overall stats error: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
                'total_movies': 0,
                'premium_movies': 0,
                'free_movies': 0,
                'total_revenue': 0,
                'total_payments': 0,
                'top_movie_title': "Mavjud emas",
                'top_movie_views': 0
            }
    
    # ========== BACKUP AND CLEANUP ==========
    def backup_database(self, backup_name=None):
        """Database ni backup qilish"""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            backup_path = os.path.join(backup_dir, f"{backup_name}.db")
            shutil.copy2("movies_bot.db", backup_path)
            
            self.logger.info(f"Backup yaratildi: {backup_path}")
            return True, backup_path
        except Exception as e:
            self.logger.error(f"Backup xatosi: {e}")
            return False, str(e)
    
    def clear_old_data(self, days=30):
        """Eski ma'lumotlarni tozalash"""
        try:
            date_threshold = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            tables_to_clean = [
                ('download_attempts', 'attempt_date'),
                ('screen_recording_detections', 'detection_time'),
                ('anti_piracy_logs', 'action_date'),
                ('video_access_logs', 'access_time')
            ]
            
            cleaned_count = 0
            
            for table, date_column in tables_to_clean:
                self.cursor.execute(f'DELETE FROM {table} WHERE {date_column} < ?', (date_threshold,))
                cleaned_count += self.cursor.rowcount
            
            self.conn.commit()
            
            self.logger.info(f"Eski ma'lumotlar tozalandi: {cleaned_count} yozuv")
            return True
        except Exception as e:
            self.logger.error(f"Clear old data error: {e}")
            return False
    
    # ========== RATING METHODS ==========
    def add_rating(self, user_id, movie_id, rating, comment=None):
        """Filmga baho qo'shish"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO ratings (user_id, movie_id, rating, comment)
                VALUES (?, ?, ?, ?)
            ''', (user_id, movie_id, rating, comment))
            
            # O'rtacha reytingni hisoblash
            self.cursor.execute('''
                UPDATE movies 
                SET 
                    rating = (SELECT AVG(rating) FROM ratings WHERE movie_id = ?),
                    total_ratings = (SELECT COUNT(*) FROM ratings WHERE movie_id = ?)
                WHERE id = ?
            ''', (movie_id, movie_id, movie_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error adding rating: {e}")
            return False
    
    def get_movie_ratings(self, movie_id, limit=10):
        """Film uchun baholarni olish"""
        try:
            self.cursor.execute('''
                SELECT r.*, u.full_name, u.username
                FROM ratings r
                JOIN users u ON r.user_id = u.user_id
                WHERE r.movie_id = ?
                ORDER BY r.created_date DESC
                LIMIT ?
            ''', (movie_id, limit))
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting movie ratings: {e}")
            return []
    
    # ========== FAVORITE METHODS ==========
    def add_to_favorites(self, user_id, movie_id):
        """Filmni sevimlilarga qo'shish"""
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO favorites (user_id, movie_id)
                VALUES (?, ?)
            ''', (user_id, movie_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error adding to favorites: {e}")
            return False
    
    def remove_from_favorites(self, user_id, movie_id):
        """Filmni sevimlilardan olib tashlash"""
        try:
            self.cursor.execute('''
                DELETE FROM favorites 
                WHERE user_id = ? AND movie_id = ?
            ''', (user_id, movie_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error removing from favorites: {e}")
            return False
    
    def get_user_favorites(self, user_id, limit=20):
        """Foydalanuvchi sevimli filmlarini olish"""
        try:
            self.cursor.execute('''
                SELECT m.* 
                FROM movies m
                JOIN favorites f ON m.id = f.movie_id
                WHERE f.user_id = ?
                ORDER BY f.added_date DESC
                LIMIT ?
            ''', (user_id, limit))
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting user favorites: {e}")
            return []
    
    def is_favorite(self, user_id, movie_id):
        """Film sevimlilarga qo'shilganligini tekshirish"""
        try:
            self.cursor.execute('''
                SELECT COUNT(*) 
                FROM favorites 
                WHERE user_id = ? AND movie_id = ?
            ''', (user_id, movie_id))
            result = self.cursor.fetchone()
            return result[0] > 0 if result else False
        except Exception as e:
            self.logger.error(f"Error checking favorite: {e}")
            return False
    
    # ========== SUBSCRIPTION METHODS ==========
    def add_subscription(self, user_id, subscription_type, price, days, auto_renew=0):
        """Obuna qo'shish"""
        try:
            start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            self.cursor.execute('''
                INSERT INTO subscriptions 
                (user_id, subscription_type, price, start_date, end_date, auto_renew)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, subscription_type, price, start_date, end_date, auto_renew))
            
            # Foydalanuvchi obunasini yangilash
            self.cursor.execute('''
                UPDATE users 
                SET subscription_expires = ?
                WHERE user_id = ?
            ''', (end_date, user_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error adding subscription: {e}")
            return False
    
    def get_user_subscriptions(self, user_id):
        """Foydalanuvchi obunalarini olish"""
        try:
            self.cursor.execute('''
                SELECT * FROM subscriptions 
                WHERE user_id = ?
                ORDER BY start_date DESC
            ''', (user_id,))
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting user subscriptions: {e}")
            return []
    
    # ========== UTILITY METHODS ==========
    def close(self):
        """Database connection ni yopish"""
        try:
            self.conn.close()
            print("✅ Database connection closed")
        except Exception as e:
            self.logger.error(f"Error closing database: {e}")
    
    def __enter__(self):
        """Context manager uchun kirish"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager uchun chiqish"""
        self.close()
        
    def get_daily_stats_summary(self):
        """Kunlik statistika xulosasi"""
        try:
            # Bugungi yangi foydalanuvchilar
            self.cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(registered_date) = DATE('now')
            ''')
            today_new = self.cursor.fetchone()[0] or 0
            
            # Haftalik yangi foydalanuvchilar
            self.cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE registered_date >= DATE('now', '-7 days')
            ''')
            weekly_new = self.cursor.fetchone()[0] or 0
            
            # Jami foydalanuvchilar
            total = self.get_users_count()
            
            # Aktiv foydalanuvchilar (oxirgi 7 kunda)
            self.cursor.execute('''
                SELECT COUNT(DISTINCT user_id) 
                FROM download_attempts 
                WHERE attempt_date >= DATE('now', '-7 days')
            ''')
            active_users = self.cursor.fetchone()[0] or 0
            
            return {
                'today_new': today_new,
                'weekly_new': weekly_new,
                'total': total,
                'active_users': active_users
            }
            
        except Exception as e:
            self.logger.error(f"Daily stats summary error: {e}")
            return {
                'today_new': 0,
                'weekly_new': 0,
                'total': 0,
                'active_users': 0
            }    


# Himoya klasslari
class EnhancedProtection:
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def create_secured_token(self, movie_id, user_id, expiry_hours=2, max_views=1):
        """Himoyalangan vaqtinchalik token yaratish"""
        try:
            token = secrets.token_urlsafe(48)
            expires_at = datetime.now() + timedelta(hours=expiry_hours)
            
            self.db.cursor.execute('''
                INSERT INTO content_tokens 
                (movie_id, token, expires_at, max_views)
                VALUES (?, ?, ?, ?)
            ''', (movie_id, token, expires_at.strftime('%Y-%m-%d %H:%M:%S'), max_views))
            
            self.db.conn.commit()
            return token
        except Exception as e:
            self.logger.error(f"Error creating secured token: {e}")
            return None
    
    def validate_token(self, token):
        """Tokenni tekshirish"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.db.cursor.execute('''
                SELECT * FROM content_tokens 
                WHERE token = ? AND is_active = 1 AND expires_at > ? AND views_count < max_views
            ''', (token, current_time))
            
            result = self.db.cursor.fetchone()
            
            if result:
                # Ko'rishlar sonini oshirish
                self.db.cursor.execute('''
                    UPDATE content_tokens 
                    SET views_count = views_count + 1
                    WHERE id = ?
                ''', (result['id'],))
                
                self.db.conn.commit()
                return dict(result)
            
            return None
        except Exception as e:
            self.logger.error(f"Error validating token: {e}")
            return None
    
    def deactivate_token(self, token):
        """Tokenni o'chirish"""
        try:
            self.db.cursor.execute('''
                UPDATE content_tokens 
                SET is_active = 0
                WHERE token = ?
            ''', (token,))
            
            self.db.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error deactivating token: {e}")
            return False
            
    def create_indexes(self):
        """Performans uchun indekslarni yaratish"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_movies_category ON movies(main_category, sub_category)",
            "CREATE INDEX IF NOT EXISTS idx_movies_premium ON movies(is_premium)",
            "CREATE INDEX IF NOT EXISTS idx_movies_added_date ON movies(added_date)",
            "CREATE INDEX IF NOT EXISTS idx_payments_user_date ON payments(user_id, payment_date)",
            "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
            "CREATE INDEX IF NOT EXISTS idx_download_attempts_user_date ON download_attempts(user_id, attempt_date)",
            "CREATE INDEX IF NOT EXISTS idx_movie_purchases_user_movie ON movie_purchases(user_id, movie_id)",
            "CREATE INDEX IF NOT EXISTS idx_ratings_movie ON ratings(movie_id)",
            "CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_video_access_logs_user_movie ON video_access_logs(user_id, movie_id)",
            "CREATE INDEX IF NOT EXISTS idx_content_tokens_token ON content_tokens(token)",
            "CREATE INDEX IF NOT EXISTS idx_content_tokens_expires ON content_tokens(expires_at)",
            # Qidiruv uchun yangi indekslar
            "CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title)",
            "CREATE INDEX IF NOT EXISTS idx_movies_description ON movies(description)",
            "CREATE INDEX IF NOT EXISTS idx_movies_search ON movies(title, description)"
        ]
        
        for index_sql in indexes:
            try:
                self.cursor.execute(index_sql)
                print(f"✅ Index created: {index_sql}")
            except Exception as e:
                self.logger.warning(f"Indeks yaratishda xatolik: {e}")     

    # ========== BA'ZI YANGI FUNKSIYALAR UCHUN DATABASE METODLARI ==========
    # database.py fayliga quyidagi metodlarni qo'shing:

    def get_premium_users_count(self):
        """Premium obuna olgan foydalanuvchilar soni"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE subscription_expires IS NOT NULL 
            AND subscription_expires > CURRENT_TIMESTAMP
        ''')
        return self.cursor.fetchone()[0] or 0

    def get_user_detailed_stats(self, user_id):
        """Foydalanuvchi batafsil statistikasi"""
        self.cursor.execute('''
            SELECT 
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
        ''', (user_id,))
        
        result = self.cursor.fetchone()
        if result:
            return {
                'payments_count': result[0] or 0,
                'total_spent': result[1] or 0,
                'purchased_movies': result[2] or 0,
                'download_attempts': result[3] or 0,
                'piracy_attempts': result[4] or 0
            }
        return None            

    # Database funksiyalarini yangilash
def get_movie_by_id(self, movie_id):
    """ID bo'yicha kino ma'lumotlarini olish (yangi ustunlar bilan)"""
    try:
        self.cursor.execute('''
            SELECT 
                id, main_category, sub_category, title, description, 
                file_id, file_type, language, views, added_date,
                is_premium, price, added_by, quality, release_year,
                duration, file_size
            FROM movies WHERE id = ?
        ''', (movie_id,))
        return self.cursor.fetchone()
    except Exception as e:
        print(f"Error getting movie by ID: {e}")
        return None

    # Ma'lumotlarni formatlash uchun yordamchi funksiyalar
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

    def format_file_size(file_size_bytes):
        """Fayl hajmini formatlash"""
        if not file_size_bytes:
            return "Noma'lum"
        
        if file_size_bytes < 1024:
            return f"{file_size_bytes} B"
        elif file_size_bytes < 1024 * 1024:
            return f"{file_size_bytes // 1024} KB"
        elif file_size_bytes < 1024 * 1024 * 1024:
            return f"{file_size_bytes // (1024 * 1024)} MB"
        else:
            return f"{file_size_bytes // (1024 * 1024 * 1024):.1f} GB"

    # Test funksiyasi
    def test_database():
        """Database ni test qilish"""
        db = Database("test_movies.db")
        
        try:
            print("Testing database...")
            
            # Foydalanuvchi qo'shish
            db.add_user(12345, "test_user", "Test User", "+1234567890")
            user = db.get_user(12345)
            print(f"User added: {user}")
            
            # Film qo'shish (bepul)
            movie_id1 = db.add_movie(
                main_category="Action",
                sub_category="Hollywood",
                title="Test Free Movie",
                description="This is a test free movie",
                file_id="test_file_id_1",
                file_type="video",
                language="en",
                added_by=12345,
                is_premium=False
            )
            print(f"Free movie added with ID: {movie_id1}")
            
            # Film qo'shish (pullik)
            movie_id2 = db.add_movie(
                main_category="Comedy",
                sub_category="Bollywood",
                title="Test Premium Movie",
                description="This is a test premium movie",
                file_id="test_file_id_2",
                file_type="video",
                language="en",
                added_by=12345,
                is_premium=True,
                price=1000
            )
            print(f"Premium movie added with ID: {movie_id2}")
            
            # Film olish
            movie1 = db.get_movie_by_id(movie_id1)
            movie2 = db.get_movie_by_id(movie_id2)
            print(f"Free movie retrieved: {movie1['title'] if movie1 else 'Not found'}")
            print(f"Premium movie retrieved: {movie2['title'] if movie2 else 'Not found'}")
            
            # Premium tekshirish
            is_premium1, price1 = db.is_premium_movie(movie_id1)
            is_premium2, price2 = db.is_premium_movie(movie_id2)
            print(f"Free movie premium status: {is_premium1}, Price: {price1}")
            print(f"Premium movie premium status: {is_premium2}, Price: {price2}")
            
            # Yuklab olish log qilish
            db.log_download_attempt(12345, movie_id1, "view_success", "test_browser")
            print("Download attempt logged")
            
            # Statistikalar
            stats = db.get_user_download_stats(12345, hours=24)
            print(f"User download stats: {stats}")
            
            users_count = db.get_users_count()
            print(f"Total users: {users_count}")
            
            movies_count = db.get_movies_count()
            print(f"Total movies: {movies_count}")
            
            premium_count = db.get_premium_movies_count()
            free_count = db.get_free_movies_count()
            print(f"Premium movies: {premium_count}, Free movies: {free_count}")
            
            # Umumiy statistika
            overall_stats = db.get_overall_stats()
            print(f"Overall stats: {overall_stats}")
            
            print("✅ Database test completed successfully!")
            
        except Exception as e:
            print(f"❌ Database test error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            db.close()


if __name__ == "__main__":
    test_database()