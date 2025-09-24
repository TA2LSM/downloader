# TA2LSM / 23.09.2025
import run

# -*- coding: utf-8 -*-
import os, sys, subprocess, platform, time, zipfile, shutil, urllib.request, requests
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from chromeDriver import get_latest_driver_version, build_driver_url
from chromium import get_chromium_version, download_chromium, build_chromium_url
from tools import download_file, extract_archive

from defaults import DEBUG, DEFAULT_CHUNK_SIZE, DEFAULT_CHROME_DRIVER_MIN_SIZE, DEFAULT_CHROMIUM_MIN_SIZE, CHROMIUM_API

IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")
IS_MAC = sys.platform.startswith("darwin")

if IS_WINDOWS:
  try:
      import win32api
  except ImportError:
      win32api = None

# ----------------------------
# Folders
# ----------------------------
cwd = os.getcwd()

if IS_WINDOWS:
    chromedriver_path = os.path.join(cwd, "chromedriver.exe")
    chromium_dir = os.path.join(cwd, "chromium")
    chromium_path = os.path.join(chromium_dir, "chrome-win", "chrome.exe")
elif IS_MAC:
    chromedriver_path = os.path.join(cwd, "chromedriver_mac")
    chromium_dir = os.path.join(cwd, "chromium")
    chromium_path = os.path.join(chromium_dir, "chrome-mac", "Chromium.app/Contents/MacOS/Chromium")
elif IS_LINUX:
    chromedriver_path = os.path.join(cwd, "chromedriver_linux")
    chromium_dir = os.path.join(cwd, "chromium")
    chromium_path = os.path.join(chromium_dir, "chrome-linux", "chrome")

# ----------------------------
# Check compatible versions 
# ----------------------------
# def detect_chromium_and_driver_versions():
#     print("[*] Chromium ve ChromeDriver kontrol ediliyor...")

#     system = platform.system()
#     machine = platform.machine()

#     chromium_version = None
#     driver_version = None
#     driver_url = None
#     chromium_url = None

#     # --- Chromium stable sürümü al ---
#     try:
#         resp = requests.get(CHROMIUM_API, timeout=5).json()
#         chromium_version = resp["channels"]["Stable"]["version"]
#         print(f"[i] Stable Chromium sürümü: {chromium_version}")

#         if DEBUG:
#           print(f"[DEBUG] API yanıtı keys: {list(resp.keys())}")
#           print(f"[DEBUG] system={system}, machine={machine}")

#         # chromium_url ekle
#         chromium_url = build_chromium_url(chromium_version, system, machine)
#     except Exception as e:
#         print(f"[!] Chromium sürümü alınamadı: {e}")
#         return None, None, None, None

#     # --- Aynı sürüm ChromeDriver var mı? ---
#     # test_url = build_driver_url(chromium_version, system, machine)
#     # resp = requests.head(test_url)
#     # if resp.status_code == 200:
#     #     driver_version = chromium_version
#     #     driver_url = test_url
#     #     print(f"[+] Uyumlu ChromeDriver bulundu: {driver_version}")
#     # else:
#     #     print(f"[!] Chromium {chromium_version} için uyumlu driver yok.")
#     #     # En güncel driver al
#     #     driver_version = get_latest_driver_version()
#     #     driver_url = build_driver_url(driver_version, system, machine)
#     #     print(f"[+] En güncel ChromeDriver kullanılacak: {driver_version}")
#     #     # Chromium da bu driver sürümüne göre indirilecek
#     #     chromium_version = driver_version
#     # --- Aynı sürüm ChromeDriver var mı? ---
#     test_url = build_driver_url(chromium_version, system, machine)
#     resp = requests.head(test_url)
#     if resp.status_code == 200:
#         driver_version = chromium_version
#         driver_url = test_url
#         print(f"[+] Uyumlu ChromeDriver bulundu: {driver_version}")
#     else:
#         print(f"[!] Chromium {chromium_version} için uyumlu driver yok.")
#         # En güncel driver al
#         driver_version = get_latest_driver_version()
#         driver_url = build_driver_url(driver_version, system, machine)
#         print(f"[+] En güncel ChromeDriver kullanılacak: {driver_version}")
#         # Chromium da bu driver sürümüne göre indirilecek
#         chromium_version = driver_version
#         chromium_url = build_chromium_url(chromium_version, system, machine)

#     return chromium_version, driver_version, driver_url, chromium_url

def detect_chromium_and_driver_versions():
    print("[*] Chromium ve ChromeDriver kontrol ediliyor...")

    system = platform.system()
    machine = platform.machine()

    chromium_version = None
    driver_version = None
    driver_url = None
    chromium_url = None

    # --- Chromium stable sürümü al ---
    try:
        resp = requests.get(CHROMIUM_API, timeout=5).json()
        chromium_version = resp["channels"]["Stable"]["version"]
        if DEBUG:
            print(f"[DEBUG] API yanıtı keys: {list(resp.keys())}")
            print(f"[DEBUG] system={system}, machine={machine}")
        print(f"[i] Stable Chromium sürümü: {chromium_version}")
    except Exception as e:
        print(f"[!] Chromium sürümü alınamadı: {e}")
        return None, None, None, None

    # --- Aynı sürüm ChromeDriver var mı? ---
    test_url = build_driver_url(chromium_version, system, machine)
    try:
        resp = requests.head(test_url, timeout=5)
        if resp.status_code == 200:
            driver_version = chromium_version
            driver_url = test_url
            chromium_url = build_chromium_url(chromium_version, system, machine)
            print(f"[+] Uyumlu ChromeDriver bulundu: {driver_version}")
        else:
            print(f"[!] Chromium {chromium_version} için uyumlu driver yok.")
            # En güncel driver al
            driver_version = get_latest_driver_version()
            driver_url = build_driver_url(driver_version, system, machine)
            chromium_version = driver_version  # Chromium da bu driver sürümüne göre indirilecek
            chromium_url = build_chromium_url(chromium_version, system, machine)
            print(f"[+] En güncel ChromeDriver kullanılacak: {driver_version}")
    except Exception as e:
        print(f"[!] Driver kontrolü sırasında hata: {e}")
        driver_version = get_latest_driver_version()
        driver_url = build_driver_url(driver_version, system, machine)
        chromium_version = driver_version
        chromium_url = build_chromium_url(chromium_version, system, machine)

    return chromium_version, driver_version, driver_url, chromium_url


DIST_DIR = os.path.join(os.getcwd(), "dist")
CHROMIUM_DIR = os.path.join(DIST_DIR, "chromium")
DRIVER_DIR = os.path.join(DIST_DIR, "driver")

def install_chromium_and_driver(chromium_url, driver_url):
    """Hem Chromium hem Driver indirip dist altına kurar."""
    os.makedirs(CHROMIUM_DIR, exist_ok=True)
    os.makedirs(DRIVER_DIR, exist_ok=True)

    # --- Driver ---
    driver_zip = os.path.join(DRIVER_DIR, "chromedriver.zip")
    if download_file(driver_url, driver_zip):
        extract_archive(driver_zip, DRIVER_DIR)
        # ZIP dosyasını sil
        if os.path.exists(driver_zip):
            os.remove(driver_zip)

    # --- Chromium ---
    chromium_pkg = os.path.join(CHROMIUM_DIR, os.path.basename(chromium_url))
    if download_file(chromium_url, chromium_pkg):
        extract_archive(chromium_pkg, CHROMIUM_DIR)
        # ZIP dosyasını sil
        if os.path.exists(chromium_pkg):
            os.remove(chromium_pkg)

    print("[i] Chromium ve ChromeDriver dist/ altına kuruldu.")


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

if not chromium_version or not driver_url or not chromium_url:
    print("[!] Chromium veya ChromeDriver bilgisi alınamadı.")
    input("Çıkmak için Enter'a basın...")
    sys.exit(1)

# Artık build_chromium_url çağırmaya gerek yok, chromium_url zaten hazır
if not install_chromium_and_driver(chromium_url, driver_url):
    print("[!] Gerekli Chromium ve ChromeDriver indirilemedi.")
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

# Başlatmadan önce yolu kontrol et
if not os.path.exists(chromium_path):
    print("[!] Chromium binary bulunamadı.")
    input("Çıkmak için Enter'a basın...")
    #sys.exit(1)
print("Chromium binary:", chromium_path, os.path.exists(chromium_path))
    
if not os.path.exists(chromedriver_path):
    print("[!] ChromeDriver bulunamadı.")
    input("Çıkmak için Enter'a basın...")
    #sys.exit(1)
print("ChromeDriver binary:", chromedriver_path, os.path.exists(chromedriver_path))

try:
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("[+] Selenium driver başlatıldı.")
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
