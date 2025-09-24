import os, shutil, zipfile, requests, platform
from defaults import DEFAULT_CHUNK_SIZE, DEFAULT_CHROME_DRIVER_MIN_SIZE

def get_latest_chromedriver_info():
    """
    API'den en güncel stable ChromeDriver bilgilerini döndürür.
    Bot gibi görünmemek için User-Agent header ekleniyor.
    """
    try:
        current_system = platform.system()
        machine = platform.machine().lower()

        # Platform ismini belirle
        if current_system == "Windows":
            platform_name = "win64"
            fallback_name = None
        elif current_system == "Darwin":
            if machine in ["arm64", "aarch64"]:
                platform_name = "mac-arm64"
                fallback_name = "mac-x64"
            else:
                platform_name = "mac-x64"
                fallback_name = None
        elif current_system == "Linux":
            platform_name = "linux64"
            fallback_name = None
        else:
            platform_name = "win64"
            fallback_name = None

        # API isteği, headers ekli
        api_url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(api_url, headers=headers, timeout=10)
        resp.raise_for_status()
        versions = resp.json()

        stable = versions.get("channels", {}).get("Stable", {})
        version = stable.get("version")
        driver_list = stable.get("downloads", {}).get("chromedriver", [])

        driver_url = None
        for item in driver_list:
            if item.get("platform") == platform_name:
                driver_url = item.get("url")
                break

        # Fallback varsa dene
        if not driver_url and fallback_name:
            for item in driver_list:
                if item.get("platform") == fallback_name:
                    driver_url = item.get("url")
                    print(f"[i] {platform_name} driver bulunamadı, fallback olarak {fallback_name} kullanılıyor.")
                    break

        if not driver_url:
            print(f"[!] Stable ChromeDriver bulunamadı: platform={platform_name}")
            return None, None

        return version, driver_url

    except requests.exceptions.RequestException as e:
        print(f"[!] ChromeDriver API isteği başarısız: {e}")
        return None, None
    except Exception as e:
        print(f"[!] Stable ChromeDriver bilgisi alınamadı: {e}")
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
# Test için çalıştır
# ----------------------------
if __name__ == "__main__":
    version, url = get_latest_chromedriver_info()
    print("Stable ChromeDriver version:", version)
    print("Download URL:", url)