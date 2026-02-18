# keep_alive.py faylini quyidagi kod bilan almashtiring:

"""
📡 Render uchun Keep-Alive va Monitoring tizimi - YANGILANGAN VERSIYA
"""

import requests
import time
import threading
import os
from datetime import datetime

class KeepAlive:
    """Render uchun Keep-Alive va Monitoring klassi - yaxshilangan versiya"""
    
    def __init__(self, url=None, interval=240):
        """
        Args:
            url (str): Monitoring qilinadigan URL (asosiy sahifa)
            interval (int): Ping intervali sekundlarda (default: 240 = 4 minut)
        """
        # Render URL ni aniqlash
        base_url = url or os.environ.get('RENDER_URL', 'https://kino-bot-5px6.onrender.com')
        
        # URL dan trailing slash ni olib tashlash
        base_url = base_url.rstrip('/')
        
        # Bir nechta endpointlarni saqlash
        self.endpoints = [
            f"{base_url}/health",
            f"{base_url}/healthz", 
            f"{base_url}/ping",
            base_url  # asosiy sahifa
        ]
        
        self.interval = interval
        self.thread = None
        self.running = False
        self.start_time = datetime.now()
        self.ping_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.current_endpoint_index = 0
        
    def ping(self):
        """URL ga HTTP so'rov yuborish va holatni tekshirish"""
        self.ping_count += 1
        
        # Endpointlarni aylantirib tekshirish
        url = self.endpoints[self.current_endpoint_index]
        self.current_endpoint_index = (self.current_endpoint_index + 1) % len(self.endpoints)
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10, allow_redirects=True)
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)  # ms
            
            status_emoji = "🟢" if response.status_code == 200 else "🟡"
            status_text = f"{response.status_code} {response.reason}"
            
            # Muvaffaqiyatli deb hisoblash
            if response.status_code < 500:  # 200-499 oralig'idagi kodlar
                self.success_count += 1
                success = True
            else:
                self.fail_count += 1
                success = False
            
            print(f"{status_emoji} Ping #{self.ping_count}: {status_text} | "
                  f"{response_time}ms | {url.split('/')[-1] or 'root'}")
            
            return success
            
        except requests.exceptions.Timeout:
            self.fail_count += 1
            print(f"🔴 Ping #{self.ping_count}: Timeout (10s) | {url}")
            return False
            
        except requests.exceptions.ConnectionError:
            self.fail_count += 1
            print(f"🔴 Ping #{self.ping_count}: Connection Error | {url}")
            return False
            
        except Exception as e:
            self.fail_count += 1
            print(f"🔴 Ping #{self.ping_count}: Error - {str(e)[:30]} | {url}")
            return False
    
    def _run_monitoring(self):
        """Monitoring thread - doimiy ping yuborish"""
        print(f"📡 Monitoring boshlanmoqda...")
        print(f"🌐 Endpoints: {', '.join(self.endpoints)}")
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
        print(f"🌐 Endpoints: {len(self.endpoints)} ta")
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
            return
        
        success_rate = (self.success_count / self.ping_count) * 100
        uptime_minutes = (datetime.now() - self.start_time).total_seconds() / 60
        
        print("\n" + "=" * 60)
        print("📊 KEEP-ALIVE STATISTIKASI")
        print("=" * 60)
        print(f"📅 Boshlangan: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Uptime: {uptime_minutes:.1f} daqiqa")
        print(f"📨 Jami pinglar: {self.ping_count}")
        print(f"✅ Muvaffaqiyatli: {self.success_count}")
        print(f"❌ Muvaffaqiyatsiz: {self.fail_count}")
        print(f"📈 Muvaffaqiyat: {success_rate:.1f}%")
        print("=" * 60 + "\n")

# Global KeepAlive obyekti
_keep_alive_instance = None

def init_keep_alive(url=None, interval=240):
    """KeepAlive ni ishga tushirish"""
    global _keep_alive_instance
    
    if _keep_alive_instance is None:
        _keep_alive_instance = KeepAlive(url=url, interval=interval)
    
    return _keep_alive_instance

def get_keep_alive():
    """Global KeepAlive obyektini olish"""
    return _keep_alive_instance