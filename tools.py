import os, time, requests, zipfile
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service

# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

from defaults import DEBUG, HEADERS, DEFAULT_MAX_WAIT_TIME

# -------------------------------------------------------------
def download_file(url, filename, min_size=1024):
    """
    Belirtilen URL'den dosyayı indirir.
    min_size ile minimum boyutu (byte) kontrol eder.
    """
    try:
        print(f"[*] İndiriliyor: {url}")
        resp = requests.get(url, stream=True, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/117.0.0.0 Safari/537.36"
        })
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        with open(filename, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        size = os.path.getsize(filename)
        if size < min_size:
            print(f"[!] Dosya çok küçük ({size} byte). İndirme başarısız.")
            return False

        print(f"[+] Dosya indirildi: {filename} ({size/1024:.1f} KB)")
        return True

    except Exception as e:
        print(f"[!] İndirme hatası: {e}")
        return False

# -------------------------------------------------------------
# def unzip(zip_path, extract_to):
#     """
#     Zip dosyasını extract_to klasörüne açar.
#     """
#     try:
#         if not os.path.exists(zip_path):
#             print(f"[!] Zip dosyası bulunamadı: {zip_path}")
#             return False

#         with zipfile.ZipFile(zip_path, 'r') as zip_ref:
#             zip_ref.extractall(extract_to)

#         print(f"[+] Açıldı: {zip_path} → {extract_to}")
#         return True
#     except Exception as e:
#         print(f"[!] Zip açma hatası: {e}")
#         return False

# -------------------------------------------------------------
def extract_archive(archive_path, extract_to):
    """Zip veya tar.xz arşivlerini açar."""
    try:
        if archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(extract_to)
        elif archive_path.endswith(".tar.xz"):
            with tarfile.open(archive_path, "r:xz") as tf:
                tf.extractall(extract_to)
        else:
            print(f"[!] Desteklenmeyen arşiv formatı: {archive_path}")
            return False
        print(f"[+] Açıldı: {archive_path} → {extract_to}")
        return True
    except Exception as e:
        print(f"[!] Arşiv açma hatası: {e}")
        return False

# -------------------------------------------------------------
# def fetch_image_links(
#     page_url: str,
#     wait_time: int = 5,
#     chromium_path: str = None,
#     chrome_options=None,
#     debug_html_path: str = None
# ) -> list:
#     """
#     Sayfadan resim linklerini çeker. 
#     - page_url: hedef URL
#     - wait_time: sayfanın JS ile yüklenmesi için bekleme süresi
#     - chromium_path: kullanmak istediğin Chromium binary yolu
#     - chrome_options: selenium/uc.Chrome için Options objesi
#     - debug_html_path: HTML debug kaydı için dosya yolu
#     """
#     if chrome_options is None:
#         chrome_options = uc.ChromeOptions()
#     if chromium_path:
#         chrome_options.binary_location = chromium_path

#     # Headless ve temel opsiyonlar
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--log-level=3")
#     chrome_options.add_argument("--window-size=1920,1080")

#     driver = uc.Chrome(options=chrome_options)

#     try:
#         print(f"[1] Sayfa yükleniyor: {page_url}")
#         driver.get(page_url)
#         time.sleep(wait_time)

#         # Optional: sayfa HTML debug kaydı
#         if debug_html_path:
#             with open(debug_html_path, "w", encoding="utf-8") as f:
#                 f.write(driver.page_source)
#             print(f"[DEBUG] HTML debug kaydedildi: {debug_html_path}")

#         # Resim linklerini al
#         elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='get_image']")
#         links = [el.get_attribute("href") for el in elements]

#         return links
#     finally:
#         driver.quit()

def fetch_image_links(page_url, wait_time, chromium_path, chrome_options, debug_html_path=None):
    if DEBUG:
        print("[i] DEBUG: Chrome binary_location ->", chrome_options.binary_location)
        print(f"[i] DEBUG: Chrome arguments -> {chrome_options.arguments}")

    if not chromium_path or not os.path.exists(chromium_path):
      raise FileNotFoundError(f"Chromium binary bulunamadı: {chromium_path}")

    # ChromeOptions içine binary_location zaten set edilmiş olmalı
    driver = uc.Chrome(options=chrome_options)

    driver.get(page_url)
    time.sleep(wait_time)

    # Sayfa HTML'sini debug için kaydet
    if debug_html_path:
        with open(debug_html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

    # Linkleri bul
    elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='get_image']")
    links = [el.get_attribute("href") for el in elements]

    driver.quit()
    return links
