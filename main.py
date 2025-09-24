# TA2LSM / 23.09.2025
import run 

# -*- coding: utf-8 -*-
import os, sys, subprocess, time, zipfile, shutil, urllib.request, requests
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from chromeDriver import get_latest_chromedriver_info, get_compatible_chromedriver_url, download_chromedriver
from chromium import get_chromium_version, download_chromium

from defaults import DEFAULT_CHUNK_SIZE, DEFAULT_CHROME_DRIVER_MIN_SIZE, DEFAULT_CHROMIUM_MIN_SIZE

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
def ensure_chromium_and_driver():
    """
    Chromium ve ChromeDriver'ı kontrol eder, yoksa veya uyumsuzsa indirir.
    """
    print("[*] Chromium ve ChromeDriver kontrol ediliyor...")

    chromium_exists = os.path.exists(chromium_path)
    driver_exists = os.path.exists(chromedriver_path)

    if not chromium_exists and not driver_exists:
        # Hiçbiri yok → Stable ChromeDriver'a göre indir
        print("[!] Chromium ve ChromeDriver bulunamadı. Stable sürüm indirilecek...")
        version, driver_url = get_latest_chromedriver_info()
        if not version or not driver_url:
            input("[!] Stable ChromeDriver bilgisi alınamadı, Enter ile çıkış yap...")
            return False

        # Önce driver indir
        print(f"[+] Stable ChromeDriver indiriliyor... ({version})")
        if not download_file(driver_url, "chromedriver.zip", DEFAULT_CHROME_DRIVER_MIN_SIZE):
            return False
        unzip("chromedriver.zip", os.getcwd())

        # Sonra chromium indir
        print(f"[+] Stable Chromium indiriliyor... ({version})")
        if not download_chromium(version):
            return False

        return True

    # Eğer sadece biri varsa veya ikisi de varsa → uyumluluk kontrol et
    chromium_version = get_chromium_version(chromium_path) if chromium_exists else None
    driver_version = get_chromedriver_version(chromedriver_path) if driver_exists else None

    if chromium_version and driver_version:
        chromium_major = chromium_version.split(".")[0]
        driver_major = driver_version.split(".")[0]

        if chromium_major != driver_major:
            print(f"[!] Uyum problemi: Chromium {chromium_version} - Driver {driver_version}")
            print("[*] Stable sürümler indirilecek...")
            cleanup_existing()
            version, driver_url = get_latest_chromedriver_info()
            if version and driver_url:
                download_file(driver_url, "chromedriver.zip", DEFAULT_CHROME_DRIVER_MIN_SIZE)
                unzip("chromedriver.zip", os.getcwd())
                download_chromium(version)
                return True
            else:
                input("[!] Stable ChromeDriver bulunamadı, Enter ile çıkış yap...")
                return False
        else:
            print(f"[i] Chromium ({chromium_version}) ve Driver ({driver_version}) uyumlu.")
            return True

    # Eğer chromium var ama driver yok → driver indir
    if chromium_version and not driver_exists:
        print(f"[!] ChromeDriver eksik. Chromium {chromium_version} için indiriliyor...")
        driver_zip_url = get_compatible_chromedriver_url(chromium_version)
        if driver_zip_url:
            download_file(driver_zip_url, "chromedriver.zip", DEFAULT_CHROME_DRIVER_MIN_SIZE)
            unzip("chromedriver.zip", os.getcwd())
            return True
        else:
            print("[!] Uyumlu driver bulunamadı. Stable ikili indirilecek.")
            cleanup_existing()
            version, driver_url = get_latest_chromedriver_info()
            if version and driver_url:
                download_file(driver_url, "chromedriver.zip", DEFAULT_CHROME_DRIVER_MIN_SIZE)
                unzip("chromedriver.zip", os.getcwd())
                download_chromium(version)
                return True

    # Eğer driver var ama chromium yok → chromium indir
    if driver_version and not chromium_exists:
        print(f"[!] Chromium eksik. Driver {driver_version} için Chromium indiriliyor...")
        download_chromium(driver_version)
        return True

    return False

# ----------------------------
# Chromium + ChromeDriver kontrol
# ----------------------------
if not ensure_chromium_and_driver():
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
