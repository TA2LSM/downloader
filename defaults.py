import os, sys, platform

PROJECT_NAME = "Downloader"
REQ_FILE = "requirements.txt"
DEBUG = True
USE_UC_BROWSER = True

# Derlenmiş exe çalışıyorsa exe'nin dizini, değilse script'in dizini
# BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
DIST_DIR = os.path.join(os.getcwd(), "dist")
CHROMIUM_DIR = os.path.join(DIST_DIR, "chromium")
DRIVER_DIR = os.path.join(DIST_DIR, "driver")

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"}

# CHROMIUM_LATEST_API_VERSIONS = "https://omahaproxy.appspot.com/all.json"
CHROMIUM_API_VERSIONS = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json"
CHROMIUM_API_WITH_DOWNLOADS = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
CHROMEDRIVER_STORAGE = "https://chromedriver.storage.googleapis.com"

DEFAULT_CHUNK_SIZE = 1024*1024  # 1 MB
DEFAULT_CHROME_DRIVER_MIN_SIZE = 5242880
DEFAULT_CHROMIUM_MIN_SIZE = 20971520

DEFAULT_TIME_BEFORE_PAGE_LOAD = 10
DEFAULT_MAX_WAIT_TIME = 15
DEFAULT_TIME_BEFORE_FILE_ERASE = 2

# Sistem bilgileri
_system = sys.platform
_machine = platform.machine().lower()

# OS bayrakları
IS_WINDOWS = _system.startswith("win")
IS_LINUX = _system.startswith("linux")
IS_MAC = _system == "darwin"

# Mimari (normalize)
if _machine in ("x86_64", "amd64"):
    ARCH = "x64"
elif _machine in ("arm64", "aarch64"):
    ARCH = "arm64"
else:
    ARCH = "unknown"

# Platform key (UC Chromium için)
if IS_WINDOWS:
    PLATFORM_KEY = "win64"
elif IS_LINUX:
    PLATFORM_KEY = "linux64"
elif IS_MAC:
    PLATFORM_KEY = "mac-arm64" if ARCH == "arm64" else "mac-x64"
else:
    PLATFORM_KEY = None

# Chromium binary isimleri (OS'e göre)
CHROMIUM_BINARY = "chrome.exe" if IS_WINDOWS else "chrome"
CHROMIUM_DIRNAME = (
    "chrome-win64" if IS_WINDOWS else
    "chrome-linux64" if IS_LINUX else
    ("chrome-mac" if ARCH == "x64" else "chrome-mac-arm64")
)

# Debug çıktısı (istersen aç/kapat)
if __name__ == "__main__":
    print("OS:", _system)
    print("ARCH:", ARCH)
    print("IS_WINDOWS:", IS_WINDOWS)
    print("IS_LINUX:", IS_LINUX)
    print("IS_MAC:", IS_MAC)
    print("PLATFORM_KEY:", PLATFORM_KEY)
    print("CHROMIUM_BINARY:", CHROMIUM_BINARY)
    print("CHROMIUM_DIRNAME:", CHROMIUM_DIRNAME)

# ----------------------------
# Folders
# ----------------------------
# cwd = os.getcwd()

# if IS_WINDOWS:
#     chromedriver_path = os.path.join(cwd, "chromedriver.exe")
#     chromium_dir = os.path.join(cwd, "chromium")
#     chromium_path = os.path.join(chromium_dir, "chrome-win", "chrome.exe")
# elif IS_MAC:
#     chromedriver_path = os.path.join(cwd, "chromedriver_mac")
#     chromium_dir = os.path.join(cwd, "chromium")
#     chromium_path = os.path.join(chromium_dir, "chrome-mac", "Chromium.app/Contents/MacOS/Chromium")
# elif IS_LINUX:
#     chromedriver_path = os.path.join(cwd, "chromedriver_linux")
#     chromium_dir = os.path.join(cwd, "chromium")
#     chromium_path = os.path.join(chromium_dir, "chrome-linux", "chrome")

# if IS_WINDOWS:
#   try:
#       import win32api
#   except ImportError:
#       win32api = None