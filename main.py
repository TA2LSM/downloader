# TA2LSM / 23.09.2025

# -*- coding: utf-8 -*-
import os, sys, subprocess, platform, time, zipfile, shutil, urllib.request, requests
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from defaults import DEBUG, IS_WINDOWS, IS_LINUX, IS_MAC, DEFAULT_CHUNK_SIZE, DEFAULT_CHROME_DRIVER_MIN_SIZE, DEFAULT_CHROMIUM_MIN_SIZE, CHROMIUM_API_WITH_DOWNLOADS, DEFAULT_TIME_BEFORE_PAGE_LOAD, DRIVER_DIR, CHROMIUM_DIR
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
chromedriver_path = find_chromedriver_binary(DRIVER_DIR)

chrome_options = Options()
chrome_options.binary_location = chromium_path
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--window-size=1920,1080")

service = Service(chromedriver_path)

if not chromium_path or not os.path.exists(chromium_path):
    print("[!] Chromium binary bulunamadı.")
    input("Çıkmak için Enter'a basın...")

if not chromedriver_path or not os.path.exists(chromedriver_path):
    print("[!] ChromeDriver bulunamadı.")
    input("Çıkmak için Enter'a basın...")

try:
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("[i] Selenium driver başlatıldı!")
except Exception as e:
    print(f"[!] Selenium driver başlatılamadı: {e}")
    input("Çıkmak için Enter'a basın...")

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
# Sayfayı yükle
# ----------------------------
# driver.get(page_url)
# time.sleep(DEFAULT_TIME_BEFORE_PAGE_LOAD)

# print(f"[1] {DEFAULT_TIME_BEFORE_PAGE_LOAD}sn gecikmeli olarak sayfa yükleniyor ve JS çalıştırılıyor...")
# driver.get(page_url)
# time.sleep(DEFAULT_TIME_BEFORE_PAGE_LOAD) # increase if necessary

# elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='get_image']")
# links = [el.get_attribute("href") for el in elements]
# total = len(links)
# if total == 0:
#     print("[!] Hiç resim linki bulunamadı. Çıkıyor.")
#     driver.quit()
#     input("Çıkmak için Enter'a basın...")
#     sys.exit(1)

# print(f"[2] Toplam {total} resim bulundu.\n")

# for idx, url in enumerate(links, start=1):
#     filename = os.path.basename(url.rstrip('/'))
#     filepath = os.path.join(outdir, filename)
#     try:
#         urllib.request.urlretrieve(url, filepath)
#         print(f"[{idx}/{total}] Kaydedildi: {filename}")
#     except Exception as e:
#         print(f"[{idx}/{total}] HATA: {filename} - {e}")

# driver.quit()
# print("\n[3] Tüm indirmeler tamamlandı.")
# input("Çıkmak için Enter'a basın...")

# 1. Sayfanın yüklenmesini bekle
driver.get(page_url)
time.sleep(DEFAULT_TIME_BEFORE_PAGE_LOAD)  # resimlerin yüklenmesi için bekle

links = fetch_image_links(driver, page_url)
if not links:
    print("[!] Hiç resim linki bulunamadı.")
else:
    print(f"[+] Toplam {len(links)} resim bulundu.")


# WebDriverWait(driver, DEFAULT_TIME_BEFORE_PAGE_LOAD).until(
#     EC.presence_of_element_located((By.TAG_NAME, "img"))
# )

# # 2. Sayfayı aşağı kaydırarak lazy-load resimleri aç
# driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

# # 3. Tüm img tag'larını çek
# images = driver.find_elements(By.TAG_NAME, "img")
# links = []
# for img in images:
#     src = img.get_attribute("src") or img.get_attribute("data-src")
#     if src:
#         links.append(src)

# total = len(links)
# if total == 0:
#     print("[!] Hiç resim linki bulunamadı. Çıkıyor.")
#     driver.quit()
#     input("Çıkmak için Enter'a basın...")
#     sys.exit(1)

# print(f"[2] Toplam {total} resim bulundu.\n")

# for idx, url in enumerate(links, start=1):
#     filename = os.path.basename(url.rstrip('/'))
#     filepath = os.path.join(outdir, filename)
#     try:
#         urllib.request.urlretrieve(url, filepath)
#         print(f"[{idx}/{total}] Kaydedildi: {filename}")
#     except Exception as e:
#         print(f"[{idx}/{total}] HATA: {filename} - {e}")

# driver.quit()
# print("\n[3] Tüm indirmeler tamamlandı.")
# input("Çıkmak için Enter'a basın...")
