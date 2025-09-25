import os, sys, time, requests, subprocess, platform, stat, shutil
import undetected_chromedriver as uc
from pathlib import Path

from tools import download_file, extract_archive
from defaults import (
  DEBUG, PLATFORM_KEY,
  IS_WINDOWS, IS_LINUX, IS_MAC, 
  CHROMIUM_DIR, DRIVER_DIR, DIST_DIR,
  CHROMIUM_API_VERSIONS, CHROMIUM_API_WITH_DOWNLOADS, CHROMEDRIVER_STORAGE, HEADERS,
  DEFAULT_TIME_BEFORE_FILE_ERASE
)

# -------------------------
# Driver helpers
# -------------------------
def get_latest_driver_version():
    """En güncel chromedriver sürümünü döndürür (string) veya None."""
    try:
        r = requests.get(f"{CHROMEDRIVER_STORAGE}/LATEST_RELEASE", timeout=8, headers=HEADERS)
        r.raise_for_status()
        v = r.text.strip()
        if DEBUG: print(f"[DEBUG] ChromeDriver LATEST_RELEASE -> {v}")
        return v
    except Exception as e:
        if DEBUG: print(f"[DEBUG] ChromeDriver LATEST_RELEASE hatası: {e}")
        return None

def build_driver_url_candidates(version, system, machine):
    """
    Belirtilen version için olası chromedriver dosya adlarını üretir (tam URL'ler).
    Dönecek listeyi HEAD ile test edip ilk 200'i kullanacağız.
    """
    candidates = []
    # driver dosya isimleri örnek: chromedriver_mac64.zip, chromedriver_mac64_m1.zip, chromedriver_win32.zip, chromedriver_linux64.zip
    if system == "Windows":
        names = ["chromedriver_win32.zip", "chromedriver_win64.zip"]
    elif system == "Darwin":
        # mac intel ve olası m1/m2 adları; sıralama: M1/ARM dene sonra intel fallback
        if machine in ("arm64", "aarch64"):
            names = ["chromedriver_mac64_m1.zip", "chromedriver_mac_arm64.zip", "chromedriver_mac64.zip"]
        else:
            names = ["chromedriver_mac64.zip"]
    else:  # Linux
        names = ["chromedriver_linux64.zip", "chromedriver_linux64.zip"]

    for n in names:
        candidates.append(f"{CHROMEDRIVER_STORAGE}/{version}/{n}")
    return candidates

def find_working_driver_url(version, system, machine):
    """Verilen version için olası driver URL'lerini HEAD ile test eder ve ilk 200 döndüreni verir."""
    if not version:
        return None
    for url in build_driver_url_candidates(version, system, machine):
        try:
            if DEBUG: print(f"[DEBUG] ChomeDriver HEAD test: {url}")
            r = requests.head(url, timeout=6, headers=HEADERS)
            if r.status_code == 200:
                if DEBUG: print(f"[DEBUG] ChomeDriver bulundu.")
                return url
            else:
                if DEBUG: print(f"[DEBUG] Bu versiyon için ChomeDriver yok: {version}")
        except Exception as e:
            if DEBUG: print(f"[DEBUG] ChomeDriver HEAD hata: {e}")
    return None

# -------------------------
# Chromium helpers
# -------------------------
# def get_latest_chromium_version(channel="Stable", platform_name="Win"):
#     """
#     Belirtilen kanal için en son stabil Chromium sürümünü döndürür.
#     - channel: "Stable", "Beta", "Dev" vs.
#     - platform_name: "Win", "Mac", "Linux"
#     """
#     try:
#         r = requests.get(CHROMIUM_API_VERSIONS, timeout=8)
#         r.raise_for_status()
#         data = r.json()  # list of dicts
#         for entry in data:
#             if entry["os"].lower() == platform_name.lower():
#                 version = entry.get("versions", [])
#                 for v in version:
#                     if v.get("channel") == channel:
#                         return v.get("current_version")
#         return None
#     except Exception as e:
#         print(f"[!] Chromium sürümü alınamadı: {e}")
#         return None

def get_latest_chromium_version(platform_name: str):
    """
    Stable son sürümü ve platforma uygun indirilebilir linki döndürür.
    platform_name: 'Win', 'Linux', 'Mac'
    """
    try:
        r = requests.get(CHROMIUM_API_VERSIONS, timeout=10)
        r.raise_for_status()
        data = r.json()
        print(data.keys())

        stable = data.get("channels", {}).get("Stable", {})
        downloads = stable.get("downloads", {}).get(platform_name, [])
        if not downloads:
            return None
        # İlk paket linki (zip/portable)
        return downloads[0].get("url")
    except Exception as e:
        print(f"[!] Chromium sürümü alınamadı: {e}")
        return None

def try_get_chromium_url_from_known_downloads(version, system, machine):
    """
    known-good-versions-with-downloads.json içinden eşleşen version varsa platforma göre URL döndürür.
    döndürür: url veya None
    """
    try:
        r = requests.get(CHROMIUM_API_WITH_DOWNLOADS, timeout=8, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        # data['versions'] bir liste; en son en yeni olabilir. bulduğumuz version'la aynısı olan entry'yi ararız.
        for entry in data.get("versions", []):
            if entry.get("version") == version:
                chrome_downloads = entry.get("downloads", {}).get("chrome", [])
                platform_key = None
                if system == "Windows":
                    platform_key = "win64"
                elif system == "Darwin":
                    platform_key = "mac-arm64" if machine in ("arm64", "aarch64") else "mac-x64"
                else:
                    platform_key = "linux64"
                for it in chrome_downloads:
                    if it.get("platform") == platform_key:
                        if DEBUG: print(f"[DEBUG] Known-good kütüphanesinde uygun eşleşme bulundu v{version} -> {it.get('url')}")
                        return it.get("url")
                # Eğer platform spesifik yoksa, varsa herhangi bir url alabiliriz (fallback)
                if chrome_downloads:
                    if DEBUG: print(f"[DEBUG] Known-good kütüphanesinden uygun bir sürüm seçildi (fallback): {chrome_downloads[0].get('url')}")
                    return chrome_downloads[0].get("url")
        return None
    except Exception as e:
        if DEBUG: print(f"[DEBUG] Known-good kütüphane hatası: {e}")
        return None

def get_revision_from_version(version):
    """
    Sürüm -> Chromium revision çevirisi denemesi.
    Önce omahaproxy.deps.json?version=... dener, yoksa None döner.
    """
    try:
        url = f"https://omahaproxy.appspot.com/deps.json?version={version}"
        r = requests.get(url, timeout=8, headers=HEADERS)
        r.raise_for_status()
        j = r.json()
        # Denenecek olası anahtarlar (bazı endpointlerde farklı isimler oluyor)
        for key in ("chromium_base_position", "chromium_revision", "chromium_base_position"):
            if key in j and j[key]:
                rev = str(j[key])
                if DEBUG: print(f"[DEBUG] get_revision_from_version: {version} -> {rev} (key={key})")
                return rev
        # fallback: bazı durumlarda 'chromium_base_position' yoktur -> None
        return None
    except Exception as e:
        if DEBUG: print(f"[DEBUG] get_revision_from_version hata: {e}")
        return None

def build_chromium_url_by_revision(revision, system, machine):
    """
    Revision'a göre snapshot URL'lerini dener. Birkaç olası dosya adı ile HEAD kontrolü yapar.
    İlk çalışan URL döner veya None.
    """
    if not revision:
        return None

    base = "https://commondatastorage.googleapis.com/chromium-browser-snapshots"
    if system == "Windows":
        folder = "Win"
        candidates = ["chrome-win.zip", "chrome-win64.zip"]
    elif system == "Darwin":
        folder = "Mac"
        # mac için farklı olası paket isimleri
        candidates = ["chrome-mac.zip", "chrome-mac-arm.zip", "chrome-mac-arm64.zip", "chrome-mac.zip"]
    else:
        folder = "Linux"
        candidates = ["chrome-linux.zip", "chrome-linux64.zip", "chrome-linux.tar.xz"]

    for name in candidates:
        url = f"{base}/{folder}/{revision}/{name}"
        try:
            if DEBUG: print(f"[DEBUG] chromium revision HEAD test: {url}")
            r = requests.head(url, timeout=6, headers=HEADERS)
            if r.status_code == 200:
                if DEBUG: print(f"[DEBUG] chromium revision url found: {url}")
                return url
        except Exception as e:
            if DEBUG: print(f"[DEBUG] chromium HEAD hata: {e}")
    return None

def build_chromium_url_from_version(version, system, machine):
    """
    Önce known-good-with-downloads.json'dan URL dene; yoksa revision bulup snapshot URL dene.
    """
    # 1) known-good downloads JSON içinde var mı?
    url = try_get_chromium_url_from_known_downloads(version, system, machine)
    if url:
        return url

    # 2) revision dene (omahaproxy)
    rev = get_revision_from_version(version)
    if rev:
        url = build_chromium_url_by_revision(rev, system, machine)
        if url:
            return url

    # 3) fallback: yoksa None
    if DEBUG: print(f"[DEBUG] build_chromium_url_from_version: URL bulunamadı for version={version}")
    return None

def get_chromium_paths(dist_dir: str):
    """
    OS'e göre chromium klasör ve binary path döner.
    """
    base_dir = Path(dist_dir) / "chromium"

    system = platform.system().lower()
    if system == "windows":
        chromium_dir = base_dir / "chrome-win64"
        chromium_path = chromium_dir / "chrome.exe"
    elif system == "linux":
        chromium_dir = base_dir / "chrome-linux"
        chromium_path = chromium_dir / "chrome"
    elif system == "darwin":  # macOS
        chromium_dir = base_dir / "chrome-mac"
        chromium_path = chromium_dir / "Chromium.app/Contents/MacOS/Chromium"
    else:
        raise RuntimeError(f"Desteklenmeyen platform: {system}")

    return base_dir, chromium_dir, chromium_path

# -------------------------------------------------------------------------
def move_unusable_chromium(chromium_base, old_suffix="_old"):
    """
    Uyumsuz Chromium klasörünü güvenli şekilde _old olarak taşır.
    """
    old_path = chromium_base.with_name(chromium_base.name + old_suffix)

    if old_path.exists():
        print(f"[i] Eski uyumsuz {old_suffix} klasörü siliniyor: {old_path}")
        remove_readonly_and_delete(old_path)
        time.sleep(1)

    print("[i] Uyumsuz Chromium taşınıyor...")
    try:
        shutil.move(str(chromium_base), str(old_path))
        if DEBUG:
          print(f"[+] Taşındı: {chromium_base} → {old_path}")
    except PermissionError:
        print("[!] Taşıma başarısız, read-only dosyalar olabilir, elle müdehale edilmeli.")
    except Exception as e:
        print(f"[!] Chromium taşıma hatası: {e}")

def rmtree_windows_safe(path: str):
    """Windows'ta readonly ve kilitli dosyalar için güvenli rmtree"""
    if not os.path.exists(path):
        return

    for entry in os.scandir(path):
        full_path = entry.path
        try:
            if entry.is_dir(follow_symlinks=False):
                rmtree_windows_safe(full_path)
            else:
                os.chmod(full_path, stat.S_IWRITE)
                os.remove(full_path)
        except Exception as e:
            print(f"[!] Silme hatası: {full_path} - {e}")

    try:
        os.rmdir(path)
    except Exception as e:
        print(f"[!] Klasör silme hatası: {path} - {e}")

def remove_readonly_and_delete(p):
    for root, dirs, files in os.walk(p, topdown=False):
        for name in files:
            filepath = os.path.join(root, name)
            os.chmod(filepath, stat.S_IWRITE)
            os.remove(filepath)
        for name in dirs:
            dirpath = os.path.join(root, name)
            os.chmod(dirpath, stat.S_IWRITE)
            os.rmdir(dirpath)
    os.rmdir(p)

# -------------------------------------------------------------------------
def is_uc_compatible(chromium_version: str) -> bool:
    """
    UC uyumlu mu diye kontrol eder.
    chromium_version: örn. "Chromium 114.0.5735.90"
    """
    # Sadece versiyon numarasını al
    parts = chromium_version.split()
    if len(parts) < 2:
        return False
    ver = parts[1]  # "114.0.5735.90"

    # UC genellikle son sürümleri destekler, mesela >= 114
    major = int(ver.split('.')[0])
    return major >= 114

def kill_chromium_processes(chromium_path):
    system = platform.system()

    if system == "Windows":
        # Windows'ta taskkill ile exe adı veya tam path üzerinden kapat
        exe_name = "chrome.exe"  # veya chromium_path.name
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", exe_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            print(f"[i] Arka plandaki Chromium (Windows) kapatıldı: {exe_name}")
        except Exception as e:
            print(f"[!] Windows Chromium kapatma hatası: {e}")
    else:
        # Linux / Mac
        try:
            subprocess.run(
                ["pkill", "-f", str(chromium_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            print(f"[i] Arka plandaki Chromium (Unix) kapatıldı: {chromium_path}")
        except Exception as e:
            print(f"[!] Unix Chromium kapatma hatası: {e}")

def ensure_uc_chromium(dist_dir: str):
    """
    UC için uyumlu Chromium varsa onu kullanır.
    Uyumsuz ise dist klasörünü temizler ve UC kendi uyumlu Chromium'unu indirir.
    """
    chromium_dir = Path(dist_dir) / "chromium" / "chrome-win64"
    chromium_path = chromium_dir / "chrome.exe"

    chromium_unusable = False
    need_download = True
    driver = None

    # Mevcut binary var mı ve başlatılabiliyor mu
    if chromium_path.exists():
        try:
            # subprocess ile sürümü al
            # result = subprocess.run(
            #     [str(chromium_path), "--version"],
            #     capture_output=True,
            #     text=True
            # )
            # version_str = result.stdout.strip()  # Örn: "Chromium 114.0.5735.90"
            # print(f"[i] Mevcut Chromium sürümü: {version_str}")

            # # Burada UC için sürüm kontrolü yapabilirsin
            # # Örn: ChromeDriver 140 uyumlu değilse need_download = True
            # if is_uc_compatible(version_str):
            #     print(f"[i] Mevcut Chromium UC ile uyumlu")
            #     need_download = False
            # else:
            #     print(f"[!] Mevcut Chromium UC ile uyumsuz")
            #     need_download = True

            # Tarayıcıyı çalıştırıp bilgi al
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument("--headless=new")  # veya "--headless"
            driver = uc.Chrome(
                browser_executable_path=str(chromium_path),
                options=chrome_options
            )

            info = driver.capabilities
            print(f"[i] Mevcut Chromium UC ile uyumlu: {info['browserVersion']}")
            need_download = False
        except Exception as e:
            chromium_unusable = True
            print("[i] UC mevcut Chromium ile başlatılamıyor.")

            if DEBUG:
                print(f"[!] DEBUG Hata: {e}")
        finally:
          print("[i] Arka plandaki çalışan Chromium var mı bakılıyor...")
          if driver is not None:
              try:
                  driver.quit()
              except Exception:
                  pass

          kill_chromium_processes(chromium_path)
          time.sleep(DEFAULT_TIME_BEFORE_FILE_ERASE)

    # Uyumsuz sürümü başka klasöre taşıma
    chromium_base, chromium_dir, chromium_path = get_chromium_paths(DIST_DIR)
    if chromium_unusable and chromium_base.exists():
        move_unusable_chromium(chromium_base)

    # Uygun sürüm indirilmeyecekse çık
    if not need_download:
        print("[i] Mevcut Chromium UC ile uyumlu, indirme atlandı.")
        return

    # Uygun sürümü indir
    print("[i] UC uyumlu Chromium indiriliyor...")
    try:
        # API'den son stable sürümü al
        r = requests.get(CHROMIUM_API_VERSIONS, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        stable = data['channels']['Stable']
        downloads = stable['downloads']

        chromium_list = downloads.get('chrome', {}).get(PLATFORM_KEY, [])
        if not chromium_list:
            print("[!] Bu platform için UC Chromium bulunamadı.")
            return

        chromium_info = chromium_list[0]  # ilk eleman
        zip_url = chromium_info['url']
        zip_name = os.path.basename(zip_url)
        zip_path = Path(dist_dir) / "chromium" / zip_name

        # indirilecek klasör
        os.makedirs(chromium_dir, exist_ok=True)

        # indir
        download_file(zip_url, zip_path, min_size=10_000_000)  # ~10MB altı yok say

        # aç
        if extract_archive(zip_path, chromium_dir):
            # indirilen zip'i sil
            os.remove(zip_path)
            print(f"[i] UC uyumlu Chromium hazır: {chromium_path}")
        else:
            print("[!] UC Chromium açılırken hata oluştu.")

        print(f"[i] UC uyumlu Chromium hazır: {chromium_path}")

    except Exception as e:
        print("[!] UC Chromium indirilemedi:", e)
        input("Çıkmak için Enter'a basın...")
        sys.exit(1)

    return chromium_path

# ----------------------------
# Check compatible versions 
# ----------------------------
def detect_chromium_and_driver_versions():
    """
    - Stable Chromium sürümünü alır (last-known-good-versions.json).
    - O sürüme uygun chromedriver varsa alır; yoksa LATEST_RELEASE driver alır.
    - Chromedriver sürümüne göre chromium URL'si bulmaya çalışır (known-good-with-downloads veya revision -> snapshot).
    Döndürür: chromium_version, driver_version, driver_url, chromium_url
    """
    print("[*] Chromium ve ChromeDriver kontrol ediliyor...")

    system = platform.system()
    machine = platform.machine()

    chromium_version = None
    driver_version = None
    driver_url = None
    chromium_url = None

    # 1) stable chromium version al
    try:
        r = requests.get(CHROMIUM_API_VERSIONS, timeout=8, headers=HEADERS)
        r.raise_for_status()
        j = r.json()
        # last-known-good-versions.json tipik olarak channels->Stable->version içerir
        chromium_version = j.get("channels", {}).get("Stable", {}).get("version")
        if DEBUG: print(f"[DEBUG] CHROMIUM_API_VERSIONS response -> keys: {list(j.keys())}")
        print(f"[i] Stable Chromium son sürümü: {chromium_version}")
        print(f"[i] Bu sürüm ile uyumlu ChromeDriver aranıyor...")
    except Exception as e:
        print(f"[!] Chromium son sürümü alınamadı: {e}")
        return None, None, None, None

    # 2) Bu chromium_version için chromedriver var mı?
    candidate_driver_url = find_working_driver_url(chromium_version, system, machine)
    if candidate_driver_url:
        driver_version = chromium_version
        driver_url = candidate_driver_url
        # chromium_url: try known downloads or revision
        chromium_url = build_chromium_url_from_version(chromium_version, system, machine)
        print(f"[+] Chromium ile uyumlu ChromeDriver bulundu: {driver_version}")
        return chromium_version, driver_version, driver_url, chromium_url

    # 3) Uyumlu driver yok -> en güncel driver al
    print("[!] Uygun ChromeDriver sürümü bulunamadı!")
    if DEBUG: print(f"[i] ChromeDriver son sürümü ile uyumlu Chromium aranıyor...")
    latest_driver = get_latest_driver_version()
    if not latest_driver:
        print("[!] En güncel ChromeDriver sürümü alınamadı!")
        return None, None, None, None

    driver_version = latest_driver
    driver_url = find_working_driver_url(driver_version, system, machine)
    if not driver_url:
        print("[!] Bu platform için ChromeDriver sürümü bulunamadı! (latest)")
        return None, None, None, None

    # Chromium'ı driver_version'a göre bul
    chromium_version = driver_version
    chromium_url = build_chromium_url_from_version(chromium_version, system, machine)
    print(f"[i] En güncel ChromeDriver ve buna uyumlu Chromium indirilecek: {driver_version}")
    return chromium_version, driver_version, driver_url, chromium_url

def build_snapshot_url(revision, system, machine):
    """
    Chromium snapshot deposundan platforma uygun URL oluşturur.
    revision: Chromium sürümünün revision numarası veya driver sürümü.
    """
    if system == "Windows":
        zip_name = "chrome-win.zip"
        platform_folder = "Win"
    elif system == "Darwin":
        zip_name = "chrome-mac-arm.zip" if machine in ["arm64", "aarch64"] else "chrome-mac.zip"
        platform_folder = "Mac"
    elif system == "Linux":
        zip_name = "chrome-linux.zip"
        platform_folder = "Linux"
    else:
        raise ValueError(f"Unsupported system: {system}")

    return f"https://commondatastorage.googleapis.com/chromium-browser-snapshots/{platform_folder}/{revision}/{zip_name}"

# -------------------------
# Installer helpers
# -------------------------
def find_chromium_binary(chromium_dir):
    """chromium_dir içinde OS’ye göre executable bulur"""
    if IS_WINDOWS:
        for root, dirs, files in os.walk(chromium_dir):
            if "chrome.exe" in files:
                return os.path.join(root, "chrome.exe")
    elif IS_MAC:
        for root, dirs, files in os.walk(chromium_dir):
            if "Chromium" in files and root.endswith("MacOS"):
                return os.path.join(root, "Chromium")
    elif IS_LINUX:
        for root, dirs, files in os.walk(chromium_dir):
            if "chrome" in files:
                return os.path.join(root, "chrome")
    return None

def find_chromedriver_binary(driver_dir):
    """driver_dir içinde OS’ye göre executable bulur"""
    if IS_WINDOWS:
        exe_name = "chromedriver.exe"
    elif IS_MAC:
        exe_name = "chromedriver_mac"
    else:
        exe_name = "chromedriver"
    for root, dirs, files in os.walk(driver_dir):
        if exe_name in files:
            return os.path.join(root, exe_name)
    return None

# -------------------------
# Installer
# -------------------------
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
