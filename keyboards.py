from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

class Keyboards:
    def __init__(self, language='uz'):
        self.language = language
        self.texts = self.get_texts()
    
    def get_texts(self):
        texts = {
            'uz': {
                'main_menu': {
                    'all_content': '🎬 Barcha kontentlar',
                    'search': '🔍 Qidiruv',
                    'premium': '⭐ Pullik Kontentlar',
                    'language': '🌐 Tilni O\'zgartirish'
                },
                'categories': {
                    'hollywood_movies': '🎭 Hollywood Kinolari',
                    'indian_movies': '🕌 Hind Filmlari',
                    'indian_series': '📺 Hind Seriallari',
                    'russian_movies': '🎪 Rus Kinolari',
                    'russian_series': '📺 Rus Seriallari',
                    'uzbek_movies': '🇺🇿 O\'zbek Kinolari',
                    'uzbek_series': '📺 O\'zbek Seriallari',
                    'islamic_movies': '🕌 Islomiy Kinolar',
                    'islamic_series': '📺 Islomiy Seriallar',
                    'turkish_movies': '🇹🇷 Turk Kinolari',
                    'turkish_series': '📺 Turk Seriallari',
                    'kids_movies': '👶 Bolalar Kinolari',
                    'kids_multfilms': '🐰 Bolalar Multfilmlari',
                    'korean_movies': '🇰🇷 Koreys Kinolari',
                    'korean_series': '📺 Koreys Seriallari',
                    'short_films': '🎥 Qisqa Filmlar',
                    'back': '⬅️ Ortga'
                }
            },
            'ru': {
                'main_menu': {
                    'all_content': '🎬 Все контенты',
                    'search': '🔍 Поиск',
                    'premium': '⭐ Платные Контенты',
                    'language': '🌐 Сменить язык'
                },
                'categories': {
                    'hollywood_movies': '🎭 Голливудские Фильмы',
                    'indian_movies': '🕌 Индийские Фильмы',
                    'indian_series': '📺 Индийские Сериалы',
                    'russian_movies': '🎪 Русские Фильмы',
                    'russian_series': '📺 Русские Сериалы',
                    'uzbek_movies': '🇺🇿 Узбекские Фильмы',
                    'uzbek_series': '📺 Узбекские Сериалы',
                    'islamic_movies': '🕌 Исламские Фильмы',
                    'islamic_series': '📺 Исламские Сериалы',
                    'turkish_movies': '🇹🇷 Турецкие Фильмы',
                    'turkish_series': '📺 Турецкие Сериалы',
                    'kids_movies': '👶 Детские Фильмы',
                    'kids_multfilms': '🐰 Детские Мультфильмы',
                    'korean_movies': '🇰🇷 Корейские Фильмы',
                    'korean_series': '📺 Корейские Сериалы',
                    'short_films': '🎥 Короткометражные Фильмы',
                    'back': '⬅️ Назад'
                }
            },
            'en': {
                'main_menu': {
                    'all_content': '🎬 All Content',
                    'search': '🔍 Search',
                    'premium': '⭐ Premium Content',
                    'language': '🌐 Change Language'
                },
                'categories': {
                    'hollywood_movies': '🎭 Hollywood Movies',
                    'indian_movies': '🕌 Indian Movies',
                    'indian_series': '📺 Indian Series',
                    'russian_movies': '🎪 Russian Movies',
                    'russian_series': '📺 Russian Series',
                    'uzbek_movies': '🇺🇿 Uzbek Movies',
                    'uzbek_series': '📺 Uzbek Series',
                    'islamic_movies': '🕌 Islamic Movies',
                    'islamic_series': '📺 Islamic Series',
                    'turkish_movies': '🇹🇷 Turkish Movies',
                    'turkish_series': '📺 Turkish Series',
                    'kids_movies': '👶 Kids Movies',
                    'kids_multfilms': '🐰 Kids Cartoons',
                    'korean_movies': '🇰🇷 Korean Movies',
                    'korean_series': '📺 Korean Series',
                    'short_films': '🎥 Short Films',
                    'back': '⬅️ Back'
                }
            }
        }
        return texts[self.language]
    
    def language_selection(self):
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🇺🇿 UZ"), KeyboardButton(text="🇷🇺 RU")],
                [KeyboardButton(text="🇬🇧 EN")]
            ],
            resize_keyboard=True
        )
        return keyboard
    
    def phone_number_request(self):
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        return keyboard
    
    def main_menu(self, is_admin=False):
        text = self.texts['main_menu']
        buttons = [
            [text['all_content'], text['search']],
            [text['premium'], text['language']],
            ["🔒 Himoya Qoidalari", "📊 Mening Statistika"]  # Yangi tugmalar
        ]
        
        if is_admin:
            buttons.append(["👑 Admin paneli"])
            buttons.append(["🔍 Himoya Monitoringi"])  # Admin uchun himoya monitoringi
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def categories_menu(self):
        text = self.texts['categories']
        categories = [
            [text['hollywood_movies']],
            [text['indian_movies'], text['indian_series']],
            [text['russian_movies'], text['russian_series']],
            [text['uzbek_movies'], text['uzbek_series']],
            [text['islamic_movies'], text['islamic_series']],
            [text['turkish_movies'], text['turkish_series']],
            [text['kids_movies'], text['kids_multfilms']],
            [text['korean_movies'], text['korean_series']],
            [text['short_films']],
            [text['back']]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat) for cat in row] for row in categories],
            resize_keyboard=True
        )
        return keyboard
    
    # Hollywood ichki kategoriyalari
    def hollywood_subcategories_menu(self):
        subcategories = [
            ["Mel Gibson Kinolari", "Denzel Washington"],
            ["Tom Kruz", "Kristian Beyl"],
            ["Jon Travolta", "Arnold Schwarzenegger Kinolari"],
            ["Sylvester Stallone Kinolari", "Jason Statham Kinolari"],
            ["Jeki Chan Kinolari", "Skod Adkins Kinolari"],
            ["Denzil Washington Kinolari", "Jan Clod Van Dam Kinolari"],
            ["Brus li Kinolari", "Jim Cerry Kinolari"],
            ["Jonni Depp Kinolari", "Rowen Adkins Kinolari"],
            ["Tom Henks Kinolari", "Uill Smitt Kinolari"],
            ["Robert Deniro Kinolari", "Mett Deymon Kinolari"],
            ["Bred Pitt Kinolari", "Ressel Krou Kinolari"],
            ["Tom Hardi Kinolari", "Lenardo Dicaprio Kinolari"],
            ["Win Dizel Kinolari", "Ben Stiller Kinolari"],
            ["Robin Uilyms Kinolari", "Shon Conneri Kinolari"],
            ["Harrison Ford Kinolari", "Mark Uolberk Kinolari"],
            ["Nicolas Keyj Kinolari", "Hiyu Jekman Kinolari"],
            ["Morgen Frimen Kinolari", "Liam Nison Kinolari"],
            ["Barcha Hollywood Kinolari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat) for cat in row] for row in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Hind filmlari ichki kategoriyalari
    def indian_subcategories_menu(self):
        subcategories = [
            ["Shakruhkhan Kinolari", "Amirkhan Kinolari"],
            ["Akshay Kumar Kinolari", "Salmonkhan Kinolari"],
            ["SayfAlihon Kinolari", "Amitahbachchan Kinolari"],
            ["MethunChakraborty Kinolari", "Dharmendra Kinolari"],
            ["Raj Kapur Kinolari", "Hrithik Roshan Konolari"],
            ["Barcha Hind Kinolari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat) for cat in row] for row in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Rus kinolari ichki kategoriyalari
    def russian_movies_subcategories_menu(self):
        subcategories = [
            ["Ishdagi Ishq"],
            ["Shurikning Sarguzashtlari"],
            ["Ivan vasilivich o'z kasbini o'zgartirib"],
            ["Gugurtga Ketib"],
            ["If Qalqasing mahbuzi"],
            ["O'nta Neger bolasi"],
            ["Qo'lga Tushmas Qasoskorlar"],
            ["Barcha Rus Kinolari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Rus seriallari ichki kategoriyalari
    def russian_series_subcategories_menu(self):
        subcategories = [
            ["Igra Seriali"],
            ["Bumer Seriali"],
            ["Birgada Seriali"],
            ["Barcha Rus Seriallari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Bolalar kinolari ichki kategoriyalari
    def kids_movies_subcategories_menu(self):
        subcategories = [
            ["Bola Uyda yolg'iz 1 2 3 Qismlar"],
            ["Uchuvchi Devid"],
            ["Garry Poter 1 2 3 4 Qismlar"],
            ["Ota-Onalar uchun Tuzoq"],
            ["Barcha Bolalar Kinolari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Bolalar multfilmlari ichki kategoriyalari
    def kids_multfilms_subcategories_menu(self):
        subcategories = [
            ["Muzlik davri 1 2 3 qismlar"],
            ["Tom&Jerry"],
            ["Bori va Quyon"],
            ["Ayiq va Masha"],
            ["Kungfu Panda 1 2 3 4 qismlar"],
            ["Mustang"],
            ["Barcha Multfilmlar to'plami"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Islomiy seriallari ichki kategoriyalari
    def islamic_series_subcategories_menu(self):
        subcategories = [
            ["Umar ibin ali hattob"],
            ["Olamga Nur soshgan Oy"],
            ["Barcha Islomiy Seriallari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Islomiy kinolar ichki kategoriyalari
    def islamic_movies_subcategories_menu(self):
        subcategories = [
            ["Bahlul Dona"],
            ["Hasan Basriy"],
            ["Qozi Iymonga Kelshi"],
            ["Barcha Islomiy Kinolar"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Koreys seriallari ichki kategoriyalari
    def korean_series_subcategories_menu(self):
        subcategories = [
            ["Qish Sonatasi 1/20 Qismlar"],
            ["Yoz Ifori 1/20 Qismlar"],
            ["Va Bank 1/20 Qismlar"],
            ["Jumong Barcha Qismlar"],
            ["Dengiz Hukumdori Barcha Qismlar"],
            ["Qalbim Chechagi 1/14 Qismlar"],
            ["Barcha Koreys Seriallari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Koreys kinolari ichki kategoriyalari
    def korean_movies_subcategories_menu(self):
        subcategories = [
            ["Jinoyatchilar Shahri 1 2 3 4 Qismlar"],
            ["Barcha Koreys Kinolari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Turk seriallari ichki kategoriyalari
    def turkish_series_subcategories_menu(self):
        subcategories = [
            ["Sulton Abdulhamidhon Barcha Qismlar"],
            ["Qashqirlar Makoni Barcha Qismlar"],
            ["Barcha Turk Seriallari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Admin uchun kategoriyalar (qo'shish uchun)
    def admin_categories_menu(self):
        categories = [
            ["🎭 Hollywood Kinolari"],
            ["🕌 Hind Filmlari", "📺 Hind Seriallari"],
            ["🎪 Rus Kinolari", "📺 Rus Seriallari"],
            ["🇺🇿 O'zbek Kinolari", "📺 O'zbek Seriallari"],
            ["🕌 Islomiy Kinolar", "📺 Islomiy Seriallar"],
            ["🇹🇷 Turk Kinolari", "📺 Turk Seriallari"],
            ["👶 Bolalar Kinolari", "🐰 Bolalar Multfilmlari"],
            ["🇰🇷 Koreys Kinolari", "📺 Koreys Seriallari"],
            ["🎥 Qisqa Filmlar"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat) for cat in row] for row in categories],
            resize_keyboard=True
        )
        return keyboard
    
    # Admin uchun Hollywood ichki kategoriyalari
    def admin_hollywood_subcategories_menu(self):
        subcategories = [
            ["Mel Gibson Kinolari", "Denzel Washington"],
            ["Tom Kruz", "Kristian Beyl"],
            ["Jon Travolta", "Arnold Schwarzenegger Kinolari"],
            ["Sylvester Stallone Kinolari", "Jason Statham Kinolari"],
            ["Jeki Chan Kinolari", "Skod Adkins Kinolari"],
            ["Denzil Washington Kinolari", "Jan Clod Van Dam Kinolari"],
            ["Brus li Kinolari", "Jim Cerry Kinolari"],
            ["Jonni Depp Kinolari", "Rowen Adkins Kinolari"],
            ["Tom Henks Kinolari", "Uill Smitt Kinolari"],
            ["Robert Deniro Kinolari", "Mett Deymon Kinolari"],
            ["Bred Pitt Kinolari", "Ressel Krou Kinolari"],
            ["Tom Hardi Kinolari", "Lenardo Dicaprio Kinolari"],
            ["Win Dizel Kinolari", "Ben Stiller Kinolari"],
            ["Robin Uilyms Kinolari", "Shon Conneri Kinolari"],
            ["Harrison Ford Kinolari", "Mark Uolberk Kinolari"],
            ["Nicolas Keyj Kinolari", "Hiyu Jekman Kinolari"],
            ["Morgen Frimen Kinolari", "Liam Nison Kinolari"],
            ["Barcha Hollywood Kinolari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat) for cat in row] for row in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Admin uchun Hind ichki kategoriyalari
    def admin_indian_subcategories_menu(self):
        subcategories = [
            ["Shakruhkhan Kinolari", "Amirkhan Kinolari"],
            ["Akshay Kumar Kinolari", "Salmonkhan Kinolari"],
            ["SayfAlihon Kinolari", "Amitahbachchan Kinolari"],
            ["MethunChakraborty Kinolari", "Dharmendra Kinolari"],
            ["Raj Kapur Kinolari", "Hrithik Roshan Konolari"],
            ["Barcha Hind Kinolari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat) for cat in row] for row in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Admin uchun Rus kinolari ichki kategoriyalari
    def admin_russian_movies_subcategories_menu(self):
        subcategories = [
            ["Ishdagi Ishq"],
            ["Shurikning Sarguzashtlari"],
            ["Ivan vasilivich o'z kasbini o'zgartirib"],
            ["Gugurtga Ketib"],
            ["If Qalqasing mahbuzi"],
            ["O'nta Neger bolasi"],
            ["Qo'lga Tushmas Qasoskorlar"],
            ["Barcha Rus Kinolari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Admin uchun Rus seriallari ichki kategoriyalari
    def admin_russian_series_subcategories_menu(self):
        subcategories = [
            ["Igra Seriali"],
            ["Bumer Seriali"],
            ["Birgada Seriali"],
            ["Barcha Rus Seriallari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Admin uchun Bolalar kinolari ichki kategoriyalari
    def admin_kids_movies_subcategories_menu(self):
        subcategories = [
            ["Bola Uyda yolg'iz 1 2 3 Qismlar"],
            ["Uchuvchi Devid"],
            ["Garry Poter 1 2 3 4 Qismlar"],
            ["Ota-Onalar uchun Tuzoq"],
            ["Barcha Bolalar Kinolari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Admin uchun Bolalar multfilmlari ichki kategoriyalari
    def admin_kids_multfilms_subcategories_menu(self):
        subcategories = [
            ["Muzlik davri 1 2 3 qismlar"],
            ["Tom&Jerry"],
            ["Bori va Quyon"],
            ["Ayiq va Masha"],
            ["Kungfu Panda 1 2 3 4 qismlar"],
            ["Mustang"],
            ["Barcha Multfilmlar to'plami"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Admin uchun Islomiy seriallari ichki kategoriyalari
    def admin_islamic_series_subcategories_menu(self):
        subcategories = [
            ["Umar ibin ali hattob"],
            ["Olamga Nur soshgan Oy"],
            ["Barcha Islomiy Seriallari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Admin uchun Islomiy kinolar ichki kategoriyalari
    def admin_islamic_movies_subcategories_menu(self):
        subcategories = [
            ["Bahlul Dona"],
            ["Hasan Basriy"],
            ["Qozi Iymonga Kelshi"],
            ["Barcha Islomiy Kinolar"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Admin uchun Koreys seriallari ichki kategoriyalari
    def admin_korean_series_subcategories_menu(self):
        subcategories = [
            ["Qish Sonatasi 1/20 Qismlar"],
            ["Yoz Ifori 1/20 Qismlar"],
            ["Va Bank 1/20 Qismlar"],
            ["Jumong Barcha Qismlar"],
            ["Dengiz Hukumdori Barcha Qismlar"],
            ["Qalbim Chechagi 1/14 Qismlar"],
            ["Barcha Koreys Seriallari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Admin uchun Koreys kinolari ichki kategoriyalari
    def admin_korean_movies_subcategories_menu(self):
        subcategories = [
            ["Jinoyatchilar Shahri 1 2 3 4 Qismlar"],
            ["Barcha Koreys Kinolari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    # Admin uchun Turk seriallari ichki kategoriyalari
    def admin_turkish_series_subcategories_menu(self):
        subcategories = [
            ["Sulton Abdulhamidhon Barcha Qismlar"],
            ["Qashqirlar Makoni Barcha Qismlar"],
            ["Barcha Turk Seriallari"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=cat[0])] for cat in subcategories],
            resize_keyboard=True
        )
        return keyboard
    
    def back_button(self):
        if self.language == 'ru':
            text = "⬅️ Назад"
        elif self.language == 'en':
            text = "⬅️ Back"
        else:
            text = "⬅️ Ortga"
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=text)]],
            resize_keyboard=True
        )
        return keyboard
    
    def pagination_menu(self, current_page, total_pages, action, data=None):
        """Sahifalash menyusi"""
        buttons = []
        
        if current_page > 1:
            buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"{action}_page_{current_page-1}_{data if data else ''}"))
        
        buttons.append(InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="current_page"))
        
        if current_page < total_pages:
            buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"{action}_page_{current_page+1}_{data if data else ''}"))
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        return keyboard

    def pagination_menu_simple(self, current_page, total_pages, action, data=None):
        """Oddiy sahifalash menyusi - faqat sahifalash tugmalari"""
        buttons = []
        
        # Oldingi tugma
        if current_page > 1:
            if data:
                callback_data = f"{action}|{current_page-1}|{data}"
            else:
                callback_data = f"{action}|{current_page-1}"
            buttons.append(InlineKeyboardButton(
                text="⬅️ Oldingi", 
                callback_data=callback_data
            ))
        
        # Joriy sahifa
        buttons.append(InlineKeyboardButton(
            text=f"📄 {current_page}/{total_pages}", 
            callback_data="current_page"
        ))
        
        # Keyingi tugma
        if current_page < total_pages:
            if data:
                callback_data = f"{action}|{current_page+1}|{data}"
            else:
                callback_data = f"{action}|{current_page+1}"
            buttons.append(InlineKeyboardButton(
                text="Keyingi ➡️", 
                callback_data=callback_data
            ))
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        return keyboard
    
    def pagination_menu_with_back(self, current_page, total_pages, action, data=None, back_action="back_to_main"):
        """Sahifalash menyusi bilan orqaga qaytish tugmasi"""
        buttons = []
        
        # Oldingi tugma
        if current_page > 1:
            if data:
                callback_data = f"{action}|{current_page-1}|{data}"
            else:
                callback_data = f"{action}|{current_page-1}"
            buttons.append(InlineKeyboardButton(
                text="⬅️ Oldingi", 
                callback_data=callback_data
            ))
        
        # Joriy sahifa
        buttons.append(InlineKeyboardButton(
            text=f"📄 {current_page}/{total_pages}", 
            callback_data="current_page"
        ))
        
        # Keyingi tugma
        if current_page < total_pages:
            if data:
                callback_data = f"{action}|{current_page+1}|{data}"
            else:
                callback_data = f"{action}|{current_page+1}"
            buttons.append(InlineKeyboardButton(
                text="Keyingi ➡️", 
                callback_data=callback_data
            ))
        
        # Orqaga qaytish tugmasi
        back_buttons = [
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_action)
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons, back_buttons])
        return keyboard
    
    def protection_info_menu(self):
        """Himoya ma'lumotlari menyusi"""
        buttons = [
            ["🔒 Himoya Qoidalari", "📊 Mening Statistika"],
            ["⚠️ Ogohlantirishlar", "📵 Ta'qiqlangan Harakatlar"],
            ["🏠 Asosiy menyu"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def admin_protection_menu(self):
        """Admin himoya menyusi"""
        buttons = [
            ["🔍 Himoya Monitoringi", "📈 Himoya Statistika"],
            ["👤 Foydalanuvchi Tekshirish", "🔧 Himoya Sozlamalari"],
            ["🚫 Bloklanganlar", "✅ Blokdan Ochish"],
            ["👑 Admin paneli", "🏠 Asosiy menyu"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def confirmation_menu(self):
        """Tasdiqlash menyusi"""
        buttons = [
            ["✅ Tasdiqlash", "❌ Bekor qilish"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def movie_languages_menu(self):
        """Kino tillari menyusi"""
        buttons = [
            ["🇺🇿 O'zbekcha", "🇷🇺 Ruscha"],
            ["🇬🇧 Inglizcha", "🌍 Aralash"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def file_type_menu(self):
        """Fayl turi menyusi"""
        buttons = [
            ["🎬 Video", "📄 Dokument"],
            ["🎵 Audio", "🖼️ Rasm"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def admin_stats_menu(self):
        """Admin statistika menyusi"""
        buttons = [
            ["📊 Umumiy Statistika", "📈 Kunlik Statistika"],
            ["👥 Foydalanuvchilar", "🎬 Filmlar"],
            ["💰 To'lovlar", "🚫 Bloklanganlar"],
            ["👑 Admin paneli"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def admin_users_menu(self):
        """Admin foydalanuvchilar menyusi"""
        buttons = [
            ["📋 Barcha Foydalanuvchilar", "📅 Yangi Foydalanuvchilar"],
            ["🔍 Foydalanuvchi Qidirish", "📈 Faollik Statistika"],
            ["🚫 Bloklash", "✅ Blokdan Ochish"],
            ["👑 Admin paneli"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def admin_content_menu(self):
        """Admin kontent menyusi"""
        buttons = [
            ["➕ Kontent Qo'shish", "🗑️ Kontent O'chirish"],
            ["📋 Kontentlar Ro'yxati", "📊 Kontent Statistika"],
            ["✏️ Kontentni Tahrirlash", "🔍 Kontent Qidirish"],
            ["👑 Admin paneli"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def admin_broadcast_menu(self):
        """Admin xabar yuborish menyusi"""
        buttons = [
            ["📢 Barchaga Xabar", "👥 Guruhga Xabar"],
            ["👤 Shaxsiy Xabar", "📊 Xabar Statistikasi"],
            ["✏️ Xabarni Tahrirlash", "🗑️ Xabarni O'chirish"],
            ["👑 Admin paneli"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def admin_settings_menu(self):
        """Admin sozlamalar menyusi"""
        buttons = [
            ["🔧 Bot Sozlamalari", "🔒 Himoya Sozlamalari"],
            ["💾 Database Backup", "🧹 Database Tozalash"],
            ["⚙️ Server Sozlamalari", "📊 Log Fayllari"],
            ["👑 Admin paneli"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def yes_no_menu(self):
        """Ha/Yo'q menyusi"""
        buttons = [
            ["✅ Ha", "❌ Yo'q"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def search_options_menu(self):
        """Qidiruv variantlari menyusi"""
        buttons = [
            ["🎬 Kino nomi", "🎭 Aktyor nomi"],
            ["🗂️ Kategoriya", "🌐 Til"],
            ["📅 Yil", "⭐ Reyting"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def filter_menu(self):
        """Filtr menyusi"""
        buttons = [
            ["🆕 Yangi", "🔥 Mashhur"],
            ["⭐ Reyting", "👁️ Ko'rishlar"],
            ["🗂️ Kategoriya", "🌐 Til"],
            ["🗑️ Filtrni Tozalash", "⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def download_options_menu(self):
        """Yuklab olish variantlari menyusi"""
        buttons = [
            ["📥 Yuklab olish", "👁️ Ko'rish"],
            ["❤️ Saqlash", "📤 Ulashish"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def movie_quality_menu(self):
        """Kino sifatlari menyusi"""
        buttons = [
            ["🎬 720p HD", "🎬 1080p Full HD"],
            ["🎬 4K Ultra HD", "🎬 480p SD"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def playback_options_menu(self):
        """O'ynatish variantlari menyusi"""
        buttons = [
            ["▶️ Davom ettirish", "⏸️ To'xtatish"],
            ["⏭️ O'tkazib yuborish", "⏮️ Orqaga"],
            ["🔊 Ovoz", "🔄 Takrorlash"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def help_menu(self):
        """Yordam menyusi"""
        buttons = [
            ["❓ FAQ", "📖 Qo'llanma"],
            ["📞 Aloqa", "⚠️ Xatolik haqida"],
            ["🔒 Himoya Qoidalari", "📊 Statistika"],
            ["🏠 Asosiy menyu"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def payment_methods_menu(self):
        """To'lov usullari menyusi"""
        buttons = [
            ["💳 Karta", "📱 Mobile"],
            ["🏦 Bank", "💰 Naqd"],
            ["📊 Hisob", "🎁 Bonus"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def subscription_plans_menu(self):
        """Obuna rejalari menyusi"""
        buttons = [
            ["💰 Oylik", "💰 Yillik"],
            ["💰 Haftalik", "💰 Kundalik"],
            ["🎁 Bepul", "🏆 Premium"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def notification_settings_menu(self):
        """Xabar berish sozlamalari menyusi"""
        buttons = [
            ["🔔 Barcha xabarlar", "📢 Muhim xabarlar"],
            ["🔕 Xabarlarsiz", "⏰ Vaqtli xabarlar"],
            ["📊 Statistika xabarlari", "🎬 Yangi filmlar"],
            ["⬅️ Ortga"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def profile_menu(self):
        """Profil menyusi"""
        buttons = [
            ["👤 Profil ma'lumotlari", "📊 Statistika"],
            ["⚙️ Sozlamalar", "🔒 Himoya"],
            ["💰 To'lovlar", "❤️ Saqlanganlar"],
            ["🏠 Asosiy menyu"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
    
    def inline_search_button(self, query=""):
        """Inline qidiruv tugmasi"""
        button = InlineKeyboardButton(
            text="🔍 Qidirish",
            switch_inline_query_current_chat=query
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
        return keyboard
    
    def inline_share_button(self, movie_id):
        """Inline ulashish tugmasi"""
        button = InlineKeyboardButton(
            text="📤 Ulashish",
            switch_inline_query=f"movie_{movie_id}"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
        return keyboard
    
    def movie_actions_menu(self, movie_id):
        """Kino harakatlari menyusi"""
        buttons = [
            [
                InlineKeyboardButton(text="❤️ Saqlash", callback_data=f"save_{movie_id}"),
                InlineKeyboardButton(text="📊 Reyting", callback_data=f"rate_{movie_id}")
            ],
            [
                InlineKeyboardButton(text="💬 Sharh", callback_data=f"comment_{movie_id}"),
                InlineKeyboardButton(text="📤 Ulashish", callback_data=f"share_{movie_id}")
            ],
            [
                InlineKeyboardButton(text="🎬 O'xshash", callback_data=f"similar_{movie_id}"),
                InlineKeyboardButton(text="📥 Yuklab olish", callback_data=f"download_{movie_id}")
            ]
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return keyboard
    
    def rating_menu(self, movie_id):
        """Reyting berish menyusi"""
        buttons = [
            [
                InlineKeyboardButton(text="⭐", callback_data=f"rate_{movie_id}_1"),
                InlineKeyboardButton(text="⭐⭐", callback_data=f"rate_{movie_id}_2"),
                InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"rate_{movie_id}_3")
            ],
            [
                InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"rate_{movie_id}_4"),
                InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"rate_{movie_id}_5"),
                InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"back_movie_{movie_id}")
            ]
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return keyboard
    
    def download_quality_menu(self, movie_id):
        """Yuklab olish sifatlari menyusi"""
        buttons = [
            [
                InlineKeyboardButton(text="🎬 480p", callback_data=f"download_{movie_id}_480"),
                InlineKeyboardButton(text="🎬 720p", callback_data=f"download_{movie_id}_720")
            ],
            [
                InlineKeyboardButton(text="🎬 1080p", callback_data=f"download_{movie_id}_1080"),
                InlineKeyboardButton(text="🎬 4K", callback_data=f"download_{movie_id}_4k")
            ],
            [
                InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"back_download_{movie_id}")
            ]
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return keyboard
    
    def episode_selection_menu(self, movie_id, episodes):
        """Qismlarni tanlash menyusi"""
        buttons = []
        
        # Har bir qatorga 3 ta tugma
        row = []
        for i in range(1, episodes + 1):
            row.append(InlineKeyboardButton(text=str(i), callback_data=f"episode_{movie_id}_{i}"))
            if len(row) == 3:
                buttons.append(row)
                row = []
        
        # Qolgan tugmalar
        if row:
            buttons.append(row)
        
        # Orqaga tugmasi
        buttons.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"back_episodes_{movie_id}")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return keyboard
    
    def playlist_menu(self):
        """Pleylist menyusi"""
        buttons = [
            ["🎵 Mening Pleylistim", "🔥 Mashhur Pleylistlar"],
            ["🆕 Yangi Pleylist", "❤️ Saqlanganlar"],
            ["📊 Statistika", "🎬 Videolar"],
            ["🏠 Asosiy menyu"]
        ]
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
            resize_keyboard=True
        )
        return keyboard
        
    def admin_payment_info(self):
        """Admin to'lov ma'lumotlari tugmalari"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💳 To'lov ma'lumotlari")],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        )

    # ==================== TO'LOV REPLY KEYBOARDS ====================
    def premium_content_keyboard(self):
        """Pullik kontent uchun oddiy tugma"""
        if self.language == 'ru':
            text = "💳 Оплатить и смотреть"
        elif self.language == 'en':
            text = "💳 Pay and Watch"
        else:  # uz
            text = "💳 To'lash va Ko'rish"
        
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=text)],
                [KeyboardButton(text="⬅️ Ortga" if self.language == 'uz' else 
                               "⬅️ Назад" if self.language == 'ru' else 
                               "⬅️ Back")]
            ],
            resize_keyboard=True
        )

    def send_check_keyboard(self):
        """Chek yuborish tugmasi"""
        if self.language == 'ru':
            text = "📤 Отправить чек"
            back_text = "⬅️ Назад"
        elif self.language == 'en':
            text = "📤 Send receipt"
            back_text = "⬅️ Back"
        else:  # uz
            text = "📤 Chek yuborish"
            back_text = "⬅️ Ortga"
        
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=text)],
                [KeyboardButton(text=back_text)]
            ],
            resize_keyboard=True
        )
        
    # keyboards.py fayliga quyidagi metodni qo'shing:

    def admin_payment_actions_reply(self, payment):
        """Admin uchun to'lov amallari tugmalarini yaratish"""
        payment_id = payment[0]
        movie_title = payment[14] if len(payment) > 14 else "Noma'lum"
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"✅ Tasdiqlash {payment_id}"), 
                 KeyboardButton(text=f"❌ Rad etish {payment_id}")],
                [KeyboardButton(text=f"👁️ Chekni ko'rish {payment_id}")],
                [KeyboardButton(text="⏳ Boshqa to'lovlar")],
                [KeyboardButton(text="👑 Admin paneli")]
            ],
            resize_keyboard=True
        )
        return keyboard    
        
        