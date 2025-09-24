# run.py
import os, sys, subprocess, platform
from defaults import PROJECT_NAME, REQ_FILE

# ----------------------------
# Kullanıcı dizininde merkezi venv
# ----------------------------
USER_HOME = os.path.expanduser("~")
VENV_BASE = os.path.join(USER_HOME, "venvs")
VENV_DIR = os.path.join(VENV_BASE, PROJECT_NAME)

# ----------------------------
# Platform kontrolü
# ----------------------------
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MAC = platform.system() == "Darwin"

req_path = os.path.join(os.path.dirname(__file__), REQ_FILE)

def create_venv():
    os.makedirs(VENV_BASE, exist_ok=True)
    if not os.path.exists(VENV_DIR):
        print(f"[i] Virtualenv yok, oluşturuluyor: {VENV_DIR}")
        subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
    else:
        print(f"[i] Virtualenv zaten mevcut: {VENV_DIR}")

def install_requirements():
    python_exe = os.path.join(VENV_DIR, "Scripts", "python.exe") if IS_WINDOWS else os.path.join(VENV_DIR, "bin", "python")

    print(f"[i] Req path: {req_path}")
    print(f"[i] Python exe: {python_exe}")

    if os.path.exists(req_path):
        print("[i] Requirements yükleniyor...")
        try:
            subprocess.check_call([python_exe, "-m", "pip", "install", "-r", req_path])
        except subprocess.CalledProcessError as e:
            print(f"[!] Pip yükleme hatası: {e}")
    else:
        print("[!] requirements.txt bulunamadı!")

def run_main():
    python_exe = os.path.join(VENV_DIR, "Scripts", "python.exe") if IS_WINDOWS else os.path.join(VENV_DIR, "bin", "python")
    if os.path.exists("main.py"):
        subprocess.check_call([python_exe, "main.py"])
    else:
        print("[!] main.py bulunamadı!")

def main():
    create_venv()
    install_requirements()
    run_main()

if __name__ == "__main__":
    main()
