import os, requests, zipfile


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


def unzip(zip_path, extract_to):
    """
    Zip dosyasını extract_to klasörüne açar.
    """
    try:
        if not os.path.exists(zip_path):
            print(f"[!] Zip dosyası bulunamadı: {zip_path}")
            return False

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

        print(f"[+] Açıldı: {zip_path} → {extract_to}")
        return True
    except Exception as e:
        print(f"[!] Zip açma hatası: {e}")
        return False


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

