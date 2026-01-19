#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import random
import shutil
import tempfile
import subprocess
import sys
import socket
import requests

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
except ImportError:
    os.system("pip install selenium requests > /dev/null 2>&1")
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

# ==========================================
# ⚙️ الإعدادات والأجهزة (Focus on Devices)
# ==========================================
TOR_PROXY = "socks5://127.0.0.1:9050"
CONTROL_PORT = 9051

DEVICES = [
    {"name": "iPhone 16 Pro Max", "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1", "plat": "iPhone", "w": 430, "h": 932, "mobile": True},
    {"name": "iPhone 15 Pro", "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1", "plat": "iPhone", "w": 393, "h": 852, "mobile": True},
    {"name": "Samsung Galaxy S24 Ultra", "ua": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.64 Mobile Safari/537.36", "plat": "Linux armv8l", "w": 384, "h": 854, "mobile": True},
    {"name": "Samsung Galaxy S23 Ultra", "ua": "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36", "plat": "Linux armv8l", "w": 360, "h": 800, "mobile": True},
    {"name": "Google Pixel 9 Pro", "ua": "Mozilla/5.0 (Linux; Android 15; Pixel 9 Pro Build/AD1A.240530.019) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.103 Mobile Safari/537.36", "plat": "Linux aarch64", "w": 412, "h": 915, "mobile": True},
    {"name": "Huawei Mate 60 Pro", "ua": "Mozilla/5.0 (Linux; Android 12; ALN-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36", "plat": "Linux aarch64", "w": 412, "h": 915, "mobile": True},
    {"name": "Xiaomi 14 Ultra", "ua": "Mozilla/5.0 (Linux; Android 14; 24030PN60G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36", "plat": "Linux armv8l", "w": 393, "h": 873, "mobile": True},
    {"name": "Windows 11 PC", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36", "plat": "Win32", "w": 1920, "h": 1080, "mobile": False},
    {"name": "MacBook Pro (macOS)", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36", "plat": "MacIntel", "w": 1440, "h": 900, "mobile": False}
]

LANG_MAP = {
    'US': 'en-US,en;q=0.9', 'GB': 'en-GB,en;q=0.9', 'DE': 'de-DE,de;q=0.9',
    'FR': 'fr-FR,fr;q=0.9', 'NL': 'nl-NL,nl;q=0.9', 'CH': 'de-CH,it;q=0.8',
    'JP': 'ja-JP,ja;q=0.9', 'KR': 'ko-KR,ko;q=0.9', 'SA': 'ar-SA,ar;q=0.9'
}

# ==========================================
# 🌍 وظيفة جلب معلومات الـ IP والمنطقة الزمنية
# ==========================================
def get_geo_info():
    try:
        proxies = {'http': TOR_PROXY, 'https': TOR_PROXY}
        response = requests.get('http://ip-api.com/json/', proxies=proxies, timeout=15).json()
        if response['status'] == 'success':
            return {
                "ip": response['query'],
                "country": response['countryCode'],
                "timezone": response['timezone'],
                "city": response['city']
            }
    except:
        pass
    return {"ip": "Unknown", "country": "US", "timezone": "America/New_York", "city": "Unknown"}

# ==========================================
# 🔄 تدوير الـ IP
# ==========================================
def rotate_ip():
    print("🔄 Requesting New Identity...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", CONTROL_PORT))
            s.send(b'AUTHENTICATE ""\r\nSIGNAL NEWNYM\r\nQUIT\r\n')
        # زدنا وقت انتظار استقرار الدائرة الجديدة لـ Tor
        time.sleep(10) 
        return get_geo_info()
    except:
        return get_geo_info()

# ==========================================
# 🛠️ بناء المتصفح مع ضبط (اللغة + الوقت + الجهاز)
# ==========================================
def create_browser(device, geo):
    profile_dir = tempfile.mkdtemp(prefix="chrome_p_")
    chrome_bin = "/usr/bin/google-chrome"
    
    options = Options()
    options.binary_location = chrome_bin
    
    user_lang = LANG_MAP.get(geo['country'], 'en-US,en;q=0.9')
    options.add_argument(f'--lang={geo["country"].lower()}')
    options.add_experimental_option('prefs', {'intl.accept_languages': user_lang})
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless=new')
    options.add_argument('--mute-audio')
    options.add_argument(f'--proxy-server={TOR_PROXY}')
    options.add_argument(f'--user-agent={device["ua"]}')
    options.add_argument(f'--user-data-dir={profile_dir}')
    
    if device['mobile']:
        mobile_emulation = {
            "deviceMetrics": {"width": device['w'], "height": device['h'], "pixelRatio": 3.0},
            "userAgent": device['ua']
        }
        options.add_experimental_option("mobileEmulation", mobile_emulation)
    else:
        options.add_argument(f'--window-size={device["w"]},{device["h"]}')

    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": geo['timezone']})
    except:
        pass

    driver.execute_script(f"Object.defineProperty(navigator, 'platform', {{get: () => '{device['plat']}'}});")
    
    return driver, profile_dir

# ==========================================
# 📺 تشغيل الفيديو وتكرار الجلسات
# ==========================================
def run_session(session_id):
    print(f"\n🚀 Session {session_id} Started")
    
    geo = rotate_ip()
    print(f"🌍 IP: {geo['ip']} | 📍 {geo['city']}, {geo['country']} | 🕒 {geo['timezone']}")
    
    device = random.choice(DEVICES)
    print(f"📱 Device: {device['name']}")
    
    driver, profile = None, None
    try:
        driver, profile = create_browser(device, geo)
        
        video_id = random.choice(["6hYLIDz-RRM", "bmgpC4lGSuQ", "AvH9Ig3A0Qo"])
        driver.get(f"https://www.youtube.com/watch?v={video_id}")
        
        # 🔥 التعديل الأهم: زدنا وقت الانتظار من 10 إلى 25 ثانية
        # لضمان تحميل مشغل الفيديو بالكامل عبر Tor قبل تنفيذ الأوامر
        time.sleep(25)
        
        # استخدام try داخلي لضمان عدم توقف السكربت إذا لم يجد الفيديو فوراً
        try:
            driver.execute_script("document.querySelector('video').playbackRate = 2.0; document.querySelector('video').play();")
        except:
            print("⚠️ Player not ready yet, waiting 10s more...")
            time.sleep(10)
            driver.execute_script("document.querySelector('video').playbackRate = 2.0; document.querySelector('video').play();")
        
        wait_time = random.randint(150, 250)
        print(f"🎬 Watching for {wait_time}s at 2x speed...")
        time.sleep(wait_time)
        
        print(f"✅ Session {session_id} Finished Successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if driver: driver.quit()
        if profile: shutil.rmtree(profile, ignore_errors=True)

if __name__ == "__main__":
    count = 1
    # تأكد من تشغيل Tor في البداية
    os.system("sudo service tor start > /dev/null 2>&1")
    time.sleep(5) 
    
    while True:
        run_session(count)
        count += 1
        # زدنا وقت الراحة بين الجلسات لتجنب كشف النشاط المتكرر
        sleep_gap = random.randint(20, 45)
        print(f"💤 Sleeping for {sleep_gap}s...")
        time.sleep(sleep_gap)
