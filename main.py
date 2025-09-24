# TA2LSM / 23.09.2025

# -*- coding: utf-8 -*-
import os, sys, subprocess, platform, time, zipfile, shutil, urllib.request, requests
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from tools import download_file, extract_archive
from package_installer import detect_chromium_and_driver_versions, build_snapshot_url, find_chromium_binary, find_chromedriver_binary
from defaults import DEBUG, IS_WINDOWS, IS_LINUX, IS_MAC, DEFAULT_CHUNK_SIZE, DEFAULT_CHROME_DRIVER_MIN_SIZE, DEFAULT_CHROMIUM_MIN_SIZE, CHROMIUM_API

if IS_WINDOWS:
  try:
      import win32api
  except ImportError:
      win32api = None

# ----------------------------
# Folders
# ----------------------------
# cwd = os.getcwd()

# if IS_WINDOWS:
#     chromedriver_path = os.path.join(cwd, "chromedriver.exe")
#     chromium_dir = os.path.join(cwd, "chromium")
#     chromium_path = os.path.join(chromium_dir, "chrome-win", "chrome.exe")
# elif IS_MAC:
#     chromedriver_path = os.path.join(cwd, "chromedriver_mac")
#     chromium_dir = os.path.join(cwd, "chromium")
#     chromium_path = os.path.join(chromium_dir, "chrome-mac", "Chromium.app/Contents/MacOS/Chromium")
# elif IS_LINUX:
#     chromedriver_path = os.path.join(cwd, "chromedriver_linux")
#     chromium_dir = os.path.join(cwd, "chromium")
#     chromium_path = os.path.join(chromium_dir, "chrome-linux", "chrome")

# Derlenmiş exe çalışıyorsa exe'nin dizini, değilse script'in dizini
# BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
DIST_DIR = os.path.join(os.getcwd(), "dist")
CHROMIUM_DIR = os.path.join(DIST_DIR, "chromium")
DRIVER_DIR = os.path.join(DIST_DIR, "driver")

# def install_chromium_and_driver(chromium_url, driver_url):
#     """Hem Chromium hem Driver indirip dist altına kurar."""
#     os.makedirs(CHROMIUM_DIR, exist_ok=True)
#     os.makedirs(DRIVER_DIR, exist_ok=True)

#     # --- Driver ---
#     driver_zip = os.path.join(DRIVER_DIR, "chromedriver.zip")
#     if download_file(driver_url, driver_zip):
#         extract_archive(driver_zip, DRIVER_DIR)
#         if os.path.exists(driver_zip):
#             os.remove(driver_zip)
#     else:
#         print("[!] ChromeDriver indirilemedi.")
#         return False

#     # --- Chromium ---
#     chromium_pkg = os.path.join(CHROMIUM_DIR, os.path.basename(chromium_url))
#     if download_file(chromium_url, chromium_pkg):
#         extract_archive(chromium_pkg, CHROMIUM_DIR)
#         if os.path.exists(chromium_pkg):
#             os.remove(chromium_pkg)
#     else:
#         print("[!] Chromium indirilemedi.")
#         return False

#     print("[i] Chromium ve ChromeDriver dist/ altına kuruldu.")
#     return True

def install_chromium_and_driver(chromium_url, driver_url):
    """Hem Chromium hem Driver indirip dist altına kurar."""
    os.makedirs(CHROMIUM_DIR, exist_ok=True)
    os.makedirs(DRIVER_DIR, exist_ok=True)

    # --- Driver ---
    chromedriver_path = find_chromedriver_binary(DRIVER_DIR)
    if chromedriver_path:
        if DEBUG: print(f"[i] ChromeDriver zaten kurulu: {chromedriver_path}")
    else:
        driver_zip = os.path.join(DRIVER_DIR, "chromedriver.zip")
        if download_file(driver_url, driver_zip):
            extract_archive(driver_zip, DRIVER_DIR)
            if os.path.exists(driver_zip):
                os.remove(driver_zip)
        chromedriver_path = find_chromedriver_binary(DRIVER_DIR)

    # --- Chromium ---
    chromium_path = find_chromium_binary(CHROMIUM_DIR)
    if chromium_path:
        if DEBUG: print(f"[i] Chromium zaten kurulu: {chromium_path}")
    else:
        chromium_pkg = os.path.join(CHROMIUM_DIR, os.path.basename(chromium_url))
        if download_file(chromium_url, chromium_pkg):
            extract_archive(chromium_pkg, CHROMIUM_DIR)
            if os.path.exists(chromium_pkg):
                os.remove(chromium_pkg)
        chromium_path = find_chromium_binary(CHROMIUM_DIR)

    print("[i] Chromium ve ChromeDriver dist/ altına kuruldu.")
    return chromium_path, chromedriver_path



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

# Başlatmadan önce yolu kontrol et
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

# if not os.path.exists(chromium_path):
#     print("[!] Chromium binary bulunamadı.")
#     input("Çıkmak için Enter'a basın...")
#     #sys.exit(1)
# print("Chromium binary:", chromium_path, os.path.exists(chromium_path))
    
# if not os.path.exists(chromedriver_path):
#     print("[!] ChromeDriver bulunamadı.")
#     input("Çıkmak için Enter'a basın...")
#     #sys.exit(1)
# print("ChromeDriver binary:", chromedriver_path, os.path.exists(chromedriver_path))

try:
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("[i] Selenium driver başlatıldı!")
except Exception as e:
    print(f"[!] Selenium driver başlatılamadı: {e}")
    input("Çıkmak için Enter'a basın...")

# ----------------------------
# Ready to go: User URL input
page_url = input("Sayfa URL'sini girin: ").strip()
if not page_url:
    print("URL girilmedi, çıkılıyor.")
    input("Çıkmak için Enter'a basın...")
    sys.exit(1)

desktop = os.path.join(os.path.expanduser("~"), "Desktop")
parsed_url = urlparse(page_url)
site_name = parsed_url.netloc
album_name = parsed_url.path.rstrip('/').split('/')[-1]
outdir = os.path.join(desktop, site_name, album_name)
os.makedirs(outdir, exist_ok=True)

driver.get(page_url)
time.sleep(5)

print("[1] Sayfa yükleniyor ve JS çalıştırılıyor...")
driver.get(page_url)
time.sleep(5) # increase if necessary

elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='get_image']")
links = [el.get_attribute("href") for el in elements]
total = len(links)
if total == 0:
    print("[!] Hiç resim linki bulunamadı. Çıkıyor.")
    driver.quit()
    input("Çıkmak için Enter'a basın...")
    sys.exit(1)

print(f"[2] Toplam {total} resim bulundu.\n")

for idx, url in enumerate(links, start=1):
    filename = os.path.basename(url.rstrip('/'))
    filepath = os.path.join(outdir, filename)
    try:
        urllib.request.urlretrieve(url, filepath)
        print(f"[{idx}/{total}] Kaydedildi: {filename}")
    except Exception as e:
        print(f"[{idx}/{total}] HATA: {filename} - {e}")

driver.quit()
print("\n[3] Tüm indirmeler tamamlandı.")
input("Çıkmak için Enter'a basın...")
