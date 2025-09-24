import re, requests, platform
from defaults import DEBUG

# API'ler
CHROMIUM_API_VERSIONS = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json"
CHROMIUM_API_WITH_DOWNLOADS = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
CHROMEDRIVER_STORAGE = "https://chromedriver.storage.googleapis.com"

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"}

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
    print(f"[i] En güncel ChromeDriver kullanılacak: {driver_version}")
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
