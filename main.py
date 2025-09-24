# TA2LSM / 23.09.2025

# -*- coding: utf-8 -*-
import os, sys, subprocess, platform, time, zipfile, shutil, urllib.request, requests
from urllib.parse import urlparse
import undetected_chromedriver as uc

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from defaults import DEBUG, HEADERS, IS_WINDOWS, IS_LINUX, IS_MAC, DEFAULT_CHUNK_SIZE, DEFAULT_CHROME_DRIVER_MIN_SIZE, DEFAULT_CHROMIUM_MIN_SIZE, CHROMIUM_API_WITH_DOWNLOADS, DEFAULT_TIME_BEFORE_PAGE_LOAD, DRIVER_DIR, CHROMIUM_DIR
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
# chromedriver_path = find_chromedriver_binary(DRIVER_DIR)

# chrome_options = Options()
chrome_options = uc.ChromeOptions()
chrome_options.binary_location = chromium_path
# chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--window-size=1920,1080")

# service = Service(chromedriver_path)

if not chromium_path or not os.path.exists(chromium_path):
    print("[!] Chromium binary bulunamadı.")
    input("Çıkmak için Enter'a basın...")

# if not chromedriver_path or not os.path.exists(chromedriver_path):
#     print("[!] ChromeDriver bulunamadı.")
#     input("Çıkmak için Enter'a basın...")

# try:
#     driver = webdriver.Chrome(service=service, options=chrome_options)
#     print("[i] Selenium driver başlatıldı!")
# except Exception as e:
#     print(f"[!] Selenium driver başlatılamadı: {e}")
#     input("Çıkmak için Enter'a basın...")

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
links = fetch_image_links(page_url, DEFAULT_TIME_BEFORE_PAGE_LOAD, chromium_path, chrome_options, debug_html_path=DEBUG_HTML)

if not links:
    print("[!] Hiç resim linki bulunamadı.")
    input("Çıkmak için Enter'a basın...")
    sys.exit(1)
else:
    print(f"[+] Toplam {len(links)} resim bulundu.")

