# TA2LSM / 23.09.2025

# -*- coding: utf-8 -*-
import os, sys, subprocess, platform, time, zipfile, shutil, urllib.request, requests
from urllib.parse import urlparse

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from defaults import DEBUG, USE_UC_BROWSER, HEADERS, IS_WINDOWS, IS_LINUX, IS_MAC, DEFAULT_CHUNK_SIZE, DEFAULT_CHROME_DRIVER_MIN_SIZE, DEFAULT_CHROMIUM_MIN_SIZE, CHROMIUM_API_WITH_DOWNLOADS, DEFAULT_TIME_BEFORE_PAGE_LOAD, DRIVER_DIR, CHROMIUM_DIR

if USE_UC_BROWSER:
    import undetected_chromedriver as uc

from package_installer import detect_chromium_and_driver_versions, build_snapshot_url, find_chromium_binary, find_chromedriver_binary, install_chromium_and_driver
from tools import download_file, extract_archive, fetch_image_links

# ----------------------------
# Test
# ----------------------------
# if __name__ == "__main__":
#     chromium_version, driver_version, driver_url, chromium_url = detect_chromium_and_driver_versions()
#     print(f"Chromium: v{chromium_version} -> {chromium_url}")
#     print(f"Driver: v{driver_version} -> {driver_url}")

# ----------------------------
# Chromium + ChromeDriver kontrol
# ----------------------------
chromium_version, driver_version, driver_url, chromium_url = detect_chromium_and_driver_versions()

# Eğer chromium_url None ise snapshot deposundan URL oluştur
if not chromium_url:
    chromium_url = build_snapshot_url(driver_version, platform.system(), platform.machine())

if not install_chromium_and_driver(chromium_url, driver_url):
    print("[!] Gerekli Chromium ve ChromeDriver indirilemedi.")
    input("Çıkmak için Enter'a basın...")
    sys.exit(1)

# Başlatmadan önce yolları kontrol et
chromium_path = find_chromium_binary(CHROMIUM_DIR)

if not chromium_path or not os.path.exists(chromium_path):
    print(f"[!] Chromium binary bulunamadı: {chromium_path}")
    input("Çıkmak için Enter'a basın...")
    sys.exit(1)

# ----------------------------
# Kullanıcı seçimine göre driver hazırlığı
# ----------------------------
if USE_UC_BROWSER:
    print("[i] Undetected Chrome Driver kullanılıyor...")

    # UC ChromeOptions
    chrome_options = uc.ChromeOptions()
    chrome_options.binary_location = str(chromium_path)
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--window-size=1920,1080")

    # Başlat
    try:
        driver = uc.Chrome(options=chrome_options)
        print("[i] UC driver başlatıldı!")
    except Exception as e:
        print(f"[!] UC driver başlatılamadı: {e}")
        input("Çıkmak için Enter'a basın...")
        sys.exit(1)

else:
    print("[i] Selenium kullanılıyor...")

    # Normal Selenium Chrome
    chromedriver_path = find_chromedriver_binary(DRIVER_DIR)

    if not chromedriver_path or not os.path.exists(chromedriver_path):
        print(f"[!] ChromeDriver bulunamadı: {chromedriver_path}")
        input("Çıkmak için Enter'a basın...")
        sys.exit(1)

    chrome_options = Options()
    chrome_options.binary_location = chromium_path
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(chromedriver_path)

    # Başlat
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("[i] Selenium driver başlatıldı!")
    except Exception as e:
        print(f"[!] Selenium driver başlatılamadı: {e}")
        input("Çıkmak için Enter'a basın...")
        sys.exit(1)

# --- READY to GO! -------------------------
page_url = input("Sayfa URL'sini girin: ").strip()
if not page_url:
    print("URL girilmedi, çıkılıyor.")
    input("Çıkmak için Enter'a basın...")
    sys.exit(1)

# ----------------------------
# Klasörleri oluştur
# ----------------------------
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
parsed_url = urlparse(page_url)
site_name = parsed_url.netloc
album_name = parsed_url.path.rstrip('/').split('/')[-1]
outdir = os.path.join(desktop, site_name, album_name)
os.makedirs(outdir, exist_ok=True)

# ----------------------------
# Sayfayı yükle ve analiz et
# ----------------------------
DEBUG_HTML = os.path.join(os.getcwd(), "debug_page.html")
if USE_UC_BROWSER:
    links = fetch_image_links(
        page_url,
        DEFAULT_TIME_BEFORE_PAGE_LOAD,
        chrome_options=chrome_options,
        use_uc=True,
        debug_html_path=DEBUG_HTML
    )
else:
    links = fetch_image_links(
        page_url,
        DEFAULT_TIME_BEFORE_PAGE_LOAD,
        chrome_options=chrome_options,
        chromedriver_path=chromedriver_path,
        use_uc=False,
        debug_html_path=DEBUG_HTML
    )

if not links:
    print("[!] Hiç resim linki bulunamadı.")
    input("Çıkmak için Enter'a basın...")
    sys.exit(1)
else:
    print(f"[+] Toplam {len(links)} resim bulundu.")

