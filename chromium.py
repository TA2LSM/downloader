import os, sys, zipfile, shutil, requests  # HTTP istekleri için
from defaults import DEFAULT_CHUNK_SIZE, DEFAULT_CHROMIUM_MIN_SIZE

def build_chromium_url(version, system, machine):
    """
    Chromium sürümüne göre platforma uygun indirme URL'sini üretir.
    """
    try:
        resp = requests.get(CHROMIUM_API, timeout=5).json()
        chrome_downloads = resp["channels"]["Stable"]["downloads"].get("chrome", [])
        platform_name = None
        if system == "Windows":
            platform_name = "win64"
        elif system == "Darwin":
            # ARM Mac için fallback x64 kullan
            platform_name = "mac-x64" if machine in ["arm64", "aarch64"] else "mac-x64"
        elif system == "Linux":
            platform_name = "linux64"
        for item in chrome_downloads:
            if item["platform"] == platform_name:
                return item["url"]
    except Exception as e:
        print(f"[!] Chromium URL alınamadı: {e}")
    return None

def get_chromium_version(chromium_path):
    """
    Chromium sürümünü exe'nin metadata'sından alır (Windows).
    Eğer Windows değilse subprocess fallback ile dener.
    """
    if not os.path.exists(chromium_path):
        print(f"[!] Chromium exe bulunamadı: {chromium_path}")
        return None

    if sys.platform.startswith("win"):
        try:
            import ctypes
            import ctypes.wintypes as wintypes

            size = ctypes.windll.version.GetFileVersionInfoSizeW(chromium_path, None)
            if not size:
                print("[!] Versiyon bilgisi bulunamadı.")
                return None

            res = ctypes.create_string_buffer(size)
            ctypes.windll.version.GetFileVersionInfoW(chromium_path, 0, size, res)

            # VS_FIXEDFILEINFO yapısını al
            r = wintypes.LPVOID()
            l = wintypes.UINT()
            ctypes.windll.version.VerQueryValueW(res, "\\", ctypes.byref(r), ctypes.byref(l))

            if not r:
                print("[!] Versiyon bilgisi okunamadı.")
                return None

            ffi = ctypes.cast(r, ctypes.POINTER(ctypes.c_uint * (l.value // ctypes.sizeof(ctypes.c_uint)))).contents

            ms = ffi[4]
            ls = ffi[5]
            version = f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
            print(f"[i] Chromium versiyonu: {version}")
            return version

        except Exception as e:
            print(f"[!] Exe metadata'dan versiyon okunamadı: {e}")

    # Windows değilse fallback subprocess
    try:
        import subprocess
        result = subprocess.run([chromium_path, "--version"], capture_output=True, text=True)
        output = result.stdout.strip()
        if output:
            version = output.split()[1]
            print(f"[i] Chromium versiyon bulundu (subprocess): {version}")
            return version
        else:
            print("[!] Chromium --version çıktısı boş.")
            return None
    except Exception as e:
        print(f"[!] Chromium version okunamadı (subprocess fallback): {e}")
        return None


def download_chromium(version=None):
    """
    Portable Chromium indirir.
    Eğer version verilirse Chrome for Testing URL'inden stable sürüm indirilir.
    Verilmezse snapshot (LAST_CHANGE) indirir.
    """
    print("[+] Portable Chromium kontrol ediliyor...")
    try:
        cwd = os.getcwd()
        zip_path = os.path.join(cwd, "chromium.zip")

        if os.path.exists(zip_path) and os.path.getsize(zip_path) >= DEFAULT_CHROMIUM_MIN_SIZE:
            print("[i] Chromium zip zaten mevcut, açılıyor...")
        else:
            if os.path.exists(zip_path):
                print("[!] Daha önceki zip dosyası hatalı, tekrar indiriliyor.")
                os.remove(zip_path)

            if version:
                print(f"[+] Stable Chromium indiriliyor... ({version})")
                # Chrome for Testing build URL
                zip_url = f"https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{version}/win64/chrome-win64.zip"
            else:
                print("[+] Portable Chromium bulunamadı. Snapshot indiriliyor...")
                revision_url = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win/LAST_CHANGE"
                resp = requests.get(revision_url, timeout=10)
                if resp.status_code != 200:
                    print(f"[!] Revision numarası alınamadı, status code: {resp.status_code}")
                    input("Çıkmak için Enter'a basın...")
                    return
                revision = resp.text.strip()
                print(f"[+] Kullanılacak Chromium snapshot revision: {revision}")
                zip_url = f"https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win/{revision}/chrome-win.zip"

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(zip_url, stream=True, headers=headers, timeout=30)
            if r.status_code != 200:
                print(f"[!] Dosya indirilemedi, status code: {r.status_code}")
                input("Çıkmak için Enter'a basın...")
                return

            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(DEFAULT_CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        f.flush()

            if os.path.getsize(zip_path) < DEFAULT_CHROMIUM_MIN_SIZE:
                print("[!] İndirilen dosya küçük, muhtemelen hatalı.")
                os.remove(zip_path)
                return

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(cwd)
        os.remove(zip_path)

        extracted = os.path.join(cwd, "chrome-win") if not version else os.path.join(cwd, "chrome-win64")
        if os.path.exists(extracted):
            if os.path.exists(chromium_dir):
                shutil.rmtree(chromium_dir, ignore_errors=True)
            os.makedirs(chromium_dir, exist_ok=True)
            shutil.move(extracted, chromium_dir)

        print("[+] Portable Chromium açıldı ve kullanıma hazır.")

    except Exception as e:
        print(f"[!] Chromium açılamadı: {e}\n")
        input("Çıkmak için Enter'a basın...")
        return

