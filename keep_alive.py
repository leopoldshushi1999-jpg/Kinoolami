"""
📡 Render uchun Keep-Alive va Monitoring tizimi
Bu fayl botning 24/7 ishlashini ta'minlaydi
"""

import requests
import time
import threading
import os
from datetime import datetime

class KeepAlive:
    """Render uchun Keep-Alive va Monitoring klassi"""
    
    def __init__(self, url=None, interval=300):
        """
        KeepAlive klassi - Botning doimiy ishlashini ta'minlash
        
        Args:
            url (str): Monitoring qilinadigan URL (default: Render URL)
            interval (int): Ping intervali sekundlarda (default: 300 = 5 minut)
        """
        # Render URL ni aniqlash
        self.url = url or os.environ.get('RENDER_URL', 'https://kino-bot-5px6.onrender.com')
        
        # Health check endpoint qo'shamiz
        if not self.url.endswith('/health'):
            self.url = f"{self.url}/health" if not self.url.endswith('/') else f"{self.url}health"
        
        self.interval = interval
        self.thread = None
        self.running = False
        self.start_time = datetime.now()
        self.ping_count = 0
        self.success_count = 0
        self.fail_count = 0
        
    def ping(self):
        """URL ga HTTP so'rov yuborish va holatni tekshirish"""
        self.ping_count += 1
        
        try:
            start_time = time.time()
            response = requests.get(self.url, timeout=15)
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)  # ms
            
            if response.status_code == 200:
                self.success_count += 1
                status = "✅ OK"
                emoji = "🟢"
            else:
                self.fail_count += 1
                status = f"⚠️ {response.status_code}"
                emoji = "🟡"
            
            print(f"{emoji} Ping #{self.ping_count}: {status} | "
                  f"Response: {response_time}ms | "
                  f"Time: {datetime.now().strftime('%H:%M:%S')}")
            
            return True
            
        except requests.exceptions.Timeout:
            self.fail_count += 1
            print(f"🔴 Ping #{self.ping_count}: Timeout (15s) | "
                  f"Time: {datetime.now().strftime('%H:%M:%S')}")
            return False
            
        except requests.exceptions.ConnectionError:
            self.fail_count += 1
            print(f"🔴 Ping #{self.ping_count}: Connection Error | "
                  f"Time: {datetime.now().strftime('%H:%M:%S')}")
            return False
            
        except Exception as e:
            self.fail_count += 1
            print(f"🔴 Ping #{self.ping_count}: Error - {str(e)[:50]}... | "
                  f"Time: {datetime.now().strftime('%H:%M:%S')}")
            return False
    
    def _run_monitoring(self):
        """Monitoring thread - doimiy ping yuborish"""
        print(f"📡 Monitoring boshlanmoqda...")
        print(f"🌐 Target URL: {self.url}")
        print(f"⏰ Interval: {self.interval} soniya")
        
        while self.running:
            self.ping()
            
            # Har 10 pingdan keyin statistikani ko'rsatish
            if self.ping_count % 10 == 0:
                self.show_stats()
            
            # Interval kutish
            time.sleep(self.interval)
    
    def start(self):
        """Monitoringni ishga tushirish"""
        if self.running:
            print("⚠️ Monitoring allaqachon ishlayapti!")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_monitoring, daemon=True)
        self.thread.start()
        
        print("=" * 60)
        print("✅ KEEP-ALIVE VA MONITORING ISHGA TUSHIRILDI!")
        print(f"📅 Boshlangan vaqt: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Monitoring URL: {self.url}")
        print(f"⏱️  Ping interval: {self.interval} soniya")
        print("=" * 60)
    
    def stop(self):
        """Monitoringni to'xtatish"""
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
            print("🛑 Monitoring to'xtatildi")
    
    def show_stats(self):
        """Joriy statistikani ko'rsatish"""
        if self.ping_count == 0:
            print("📊 Hech qanday ping yuborilmagan")
            return
        
        success_rate = (self.success_count / self.ping_count) * 100
        uptime_minutes = (datetime.now() - self.start_time).total_seconds() / 60
        
        print("\n" + "=" * 60)
        print("📊 KEEP-ALIVE STATISTIKASI")
        print("=" * 60)
        print(f"📅 Monitoring boshlangan: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Uptime: {uptime_minutes:.1f} daqiqa")
        print(f"📨 Jami pinglar: {self.ping_count}")
        print(f"✅ Muvaffaqiyatli: {self.success_count}")
        print(f"❌ Muvaffaqiyatsiz: {self.fail_count}")
        print(f"📈 Muvaffaqiyat darajasi: {success_rate:.1f}%")
        print(f"🌐 URL: {self.url}")
        print("=" * 60 + "\n")
    
    def health_check(self):
        """Tezkor health check"""
        print("🔍 Health check amalga oshirilmoqda...")
        return self.ping()

# Global KeepAlive obyekti
_keep_alive_instance = None

def init_keep_alive(url=None, interval=300):
    """
    KeepAlive ni ishga tushirish (asosiy funksiya)
    
    Args:
        url (str): Monitoring URL
        interval (int): Ping intervali (default: 300s = 5 minut)
    
    Returns:
        KeepAlive: KeepAlive obyekti
    """
    global _keep_alive_instance
    
    if _keep_alive_instance is None:
        _keep_alive_instance = KeepAlive(url=url, interval=interval)
    
    return _keep_alive_instance

def get_keep_alive():
    """Global KeepAlive obyektini olish"""
    return _keep_alive_instance

# Test uchun
if __name__ == "__main__":
    print("🧪 KeepAlive sinov rejimi...")
    
    # Test uchun localhost URL
    keeper = init_keep_alive(url="http://localhost:8080/health", interval=10)
    keeper.start()
    
    try:
        # 1 daqiqa davomida test qilish
        time.sleep(60)
        keeper.show_stats()
        keeper.stop()
    except KeyboardInterrupt:
        print("\n🛑 Foydalanuvchi tomonidan to'xtatildi")
        keeper.stop()