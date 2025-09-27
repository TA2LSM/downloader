import os, sys, time, requests, zipfile, tarfile, urllib.request
from bs4 import BeautifulSoup

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from defaults import (
  DEBUG, TEMP_DIR, DEFAULT_HEADER, SEARCH_CLASS_NAMES, DEFAULT_MAX_SCROLLS, DEFAULT_SCROLL_WAIT_TIME,
  USE_UC_BROWSER, DEF_DOWNLOAD_TIMEOUT, DEFAULT_TIME_BEFORE_PAGE_LOAD, EXTENSIONS
)

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
def scroll_page(driver, pause_time=2, max_scrolls=10):
    """
    Sayfayı aşağı kaydırır, lazy load içerikleri yükler.
    pause_time: Her kaydırma sonrası bekleme süresi
    max_scrolls: En fazla kaç kez kaydırılacak
    """
    last_height = driver.execute_script("return document.body.scrollHeight")

    for i in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("[i] Sayfanın sonuna ulaşıldı.")
            break
        last_height = new_height

    print("[i] Kaydırma işlemi tamamlandı.")

# -------------------------------------------------------------
def fetch_links(
    page_url: str,
    wait_time: int = 5,
    chrome_options = None,
    chromedriver_path: str = None,
    use_uc: bool = False,
    search_classes = None
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
        print(f"[1] Sayfanın tam yüklenmesi için {wait_time} sn gecikme olacak. Bekleyiniz...")
        driver.get(page_url)

        if DEBUG:
          print(f"[i] Sayfa {DEFAULT_MAX_SCROLLS} kere aşağı kaydırılıyor. Bekleyiniz...")
        else:
          print("Sayfa aşağı kaydırılıyor. Bekleyiniz...")

        scroll_page(driver, pause_time=DEFAULT_SCROLL_WAIT_TIME, max_scrolls=DEFAULT_MAX_SCROLLS)
             
        # time.sleep(wait_time)
        # searchedClassname = "album-holder"
        # try:
        #     # Maksimum DEFAULT_TIME_BEFORE_PAGE_LOAD kadar bekle, element DOM'a eklenene kadar
        #     album_holder = WebDriverWait(driver, wait_time).until(
        #         EC.presence_of_element_located((By.CLASS_NAME, searchedClassname))
        #     )
        #     print(f'[i] Aranan HTML key "{searchedClassname}" bulundu')
        # except Exception as e:
        #     print(f'[!] Aranan HTML key "{searchedClassname}" bulunamadı!')
        #     return

        if search_classes:
          found_element = None
          for classname in SEARCH_CLASS_NAMES:
              try:
                  found_element = WebDriverWait(driver, wait_time).until(
                      EC.presence_of_element_located((By.CLASS_NAME, classname))
                  )
                  print(f'[i] Aranan HTML key "{classname}" bulundu')
                  break
              except Exception:
                  print(f'[!] Aranan HTML key "{classname}" bulunamadı!')  

          if not found_element:
              print("[!] Aranan hiçbir HTML key bulunamadı!") 
        else:
          # search_classes yoksa, sayfanın tamamen yüklenmesini bekle
          try:
              WebDriverWait(driver, wait_time).until(
                  lambda d: d.execute_script("return document.readyState") == "complete"
              )
              print("[i] Sayfa tamamen yüklendi")
          except Exception:
              print("[!] Sayfa yüklenirken bir sorun oluştu")


        # indirilen HTML dosyasını kaydet
        if DEBUG:
            os.makedirs(TEMP_DIR, exist_ok=True)
            debug_html_path = os.path.join(TEMP_DIR, "page.html")

            with open(debug_html_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"[DEBUG] HTML dosyası kaydedildi: {debug_html_path}")
 
                 
        # Tüm linklerini al
        print("[2] Linkler ayıklanıyor...")

        # elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='get_image']")
        # links = [el.get_attribute("href") for el in elements]

        soup = BeautifulSoup(driver.page_source, "html.parser")
        a_tags = soup.find_all("a")
        links = [a.get("href") for a in a_tags if a.get("href")]        

        valid_links = filter_links_by_ext(links)
        return valid_links

    finally:
        if driver:
            driver.quit()

# -------------------------------------------------------------
def filter_links_by_ext(links: list, exts=None) -> list:
    """
    Belirli uzantılara göre linkleri filtreler.
    exts: ['jpg', 'jpeg', 'png', 'webp'] gibi bir liste
    """
    if exts is None:
        exts = EXTENSIONS

    allowed = tuple(f".{ext.lower()}" for ext in exts)
    filtered = [url for url in links if url.lower().endswith(allowed)]
    
    return filtered

# -------------------------------------------------------------
def download_links(links: list, outdir: str):
    os.makedirs(outdir, exist_ok=True)
    total = len(links)

    for idx, url in enumerate(links, start=1):
        filename = os.path.basename(url.rstrip('/'))
        filepath = os.path.join(outdir, filename)

        try:
            req = urllib.request.Request(url, headers=DEFAULT_HEADER)
            with urllib.request.urlopen(req) as response, open(filepath, "wb") as out_file:
                out_file.write(response.read())

            print(f"[{idx}/{total}] Kaydedildi: {filename}")

        except Exception as e:
            print(f"[{idx}/{total}] HATA: {filename} - {e}")

# -------------------------------------------------------------
def use_pageHtml_for_links() -> list[str]:
    """
    temp/page.html dosyasını parse ederek linkleri döndürür.
    Eğer dosya yoksa veya link bulunamazsa programı sonlandırır.
    """
    DEBUG_HTML = os.path.join(TEMP_DIR, "page.html")

    if not os.path.exists(DEBUG_HTML):
        print(f"[!] {DEBUG_HTML} bulunamadı.")
        input("Çıkmak için Enter'a basın...")
        sys.exit(1)

    print(f"[i] {DEBUG_HTML} dosyası parse ediliyor...")

    with open(DEBUG_HTML, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    # tüm linkler
    links = [a.get("href") for a in soup.select("a") if a.get("href")]

    # sadece <div class="images"> içindeki <a> etiketlerini seç
    # container = soup.find("div", class_="images")
    # if not container:
    #     print("[!] page.html içinde <div class='images'> bulunamadı.")
    #     input("Çıkmak için Enter'a basın...")
    #     sys.exit(1)

    # links = [a.get("href") for a in container.find_all("a", href=True)]

    if not links:
        print("[!] page.html içinde hiç link bulunamadı.")
        input("Çıkmak için Enter'a basın...")
        sys.exit(1)

    valid_links = filter_links_by_ext(links)
    print(f"[i] page.html üzerinden toplam {len(valid_links)} link bulundu.")
    return valid_links
