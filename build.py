import os, sys, platform
import subprocess

from defaults import PROJECT_NAME

# ----------------------------
# Proje ayarları
# ----------------------------
VENV_DIR = os.path.join(os.getcwd(), "venv")  # proje dizini içinde venv
REQ_FILE = os.path.join(os.getcwd(), "requirements.txt")
MAIN_FILE = os.path.join(os.getcwd(), "main.py") # PyInstaller giriş noktası

# ----------------------------
# Platform kontrolü
# ----------------------------
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MAC = platform.system() == "Darwin"

# ----------------------------
# Sanal ortam oluşturma
# ----------------------------
def venv_exists():
    if not os.path.exists(VENV_DIR):
        return False
    # temel pip ve python dosyalarının varlığını kontrol et
    if IS_WINDOWS:
        return os.path.exists(os.path.join(VENV_DIR, "Scripts", "python.exe")) and \
               os.path.exists(os.path.join(VENV_DIR, "Scripts", "pip.exe"))
    else:
        return os.path.exists(os.path.join(VENV_DIR, "bin", "python")) and \
               os.path.exists(os.path.join(VENV_DIR, "bin", "pip"))

def create_venv():
    if not venv_exists():
        print(f"[i] Virtualenv yok veya eksik, oluşturuluyor: {VENV_DIR}")
        subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
    else:
        print(f"[i] Virtualenv zaten mevcut ve geçerli: {VENV_DIR}")

# ----------------------------
# Requirements yükleme
# ----------------------------
def install_requirements():
    if not os.path.exists(REQ_FILE):
        print(f"[!] {REQ_FILE} bulunamadı!")
        return

    print("[i] Requirements yükleniyor...")
    pip_exe = os.path.join(VENV_DIR, "Scripts", "pip.exe") if IS_WINDOWS else os.path.join(VENV_DIR, "bin", "pip")
    if not os.path.exists(pip_exe):
        pip_exe = os.path.join(VENV_DIR, "bin", "pip3")

    subprocess.check_call([pip_exe, "install", "--upgrade", "pip"])
    subprocess.check_call([pip_exe, "install", "-r", REQ_FILE])

# ----------------------------
# PyInstaller ile tek dosya derleme
# ----------------------------
def build_executable():
    print("[i] PyInstaller ile tek dosya derleniyor...")
    python_exe = os.path.join(VENV_DIR, "Scripts", "python.exe") if IS_WINDOWS else os.path.join(VENV_DIR, "bin", "python")

    entry_file = MAIN_FILE
    if not os.path.exists(entry_file):
        print(f"[!] {entry_file} bulunamadı, derleme yapılamıyor!")
        return

    cmd = [
        python_exe,
        "-m",
        "PyInstaller",
        "--clean",
        "--onefile",
        f"--name={PROJECT_NAME}",
        "--hidden-import=requests",
        "--hidden-import=selenium",
        entry_file
    ]
    try:
        subprocess.check_call(cmd)
        print("[i] Derleme tamamlandı. dist/ dizininde çalıştırılabilir dosya oluştu.")
    except Exception as e:
        print(f"[!] Derleme sırasında hata: {e}")
        sys.exit(1)

# ----------------------------
# Akış
# ----------------------------
def main():
    try:
        create_venv()
        install_requirements()
        build_executable()
    except KeyboardInterrupt:
        print("\n[i] İşlem kullanıcı tarafından durduruldu.")
        sys.exit(0)
    except Exception as e:
        print(f"[!] Beklenmeyen hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()