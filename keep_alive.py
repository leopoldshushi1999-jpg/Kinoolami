# keep_alive.py - UptimeRobot monitoring uchun
import requests
import time
import threading
import os
from datetime import datetime

def ping_uptimerobot():
    """UptimeRobot ga avtomatik ping yuboradi"""
    try:
        # Sizning Render URL manzilingiz
        url = "https://kino-bot-5px6.onrender.com/health"
        
        while True:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ UptimeRobot ping: OK - {datetime.now().strftime('%H:%M:%S')}")
                else:
                    print(f"⚠️ UptimeRobot ping: {response.status_code}")
            except Exception as e:
                print(f"❌ UptimeRobot ping xatosi: {e}")
            
            # Har 2 daqiqada ping yuborish
            time.sleep(120)
    except:
        pass

def start_uptimerobot_monitoring():
    """UptimeRobot monitoringni ishga tushiradi"""
    monitor_thread = threading.Thread(target=ping_uptimerobot, daemon=True)
    monitor_thread.start()
    print("📊 UptimeRobot monitoring ishga tushdi")

# Agar kerak bo'lsa, Flask serverni ishga tushirish
def keep_alive():
    """Flask server va monitoringni ishga tushiradi"""
    start_uptimerobot_monitoring()
    print("✅ keep_alive ishga tushdi")