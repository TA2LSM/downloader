# TA2LSM / 23.09.2025

# -*- coding: utf-8 -*-
import os, sys, subprocess, platform, time, zipfile, shutil, urllib.request, requests
from urllib.parse import urlparse

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from defaults import (
  DEBUG, SYSTEM, MACHINE,
  IS_WINDOWS, IS_LINUX, IS_MAC,
  USE_UC_BROWSER, DEFAULT_HEADER,
  DEFAULT_CHUNK_SIZE, DEFAULT_CHROME_DRIVER_MIN_SIZE,
  DEFAULT_CHROMIUM_MIN_SIZE, CHROMIUM_API_WITH_DOWNLOADS,
  DEFAULT_TIME_BEFORE_PAGE_LOAD, DIST_DIR, DRIVER_DIR, CHROMIUM_DIR, TEMP_DIR
  )

if USE_UC_BROWSER:
    import undetected_chromedriver as uc

from package_installer import (
  detect_chromium_and_driver_versions,
  build_snapshot_url, find_chromium_binary,
  find_chromedriver_binary,
  install_chromium_and_driver,
  ensure_uc_chromium
)

from tools import download_file, extract_archive, fetch_links, download_links

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

# # Başlatmadan önce yolları kontrol et
# chromium_path = find_chromium_binary(CHROMIUM_DIR)

# if not chromium_path or not os.path.exists(chromium_path):
#     print(f"[!] Chromium binary bulunamadı: {chromium_path}")
#     input("Çıkmak için Enter'a basın...")
#     sys.exit(1)

# Kurulu dosya yolları
CHROMIUM_PATH = os.path.join(DIST_DIR, "chromium", "chrome-win64", "chrome.exe")
CHROMEDRIVER_PATH = os.path.join(DIST_DIR, "driver", "chromedriver.exe")

# Undetected Chrome Driver
if USE_UC_BROWSER:
    print("[i] Undetected Chrome Driver kullanılacak, UC uyumlu Chromium kontrol ediliyor...")

    # UC için uyumlu Chromium varsa kullanır, yoksa indirir
    ensure_uc_chromium(DIST_DIR)

    chromium_path = CHROMIUM_PATH
    chromedriver_path = None  # UC kendi driver'ını kullanır

# Selenium
else:
    # Eğer her ikisi de varsa sürüm kontrolü atla
    if os.path.exists(CHROMIUM_PATH) and os.path.exists(CHROMEDRIVER_PATH):
        print("[i] Chromium ve ChromeDriver zaten kurulu, sürüm kontrolü atlanıyor.")
        chromium_path = CHROMIUM_PATH
        chromedriver_path = CHROMEDRIVER_PATH
    else:
        # Kurulu değilse sürüm kontrolü ve indirme
        chromium_version, driver_version, driver_url, chromium_url = detect_chromium_and_driver_versions()

        # Eğer chromium_url None ise snapshot deposundan URL oluştur
        if not chromium_url:
            chromium_url = build_snapshot_url(driver_version, SYSTEM, MACHINE)

        if not install_chromium_and_driver(chromium_url, driver_url):
            print("[!] Gerekli Chromium ve ChromeDriver indirilemedi.")
            input("Çıkmak için Enter'a basın...")
            sys.exit(1)

        # Kurulum sonrası yolları ayarla
        chromium_path = CHROMIUM_PATH
        chromedriver_path = CHROMEDRIVER_PATH

if DEBUG:
    print(f"[i] Chromium path: {chromium_path}")

    if chromedriver_path:
        print(f"[i] ChromeDriver path: {chromedriver_path}")

# ----------------------------
# Kullanıcı seçimine göre driver hazırlığı
# ----------------------------
if USE_UC_BROWSER:
    # print("[i] Undetected Chrome Driver kullanılıyor...")
    # chromium_path = find_chromium_binary(CHROMIUM_DIR)

    # if chromium_path and not uc_version_compatible(chromium_path):
    #     print("[i] UC ile uyumsuz Chromium bulundu. Siliniyor...")
    #     os.remove(chromium_path)  # veya tüm klasörü temizle    

    # UC ChromeOptions
    chrome_options = uc.ChromeOptions()
    chrome_options.binary_location = str(chromium_path)

    # tarayıcıyı arka planda açar
    if not DEBUG:
      chrome_options.add_argument("--headless=new")
      # chrome_options.add_argument("--headless")    

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--window-size=800,600")

    # chrome_options.add_argument('--proxy-server=http://127.0.0.1:8080')
    chrome_options.add_argument(f"user-agent={DEFAULT_HEADER['User-Agent']}")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--disable-web-security")

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

    if not DEBUG:
      chrome_options.add_argument("--headless=new")
      # chrome_options.add_argument("--headless")

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--window-size=800,600")

    # chrome_options.add_argument('--proxy-server=http://127.0.0.1:8080')
    chrome_options.add_argument(f"user-agent={DEFAULT_HEADER['User-Agent']}")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--disable-web-security")

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
# Sayfayı yükle, analiz et ve resimleri indir
# ----------------------------
if USE_UC_BROWSER:
    links = fetch_links(
        page_url,
        DEFAULT_TIME_BEFORE_PAGE_LOAD,
        chrome_options=chrome_options,
        use_uc=True,
    )
else:
    links = fetch_links(
        page_url,
        DEFAULT_TIME_BEFORE_PAGE_LOAD,
        chrome_options=chrome_options,
        chromedriver_path=chromedriver_path,
        use_uc=False,
    )

if not links:
    print("[!] Hiç link bulunamadı.")
    input("Çıkmak için Enter'a basın...")
    sys.exit(1)
else:
    print(f"[i] Toplam {len(links)} link bulundu.")

    print("[3] Linkler indiriliyor...")
    download_links(links, outdir)
    print("[4] Tüm linkler indirildi.")

    input("Çıkmak için Enter'a basın...")
