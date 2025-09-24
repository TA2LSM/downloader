import os, shutil, zipfile, requests, platform
from defaults import DEBUG, CHROMEDRIVER_BASE, DEFAULT_CHUNK_SIZE, DEFAULT_CHROME_DRIVER_MIN_SIZE

def get_latest_driver_version():
    """En güncel ChromeDriver sürümünü döndürür."""
    url = f"{CHROMEDRIVER_BASE}/LATEST_RELEASE"
    return requests.get(url, timeout=5).text.strip()

# def build_driver_url(version: str, system: str, machine: str) -> str:
#     """ChromeDriver indirme URL'si oluşturur."""
#     if system == "Windows":
#         suffix = "win32.zip"
#     elif system == "Darwin":
#         if machine in ["arm64", "aarch64"]:
#             print("[i] ARM Mac için driver yok, fallback x64 kullanılıyor...")
#         suffix = "mac64.zip"
#     elif system == "Linux":
#         suffix = "linux64.zip"
#     else:
#         suffix = "win32.zip"
#     return f"{CHROMEDRIVER_BASE}/{version}/chromedriver_{suffix}"

def build_driver_url(version, system, machine):
    """
    Chromium sürümüne göre ChromeDriver URL'sini üretir.
    """
    if system == "Windows":
        plat = "win64"
    elif system == "Darwin":
        plat = "mac64" if machine != "arm64" else "mac64"  # fallback: ARM Mac için x64 kullan
    elif system == "Linux":
        plat = "linux64"
    else:
        plat = "win64"
    return f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_{plat}.zip"

# https://chromedriver.storage.googleapis.com/index.html
# def get_latest_chromedriver_info():
#     """
#     API'den en güncel stable ChromeDriver bilgilerini döndürür.
#     ARM Mac için x64 fallback uygulanır.
#     """
#     try:
#         current_system = platform.system()
#         machine = platform.machine()

#         # Platform ismini belirle
#         if current_system == "Windows":
#             platform_name = "win64"
#             fallback_name = None
#         elif current_system == "Darwin":
#             if machine in ["arm64", "aarch64"]:
#                 platform_name = "mac-arm64"
#                 fallback_name = "mac-x64"  # ARM Mac fallback
#             else:
#                 platform_name = "mac-x64"
#                 fallback_name = None
#         elif current_system == "Linux":
#             platform_name = "linux64"
#             fallback_name = None
#         else:
#             platform_name = "win64"
#             fallback_name = None

#         if DEBUG:
#             print(f"[DEBUG] current_system={current_system}, machine={machine}")
#             print(f"[DEBUG] platform_name={platform_name}, fallback_name={fallback_name}")

#         api_url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json"
#         # api_url = CHROME_DRIVER_URL
#         headers = {
#             "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
#         }
#         resp = requests.get(api_url, headers=headers, timeout=10)
#         if resp.status_code != 200:
#             print(f"[!] Chrome for Testing API alınamadı, status code: {resp.status_code}")
#             return None, None

#         versions = resp.json()
#         stable = versions.get("channels", {}).get("Stable", {})
#         version = stable.get("version")
#         driver_list = stable.get("downloads", {}).get("chromedriver", [])

#         if DEBUG:
#             print(f"[DEBUG] Stable version={version}, driver_list length={len(driver_list)}")

#         # driver URL'sini bul
#         driver_url = None
#         for item in driver_list:
#             if item.get("platform") == platform_name:
#                 driver_url = item.get("url")
#                 break

#         # ARM Mac fallback
#         if not driver_url and fallback_name:
#             for item in driver_list:
#                 if item.get("platform") == fallback_name:
#                     driver_url = item.get("url")
#                     if DEBUG:
#                         print(f"[DEBUG] Fallback driver_url kullanıldı: {driver_url}")
#                     break

#         if not driver_url:
#             print(f"[!] Stable ChromeDriver bulunamadı: platform={platform_name}")
#             return None, None

#         return version, driver_url

#     except Exception as e:
#         print(f"[!] Stable ChromeDriver bilgisi alınamadı: {e}")
#         return None, None


def get_latest_chromedriver_info():
    """
    En güncel stable ChromeDriver bilgilerini döndürür.
    ARM Mac (arm64) için fallback olarak mac-x64 kullanır.
    """
    try:
        current_system = platform.system()
        machine = platform.machine()
        print(f"[DEBUG] current_system={current_system}, machine={machine}")

        # Platform ismini belirle
        if current_system == "Windows":
            platform_name = "win64"
            fallback_name = None
        elif current_system == "Darwin":
            if machine in ["arm64", "aarch64"]:
                platform_name = "mac-x64"  # ARM Mac fallback
                fallback_name = None
            else:
                platform_name = "mac-x64"
                fallback_name = None
        elif current_system == "Linux":
            platform_name = "linux64"
            fallback_name = None
        else:
            platform_name = "win64"
            fallback_name = None

        api_url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json"
        resp = requests.get(api_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            print(f"[!] Chrome for Testing API alınamadı, status code: {resp.status_code}")
            return None, None

        versions = resp.json()
        stable = versions.get("channels", {}).get("Stable", {})
        version = stable.get("version")
        driver_list = stable.get("downloads", {}).get("chromedriver", [])

        print(f"[DEBUG] Stable version={version}, driver_list length={len(driver_list)}")

        driver_url = None
        for item in driver_list:
            if item.get("platform") == platform_name:
                driver_url = item.get("url")
                break

        # Eğer fallback gerekiyorsa
        if not driver_url and fallback_name:
            for item in driver_list:
                if item.get("platform") == fallback_name:
                    driver_url = item.get("url")
                    print(f"[DEBUG] Fallback driver kullanıldı: {fallback_name}")
                    break

        if not driver_url:
            print(f"[!] Stable ChromeDriver bulunamadı: platform={platform_name}")
        return version, driver_url

    except Exception as e:
        print(f"[!] Stable ChromeDriver bilgisi alınamadı: {e}")
        return None, None


# def get_chromedriver_for_chromium(chromium_version):
#     """
#     Chromium sürümüne uygun ChromeDriver sürümünü bulur.
#     Eğer ARM Mac için driver yoksa x64 fallback kullanır.
#     """
#     major_version = chromium_version.split(".")[0]  # örn. "140"
#     system = platform.system()
#     machine = platform.machine()

#     # Platform adı belirleme
#     if system == "Windows":
#         platform_name = "win32"  # veya win64 driver varsa onu kullan
#     elif system == "Darwin":
#         if machine in ["arm64", "aarch64"]:
#             platform_name = "mac64_m1"  # ARM Mac
#             fallback_name = "mac64"      # Intel Mac
#         else:
#             platform_name = "mac64"
#             fallback_name = None
#     elif system == "Linux":
#         platform_name = "linux64"
#         fallback_name = None
#     else:
#         platform_name = "win32"
#         fallback_name = None

#     # ChromeDriver Storage API URL
#     # Major version mapping kullanıyoruz: https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major}
#     driver_version_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
#     try:
#         resp = requests.get(driver_version_url, timeout=10)
#         resp.raise_for_status()
#         driver_version = resp.text.strip()
#     except Exception as e:
#         print(f"[!] ChromeDriver versiyonu alınamadı: {e}")
#         return None, None

#     driver_download_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_{platform_name}.zip"

#     # Eğer ARM Mac ve URL yoksa fallback deneyelim
#     if system == "Darwin" and machine in ["arm64", "aarch64"]:
#         check = requests.head(driver_download_url)
#         if check.status_code != 200 and fallback_name:
#             print(f"[i] ARM Mac için driver yok, fallback x64 kullanılıyor...")
#             platform_name = fallback_name
#             driver_download_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_{platform_name}.zip"

#     return driver_version, driver_download_url


def get_chromedriver_for_chromium(chromium_version: str):
    """
    Belirtilen Chromium sürümüne karşılık gelen ChromeDriver URL'sini döndürür.
    Eğer tam eşleşme yoksa en güncel ChromeDriver alınır ve onun versiyonu döndürülür.
    """
    try:
        base_url = "https://chromedriver.storage.googleapis.com"
        machine = platform.machine()
        system = platform.system()

        if system == "Windows":
            suffix = "win32.zip"
        elif system == "Darwin":
            if machine in ["arm64", "aarch64"]:
                print("[i] ARM Mac için driver yok, fallback x64 kullanılıyor...")
            suffix = "mac64.zip"
        elif system == "Linux":
            suffix = "linux64.zip"
        else:
            suffix = "win32.zip"

        # Önce birebir Chromium sürümüne karşılık gelen driver'ı dene
        driver_url = f"{base_url}/{chromium_version}/chromedriver_{suffix}"
        resp = requests.head(driver_url, timeout=5)
        if resp.status_code == 200:
            return chromium_version, driver_url

        # Olmazsa → en güncel ChromeDriver sürümünü al
        latest_url = f"{base_url}/LATEST_RELEASE"
        latest_version = requests.get(latest_url, timeout=5).text.strip()

        print(f"[!] Chromium {chromium_version} için ChromeDriver bulunamadı.")
        print(f"[+] En güncel ChromeDriver kullanılacak: {latest_version}")

        driver_url = f"{base_url}/{latest_version}/chromedriver_{suffix}"
        return latest_version, driver_url

    except Exception as e:
        print(f"[!] ChromeDriver sürümü alınamadı: {e}")
        return None, None


def get_compatible_chromedriver_url(chromium_version):
    """
    Chromium sürümüne uygun ChromeDriver zip URL'sini döndürür.
    """
    try:
        api_url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json"
        resp = requests.get(api_url, timeout=10)
        if resp.status_code != 200:
            print(f"[!] Chrome for Testing API alınamadı, status code: {resp.status_code}")
            return None
        
        versions = resp.json()
        major_version = chromium_version.split(".")[0]

        # "channels" içinden ara
        channels = versions.get("channels", {})
        for channel_name, data in channels.items():
            if data.get("version", "").startswith(major_version):
                driver_downloads = data.get("downloads", {}).get("chromedriver", [])
                for item in driver_downloads:
                    if item.get("platform") == "win64":
                        return item.get("url")

        print(f"[!] Chromium v{chromium_version} için uyumlu ChromeDriver bulunamadı!")
        return None

    except Exception as e:
        print(f"[!] ChromeDriver URL alınamadı: {e}")
        return None


def download_chromedriver():
    print("[+] Chrome Driver kontrol ediliyor...")
    zip_path = os.path.join(os.getcwd(), "chromedriver.zip")
    
    # Daha önce indirilmiş ve yeterli boyutta bir zip varsa indirmeyi atla
    if os.path.exists(zip_path) and os.path.getsize(zip_path) >= DEFAULT_CHROME_DRIVER_MIN_SIZE:
        print("[i] ChromeDriver zip zaten mevcut. Açılıyor...")
    else:
        print("[+] ChromeDriver bulunamadı veya hatalı, indiriliyor...")
        try:
            # Chromium sürümünü al
            print("[!] Chromium versionu okunuyor...")
            chromium_version = get_chromium_version(chromium_path)
            
            driver_zip_url = None
            if chromium_version:
                driver_zip_url = get_compatible_chromedriver_url(chromium_version)
            
            # Uyumlu driver bulunamadıysa fallback yap
            if not driver_zip_url:
                print("[!] Mevcut Chromium siliniyor. Stable ChromeDriver sürümüne göre Chromium indirilecek...")
                if os.path.exists(chromium_dir):
                    shutil.rmtree(chromium_dir, ignore_errors=True)

                stable_version, stable_driver_url = get_latest_chromedriver_info()
                if not stable_driver_url:
                    input("Stable ChromeDriver da bulunamadı, Enter ile çıkış yap...")
                    return
                
                print(f"[+] Stable ChromeDriver bulundu: {stable_version}")
                driver_zip_url = stable_driver_url

                # Stable versiyona uygun Chromium indir
                print(f"[+] Stable Chromium ({stable_version}) indiriliyor...")
                download_chromium(stable_version)  # burada download_chromium fonksiyonunu stable_version'a göre uyarlayabilirsin

            # Driver indir
            print(f"[+] ChromeDriver indiriliyor: {driver_zip_url}")
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(driver_zip_url, stream=True, headers=headers, timeout=30)
            if r.status_code != 200:
                print(f"[!] ChromeDriver indirilemedi, status code: {r.status_code}")
                input("Çıkmak için Enter'a basın...")
                return

            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(DEFAULT_CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        f.flush()

            if os.path.getsize(zip_path) < DEFAULT_CHROME_DRIVER_MIN_SIZE:
                print("[!] İndirilen dosya küçük, muhtemelen hatalı.")
                os.remove(zip_path)
                return

        except Exception as e:
            print(f"[!] ChromeDriver indirilemedi: {e}")
            input("Çıkmak için Enter'a basın...")
            return

    # Zip’i aç
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.getcwd())
        os.remove(zip_path)
        print("[+] ChromeDriver açıldı ve kullanıma hazır.\n")
    except Exception as e:
        print(f"[!] Zip açılamadı: {e}\n")
        input("Çıkmak için Enter'a basın...")
        return

# ----------------------------
# Self Test
# ----------------------------
# if __name__ == "__main__":
#     version, url = get_latest_chromedriver_info()
#     print(f"Stable ChromeDriver version: {version}")
#     print(f"Download URL: {url}")

if __name__ == "__main__":
    chromium_version = "140.0.7339.207"  # Örnek Chromium sürümü
    # chromium_version = "112.0.5615.49"  # Örnek Chromium sürümü
    driver_version, url = get_chromedriver_for_chromium(chromium_version)
    print(f"Chromedriver version: {driver_version}")
    print(f"Download URL: {url}")