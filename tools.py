import os, sys, time, requests, zipfile, tarfile, urllib.request

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from defaults import DEBUG, TEMP_DIR, USE_UC_BROWSER, DEF_DOWNLOAD_TIMEOUT, DEFAULT_TIME_BEFORE_PAGE_LOAD

if USE_UC_BROWSER:
    import undetected_chromedriver as uc

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
def download_file(url, filename, min_size=1024*1024):
    """
    Belirtilen URL'den dosyayı indirir.
    min_size ile minimum boyutu (byte) kontrol eder.
    """
    try:
        print(f"[*] İndiriliyor: {url}")
        resp = requests.get(url, stream=True, timeout=DEF_DOWNLOAD_TIMEOUT, headers={
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
def fetch_links(
    page_url: str,
    wait_time: int = 5,
    chrome_options = None,
    chromedriver_path: str = None,
    use_uc: bool = False,
) -> list:
    """
    Sayfadan resim linklerini çeker.
    - page_url: hedef URL
    - wait_time: JS yüklenmesi için bekleme süresi
    - chrome_options: dışarıda hazırlanmış ChromeOptions objesi
    - chromedriver_path: Selenium modu için driver yolu
    - use_uc: undetected_chromedriver kullanılacaksa True
    """
    if DEBUG:
      print("[i] DEBUG: Chrome Binary Location ->", chrome_options.binary_location)
      print(f"[i] DEBUG: Chrome arguments -> {chrome_options.arguments}")

    driver = None
    try:
        # Undetected Chrome Driver
        if use_uc:
            # Start
            try:
                driver = uc.Chrome(options=chrome_options)
                print("[i] UC driver başlatıldı!")
            except Exception as e:
                print(f"[!] UC driver başlatılamadı: {e}")
                input("Çıkmak için Enter'a basın...")
                sys.exit(1)
        
        # Selenium
        else:
            if not chromedriver_path:
                raise RuntimeError("[!] chromedriver_path verilmedi! (Selenium modu için gerekli)")

            service = Service(chromedriver_path)    
            # Start
            try:
                driver = webdriver.Chrome(service=service, options=chrome_options)
                if DEBUG:
                  print("[i] DEBUG: Selenium driver başlatıldı!")
            except Exception as e:
                print(f"[!] Selenium driver başlatılamadı: {e}")
                input("Çıkmak için Enter'a basın...")
                sys.exit(1)

        # print(f"[1] Sayfa yükleniyor: {page_url}")
        print(f"[1] Sayfanın tam yüklenmesi için {DEFAULT_TIME_BEFORE_PAGE_LOAD} sn gecikme olacak. Bekleyiniz...")
        driver.get(page_url)
             
        # time.sleep(wait_time)
        searchedClassname = "album-holder"
        try:
            # Maksimum DEFAULT_TIME_BEFORE_PAGE_LOAD kadar bekle, element DOM'a eklenene kadar
            album_holder = WebDriverWait(driver, DEFAULT_TIME_BEFORE_PAGE_LOAD).until(
                EC.presence_of_element_located((By.CLASS_NAME, searchedClassname))
            )
            print(f'[i] Aranan key "{searchedClassname}" bulundu')
        except Exception as e:
            print(f'[!] Aranan key "{searchedClassname}" bulunamadı!')
            return

        # indirilen HTML dosyasını kaydet
        if DEBUG:
            os.makedirs(TEMP_DIR, exist_ok=True)
            debug_html_path = os.path.join(TEMP_DIR, "page.html")
            with open(debug_html_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"[DEBUG] HTML dosyası kaydedildi: {debug_html_path}")

        # Resim linklerini al
        print("[2] Linkler ayıklanıyor...")
        elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='get_image']")
        links = [el.get_attribute("href") for el in elements]

        return links

    finally:
        if driver:
            driver.quit()

# -------------------------------------------------------------
def download_links(links: list, outdir: str):
    os.makedirs(outdir, exist_ok=True)
    total = len(links)

    for idx, url in enumerate(links, start=1):
        filename = os.path.basename(url.rstrip('/'))
        filepath = os.path.join(outdir, filename)
        try:
            urllib.request.urlretrieve(url, filepath)
            print(f"[{idx}/{total}] Kaydedildi: {filename}")
        except Exception as e:
            print(f"[{idx}/{total}] HATA: {filename} - {e}")
